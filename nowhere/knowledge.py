"""Knowledge encounters -- local facts via offline Wikipedia ZIM file."""

from __future__ import annotations

import asyncio
import json
import logging
import pathlib
import random as _random
import re
import urllib.parse

logger = logging.getLogger(__name__)

_ZIM_PATH = pathlib.Path(__file__).resolve().parent / "data" / "packs" / "wikipedia_zh_mini.zim"
_NAMESPACE = "C"  # articles namespace in this ZIM
_WIKI_BASE = "https://zh.wikipedia.org/wiki/"
_MAX_EXTRACT = 500  # chars

_zim = None  # lazy singleton

# --- Local knowledge base -------------------------------------------------
_DATA = pathlib.Path(__file__).resolve().parent / "data"

_KB_FILES = [
    "knowledge.json",
]

_local_kb: dict[str, dict] | None = None


def _load_local_kb() -> dict[str, dict]:
    """Load and merge all local knowledge base JSON files (cached)."""
    global _local_kb
    if _local_kb is None:
        _local_kb = {}
        for fname in _KB_FILES:
            fp = _DATA / fname
            if fp.exists():
                data = json.loads(fp.read_text(encoding="utf-8"))
                _local_kb.update(data)
    return _local_kb


def _format_kb_entry(name: str, entry: dict) -> dict:
    """Format a local KB entry as a knowledge result.

    Two shapes live in ``knowledge.json``:
    * Country entries: ``{一句话, 特色, ...}`` → join those fields.
    * Card entries:   ``{card: [{topic, content, ...}, ...]}`` → join the
      ``content`` of each card so the prose is readable.
    Mixed entries (both shapes) are concatenated.
    """
    parts: list[str] = []
    for key in ["一句话", "特色", "语言", "首都"]:
        if key in entry and isinstance(entry[key], str):
            parts.append(entry[key])
    # 海拔是结构化数据（如 "71m"），原样拼接会漏进散文，转成自然句
    alt = entry.get("海拔")
    if isinstance(alt, str) and alt:
        m = re.match(r"([\d.]+)\s*m", alt.strip())
        parts.append(f"海拔约 {m.group(1)} 米" if m else alt)
    cards = entry.get("card")
    if isinstance(cards, list):
        for c in cards:
            if isinstance(c, dict):
                content = c.get("content")
                if isinstance(content, str) and content:
                    parts.append(content)
    # 各字段自带句号, join 前去掉, 避免 "。。"
    extract = "。".join(p.rstrip("。") for p in parts if p)
    return {
        "title": name,
        "extract": extract,
        "url": "",
        "source": "local_kb",
    }

# Common short queries → known article titles that should exist in the ZIM
_COMMON_TOPICS: dict[str, str] = {
    "火山": "火山",
    "地震": "地震",
    "河流": "河",
    "山": "山",
    "海": "海",
    "沙漠": "沙漠",
    "森林": "森林",
    "冰川": "冰川",
    "雨林": "热带雨林",
    "草原": "草原",
    "湖": "湖",
    "瀑布": "瀑布",
    "峡谷": "峡谷",
    "岛屿": "岛",
    "半岛": "半岛",
}


def _get_zim():
    """Open the ZIM file once and cache."""
    global _zim
    if _zim is not None:
        return _zim
    if not _ZIM_PATH.exists():
        logger.warning("ZIM file not found: %s", _ZIM_PATH)
        return None
    try:
        # zimply imports gevent which calls monkey.patch_all().
        # On exit, gevent's cleanup throws KeyError from destroyed thread state.
        # Suppress stderr during atexit to hide the traceback.
        import atexit
        import os
        import sys

        def _suppress_gevent_cleanup():
            try:
                sys.stderr = open(os.devnull, "w")
            except Exception:
                pass

        atexit.register(_suppress_gevent_cleanup)

        from zimply.zimply import ZIMFile
        _zim = ZIMFile(str(_ZIM_PATH), encoding="utf-8")
        return _zim
    except Exception as exc:
        logger.warning("Failed to open ZIM file: %s", exc)
        return None


def _strip_html(html: str) -> str:
    """Extract plain text from the first non-empty <p> block of a Wikipedia HTML article."""
    # Remove <style> and <script> blocks entirely
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML comments
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    # Try each <p>...</p> block until we find one with real text
    for m in re.finditer(r"<p[^>]*>(.*?)</p>", html, re.DOTALL):
        text = m.group(1)
        # Remove <sup>...</sup> (references)
        text = re.sub(r"<sup[^>]*>.*?</sup>", "", text, flags=re.DOTALL)
        # Remove all remaining tags
        text = re.sub(r"<[^>]+>", "", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            return text
    return ""


def _article_title_from_html(html: str) -> str | None:
    """Extract the <title> content from the HTML."""
    m = re.search(r"<title>([^<]+)</title>", html)
    return m.group(1).strip() if m else None


async def about(lat: float, lon: float, topic: str) -> dict | None:
    """Return a Wikipedia article from the offline ZIM, or *None*.

    Parameters
    ----------
    topic:
        Search filter.  If non-empty, look up the article by that title.
        If empty, try to find the nearest named place from *lat/lon*.
    """
    title = topic.strip() if topic else ""
    place_name = ""  # resolved below if needed

    # --- 1. Try local knowledge base first ---
    kb = _load_local_kb()

    # Exact match on topic
    if title and title in kb:
        return _format_kb_entry(title, kb[title])

    # Fuzzy match (contains): 只允许"查询词是条目名的子串"。
    # 反向(条目名是查询词子串)会让组合查询"洛杉矶 富士山"误命中"洛杉矶"。
    if title:
        for name, entry in kb.items():
            if title in name:
                return _format_kb_entry(name, entry)

    # 只在不带话题（"问问这里的事"）时才按坐标兜底到当前地名。
    # 指定了话题（如"富士山"）但没查到, 交给 ask_impl 的组合查询/不知道。
    if not title:
        place_name = await _resolve_place_name(lat, lon)
        if place_name and place_name in kb:
            return _format_kb_entry(place_name, kb[place_name])

    # --- 2. Fall back to ZIM lookup ---
    if not title:
        if not place_name:
            return None
        title = place_name

    # ZIM 加载可能很慢（3.3GB），用线程+超时保护
    try:
        zim = await asyncio.wait_for(asyncio.to_thread(_get_zim), timeout=8.0)
    except (asyncio.TimeoutError, Exception):
        return None
    if zim is None:
        return None

    # Strategy 1: Try direct lookup
    result = _try_zim_lookup(zim, title)
    if result is not None:
        return result

    # Strategy 2: Try URL-encoded title (ZIM may store URLs encoded)
    encoded = urllib.parse.quote(title, safe="")
    if encoded != title:
        result = _try_zim_lookup(zim, encoded)
        if result is not None:
            return result

    # Strategy 3: Try with underscores instead of spaces
    if " " in title:
        result = _try_zim_lookup(zim, title.replace(" ", "_"))
        if result is not None:
            return result

    # Strategy 4: Check _COMMON_TOPICS for known article titles
    if title in _COMMON_TOPICS:
        mapped = _COMMON_TOPICS[title]
        if mapped != title:
            result = _try_zim_lookup(zim, mapped)
            if result is not None:
                return result

    # Strategy 5: Try common Wikipedia disambiguation / related suffixes
    for suffix in (" (地理)", " (地质学)", " (消歧義)", "地貌", "地形"):
        result = _try_zim_lookup(zim, title + suffix)
        if result is not None:
            return result

    # Strategy 6: combine with nearest place name (reuse already-resolved name)
    place = place_name
    if place and place != title:
        for combo in (f"{place} {title}", f"{title}_{place}"):
            result = _try_zim_lookup(zim, combo)
            if result is not None:
                return result

    # Strategy 7: Try ZIM index search for titles containing the query
    if len(title) >= 2:
        try:
            matches = zim.suggest(title)
            if matches:
                # suggest returns a list of title strings
                for match_title in matches[:5]:
                    if match_title and match_title != title:
                        result = _try_zim_lookup(zim, match_title)
                        if result is not None:
                            return result
        except Exception as exc:
            logger.debug("ZIM suggest failed for %r: %s", title, exc)

    # Strategy 8: Try fulltext search if available
    if len(title) >= 2:
        try:
            search_results = zim.search(title, 5)
            if search_results:
                for entry in search_results:
                    entry_title = entry if isinstance(entry, str) else getattr(entry, "title", None) or getattr(entry, "url", "")
                    if entry_title and entry_title != title:
                        result = _try_zim_lookup(zim, entry_title)
                        if result is not None:
                            return result
        except Exception as exc:
            logger.debug("ZIM search failed for %r: %s", title, exc)

    return None


def _try_zim_lookup(zim, title: str) -> dict | None:
    """Attempt a single ZIM article lookup.  Returns result dict or None."""
    art = zim.get_article_by_url(_NAMESPACE, title)
    if art is None or art.data is None:
        return None

    html = art.data.decode("utf-8", errors="replace") if isinstance(art.data, bytes) else art.data

    display_title = _article_title_from_html(html) or title
    extract = _strip_html(html)
    if not extract:
        return None

    if len(extract) > _MAX_EXTRACT:
        # Cut at sentence boundary if possible
        cut = extract[:_MAX_EXTRACT]
        last_period = max(cut.rfind("。"), cut.rfind("．"), cut.rfind(". "), cut.rfind("."))
        extract = cut[: last_period + 1] if last_period > 100 else cut + "..."

    url = _WIKI_BASE + urllib.parse.quote(title, safe="")

    return {
        "title": display_title,
        "extract": extract,
        "url": url,
    }


async def _resolve_place_name(lat: float, lon: float) -> str:
    """Get the nearest named place for given coordinates."""
    try:
        from nowhere import places
        nearby = places.nearby(lat, lon, radius_km=20, limit=1)
        if nearby:
            return nearby[0]["name"]
    except Exception as exc:
        logger.debug("places.nearby failed: %s", exc)
    return ""


# ── 声口层: voice processing for knowledge results ────────────────

_MAX_VOICE_LEN = 150

_WIKI_OPENING_RE = re.compile(
    r'^[一-鿿·]{1,20}(?:是|位于|坐落于|地处|属于|为)'
)

_DISTANCING_LINES: list[str] = [
    "这是书上说的。",
    "书里这么写的,对不对你到了再看。",
    "文字是这么记的。",
]


def _t2s(text: str) -> str:
    """Traditional → Simplified Chinese (opencc t2s, same as art.py)."""
    try:
        import opencc
        converter = opencc.OpenCC("t2s")
        return converter.convert(text)
    except Exception:
        return text


def _strip_wiki_opening(text: str) -> str:
    """Replace encyclopedia-style opening ('XX是…' / 'XX位于…') with natural entry."""
    m = _WIKI_OPENING_RE.match(text)
    if m:
        text = text[m.end():]
        text = text.lstrip('，,。 ')
    return text


def _truncate_at_boundary(text: str, max_len: int = _MAX_VOICE_LEN) -> str:
    """Cut to <=max_len chars, preferring sentence boundaries."""
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    for sep in ('。', '！', '？', '；', '.', '!', '?'):
        idx = cut.rfind(sep)
        if idx > 50:
            return cut[:idx + 1]
    return cut + "……"


def voice_layer(text: str, rng: _random.Random | None = None) -> str:
    """声口层: t2s, strip wiki tone, truncate, add distancing line.

    Call this on every ZIM/KB extract before returning to the user.
    """
    if not text:
        return text
    text = _t2s(text)
    text = _strip_wiki_opening(text)
    text = _truncate_at_boundary(text)
    if rng is None:
        rng = _random.Random()
    text += rng.choice(_DISTANCING_LINES)
    return text


def has_knowledge(topic: str) -> bool:
    """Quick sync check: does the local knowledge base have content for *topic*?

    Used by walk_impl to decide whether to hint 'ask 能问出更多'.
    Only checks local_kb (fast, no ZIM access).
    """
    kb = _load_local_kb()
    if not topic:
        return False
    if topic in kb:
        return True
    for name in kb:
        if topic in name:
            return True
    return False
