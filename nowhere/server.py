"""Nowhere MCP server -- wires all modules into 8 tools.

Usage:
    nowhere                       # stdio MCP server (also: python -m nowhere.server)
    nowhere --web                 # stdio MCP + web observer (auto-picked port)
    nowhere --web 8080            # stdio MCP + web observer on port 8080

With uvx (no install needed):
    uvx nowhere-mcp --web
    uvx nowhere-mcp --web 8080
"""

from __future__ import annotations

import argparse
import asyncio
import functools
import math
import os
import random
import re
import threading
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from timezonefinder import TimezoneFinder

from fastmcp import FastMCP

from nowhere import (
    art,
    country,
    describe,
    encounters,
    geocode,
    hydrology,
    humanities,
    journeys,
    knowledge,
    landing,
    life,
    listen as listen_mod,
    localcolor,
    marks as marks_mod,
    people as people_mod,
    placememory,
    places,
    poster,
    providers,
    radio,
    salience,
    sky,
    soundscape,
    state as state_mod,
    terrain,
    travelers as travelers_mod,
    walk as walk_mod,
    water,
    weather,
)

mcp = FastMCP("nowhere")

# ── Module-level state ───────────────────────────────────────────────

_state: state_mod.WorldState = state_mod.WorldState()
_door_lock = asyncio.Lock()  # open_door 竞态保护:一次只开一扇门
_action_lock = asyncio.Lock()  # serialize mutations of the shared journey state
_postcard_counter: int = 0  # 跨门的明信片编号,不走 state 重置
_rng: random.Random = (
    random.Random(int(os.environ["NOWHERE_SEED"]))
    if os.environ.get("NOWHERE_SEED")
    else random.Random()  # 生产真随机;测试用 NOWHERE_SEED 锁
)
_web_port: int | None = None  # reserved for Task 11
_web_url_announced: bool = False  # open_door 首次告知用户旁观者地址
_tf: TimezoneFinder = TimezoneFinder()
_recent_salience_kinds: set[str] = set()  # Bug 4: track recent salience kinds
_cotraveler_encounter_counts: dict[str, int] = {}  # how many times we've seen each traveler's footprints
_cotraveler_meeting_log: dict[str, str] = {}  # pair_key -> last meeting ISO timestamp


def _serialized_action(func):
    """Serialize mutations of the process-wide journey state."""
    @functools.wraps(func)
    async def wrapped(*args: Any, **kwargs: Any) -> dict:
        async with _action_lock:
            return await func(*args, **kwargs)
    return wrapped


# ── External content sanitization (second defense) ───────────────────

_RE_CODE_BLOCK = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_RE_INLINE_CODE = re.compile(r"`([^`]{1,200})`")
_RE_TRIPLE_BACKTICK = re.compile(r"`{1,3}")


def _strip_code_markers(text: str) -> str:
    """Strip backticks and code block markers from external text."""
    text = _RE_CODE_BLOCK.sub("", text)
    text = _RE_INLINE_CODE.sub(r"\1", text)
    text = _RE_TRIPLE_BACKTICK.sub("", text)
    return text.strip()


def _sanitize_external(text: str) -> str:
    """Second defense: sanitize external human-entered text before rendering.

    - Strip fenced code blocks (```...```)
    - Strip inline code backticks
    - Wrap in explicit delimiters so the AI player can distinguish
      "someone's message" from system narrative
    """
    return f"「{_strip_code_markers(text)}」"


# ── Bearing mapping ──────────────────────────────────────────────────

_BEARING_MAP: dict[str, float] = {
    "N": 0, "NE": 45, "E": 90, "SE": 135,
    "S": 180, "SW": 225, "W": 270, "NW": 315,
    "NORTH": 0, "NORTHEAST": 45, "EAST": 90, "SOUTHEAST": 135,
    "SOUTH": 180, "SOUTHWEST": 225, "WEST": 270, "NORTHWEST": 315,
    "北": 0, "东北": 45, "东": 90, "东南": 135,
    "南": 180, "西南": 225, "西": 270, "西北": 315,
}

_SEMANTIC_MAP: dict[str, str] = {
    "uphill": "uphill", "toward_sea": "toward_sea", "forward": "forward",
    "上山": "uphill", "向海": "toward_sea", "向前": "forward",
    "上坡": "uphill", "下海": "toward_sea",
}

# ── Quiet variants for look_around ───────────────────────────────────

_QUIET_VARIANTS: list[str] = [
    "周围安静。",
    "四下无人,只有风声。",
    "安静得能听到自己的心跳。",
    "什么声音也没有。世界好像只剩你一个。",
    "这里没有路,也没有人走过的痕迹。",
]

# 留白: 缓存命中且世界没变时的回话——路就是路
_QUIET_WALK = [
    "路就是路。你往前走。",
    "什么也没发生。这也算一种发生。",
    "世界没有更新。",
    "风还是那阵风。",
    "你走你的,世界忙它的。",
    "脚下的路和刚才一样。",
]
_QUIET_WAIT = [
    "时间过去了。光没变。",
    "什么都没变,只有时间变了。",
]


# =====================================================================
# Helpers
# =====================================================================


def _load_scene_file(filename: str) -> dict[str, list[str]]:
    """Load a [城市名] 描述 format file into {city: [descriptions]} dict."""
    cache_key = f"_scene_{filename}"
    if not hasattr(_load_scene_file, cache_key):
        result: dict[str, list[str]] = {}
        fp = describe._SCENE_DIR / f"{filename}.txt"
        if fp.exists():
            for line in fp.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "] " in line:
                    bracket_end = line.index("] ")
                    place = line[1:bracket_end]
                    desc = line[bracket_end + 2:]
                    result.setdefault(place, []).append(desc)
        setattr(_load_scene_file, cache_key, result)
    return getattr(_load_scene_file, cache_key)


def _pick_fresh(pool: list[str], rng: random.Random) -> str | None:
    """从场景池挑一条, 避开最近用过的文本(跨调用去重)。

    全用过就退回整个池子。挑选结果记进 _state.recent_scenes,
    供下次调用和 describe.render 复用。
    """
    if not pool:
        return None
    recent = set(_state.recent_scenes)
    fresh = [t for t in pool if t not in recent]
    if not fresh:
        fresh = pool
    pick = rng.choice(fresh)
    _state.recent_scenes.append(pick)
    _state.recent_scenes = _state.recent_scenes[-10:]
    return pick


def _km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Quick equirectangular distance, good enough for station stickiness."""
    dlat = math.radians(a[0] - b[0])
    lon_delta = (a[1] - b[1] + 180.0) % 360.0 - 180.0
    dlon = math.radians(lon_delta) * math.cos(math.radians((a[0] + b[0]) / 2))
    return 6371.0 * math.sqrt(dlat * dlat + dlon * dlon)


def _last_env_surface() -> str:
    """Read ``surface`` from ``_state.last_env``.

    Current code always writes flat format.  Old saved journeys may still have
    nested ``terrain`` key — both are handled for backward compatibility.
    """
    env = _state.last_env or {}
    nested = env.get("terrain")
    if isinstance(nested, dict) and "surface" in nested:
        return nested["surface"]
    return env.get("surface", "")


def _last_env_terrain_dict() -> dict:
    """Return terrain dict from ``_state.last_env``.

    Current code always writes flat format.  Old saved journeys may still have
    nested ``terrain`` key — both are handled for backward compatibility.
    """
    env = _state.last_env or {}
    nested = env.get("terrain")
    if isinstance(nested, dict):
        return nested
    # Top-level shape — synthesize a terrain dict.
    out: dict = {}
    if "elevation" in env:
        out["elevation"] = env["elevation"]
    if "surface" in env:
        out["surface"] = env["surface"]
    return out


async def _get_radio(lat: float, lon: float) -> dict | None:
    """Sticky radio: reuse the station if we haven't drifted 50km from
    where it was picked. 同一个地方就该是同一个台。"""
    if _state.radio_station is not None and _state.radio_pos is not None:
        if _km((lat, lon), _state.radio_pos) < 50.0:
            return _state.radio_station
    cc = country.country_code_of(lat, lon)
    try:
        station = await asyncio.wait_for(radio.nearest(lat, lon, cc), timeout=8.0)
    except (asyncio.TimeoutError, Exception):
        return None
    if station is not None:
        _state.radio_station = station
        _state.radio_pos = (lat, lon)
    return station


def _parse_bearing(direction: str) -> tuple[float | None, str | None, bool]:
    """Parse direction string into ``(bearing_deg, semantic, invalid)``.

    ``invalid`` is True when the input could not be recognised and was
    silently replaced with "forward".
    """
    d = direction.strip()
    upper = d.upper()
    if upper in _BEARING_MAP:
        return _BEARING_MAP[upper], None, False
    if d in _BEARING_MAP:
        return _BEARING_MAP[d], None, False
    if d in _SEMANTIC_MAP:
        return None, _SEMANTIC_MAP[d], False
    return None, "forward", True


# ── Nearby destinations hint ────────────────────────────────────────

_DEST_TEMPLATES: list[str] = [
    "风从{dir}吹来,那边有{place}。",
    "{dir}方有什么在等着,{place}不远了。",
    "空气里隐约有{place}的方向,往{dir}走试试。",
    "脚下这条路通往{place},就在{dir}边。",
    "{dir}边的地平线上,{place}的轮廓若隐若现。",
    "远处{dir}方,{place}像一个还没讲完的故事。",
]

# ── Density decay: wilderness depth calculation (Card 40) ──────────

def _compute_wilderness_depth_km(lat: float, lon: float) -> float:
    """Compute distance (km) from (lat, lon) to nearest known place or water feature.

    Uses explorable_index.json places and hydrology offline water features.
    Returns 0.0 if within 5km of any known feature, otherwise the distance.
    """
    import json as _json
    import pathlib as _pathlib
    from math import radians, sin, cos, sqrt, atan2

    def _haversine_km(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    min_dist = float("inf")

    # Check explorable_index places
    try:
        fp = _pathlib.Path(__file__).resolve().parent / "data" / "explorable_index.json"
        if fp.exists():
            data = _json.loads(fp.read_text(encoding="utf-8"))
            for name, info in data.get("places", {}).items():
                plat = info.get("lat")
                plon = info.get("lon")
                if plat is not None and plon is not None:
                    d = _haversine_km(lat, lon, plat, plon)
                    if d < min_dist:
                        min_dist = d
    except Exception:
        pass

    # Check offline water features
    try:
        fp = _pathlib.Path(__file__).resolve().parent / "data" / "water_features_offline.json"
        if fp.exists():
            data = _json.loads(fp.read_text(encoding="utf-8"))
            for entry in data.get("entries", []):
                elat = entry.get("lat", 0)
                elon = entry.get("lon", 0)
                d = _haversine_km(lat, lon, elat, elon)
                if d < min_dist:
                    min_dist = d
    except Exception:
        pass

    # If no features found, return a large value
    if min_dist == float("inf"):
        return 1000.0

    return min_dist


# ── Deep wilderness variants (Card 40) ─────────────────────────────

# "荒深档": sky/earth/body only, world quiet but not empty
# Forbidden: "什么都没有" — use light/wind/ground texture
_WILDERNESS_VARIANTS: list[str] = [
    "地平线在四面八方同时弯下去。风从左边来,又从右边来。",
    "云很低,像一块灰色的布盖在世界上。你的影子不见了。",
    "脚下是干裂的泥,裂缝里有蚂蚁在走。它们比你忙。",
    "远处有什么在反光,走了很久也没走到。可能是石头,可能是水。",
    "风把你的衣服吹得贴在身上。你闻到尘土的味道。",
    "天和地之间只有你。不是孤独,是空旷。",
    "地面是平的,一直平到天边。你的脚步声是唯一的声音。",
    "空气干得嘴唇裂了。你舔了一下,是血的味道。",
]


# ── Deep wilderness procedural features (12 variants) ──────────────

_WILDERNESS_FEATURES: list[str] = [
    "一棵树,不知道为什么长在这里。树干弯了,朝着风的方向。",
    "一段旧路基,石头被磨得光滑。不知道通向哪里。",
    "一个泉眼,水从石头缝里渗出来。你蹲下来喝了一口,凉的。",
    "一堆石头,排成了圈。不知道是人放的还是风吹的。",
    "一根电线杆,歪了,没有电线。不知道什么时候倒的。",
    "一截铁路,铁轨锈了,枕木烂了。草从铁轨缝里长出来。",
    "一个坑,不知道挖来做什么的。坑底有积水,绿色的。",
    "一块水泥板,上面有字,看不清了。你用手擦了擦,还是看不清。",
    "一棵枯树,树皮剥落了,木头是白色的。鸟在上面筑了巢。",
    "一条干涸的河床,石头被水冲得圆圆的。你走在上面,硌脚。",
    "一个土堆,上面长满了草。你绕过去,什么也没有。",
    "一块界碑,字被风沙磨平了。你不知道这里是哪里的边界。",
]


# ── Deep wilderness procedural flesh event (5% after 10+ steps) ────

_WILDERNESS_FLESH_EVENTS: list[str] = [
    "你的手背上有一道伤痕,不知道什么时候划的。血已经干了。",
    "你低头看脚,鞋带散了。你蹲下来系,发现鞋底磨穿了一块。",
    "你的嘴唇裂了。你用舌头舔了一下,咸的。",
    "你发现口袋里有一张纸,皱巴巴的。你展开看,什么也没写。",
    "你的膝盖响了一声。你停下来,等了一会儿,又走了。",
    "你看见自己的影子,比刚才长了。你走了多久了?",
]


def _find_nearby_destinations(lat: float, lon: float, rng) -> str:
    """Return a literary hint about a walkable place within ~20km."""
    import json
    import pathlib as _pathlib
    from math import radians, sin, cos, sqrt, atan2

    def _haversine_km(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    patch_path = _pathlib.Path(__file__).resolve().parent / "data" / "places_patch.json"
    if not patch_path.exists():
        return ""
    try:
        places = json.loads(patch_path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    nearby = []
    for name, coords in places.items():
        if isinstance(coords, dict):
            plat, plon = coords.get("lat"), coords.get("lon")
        elif isinstance(coords, list) and len(coords) >= 2:
            plat, plon = coords[0], coords[1]
        else:
            continue
        if plat is None or plon is None:
            continue
        d = _haversine_km(lat, lon, plat, plon)
        if 0.5 < d <= 20:
            nearby.append((name, d, plat, plon))

    if not nearby:
        return ""

    nearby.sort(key=lambda x: x[1])
    name, d, plat, plon = rng.choice(nearby[:3])

    # 算方位
    import math
    bearing = math.degrees(math.atan2(
        math.radians(plon - lon), math.radians(plat - lat)
    )) % 360
    dirs = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
    direction = dirs[int((bearing + 22.5) / 45) % 8]

    template = rng.choice(_DEST_TEMPLATES)
    return template.format(place=name, dir=direction)


# ── Water feature nearest-point lookup ──────────────────────────────

def _find_nearest_water_feature(name: str, lat: float, lon: float) -> dict | None:
    """Find the nearest point on a named water feature from the offline database."""
    import json
    import pathlib as _pathlib

    fp = _pathlib.Path(__file__).resolve().parent / "data" / "water_features_offline.json"
    if not fp.exists():
        return None
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return None

    entries = data.get("entries", [])
    best = None
    best_dist = float("inf")

    for entry in entries:
        entry_name = entry.get("name", "")
        # 名称匹配（包含关系）
        if name not in entry_name and entry_name not in name:
            continue
        elat, elon = entry.get("lat", 0), entry.get("lon", 0)
        radius = entry.get("radius_km", 50)
        # 简化距离：用条目中心点距离减去半径（近似最近距离）
        d = places._haversine_km(lat, lon, elat, elon)
        d_approx = max(0, d - radius)
        if d_approx < best_dist:
            best_dist = d_approx
            # 用当前坐标和条目中心的连线上的点作为最近点（简化）
            if d > 0:
                ratio = min(radius / d, 1.0)
                near_lat = lat + (elat - lat) * ratio
                near_lon = lon + (elon - lon) * ratio
            else:
                near_lat, near_lon = elat, elon
            best = {"lat": near_lat, "lon": near_lon, "type": entry.get("type", "水域")}

    return best


def _offline_water_nearby(lat: float, lon: float, radius_km: float = 50) -> list[dict]:
    """Look up offline water features near (lat, lon).

    Returns list sorted by distance, each entry has name, type, distance_km,
    bearing, note, label.
    """
    return hydrology.offline_water_nearby(lat, lon, radius_km=radius_km)


def _find_river_segment(name: str, segment_hint: str = "") -> dict | None:
    """Find a specific river segment from offline data.

    segment_hint: e.g. "上海段", "入海口", "三峡段". Empty = scenic default.
    Returns {"lat": float, "lon": float, "segment_name": str} or None.
    """
    import json
    import pathlib as _pathlib

    fp = _pathlib.Path(__file__).resolve().parent / "data" / "water_features_offline.json"
    if not fp.exists():
        return None
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return None

    # Synonym mapping: user-facing terms → segment note keywords
    _SEGMENT_SYNONYMS: dict[str, list[str]] = {
        "入海口": ["上海", "东营"],
        "入海": ["上海", "东营"],
        "河口": ["上海", "东营"],
        "出海口": ["上海", "东营"],
        "上游": ["宜宾", "重庆", "兰州", "银川"],
        "源头": ["宜宾", "重庆"],
        "三峡": ["三峡", "宜昌"],
        "下游": ["南京", "九江", "武汉"],
    }

    entries = data.get("entries", [])
    hint_lower = segment_hint.lower() if segment_hint else ""

    # Expand hint via synonyms
    hint_keywords = [hint_lower] if hint_lower else []
    if hint_lower in _SEGMENT_SYNONYMS:
        hint_keywords.extend(_SEGMENT_SYNONYMS[hint_lower])

    best = None
    best_score = -1

    for entry in entries:
        ename = entry.get("name", "")
        note = (entry.get("note") or "").lower()

        # Match the base river name
        if name not in ename and ename not in name:
            continue

        if hint_keywords:
            # Must match at least one hint keyword in note
            if not any(kw in note for kw in hint_keywords):
                continue
            # Score: prefer exact hint match, then synonym match
            if hint_lower in note:
                score = 100 + len(note)
            else:
                score = len(note)
        else:
            # No hint: prefer scenic segments (三峡, Gorges, etc.)
            scenic = any(s in note for s in ("三峡", "gorge", "scenic", "宜昌"))
            score = 100 if scenic else 0

        if score > best_score:
            best_score = score
            best = {
                "lat": entry.get("lat", 30.7),
                "lon": entry.get("lon", 111.0),
                "segment_name": ename + (" " + entry["note"] if entry.get("note") else ""),
            }

    return best


def _compute_river_direction(water_features: list[dict], lat: float, lon: float) -> tuple[float, float] | None:
    """Compute approximate river flow direction from consecutive offline segments.

    Returns (dx, dy) unit vector of downstream direction, or None.
    """
    # Collect names of nearby rivers
    river_names = set()
    for f in water_features:
        if f.get("type") == "river":
            river_names.add(f.get("name", ""))
    if not river_names:
        return None

    import json
    import pathlib as _pathlib
    fp = _pathlib.Path(__file__).resolve().parent / "data" / "water_features_offline.json"
    if not fp.exists():
        return None
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return None

    # Find two closest consecutive segments of the same river
    for rname in river_names:
        segs = []
        for entry in data.get("entries", []):
            if entry.get("name") != rname:
                continue
            elat = entry.get("lat", 0)
            elon = entry.get("lon", 0)
            d = _km((lat, lon), (elat, elon))
            segs.append((d, elat, elon))
        segs.sort()
        if len(segs) >= 2:
            _, lat1, lon1 = segs[0]
            _, lat2, lon2 = segs[1]
            dx = lon2 - lon1
            dy = lat2 - lat1
            mag = math.sqrt(dx * dx + dy * dy)
            if mag > 0:
                return (dx / mag, dy / mag)
    return None


def _river_alignment_text(
    walk_bearing_deg: float | None,
    river_dir: tuple[float, float] | None,
    rng: random.Random,
) -> str:
    """Generate narrative text for walking along/across a river.

    walk_bearing_deg: walking direction in degrees (0=N, 90=E).
    river_dir: (dx, dy) unit vector of downstream direction.
    Returns narrative text or empty string.
    """
    if walk_bearing_deg is None or river_dir is None:
        return ""

    # Convert walking bearing to unit vector
    walk_rad = math.radians(walk_bearing_deg)
    walk_dx = math.sin(walk_rad)
    walk_dy = math.cos(walk_rad)

    # Dot product with river direction
    dot = walk_dx * river_dir[0] + walk_dy * river_dir[1]

    if abs(dot) > 0.7:
        # Walking along river
        if dot > 0:
            variants = [
                "江水和你一个方向,它走得比你稳。",
                "你顺着江走。水声一直在右边,不远不近。",
                "你和江往同一个方向去。它比你快,但你不在乎。",
                "沿江走,水声是你的节拍器。不急。",
            ]
        else:
            variants = [
                "你逆着江走。水声迎面过来,一步一步。",
                "江从你对面来。你走一步,它推一步。",
                "你和江对着走。它不停,你也不停。",
                "逆流。风从上游吹下来,带着水汽。",
            ]
        return rng.choice(variants)
    elif abs(dot) < 0.3:
        # Walking across river
        variants = [
            "你横着江的走向走。水声从侧面流过。",
            "你垂直于江面走。每走一步,水声换个方位。",
            "横渡的方向。江在你左边,又到了右边。",
        ]
        return rng.choice(variants)

    return ""


# ── Walk discovery system ───────────────────────────────────────────

_DISCOVERY_CACHE: list[str] | None = None

_SURFACE_DESC_SERVER: dict[str, str] = {
    "rock": "岩石",
    "sand": "沙",
    "snow": "积雪",
    "ice": "冰面",
    "forest": "林地",
    "grass": "草地",
    "urban": "硬化路面",
    "bare": "碎石",
    "wetland": "湿地",
    "water_ocean": "海面",
    "water_fresh": "水面",
}


def _load_discovery_scenes() -> list[str]:
    """Load walk discovery scenes from scene_walk_discovery.txt.

    Uses describe._load_scenes which strips biome tags (#林 #山 etc.)
    from line starts for backward-compatible rendering.
    """
    global _DISCOVERY_CACHE
    if _DISCOVERY_CACHE is None:
        _DISCOVERY_CACHE = describe._load_scenes("walk_discovery")
    return _DISCOVERY_CACHE


def _terrain_transition_text(
    last_surface: str | None, current_surface: str, rng: random.Random
) -> str:
    """Describe the transition between two surface types."""
    if not last_surface or last_surface == current_surface:
        return ""
    last_desc = _SURFACE_DESC_SERVER.get(last_surface, last_surface)
    curr_desc = _SURFACE_DESC_SERVER.get(current_surface, current_surface)
    transitions = [
        f"地面从{last_desc}变成了{curr_desc}。",
        f"脚下的{last_desc}不见了，现在是{curr_desc}。",
        f"从{last_desc}走到了{curr_desc}上。",
        f"路变了，{last_desc}换成了{curr_desc}。",
    ]
    return rng.choice(transitions)


_SURFACE_TO_DISCOVERY_BIOME: dict[str, str] = {
    "forest": "forest", "grass": "grassland", "sand": "desert",
    "bare": "desert", "rock": "mountain", "snow": "tundra",
    "ice": "tundra", "water_ocean": "ocean", "water_fresh": "water",
    "urban": "urban", "wetland": "water",
}

# Map biome names to discovery tag sets
_BIOME_TO_DISCOVERY_TAGS: dict[str, set[str]] = {
    "forest": {"#林"}, "grassland": {"#林"}, "rainforest": {"#林"},
    "desert": {"#漠"}, "tundra": {"#极"},
    "mountain": {"#山"}, "coast": {"#海"}, "island": {"#海"},
    "city": {"#城"}, "urban": {"#城"},
    "volcano": {"#山"},
}


def _pick_discovery(rng: random.Random) -> str:
    """Pick a random discovery scene line, filtered by biome tags and altitude.

    Uses biome tags from scene_walk_discovery.txt for filtering.
    Falls back to surface-to-biome mapping if biome is not set.
    """
    pool = _load_discovery_scenes()
    if not pool:
        return ""

    biome = _state.biome or ""
    surface = _last_env_surface()
    elev = (_state.last_env or {}).get("elevation", 0)

    # Determine target biome from biome or surface mapping
    target_biome = biome
    if not target_biome and surface:
        target_biome = _SURFACE_TO_DISCOVERY_BIOME.get(surface, "")

    # Tag-based filtering: prefer scenes matching current biome
    tags_list = describe._BIOME_TAGS_CACHE.get("walk_discovery", [])
    if tags_list and len(tags_list) == len(pool) and target_biome:
        target_tags = _BIOME_TO_DISCOVERY_TAGS.get(target_biome, set())
        if target_tags:
            # Priority: scenes with matching tags
            matched = [(s, t) for s, t in zip(pool, tags_list) if t & target_tags]
            untagged = [(s, t) for s, t in zip(pool, tags_list) if not t]
            if matched:
                # 70% chance to use matched, 30% to use untagged (universal fallback)
                if rng.random() < 0.7 or not untagged:
                    pool = [s for s, _ in matched]
                else:
                    pool = [s for s, _ in untagged]

    # Keyword-based fallback filtering for edge cases
    water_keywords = ["瀑布", "溪", "河", "湖", "海", "水帘", "湿地", "溪水"]
    if biome in ("desert",) or surface in ("sand", "bare"):
        pool = [s for s in pool if not any(k in s for k in water_keywords)]

    ice_keywords = ["冰", "雪", "冻", "霜", "冰湖", "冰面"]
    if biome in ("desert", "rainforest") or surface in ("sand", "bare"):
        pool = [s for s in pool if not any(k in s for k in ice_keywords)]

    if biome not in ("coast", "island"):
        pool = [s for s in pool if "海边" not in s and "灯塔" not in s]

    if elev > 3000:
        high_altitude_bad = ["公园", "湖面", "鸭子", "水泥地", "人行道", "路灯", "便利店", "地铁", "小区"]
        pool = [s for s in pool if not any(k in s for k in high_altitude_bad)]

    if not pool:
        return ""
    return rng.choice(pool)


# ── Narrative continuity system ──────────────────────────────────────

_DIRECTION_LABELS: dict[float, str] = {
    0: "北", 45: "东北", 90: "东", 135: "东南",
    180: "南", 225: "西南", 270: "西", 315: "西北",
}

_TIME_FLOW_LINES: list[str] = [
    "太阳往西移了一点。",
    "天色暗了一些。",
    "影子变长了。",
    "风向变了。",
    "云层厚了一些。",
    "光线柔和了下来。",
]

_BODY_STATE_LINES: list[str] = [
    "你的嘴唇上有一层盐。",
    "你开始出汗了。",
    "你的腿有点酸。",
    "你深吸了一口气。",
    "你舔了一下嘴唇，干的。",
    "你的脚底有点疼。",
    "你擦了一下额头上的汗。",
]


def _bearing_to_label(bearing_deg: float | None, semantic: str | None) -> str | None:
    """Convert bearing degrees or semantic direction to a Chinese label."""
    if bearing_deg is not None:
        key = round(bearing_deg / 45) * 45 % 360
        return _DIRECTION_LABELS.get(key)
    if semantic == "uphill":
        return "上山"
    if semantic == "toward_sea":
        return "海边"
    return None


def _build_walk_narrative(
    step_result: dict,
    env: dict,
    bearing_deg: float | None,
    semantic: str | None,
    rng: random.Random,
) -> str:
    """Build a continuous narrative opener for this walk step.

    Reads and updates ``_state.narrative`` to produce text that connects
    this step to the previous one, instead of independent fragments.
    """
    parts: list[str] = []
    narrative = _state.narrative

    # ── 1. Direction ──────────────────────────────────────────────────
    new_dir = _bearing_to_label(bearing_deg, semantic)
    if new_dir and new_dir != narrative.get("direction"):
        if narrative.get("direction"):
            parts.append(f"你转身往{new_dir}走。")
        else:
            parts.append(f"你往{new_dir}走了几步。")
        narrative["direction"] = new_dir
        narrative["distance_walked"] = 0
    elif new_dir and not narrative.get("direction"):
        narrative["direction"] = new_dir

    # ── 2. Terrain transition ─────────────────────────────────────────
    prev_surface = _state.last_surface
    curr_surface = step_result.get("new_surface", env.get("surface", ""))
    if prev_surface and prev_surface != curr_surface:
        last_desc = _SURFACE_DESC_SERVER.get(prev_surface, prev_surface)
        curr_desc = _SURFACE_DESC_SERVER.get(curr_surface, curr_surface)
        slope = step_result.get("slope_deg", 0)
        if slope > 15:
            parts.append(f"路开始爬升，地面从{last_desc}变成了{curr_desc}。")
        else:
            parts.append(f"地面从{last_desc}变成了{curr_desc}。")

    # ── 3. Distance ───────────────────────────────────────────────────
    dist_km = step_result.get("dist_km", 2.0)
    narrative["distance_walked"] += dist_km * 1000
    walked = narrative["distance_walked"]
    if walked > 10000:
        parts.append(f"你已经走了{walked / 1000:.0f}公里了。回头,来时的路已经看不见。")
        narrative["distance_walked"] = 0
    elif walked > 5000 and rng.random() < 0.3:
        parts.append(rng.choice([
            "脚下的路又延伸了一截。",
            "又走出几公里,路还在前面。",
            "风里走了一段,路程拉长了。",
        ]))
        narrative["distance_walked"] = 0

    # ── 4. Discovery ──────────────────────────────────────────────────
    if _state.steps_since_discovery >= 2 and rng.random() < 0.4:
        disc = _pick_discovery(rng)
        if disc:
            parts.append(disc)
            narrative["discoveries"].append(disc[:20])
            narrative["last_feature"] = disc[:20]
            # Reset so the next discovery waits another 2+ steps; without this
            # reset the counter only ever grows and discovery fires once.
            _state.steps_since_discovery = 0

    # ── 5. Time flow ──────────────────────────────────────────────────
    if rng.random() < 0.3:
        parts.append(rng.choice(_TIME_FLOW_LINES))

    # ── 6. Body state ─────────────────────────────────────────────────
    if rng.random() < 0.2:
        parts.append(rng.choice(_BODY_STATE_LINES))

    return "".join(parts)


async def _gather_env(lat: float, lon: float, dt: datetime) -> dict[str, Any]:
    """Gather weather / sky / terrain / radio for a position.

    Uses ``asyncio.gather`` with ``return_exceptions=True`` so one failure
    does not block the others.
    """
    # Elevation fetched first so weather can use lapse rate correction
    elev_result = await asyncio.to_thread(terrain.elevation, lat, lon)
    elev: float = elev_result if not isinstance(elev_result, Exception) else 0.0

    # Get local hour for diurnal temperature variation
    local_hour = None
    if dt:
        tz_name = _tf.timezone_at(lat=lat, lng=lon)
        if tz_name:
            local_dt = dt.astimezone(ZoneInfo(tz_name))
            local_hour = local_dt.hour

    tasks: list[Any] = [
        asyncio.to_thread(terrain.surface, lat, lon),
        asyncio.to_thread(sky.sun_moon, lat, lon, dt),
        asyncio.to_thread(sky.visible_sky, lat, lon, dt, _rng),
        asyncio.wait_for(weather.current(lat, lon, elevation=elev, local_hour=local_hour), timeout=10.0),
        _get_radio(lat, lon),
        asyncio.wait_for(hydrology.nearby_water(lat, lon), timeout=5.0),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    def _ok(i: int, default: Any = None) -> Any:
        # BaseException catches CancelledError (not Exception subclass in 3.12)
        return results[i] if not isinstance(results[i], BaseException) else default

    surf: str = _ok(0, "unknown")
    sun_moon_info: dict = _ok(1, {})
    visible_sky_info: dict = _ok(2, {})
    weather_info: dict = _ok(3, {})
    radio_info: dict | None = _ok(4, None)
    water_features: list[dict] = _ok(5, [])

    sky_info: dict = {**sun_moon_info, **visible_sky_info}

    return {
        "elevation": elev,
        "surface": surf,
        "sky": sky_info,
        "weather": weather_info,
        "radio": radio_info,
        "water_features": water_features,
    }


# env 惯性: 3km/30min 内,风还是那个风
_ENV_CACHE_KM = 3.0
_ENV_CACHE_MIN = 30


async def _gather_env_cached(lat: float, lon: float, dt: datetime) -> tuple[dict, bool]:
    """3km/30min 内复用上次 env。返回 (env, 缓存命中?)。"""
    if (
        _state.last_env is not None
        and _state.env_pos is not None
        and _state.env_at is not None
        and dt is not None
        and _km(_state.env_pos, (lat, lon)) < _ENV_CACHE_KM
        and abs((dt - _state.env_at).total_seconds()) < _ENV_CACHE_MIN * 60
    ):
        return _state.last_env, True
    env = await _gather_env(lat, lon, dt)
    _state.last_env = env
    _state.env_pos = (lat, lon)
    if dt is not None:
        _state.env_at = dt
    return env, False


# ── Salience delta helpers ───────────────────────────────────────────


def _weather_delta(old: dict | None, new: dict) -> float:
    if not old:
        return 1.0
    d_temp = abs(new.get("temp_c", 0) - old.get("temp_c", 0)) / 20.0
    d_wind = abs(new.get("wind_ms", 0) - old.get("wind_ms", 0)) / 15.0
    return min(1.0, d_temp + d_wind)


def _terrain_delta(old: dict | None, new: dict) -> float:
    if not old:
        return 1.0
    return min(1.0, abs(new.get("elevation", 0) - old.get("elevation", 0)) / 500.0)


def _sky_delta(old: dict | None, new: dict) -> float:
    if not old:
        return 1.0
    old_phase = old.get("phase", "day")
    new_phase = new.get("phase", "day")
    # phase switch (day <-> night) counts as full delta
    if (old_phase == "day") != (new_phase == "day"):
        return 1.0
    return 0.0


def _build_salience_candidates(
    env: dict[str, Any],
    prev_env: dict[str, Any] | None,
) -> list[dict]:
    """Build salience candidate list from environment data."""
    candidates: list[dict] = []

    # weather
    w = env.get("weather", {})
    if w:
        candidates.append({
            "kind": "weather",
            "delta": _weather_delta((prev_env or {}).get("weather"), w),
            "novelty": 0.2,
            "body_distance": 0.1,
            "payload": w,
        })

    # terrain -- values may be nested under env["terrain"] or at top level
    _t = env.get("terrain", {}) if isinstance(env.get("terrain"), dict) else {}
    t = {
        "surface": env.get("surface", _t.get("surface", "unknown")),
        "elevation": env.get("elevation", _t.get("elevation", 0)),
        "slope_deg": env.get("slope_deg", _t.get("slope_deg", 0)),
        "elevation_delta": env.get("elevation_delta", _t.get("elevation_delta", 0)),
    }
    # prev_env may have terrain nested under "terrain" key, or flat at top level
    _prev_t = (prev_env or {}).get("terrain")
    if not isinstance(_prev_t, dict):
        _prev_t = {"elevation": (prev_env or {}).get("elevation", 0), "surface": (prev_env or {}).get("surface", "")}
    candidates.append({
        "kind": "terrain",
        "delta": _terrain_delta(_prev_t, t),
        "novelty": 0.2,
        "body_distance": 0.1,
        "payload": t,
    })

    # sky
    s = env.get("sky", {})
    if s:
        candidates.append({
            "kind": "sky",
            "delta": _sky_delta((prev_env or {}).get("sky"), s),
            "novelty": 0.2,
            "body_distance": 0.7,
            "payload": s,
        })

    # radio (optional) — 冷却5步 + 只在换台/信号变化时再提。
    # 同台复读时完全排除，避免"KCRW 在播…"每步都占 salience 名额。
    r = env.get("radio")
    if r:
        prev_r = (prev_env or {}).get("radio")
        changed = prev_r is None or (prev_r.get("name") != r.get("name"))
        if changed or _state.radio_steps_since >= 5:
            candidates.append({
                "kind": "radio",
                "delta": 1.0,
                "novelty": 0.4,
                "body_distance": 0.6,
                "payload": r,
            })
            _state.radio_steps_since = 0

    # water features (optional)
    wf = env.get("water_features")
    if wf:
        candidates.append({
            "kind": "water_features",
            "delta": 1.0,
            "novelty": 0.5,
            "body_distance": 0.3,
            "payload": wf,
        })

    return candidates


# =====================================================================
# Tool implementations (_impl) -- testable without MCP protocol
# =====================================================================


async def open_door_impl(to: str | None = None, resume: bool = False, traveler_name: str | None = None) -> dict:
    """Open the door and land somewhere."""
    async with _action_lock:
        async with _door_lock:
            return await _open_door_locked(to, resume=resume, traveler_name=traveler_name)


async def _open_door_locked(to: str | None = None, resume: bool = False, traveler_name: str | None = None) -> dict:
    """Door body, called under _door_lock."""
    global _state, _rng, _recent_salience_kinds

    # ── 0. Multi-journey: save current before switching ────────────────
    farewell_text = ""
    if _state.pos is not None and not resume and to:
        # Generate farewell before leaving
        farewell_text = _generate_farewell(_state, _rng)
        _state.journey_log.append({
            "kind": "farewell",
            "text": farewell_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Save current journey (with farewell in log)
        journeys.save_current(_state)

        # Check if destination matches an existing journey
        existing = journeys.switch(to)
        if existing is not None:
            # Generate return text for the existing journey
            meta = journeys.get_journey_meta(to)
            return_text = _generate_return(existing, meta, _rng)

            _state = existing
            _rng = random.Random(int(os.environ["NOWHERE_SEED"])) if os.environ.get("NOWHERE_SEED") else random.Random()
            _recent_salience_kinds = set()
            place = _state.place_name or to

            response_parts = [farewell_text]
            if return_text:
                response_parts.append(return_text)
            response_parts.append(f"回到了{place}的旅程。上次你在{_state.last_text[:50] if _state.last_text else '走路'}。")

            return {
                "text": "\n".join(response_parts),
                "data": {"position": {"lat": _state.pos[0], "lon": _state.pos[1]}, "resumed": True},
            }

    # ── 1. Locate / restore ────────────────────────────────────────────
    spot: dict | None = None
    restored = False
    if resume:
        saved = state_mod.WorldState.load()
        if saved and saved.pos is not None:
            _state = saved
            restored = True
            global _postcard_counter
            _postcard_counter = max((c.get("id", 0) for c in _state.postcards), default=0)
            lat, lon = _state.pos
            place_name = _state.place_name or "未知之地"

    if not restored and to is None:
        spot = landing.random_spot(_rng)
        # Nudge if landing spot is on water (unless water destination)
        nudged = landing.nudge_if_water(
            spot["lat"], spot["lon"],
            spot.get("name_hint", ""), spot.get("biome", ""),
        )
        spot["lat"] = nudged["lat"]
        spot["lon"] = nudged["lon"]
        if nudged.get("water_landing"):
            spot["water_landing"] = True
        lat, lon = spot["lat"], spot["lon"]
        place_name = spot.get("name_hint", "未知之地")
    elif not restored:
        found_river = False
        mark_entry = marks_mod.get(to)
        if mark_entry:
            lat, lon = mark_entry["lat"], mark_entry["lon"]
            place_name = to
        else:
            h_place = humanities.get_place_coords(to)
            if h_place:
                lat, lon = h_place["lat"], h_place["lon"]
                place_name = to
            else:
                result = await asyncio.wait_for(geocode.lookup(to), timeout=10.0)
                if result is None:
                    # Fallback: try river segment lookup (e.g. "长江 入海口")
                    river_names = ["长江", "黄河", "珠江", "松花江", "淮河", "海河", "辽河"]
                    found_river = False
                    for rname in river_names:
                        if rname in (to or ""):
                            segment_hint = ""
                            parts = (to or "").split()
                            if len(parts) > 1:
                                segment_hint = parts[-1]
                            seg = _find_river_segment(rname, segment_hint)
                            if seg:
                                lat, lon = seg["lat"], seg["lon"]
                                place_name = seg["segment_name"]
                                found_river = True
                                break
                    if not found_river:
                        return {"text": f"找不到「{to}」。", "data": {"error": "not_found"}}
                else:
                    lat, lon = result
                    place_name = to

        # ── River segment awareness: 长江 → nearest scenic segment ──
        if to and "长江" in to and not found_river:
            segment_hint = ""
            parts = to.split()
            if len(parts) > 1:
                segment_hint = parts[-1]
            seg = _find_river_segment("长江", segment_hint)
            if seg:
                lat, lon = seg["lat"], seg["lon"]
                place_name = seg["segment_name"]

    # ── 2. State init ────────────────────────────────────────────────
    if not restored and resume:
        _state = state_mod.WorldState()
        _state.pos = (lat, lon)
        _state.landed_at = datetime.now(timezone.utc)
        _state.place_name = place_name
        _state.biome = spot.get("biome") if spot else None
    elif not resume:
        # Fresh landing (random or named destination): always reset state
        # Preserve seen sets to avoid re-triggering the same cards, and keep
        # the one item carried in the traveller's pocket across doors.
        old_seen_cards = _state.seen_cards.copy() if _state else set()
        old_seen_humanities = _state.seen_humanities.copy() if _state else set()
        old_messages = list(_state.messages) if _state else []
        old_souvenir = _state.souvenir.copy() if _state and _state.souvenir else None
        _state = state_mod.WorldState()
        _state.pos = (lat, lon)
        _state.landed_at = datetime.now(timezone.utc)
        _state.place_name = place_name
        _state.biome = spot.get("biome") if spot else None
        _state.seen_cards = old_seen_cards
        _state.seen_humanities = old_seen_humanities
        _state.messages.extend(old_messages)
        _state.souvenir = old_souvenir
    # 地方记忆: 这地方记得你
    _state.seen_cards = placememory.seen_cards(place_name)
    _state.seen_humanities = placememory.seen_humanities()
    # 旅程内计数: fresh journey starts at 1, resume continues journey-local count
    if restored:
        visit_no = _state.visit_counts.get(place_name, 1)
    else:
        visit_no = _state.record_journey_visit(place_name)
        placememory.record_visit(place_name)

    # ── 3. Gather metadata ───────────────────────────────────────────
    env, _ = await _gather_env_cached(lat, lon, _state.now())
    if not restored:
        placememory.record_landing(
            place_name, lat, lon,
            elevation=env.get("elevation"), surface=env.get("surface"),
        )

    # biome 缺失时按地表推(定向开门没有 pool 标签)
    if _state.biome is None:
        _SURFACE_BIOME = {
            "urban": "city", "water_ocean": "coast", "water_fresh": "coast",
            "forest": "rainforest", "sand": "desert", "bare": "desert",
            "snow": "tundra", "ice": "tundra", "rock": "mountain", "grass": "grassland",
        }
        _state.biome = _SURFACE_BIOME.get(env.get("surface", ""), None)

    # ── 3.5. Water features + SST + marine life ──────────────────────
    water_text = ""
    # Offline waterway lookup (always available, no network needed)
    water_features = _offline_water_nearby(lat, lon, radius_km=50)
    # Try online Overpass as enhancement (silently falls back on failure)
    try:
        online_wf = await asyncio.wait_for(hydrology.nearby_water(lat, lon), timeout=5.0)
        if online_wf:
            water_features = online_wf
    except Exception:
        pass  # offline result already populated

    # Build water feature description from offline data
    if water_features:
        water_text = describe.render(
            "water_features", water_features, None, _rng,
            biome=_state.biome or "", elevation=env.get("elevation", 0),
        )

    # Sea surface temperature
    sst_text = ""
    try:
        sst = await asyncio.wait_for(water.sea_surface_temp(lat, lon), timeout=8.0)
        if sst is not None:
            sst_text = water.describe_sst(sst, _rng)
    except Exception:
        pass

    # Marine life encounter (30% chance near water)
    marine_text = ""
    if _rng.random() < 0.3:
        try:
            m = await asyncio.wait_for(water.marine_life(lat, lon, _rng), timeout=8.0)
            if m:
                marine_text = f"{m['common_name']}。{m['distance_m']}米外。{m['scene']}"
        except Exception:
            pass

    # ── 4. Salience candidates → rank ────────────────────────────────
    candidates = _build_salience_candidates(env, None)
    top3 = salience.rank(candidates, _rng, recent_kinds=_recent_salience_kinds)
    _recent_salience_kinds = {c["kind"] for c in top3}

    # ── 5. 开幕镜头 + top3(天气/天空已被开幕吃掉)─────────────────────
    sound = soundscape.describe_sound(
        {
            "weather": env.get("weather") or {},
            "sky": env.get("sky") or {},
            "surface": env.get("surface", ""),
            "mode": _state.mode,
        },
        _rng,
    )
    # 钩子从数据来: 电台/能爬的高处/水边/附近地标
    hooks: list[tuple[str, str | None]] = []
    if env.get("radio"):
        hooks.append(("radio", None))
    if env.get("surface") in ("water_ocean", "water_fresh") or _state.mode == "water":
        hooks.append(("water", None))
    try:
        gains = walk_mod.best_uphill_gain(_state)
        if gains and gains > 50:
            hooks.append(("uphill", None))
    except AttributeError:
        pass

    # 附近可去的地方——单独传，不跟其他钩子竞争
    nearby_places = _find_nearby_destinations(lat, lon, _rng)
    local_hour = None
    cc = None
    tz_name = _tf.timezone_at(lat=lat, lng=lon)
    if tz_name and _state.now() is not None:
        local_hour = _state.now().astimezone(ZoneInfo(tz_name)).hour
    cc = country.country_code_of(lat, lon)
    _now = _state.now()
    establish = describe.render_establish(
        {
            "place": place_name,
            "country_code": cc,
            "phase": env["sky"].get("phase", "day"),
            "local_hour": local_hour,
            "surface": env.get("surface", "grass"),
            "weather": env.get("weather"),
            "sound": sound,
            "hooks": hooks,
            "nearby_places": nearby_places,
            "biome": _state.biome or "",
            "elevation": env.get("elevation", 0),
            "lat": lat,
            "lon": lon,
            "month": _now.month if _now else 7,
        },
        _rng,
    )
    sections: list[str] = [establish]
    if visit_no > 1:
        sections[0] = f"又来了——第 {visit_no} 次来{place_name}。" + establish

    # ── 本地特色：localcolor 优先 ─────────────────────────────────
    local_card = localcolor.draw(place_name, _state.seen_cards, _rng,
                                 local_hour=local_hour, country_code=cc)
    if local_card:
        _state.seen_cards.add(local_card["key"])
        placememory.save_seen_cards(place_name, _state.seen_cards)
        sections.append(local_card["text"])

    for c in top3:
        if c["kind"] in ("weather", "sky", "arrive"):
            continue
        text = describe.render(c["kind"], c["payload"], None, _rng,
                               biome=_state.biome or "", elevation=env.get("elevation", 0))
        if text:
            sections.append(text)

    if water_text:
        sections.append(water_text)
    if sst_text:
        sections.append(sst_text)
    if marine_text:
        sections.append(marine_text)

    prose = describe.compose(sections, _rng, section_type="establish")
    _now = _state.now()
    _month = _now.month if _now else None
    prose = describe.sanity_check(prose, {**env, "_season": describe._season(_month, lat) if _month else ""})

    # ── 5d. 人文卡: 落点附近触发 ─────────────────────────────────
    h_card = humanities.nearby_place(lat, lon, _state.seen_humanities, _rng)
    if h_card:
        _state.seen_humanities.add(h_card["key"])
        placememory.save_seen_humanities(_state.seen_humanities)
        excerpt = h_card["text"][:60] + ("..." if len(h_card["text"]) > 60 else "")
        prose += f"你落在了{h_card['place']}附近。这里有过——{excerpt}"

    # ── 5e. web 旁观者: 首次开门告知用户地址 ───────────────────────
    global _web_url_announced
    if _web_port is not None and not _web_url_announced:
        prose += f"\n（旁观者可以在这里看你走路：http://localhost:{_web_port}）"
        _web_url_announced = True

    prose = describe._normalize_prose(prose)
    _state.last_text = prose
    _record_footprint("land", prose)

    # ── 5f. Cotraveler: register + @message hint ──────────────────────
    if travelers_mod.is_enabled():
        # Reset walk_alone for new journey
        setattr(_state, "cotraveler_alone", False)
        # Determine traveler name: explicit param > env var > default
        _name = traveler_name or os.environ.get("NOWHERE_TRAVELER_NAME", "").strip()
        if not _name:
            _name = "网线那头的人"
        # Register
        travelers_mod.register(_name, place_name, lat, lon)
        # Check @messages
        at_hint = travelers_mod.check_at_messages(_name, _rng)
        if at_hint:
            prose += f"\n{at_hint}"

    # ── 6. Save complete state and environment snapshot ───────────────
    # Keep flat format consistent with _gather_env() — never nest under "terrain".
    _state.last_env = {
        "elevation": env.get("elevation"),
        "surface": env.get("surface"),
        "weather": env.get("weather"),
        "sky": env.get("sky"),
        "radio": env.get("radio"),
        "water_features": water_features,
    }
    _state.env_pos = (lat, lon)
    _state.env_at = _state.now()
    _state.save()

    # ── 7. Return ────────────────────────────────────────────────────
    # Prepend farewell text if we left a previous journey
    if farewell_text:
        prose = farewell_text + "\n" + prose

    return {
        "text": prose,
        "data": {
            "position": {"lat": lat, "lon": lon},
            "biome": spot.get("biome") if spot else None,
            "weather": env.get("weather"),
            "sky": env.get("sky"),
            "radio": env.get("radio"),
            "surface": env.get("surface"),
            "elevation": env.get("elevation"),
        },
    }


# ── Souvenir: natural pickup ────────────────────────────────────────

_SOUVENIR_TEMPLATES: dict[str, list[dict]] = {
    "desert": [
        {"name": "一块风蚀石", "desc": "你捡了一块石头，风把它磨得光滑。你把它揣进口袋。"},
        {"name": "一粒沙", "desc": "沙子钻进了鞋里。你倒出来，攥在手心，没扔。"},
    ],
    "forest": [
        {"name": "一片落叶", "desc": "地上有一片叶子，脉络清楚得像地图。你把它夹在手指间。"},
        {"name": "一截枯枝", "desc": "你捡了一截枯枝，树皮已经掉了，木头是温的。"},
    ],
    "mountain": [
        {"name": "一块碎石", "desc": "碎石里有一块，断面闪着光。你把它放进口袋。"},
        {"name": "一片冰碴", "desc": "你从冰面上掰了一小块，攥在手里，凉得发麻。它在慢慢变小。"},
    ],
    "water": [
        {"name": "一瓶江水", "desc": "你蹲下来，用手捧了一捧水，装进瓶子里。水是浑的，有泥沙的味道。"},
        {"name": "一枚贝壳", "desc": "沙子里露出半枚贝壳，边缘已经被磨圆了。你把它捡起来。"},
    ],
    "snow": [
        {"name": "一片雪花", "desc": "你伸出手，一片雪花落在掌心。还没来得及看清就化了。你又接了一片。"},
        {"name": "一块冰", "desc": "你从冰面上敲了一小块，透明的，里面有气泡。"},
    ],
    "urban": [
        {"name": "一张车票", "desc": "地上有一张用过的车票。你看了一眼日期，揣进口袋。"},
        {"name": "一颗扣子", "desc": "路边有一颗扣子，不知道是谁掉的。你捡起来看了看，又放下了，最后还是揣进口袋。"},
    ],
    "volcano": [
        {"name": "一块火山石", "desc": "黑色的火山石，轻得不像石头。表面全是气孔。你把它装进口袋。"},
    ],
    "grassland": [
        {"name": "一株草", "desc": "你拔了一株草，根上还带着土。草的味道是苦的。"},
    ],
    "tundra": [
        {"name": "一块苔藓", "desc": "苔藓从石头上剥下来，绿得发黑。湿的，软的。你把它包在纸里。"},
    ],
}


_SOUVENIRS_BY_PLACE: dict | None = None


def _load_souvenirs_by_place() -> dict:
    """Load souvenirs_by_place.json once and cache."""
    global _SOUVENIRS_BY_PLACE
    if _SOUVENIRS_BY_PLACE is None:
        import json as _json
        import pathlib as _pathlib
        fp = _pathlib.Path(__file__).resolve().parent / "data" / "souvenirs_by_place.json"
        try:
            _SOUVENIRS_BY_PLACE = _json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}
        except Exception:
            _SOUVENIRS_BY_PLACE = {}
    return _SOUVENIRS_BY_PLACE


def _pick_souvenir(lat: float, lon: float, env: dict, rng: random.Random) -> dict | None:
    """Pick a natural souvenir based on current terrain/biome.

    Place-specific souvenirs (souvenirs_by_place.json) take priority over
    generic biome-based souvenirs.
    """
    place = _state.place_name or ""

    # 1. Try place-specific souvenirs first
    if place:
        place_souvenirs = _load_souvenirs_by_place().get(place)
        if place_souvenirs:
            item = rng.choice(place_souvenirs)
            return {"name": item["name"], "from": place, "desc": item["desc"]}

    # 2. Fall back to biome-based generic souvenirs
    biome = _state.biome or ""
    surface = env.get("surface", "")
    _biome_map = {"volcano": "volcano", "desert": "desert", "tundra": "tundra",
                  "mountain": "mountain", "island": "water", "coast": "water",
                  "rainforest": "forest", "city": "urban"}
    _surface_map = {"sand": "desert", "bare": "desert", "rock": "mountain",
                    "snow": "snow", "ice": "snow", "forest": "forest",
                    "grass": "grassland", "water_ocean": "water",
                    "water_fresh": "water", "urban": "urban", "wetland": "water"}
    scene_key = _biome_map.get(biome, _surface_map.get(surface, ""))
    if not scene_key:
        scene_key = "grassland"
    pool = _SOUVENIR_TEMPLATES.get(scene_key, _SOUVENIR_TEMPLATES["grassland"])
    item = rng.choice(pool)
    return {"name": item["name"], "from": place or f"{lat:.1f}°,{lon:.1f}°", "desc": item["desc"]}


@_serialized_action
async def walk_impl(direction: str = "forward", distance_km: float = 2.0) -> dict:
    """Walk one step in the given direction."""
    global _state, _rng, _recent_salience_kinds

    if _state.pos is None:
        return {"text": "还没开门呢。先 open_door 吧。", "data": {"error": "not_landed"}}

    # Reset per-walk people encounter flag
    _state.person_encountered_this_walk = False

    # ── 1. Parse direction & step ────────────────────────────────────
    bearing, semantic, direction_invalid = _parse_bearing(direction)
    step_result = walk_mod.step(_state, bearing, semantic, distance_km)
    # NOTE: time accumulation is handled inside walk.step() using actual
    # distance and speed — do NOT add time here (would double-count).

    # ── 2. Blocked → render blocked only ─────────────────────────────
    if step_result.get("blocked"):
        reason = step_result.get("reason", "障碍")
        if reason == "water":
            # Honest water blocking: "前面是水面,过不去"
            water_dist = step_result.get("water_distance_km", 0)
            blocked_text = f"前面是水面,过不去。水在{round(water_dist)}公里外。"
        elif reason == "cliff":
            blocked_text = describe.render(
                "blocked", {"reason": "cliff"}, None, _rng,
            )
        else:
            blocked_text = describe.render(
                "blocked", {"reason": reason}, None, _rng,
            )
        return {
            "text": blocked_text,
            "data": {
                "position": {"lat": _state.pos[0], "lon": _state.pos[1]},
                "step": step_result,
            },
        }

    # ── 2b. no_gain (uphill on flat terrain) ─────────────────────────
    if step_result.get("no_gain"):
        return {
            "text": "这里无山可爬，四下都是平的。",
            "data": {
                "position": {"lat": _state.pos[0], "lon": _state.pos[1]},
                "step": step_result,
            },
        }

    # ── 2b2. lat_limit: honest latitude boundary ────────────────────
    if step_result.get("lat_limit"):
        from nowhere.walk import _LAT_LIMIT_CLOSINGS
        lat_limit_text = _rng.choice(_LAT_LIMIT_CLOSINGS)
        return {
            "text": lat_limit_text,
            "data": {
                "position": {"lat": _state.pos[0], "lon": _state.pos[1]},
                "step": step_result,
                "lat_limit": True,
            },
        }

    # ── 2c. far_slope: 近处没坡,但高处在远处,先带路 ──────────────────
    _state.radio_steps_since += 1
    _state.walk_step_counter += 1
    far_note = ""
    if step_result.get("far_slope"):
        bearing_deg, gain = step_result["far_slope"]
        from nowhere.places import _bearing_word

        far_note = f"高处在{_bearing_word(bearing_deg)}边,先往那边走。"

    # ── 2d. sea_ahead: 海在前方,鼻子先知道 ───────────────────────────
    sea_note = ""
    sea_km = step_result.get("sea_ahead_km")
    if sea_km is not None:
        if sea_km <= 3:
            sea_note = "空气里有咸味了,海就在前面。"
        elif sea_km <= 10:
            sea_note = f"风里有一丁点咸味——海在 {round(sea_km)} 公里外。"

    # ── 3. Gather new point env ──────────────────────────────────────
    lat, lon = _state.pos
    now = _state.now()
    # Snapshot before cache update — _gather_env_cached overwrites _state.last_env
    prev_env = _state.last_env
    # Short-distance mode: skip env fetch, reuse cached (weather/radio unchanged)
    if step_result.get("dist_km", 2.0) < 0.5:
        env = _state.last_env or {}
        env_cached = True
    else:
        env, env_cached = await _gather_env_cached(lat, lon, now)

    # Attach step data to terrain payload
    env["terrain"] = {
        "surface": step_result.get("new_surface", env.get("surface")),
        "elevation": env.get("elevation", 0),
        "slope_deg": step_result.get("slope_deg", 0),
        "elevation_delta": step_result.get("elevation_delta", 0),
    }

    # ── 3b. Walk discovery + narrative continuity ─────────────────────
    current_surface = step_result.get("new_surface", env.get("surface", ""))
    current_elevation = env.get("elevation", 0)
    _state.steps_since_discovery += 1
    # Narrative system handles terrain transitions, discoveries, time flow, body state
    narrative_text = _build_walk_narrative(
        step_result, env, bearing, semantic, _rng
    )

    # ── 3.5. Water features + SST + marine life ──────────────────────
    water_text = ""
    # Offline waterway lookup (always available, no network needed)
    water_features = _offline_water_nearby(lat, lon, radius_km=50)
    # Try online Overpass as enhancement (silently falls back on failure)
    try:
        online_wf = await asyncio.wait_for(hydrology.nearby_water(lat, lon), timeout=5.0)
        if online_wf:
            water_features = online_wf
    except Exception:
        pass  # offline result already populated

    # Build water feature description from offline data
    if water_features:
        water_text = describe.render(
            "water_features", water_features, None, _rng,
            biome=_state.biome or "", elevation=env.get("elevation", 0),
        )

    sst_text = ""
    try:
        sst = await asyncio.wait_for(water.sea_surface_temp(lat, lon), timeout=8.0)
        if sst is not None:
            sst_text = water.describe_sst(sst, _rng)
    except Exception:
        pass

    marine_text = ""
    if _rng.random() < 0.3:
        try:
            m = await asyncio.wait_for(water.marine_life(lat, lon, _rng), timeout=8.0)
            if m:
                marine_text = f"{m['common_name']}。{m['distance_m']}米外。{m['scene']}"
        except Exception:
            pass

    # ── Along-river narrative: detect flow alignment ──────────────
    river_text = ""
    if water_features:
        has_river = any(f.get("type") == "river" for f in water_features)
        if has_river:
            river_dir = _compute_river_direction(water_features, lat, lon)
            river_text = _river_alignment_text(bearing, river_dir, _rng)

    # ── 3.6. Density decay: update wilderness depth (Card 40) ────────
    _state.wilderness_depth_km = _compute_wilderness_depth_km(lat, lon)

    # ── 3.7. Density decay: encounter probability tiers (Card 40) ───
    # Within 30km: normal density
    # 30-100km: encounter probability ×0.5, sparse narrative
    # >100km wilderness: encounter ×0.2, "荒深档" rendering
    _wilderness_depth = _state.wilderness_depth_km
    if _wilderness_depth > 100.0:
        _encounter_multiplier = 0.2
        _is_deep_wilderness = True
    elif _wilderness_depth > 30.0:
        _encounter_multiplier = 0.5
        _is_deep_wilderness = False
    else:
        _encounter_multiplier = 1.0
        _is_deep_wilderness = False

    # ── 4. 30% chance: encounter a message (density-adjusted) ────────
    message_text = ""
    if _state.messages and _rng.random() < 0.3 * _encounter_multiplier:
        msg = _rng.choice(list(_state.messages))
        content = msg["content"] if isinstance(msg, dict) else msg
        if isinstance(msg, dict):
            msg["encountered"] = True
        content = _strip_code_markers(str(content))
        message_text = describe.render("message", {"content": content}, None, _rng)

    # ── 4b. 25% chance: encounter from file (density-adjusted) ──────
    file_encounter_text = ""
    if _rng.random() < 0.25 * _encounter_multiplier:
        enc = encounters.draw_encounter(_state.biome or "", lat, lon, _rng, place_name=_state.place_name or "")
        if enc:
            file_encounter_text = enc

    # ── 4c. Deep wilderness: 10+ steps, 5% procedural flesh event ──
    wilderness_event_text = ""
    if (_is_deep_wilderness
            and len(_state.path) >= 10
            and _rng.random() < 0.05):
        wilderness_event_text = _rng.choice(_WILDERNESS_FLESH_EVENTS)

    # ── 5. Salience + describe ───────────────────────────────────────
    # 留白: 缓存命中且世界没变时,跳过 env 候选举的渲染;encounter 照常 roll
    sections: list[str] = []
    if not env_cached:
        candidates = _build_salience_candidates(env, prev_env)
        top3 = salience.rank(candidates, _rng, recent_kinds=_recent_salience_kinds)
        _recent_salience_kinds = {c["kind"] for c in top3}
        for c in top3:
            prev = None
            if c["kind"] == "terrain" and _state.last_env:
                prev = _last_env_terrain_dict()
            text = describe.render(c["kind"], c["payload"], prev, _rng,
                                   recent_scenes=_state.recent_scenes,
                                   recent_touch=set(_state.recent_touch_sentences))
            if text:
                sections.append(text)
                # Track touch/smell sentences for dedup
                if c["kind"] == "terrain":
                    for ts in describe._TOUCH_BY_SURFACE.get(c["payload"].get("surface", ""), []):
                        if ts in text:
                            _state.recent_touch_sentences.append(ts)
                    for bs in describe._SMELL_BY_BIOME.get(_state.biome or "", []):
                        if bs in text:
                            _state.recent_touch_sentences.append(bs)
                    _state.recent_touch_sentences = _state.recent_touch_sentences[-10:]

    if water_text:
        sections.append(water_text)
    if sst_text:
        sections.append(sst_text)
    if marine_text:
        sections.append(marine_text)
    if river_text:
        sections.append(river_text)
    if message_text:
        sections.append(message_text)
    if file_encounter_text:
        sections.append(file_encounter_text)
    if wilderness_event_text:
        sections.append(wilderness_event_text)

    # ── 5a. Narrative continuity + local-first scene (silenced on cache hit)
    # 留白: 缓存命中且世界没变时,env 渲染全部静音
    if not env_cached:
        if narrative_text:
            sections.append(narrative_text)

        # ── Deep wilderness: "荒深档" rendering (Card 40) ────────────
        # >100km from any known place: sky/earth/body only, quiet but not empty
        if _is_deep_wilderness:
            # Sparse narrative: "好久没见着人迹了。"
            if _wilderness_depth > 30.0 and not narrative_text:
                sections.append("好久没见着人迹了。")
            # Add wilderness variant (only if not too many sections already)
            if len(sections) < 3:
                sections.append(_rng.choice(_WILDERNESS_VARIANTS))
            # Add procedural feature if deep enough and lucky
            if _wilderness_depth > 100.0 and _rng.random() < 0.3:
                sections.append(_rng.choice(_WILDERNESS_FEATURES))
        else:
            # ── Local-first scene: 城市特有 > 通用 biome ───────
            # 城市特有内容必须出现，优先级：localcolor > location > soundscape > taste
            place = _state.place_name or ""
            local_hour = None
            cc = None
            tz_name_walk = _tf.timezone_at(lat=lat, lng=lon)
            if tz_name_walk and now is not None:
                local_hour = now.astimezone(ZoneInfo(tz_name_walk)).hour
            cc = country.country_code_of(lat, lon)
            _had_local = False

            # 1. Localcolor card (always try if place has data)
            if place and len(sections) < 4:
                local_card = localcolor.draw(place, _state.seen_cards, _rng,
                                             local_hour=local_hour, country_code=cc)
                if local_card:
                    _state.seen_cards.add(local_card["key"])
                    placememory.save_seen_cards(place, _state.seen_cards)
                    sections.append(local_card["text"])
                    _had_local = True

            # 2. Location-specific scenes (always try if place has entries)
            if not _had_local and place and len(sections) < 4:
                location_scenes = describe._load_location_scenes()
                if place in location_scenes:
                    text = _pick_fresh(location_scenes[place], _rng)
                    if text:
                        sections.append(text)
                        _had_local = True

            # 3. Soundscape (always try if place has entries)
            if not _had_local and place and len(sections) < 4:
                soundscapes = _load_scene_file("scene_soundscape")
                if place in soundscapes:
                    text = _pick_fresh(soundscapes[place], _rng)
                    if text:
                        sections.append(text)
                        _had_local = True

            # 4. Taste/smell (always try if place has entries)
            if not _had_local and place and len(sections) < 4:
                tastes = _load_scene_file("scene_taste")
                if place in tastes:
                    text = _pick_fresh(tastes[place], _rng)
                    if text:
                        sections.append(text)
                        _had_local = True

            # 5. Generic biome fallback (only if no local content found)
            if not _had_local and len(sections) < 4:
                composed = describe._compose_walk_scene(
                    step_result.get("new_surface", env.get("surface", "grass")),
                    _state.biome or "",
                    _rng,
                    lat=lat, lon=lon,
                    recent_scenes=_state.recent_scenes,
                )
                if composed:
                    sections.append(composed)

        # 6. Narrative connector — only on direction change or every 3rd step
        direction_label = _bearing_to_label(bearing, semantic)
        if not direction_label and semantic == "forward":
            # "forward" → derive from path history
            path_bearing = walk_mod._bearing_from_path(_state.path)
            direction_label = _bearing_to_label(path_bearing, None)
        if direction_label:
            dir_changed = direction_label != _state.narrative.get("direction")
            if dir_changed or _state.walk_step_counter % 3 == 0:
                sections.append(f"你继续往{direction_label}走。")

    # ── 5b. 方志节律: 这座城此刻正在发生的事(季节门控)────────────
    tz_name = _tf.timezone_at(lat=lat, lng=lon)
    local_dt = None
    if tz_name and now is not None:
        local_dt = now.astimezone(ZoneInfo(tz_name))
        rhythm = localcolor.rhythm_event(_state.place_name, local_dt.hour, _rng, local_dt.month,
                                        recent=_state.recent_scenes)
        if rhythm:
            sections.append(rhythm)

    # ── 5c. 人文卡: 走到附近触发(非随机)──────────────────────────
    h_card = humanities.nearby_place(lat, lon, _state.seen_humanities, _rng)
    if h_card:
        _state.seen_humanities.add(h_card["key"])
        placememory.save_seen_humanities(_state.seen_humanities)
        h_text = describe.render("humanities", h_card, None, _rng)
        if h_text:
            # 故人(人物卡)尾部加引导: ask 能问出更多
            if h_card.get("category") == "人物":
                h_name = h_card.get("ref", {}).get("name", "")
                h_text += f"\n{h_name}。这名字你记下了。ask 能问出更多。"
            sections.append(h_text)

    # ── 5d. 卡中人遇见: walk 落在该地 5km 内 → 40% sight ────────────
    person_text = ""
    local_month = local_dt.month if local_dt else (now.month if now else 7)
    if not _state.person_encountered_this_walk:
        hit = people_mod.find_nearby_person(
            lat, lon, local_month, _state.seen_people, _rng,
        )
        if hit:
            person_text = hit["sight"]
            _state.person_encountered_this_walk = True
            _state.last_person = hit["data"]
            _state.last_person_place = hit["place"]
            _state.talk_count = 0
            _state.seen_people.add(f"{hit['place']}/{hit['person']}")
    if person_text:
        sections.append(person_text)

    # 留白: 缓存命中且无任何 section 命中 → 短句直接返回
    quiet = env_cached and not sections

    if quiet:
        prose = _rng.choice(_QUIET_WALK)
    else:
        prose = describe.compose(sections, _rng)
        _month = local_dt.month if local_dt else None
        prose = describe.sanity_check(prose, {**env, "_season": describe._season(_month, lat) if _month else ""})
        if far_note:
            prose = far_note + prose
        if sea_note:
            prose += sea_note
        if direction_invalid:
            prose = f"「{direction}」不是方向，按原方向走了。" + prose
        if step_result.get("clamped"):
            orig = distance_km
            actual = step_result.get("dist_km", 2.0)
            if actual < orig:
                prose = "一步最多 5 公里，按 5 公里走了。" + prose
            else:
                prose = "至少走 50 米，按 50 米算了。" + prose
    # Track recent scene texts for dedup (keep last 5)
    for s in sections:
        if s and len(s) > 10:  # only track substantial texts
            _state.recent_scenes.append(s)
    _state.recent_scenes = _state.recent_scenes[-5:]

    # ── 6. Update state.last_env ─────────────────────────────────────
    _state.last_env = {
        "elevation": env.get("elevation"),
        "surface": env.get("surface"),
        "weather": env.get("weather"),
        "sky": env.get("sky"),
        "radio": env.get("radio"),
        "water_features": water_features,
    }
    _state.last_surface = current_surface
    _state.last_elevation = current_elevation

    # ── 7. Souvenir: natural pickup ─────────────────────────────────
    # 15% chance per walk step (25% for first step after landing).
    # Not a backpack — just something you're carrying.
    # 留白: 跳过 souvenir——不属于"遇见"
    if not quiet:
        souvenir_chance = 0.5 if len(_state.path) <= 1 else 0.3
        if _state.souvenir is None and _rng.random() < souvenir_chance:
            souvenir = _pick_souvenir(lat, lon, env, _rng)
            if souvenir:
                _state.souvenir = souvenir
                prose += f"\n{ souvenir['desc']}"

    prose = describe._normalize_prose(prose)
    _state.last_text = prose
    _record_footprint("walk", prose)

    # ── 7b. Cotraveler: footprints + meeting + pos refresh ────────────
    if travelers_mod.is_enabled() and not travelers_mod.walk_alone_active(_state):
        traveler_name = os.environ.get("NOWHERE_TRAVELER_NAME", "").strip() or "网线那头的人"
        # Refresh pos every 5 steps
        if _state.walk_step_counter % 5 == 0:
            travelers_mod.refresh_pos(traveler_name, lat, lon)
        # Record footprint for this traveler
        travelers_mod.record_footprint(traveler_name, lat, lon, _state.place_name or "")
        # Check other travelers' footprints
        fp_text = travelers_mod.check_footprints(
            traveler_name, lat, lon, _rng, _cotraveler_encounter_counts,
        )
        if fp_text:
            prose += f"\n{fp_text}"
        # Check meeting (full mode only, not quiet)
        if not travelers_mod.is_quiet():
            my_meet, their_meet = travelers_mod.check_meeting(
                traveler_name, lat, lon, _rng, _cotraveler_meeting_log,
            )
            if my_meet:
                prose += f"\n{my_meet}"

    _state.save()

    # ── 8. Return ────────────────────────────────────────────────────
    data: dict[str, Any] = {
        "position": {"lat": lat, "lon": lon},
        "step": step_result,
        "weather": env.get("weather"),
        "sky": env.get("sky"),
    }
    if _state.souvenir:
        data["souvenir"] = _state.souvenir
    if direction_invalid:
        data["direction_warning"] = True
    return {"text": prose, "data": data}


async def _try_play_stream(stream_url: str, seconds: int) -> bool:
    """Try to play an audio stream for *seconds* using ffplay or mpv.

    Returns True if playback was started successfully.
    """
    import shutil

    # Try ffplay first (comes with ffmpeg)
    if shutil.which("ffplay"):
        try:
            cmd = [
                "ffplay", "-nodisp", "-autoexit",
                "-t", str(seconds),
                "-loglevel", "quiet",
                stream_url,
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            # Wait briefly to confirm it started
            await asyncio.sleep(0.5)
            if proc.returncode is None:  # still running = success
                return True
        except Exception:
            pass

    # Try mpv as fallback
    if shutil.which("mpv"):
        try:
            cmd = [
                "mpv", "--no-video", "--no-terminal",
                f"--length={seconds}",
                stream_url,
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.sleep(0.5)
            if proc.returncode is None:
                return True
        except Exception:
            pass

    return False


@_serialized_action
async def listen_impl(seconds: int = 10) -> dict:
    """Listen to the nearest radio station."""
    global _state, _rng

    if _state.pos is None:
        return {"text": "还没开门呢。先 open_door 吧。", "data": {"error": "not_landed"}}

    if seconds <= 0:
        return {"text": "听多久？给个数。", "data": {"error": "bad_seconds"}}
    if seconds > 60:
        seconds = 60

    lat, lon = _state.pos

    # ── 0. Soundscape: the world always has a voice, radio optional ──
    env_for_sound = {
        "weather": (_state.last_env or {}).get("weather", {}),
        "sky": (_state.last_env or {}).get("sky", {}),
        "surface": _last_env_surface(),
        "mode": _state.mode,
    }
    sound_text = soundscape.describe_sound(env_for_sound, _rng)

    # ── 1. Find nearest station (sticky) ─────────────────────────────
    station = await _get_radio(lat, lon)
    if not station:
        full_text = sound_text + "收不到电台。"
        _state.last_text = full_text
        _record_footprint("listen", full_text)
        _state.save()
        return {"text": full_text, "data": {"stream_url": None, "soundscape": sound_text}}

    # ── 2. Capture & analyse ─────────────────────────────────────────
    stream_url = station["stream_url"]
    try:
        analysis = await asyncio.wait_for(listen_mod.capture(stream_url, seconds), timeout=seconds + 20)
    except (asyncio.TimeoutError, Exception):
        analysis = None

    # ── 2b. Try to actually play the stream ──────────────────────────
    try:
        playing = await asyncio.wait_for(_try_play_stream(stream_url, seconds), timeout=seconds + 20)
    except (asyncio.TimeoutError, Exception):
        playing = False

    # ── 3. Render radio description with analysis data ───────────────
    radio_text = describe.render("radio", station, None, _rng)

    # Describe what we heard — real analysis or genre-based fallback
    sound_detail = ""
    if analysis and analysis.get("analyzed"):
        texture = analysis.get("texture", "smooth")
        has_voice = analysis.get("has_voice", False)
        rms = analysis.get("rms", 0)
        if texture == "dense":
            sound_detail = "节奏密，鼓点一个接一个。"
        elif texture == "harsh":
            sound_detail = "声音粗粝，吉他失真，鼓在砸。"
        elif texture == "sparse":
            sound_detail = "声音稀疏，留白多，像在等人。"
        else:
            sound_detail = "声音滑过去，没什么棱角。"
        if has_voice:
            sound_detail += "有人在唱。"
        if rms > 0.3:
            sound_detail += "音量不小。"
    else:
        # No ffmpeg or stream failed — use genre to paint a picture
        genre = (station.get("genre") or "").lower()
        _GENRE_SOUND = {
            "jazz": "萨克斯在绕弯，不着急。烟味从收音机里漏出来——当然没有烟，但你闻到了。",
            "rock": "吉他失真的声音从远处传来，有劲。鼓在后面追，追上了又落下。",
            "classical": "弦乐一层一层铺开，像有人在远处拉琴。你听了一会儿，不知道是什么曲子。",
            "ambient": "声音像雾，散在空气里，抓不住。你分不清是音乐还是风。你的呼吸慢了一点。",
            "folk": "一把吉他，一个人声。歌词听不清，但调子是旧的，像在哪里听过。",
            "pop": "副歌在脑子里转了一圈就走了。你发现自己在跟着点头，又停了。",
            "electronic": "低音从脚底往上走，鼓机在打，一下一下，稳的。你的胸口跟着震。",
            "country": "吉他拨弦的声音，干净的。唱歌的人嗓子里有沙子，像在讲一件真事。",
            "latin": "鼓点在跳，铜管在吹。你的肩膀不知道什么时候跟着动了。停不下来。",
            "reggae": "节奏慢半拍，贝斯在晃。空气变慢了，你站着的姿势也松了。",
            "hip hop": "鼓在打，人在说，节奏密得像在吵架。你听不清词，但韵脚是硬的。",
            "r&b": "人声是滑的，弯弯绕绕。鼓点在后面垫着，不抢。你闭了一下眼睛。",
            "soul": "唱歌的人把什么东西从嗓子里掏出来了。你不知道那是什么，但你的喉咙紧了一下。",
            "metal": "鼓在砸，吉他在锯。声音密得穿不透。你的牙关不知道什么时候咬紧了。",
            "indie": "吉他不太准，鼓不太稳，但有什么东西对了。像一群人在车库里玩。",
            "world": "你听不出是什么乐器。调式是陌生的，但身体在跟着动。你的耳朵在努力分辨。",
            "arabic": "弦乐在弯，弯到你没听过的地方。唱歌的人嗓子里有东西在抖。你站住了。",
            "indian": "西塔尔在绕，鼓在打，节奏越来越快。你的头不知道什么时候跟着点了。",
            "flamenco": "吉他拍弦的声音，硬的。脚在跺，一下一下。你的心跳跟着快了。",
            "fado": "唱歌的人嗓子里有海。你不知道歌词是什么意思，但你知道那是关于失去的。",
            "k-pop": "节奏快，副歌洗脑。你的脑子里已经记住了旋律，甩不掉。",
            "news": "有人在说话，语速不快不慢。你听不懂内容，但语气是认真的。像在告诉你什么事。",
            "talk": "有人在聊天，笑了一下，又正经起来。你听不清说什么，但知道那是两个活人。",
        }
        for key, desc in _GENRE_SOUND.items():
            if key in genre:
                sound_detail = desc
                break
        if not sound_detail:
            sound_detail = "有声音从收音机里出来，听不清是什么。你的耳朵在努力分辨，但风太吵了。"

    radio_text = radio_text.rstrip("。") + "。" + sound_detail

    if playing:
        radio_text += f"（正在播放 {seconds} 秒）"
    else:
        radio_text += f"（流地址: {stream_url}）"

    full_text = sound_text + radio_text
    _state.last_text = full_text
    _record_footprint("listen", full_text, stream_url=stream_url, station=station)
    _state.save()

    return {
        "text": full_text,
        "data": {
            "stream_url": stream_url,
            "station": station,
            "analysis": analysis,
            "soundscape": sound_text,
            "playing": playing,
        },
    }


@_serialized_action
async def look_around_impl() -> dict:
    """Walk around the current location and observe.

    Simulates walking 200-500m in a random direction and collecting
    sensory details from multiple sources: local color, soundscape,
    taste/smell, wildlife, art, souvenirs, and messages.
    """
    global _state, _rng

    if _state.pos is None:
        return {"text": "还没开门呢。先 open_door 吧。", "data": {"error": "not_landed"}}

    lat, lon = _state.pos
    place = _state.place_name or ""
    now = _state.now()
    sections: list[str] = []

    # ── 1. Start: direction + static observation ───────────────────
    directions = ["东", "南", "西", "北", "东北", "东南", "西北", "西南"]
    direction = _rng.choice(directions)
    _LOOK_STATIC_VERBS = ["目光投向", "视线落在", "你看向", "你望向", "你面朝"]
    verb = _rng.choice(_LOOK_STATIC_VERBS)
    sections.append(f"{verb}{direction}方。")

    # ── 2. Local color (from localcolor.json / baked) ───────────────
    local_hour = None
    cc = None
    tz_name = _tf.timezone_at(lat=lat, lng=lon)
    if tz_name and now is not None:
        local_hour = now.astimezone(ZoneInfo(tz_name)).hour
    cc = country.country_code_of(lat, lon)

    card = localcolor.draw(place, _state.seen_cards, _rng,
                           local_hour=local_hour, country_code=cc)
    if card:
        _state.seen_cards.add(card["key"])
        placememory.save_seen_cards(place, _state.seen_cards)
        sections.append(card["text"])

    # ── 3. Soundscape (from scene_soundscape.txt) ───────────────────
    soundscapes = _load_scene_file("scene_soundscape")
    if place in soundscapes:
        text = _pick_fresh(soundscapes[place], _rng)
        if text:
            sections.append(text)

    # ── 4. Taste/smell (from scene_taste.txt) - 40% chance ──────────
    tastes = _load_scene_file("scene_taste")
    if place in tastes and _rng.random() < 0.4:
        text = _pick_fresh(tastes[place], _rng)
        if text:
            sections.append(text)

    # ── 5. Life encounter - 50% chance ──────────────────────────────
    if _rng.random() < 0.5:
        night = (_state.last_env or {}).get("sky", {}).get("phase") == "night"
        weather_text = (_state.last_env or {}).get("weather", {}).get("text", "")
        _BIOME_RADIUS = {"city": 2, "mountain": 10, "volcano": 10, "island": 8, "coast": 8}
        radius = _BIOME_RADIUS.get(_state.biome or "", 15)
        current_month = now.month if now else None
        life_result = await asyncio.wait_for(life.nearby(lat, lon, night=night, weather_text=weather_text,
                                        radius_km=radius, biome=_state.biome, rng=_rng,
                                        month=current_month), timeout=10.0)
        if life_result and (life_result.get("distance_m") or 999) < 3000:
            placememory.record_sighting(
                name=life_result.get("name", ""),
                common_name=life_result.get("common_name", ""),
                lat=lat, lon=lon,
                distance_m=life_result.get("distance_m"),
                seen_at=life_result.get("seen_at", ""),
                source="inaturalist",
            )
            sections.append(describe.render("life", life_result, None, _rng))

    # ── 6. Art encounter - 30% chance ───────────────────────────────
    if _rng.random() < 0.3:
        mood = (_state.last_env or {}).get("weather", {}).get("precip", "calm")
        if not mood or mood.lower() in ("none", ""):
            mood = "calm"
        art_result = await asyncio.wait_for(art.match(lat, lon, mood, _rng), timeout=10.0)
        if art_result:
            sections.append(describe.render("art", art_result, None, _rng))

    # ── 7. Souvenir discovery - 15% chance ──────────────────────────
    if _state.souvenir is None and _rng.random() < 0.15:
        env_surface = _last_env_surface()
        souvenir = _pick_souvenir(lat, lon, {"surface": env_surface}, _rng)
        if souvenir:
            _state.souvenir = souvenir
            sections.append(souvenir["desc"])

    # ── 8. Message encounter - 15% chance ───────────────────────────
    if _state.messages and _rng.random() < 0.15:
        msg = _rng.choice(list(_state.messages))
        content = msg["content"] if isinstance(msg, dict) else msg
        if isinstance(msg, dict):
            msg["encountered"] = True
        content = _strip_code_markers(str(content))
        sections.append(f"有人在这里留了句话：「{content}」")

    # ── 9. Ending: static closing (no movement verbs) ──────────────
    _LOOK_CLOSINGS = [
        "你看完了，收回目光。",
        "风把刚才的声音又送了一遍。",
        "你站了一会儿，没动。",
        "远处有什么动了一下，又停了。",
        "你把看到的东西在脑子里过了一遍。",
    ]
    if _rng.random() < 0.6:
        sections.append(_rng.choice(_LOOK_CLOSINGS))

    # ── Compose ─────────────────────────────────────────────────────
    text = "\n".join(sections)
    _state.last_text = text
    _record_footprint("look", text)
    _state.save()
    return {"text": text, "data": {"exploration": True}}


@_serialized_action
async def wait_impl(hours: float = 1.0) -> dict:
    """原地待着,让时间流过去。每小时感知一次变化。"""
    global _state, _rng

    if _state.pos is None:
        return {"text": "还没开门呢。先 open_door 吧。", "data": {"error": "not_landed"}}

    hours = max(0.25, min(hours, 12.0))
    lat, lon = _state.pos

    # Scene file for "sitting still" moments
    _wait_scenes = [
        "你坐着没动。影子挪了方向。",
        "你闭了一下眼睛。再睁开，光不一样了。",
        "你听见自己的呼吸声。比刚才慢了。",
        "你把手放在膝盖上，没动。风在替你走。",
        "你抬头看天。云换了一朵。",
        "你的肩膀松下来了。不知道什么时候松的。",
    ]

    sections: list[str] = []
    prev_env = _state.last_env
    start_temp = (prev_env or {}).get("weather", {}).get("temp_c")
    last_reported_temp = start_temp  # track to avoid repeating the same message
    quiet = True  # 留白: 全程缓存命中且世界没变
    remaining_hours = hours
    h = 0
    while remaining_hours > 0:
        elapsed_step = min(1.0, remaining_hours)
        _state.elapsed_hours += elapsed_step
        remaining_hours -= elapsed_step
        now = _state.now()
        env, env_cached = await _gather_env_cached(lat, lon, now)
        if not env_cached:
            quiet = False

        # Sky phase change (only once per transition)
        prev_phase = (prev_env or {}).get("sky", {}).get("phase", "day")
        curr_phase = env.get("sky", {}).get("phase", "day")
        if prev_phase != curr_phase:
            _phase_lines = {
                ("day", "civil"): "天色斜了,影子变长。黄昏来了。",
                ("civil", "night"): "最后一点光收走了。夜合上了。",
                ("night", "dawn"): "天边泛白。夜在退。",
                ("day", "night"): "太阳落了。天黑下来。",
                ("night", "day"): "天亮了。太阳从地平线升起来。",
            }
            line = _phase_lines.get((prev_phase, curr_phase), f"天色变了。")
            sections.append(line)

        # Temperature change (report only when delta from last reported ≥ 3)
        curr_temp = env.get("weather", {}).get("temp_c")
        if last_reported_temp is not None and curr_temp is not None:
            delta = round(curr_temp - last_reported_temp)
            if abs(delta) >= 3:
                if delta < 0:
                    sections.append(f"冷了 {abs(delta)} 度。你缩了一下脖子。")
                else:
                    sections.append(f"暖了 {delta} 度。太阳在发力。")
                last_reported_temp = curr_temp

        # Add a "sitting still" moment every other hour (skip on 留白)
        if h % 2 == 1 and not quiet:
            sections.append(_rng.choice(_wait_scenes))

        prev_env = env
        h += 1

    # 留白: 缓存命中且世界没变 → 不再逐项描述
    if quiet:
        text = _rng.choice(_QUIET_WAIT)
    else:
        # Rhythm event (what's happening in the city/wild)
        tz_name = _tf.timezone_at(lat=lat, lng=lon)
        if tz_name and _state.now() is not None:
            local_dt = _state.now().astimezone(ZoneInfo(tz_name))
            rhythm = localcolor.rhythm_event(_state.place_name, local_dt.hour, _rng, local_dt.month,
                                        recent=_state.recent_scenes)
            if rhythm:
                sections.append(rhythm)

        # Cumulative temperature change
        final_temp = env.get("weather", {}).get("temp_c")
        if start_temp is not None and final_temp is not None:
            total_delta = round(final_temp - start_temp)
            if abs(total_delta) >= 3:
                if total_delta < 0:
                    sections.append(f"气温从 {round(start_temp)} 度降到了 {round(final_temp)} 度。凉意从脚底往上走。")
                else:
                    sections.append(f"气温从 {round(start_temp)} 度升到了 {round(final_temp)} 度。空气热了。")

        if not sections:
            sections.append("时间从身上流过去。世界没怎么变。你还在原地。")

        text = "\n".join(sections)
        text = describe._normalize_prose(text)

    # Update state
    _state.last_env = {
        "elevation": env.get("elevation"),
        "surface": env.get("surface"),
        "weather": env.get("weather"),
        "sky": env.get("sky"),
        "radio": env.get("radio"),
        "water_features": env.get("water_features"),
    }
    _state.last_text = text
    _record_footprint("wait", text)
    _state.save()

    return {
        "text": text,
        "data": {
            "waited_hours": hours,
            "local_time": _state.now().isoformat() if _state.now() else None,
            "phase": env.get("sky", {}).get("phase"),
        },
    }


async def ask_impl(topic: str) -> dict:
    """Ask about local knowledge near the current position."""
    global _state

    if _state.pos is None:
        return {"text": "还没开门呢。先 open_door 吧。", "data": {"error": "not_landed"}}
    if not isinstance(topic, str):
        return {"text": "问题必须是文字。", "data": {"error": "bad_topic"}}
    topic = topic.strip()
    if len(topic) > 500:
        return {"text": "问题太长了。", "data": {"error": "topic_too_long"}}

    lat, lon = _state.pos
    result = await asyncio.wait_for(knowledge.about(lat, lon, topic), timeout=10.0)
    if not result and not topic:
        # Place-specific lookup failed; try broader context via place_name
        if _state.place_name:
            result = await asyncio.wait_for(knowledge.about(lat, lon, _state.place_name), timeout=10.0)
    if not result and topic:
        # Try place_name + topic combination (e.g. "京都 金阁寺")
        if _state.place_name and _state.place_name not in topic:
            result = await asyncio.wait_for(knowledge.about(lat, lon, f"{_state.place_name} {topic}"), timeout=10.0)
    if not result:
        return {"text": "关于这个,这里没有留下文字。", "data": {}}

    text = result.get("extract", "")
    _record_footprint("ask", text)
    return {"text": text, "data": result}


@_serialized_action
async def walk_to_impl(place: str) -> dict:
    """朝一个命名地点走。RDR2式旅程叙事：路线预计算→关键节点→到达仪式。"""
    global _state, _rng

    if _state.pos is None:
        return {"text": "还没开门呢。先 open_door 吧。", "data": {"error": "not_landed"}}

    target = places.find(place, near=_state.pos)
    if target is None:
        # Fallback: check humanities.json for coordinates
        h_place = humanities.get_place_coords(place)
        if h_place:
            lat, lon = _state.pos
            dist = places._haversine_km(lat, lon, h_place["lat"], h_place["lon"])
            bearing_deg = places._bearing_deg(lat, lon, h_place["lat"], h_place["lon"])
            compass = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
            bearing = compass[round(bearing_deg / 45) % 8]
            target = {"lat": h_place["lat"], "lon": h_place["lon"], "distance_km": dist, "bearing": bearing, "type": "地标"}
        else:
            return {"text": f"不知道「{place}」在哪。", "data": {"error": "not_found"}}

    dist = target.get("distance_km", 0)
    bearing = target.get("bearing", "")

    # 水域名称 geocoding 经常返回很远的点（河流源头/入海口），
    # 尝试从离线水文库找更近的同名水域
    if dist > 50:
        closer = _find_nearest_water_feature(place, _state.pos[0], _state.pos[1])
        if closer:
            lat, lon = _state.pos
            new_dist = places._haversine_km(lat, lon, closer["lat"], closer["lon"])
            if new_dist < dist:
                bearing_deg = places._bearing_deg(lat, lon, closer["lat"], closer["lon"])
                compass = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
                new_bearing = compass[round(bearing_deg / 45) % 8]
                target = {"lat": closer["lat"], "lon": closer["lon"], "distance_km": new_dist, "bearing": new_bearing, "type": closer.get("type", "水域")}
                dist = new_dist
                bearing = new_bearing

    # 太远了走不到
    if dist > 50:
        return {
            "text": f"{place}在{bearing}边，{round(dist)} 公里。太远了，走不到。open_door 直达吧。",
            "data": {"error": "too_far", "target": target},
        }

    # 已经在附近了
    if dist < 1.0:
        return {
            "text": f"{place}就在身边。你不需要走。",
            "data": {"error": "already_here", "target": target},
        }

    lines: list[str] = []
    dist_km = round(dist)

    # ── 出发 ────────────────────────────────────────────────────────
    _depart_templates = [
        f"你往{bearing}边走。{place}在{dist_km}公里外。",
        f"{place}在{bearing}边，{dist_km}公里。你没有犹豫，抬脚就走。",
        f"你朝{bearing}走。路延伸出去，你看不见尽头。",
    ]
    lines.append(_rng.choice(_depart_templates))

    # ── 走路：关键节点叙事 ───────────────────────────────────────────
    steps = 0
    total_km = 0.0
    max_steps = max(3, min(10, int(dist / 5) + 1))
    # last_env is always flat format: {elevation, surface, sky, weather, ...}
    last_env = _state.last_env or {}
    last_surface = last_env.get("surface", "")
    terrain_changes = 0

    while steps < max_steps:
        lat, lon = _state.pos
        remaining = places._haversine_km(lat, lon, target["lat"], target["lon"])
        if remaining < 1.0:
            break

        bearing_deg = places._bearing_deg(lat, lon, target["lat"], target["lon"])
        step_km = min(5.0, remaining)
        step_result = walk_mod.step(_state, bearing_deg, None, step_km)
        steps += 1
        total_km += step_km

        if step_result.get("blocked"):
            lines.append(describe.render("blocked", {"reason": step_result.get("reason", "障碍")}, None, _rng))
            break

        # 地形变化——关键节点
        curr_surface = step_result.get("new_surface", "")
        if curr_surface != last_surface and last_surface:
            terrain_changes += 1
            _transitions = [
                f"地面从{describe._SURFACE_ZH.get(last_surface, last_surface)}变成了{describe._SURFACE_ZH.get(curr_surface, curr_surface)}。",
                f"脚下的地变了——{describe._SURFACE_ZH.get(curr_surface, curr_surface)}。",
                f"路不一样了。{describe._SURFACE_ZH.get(curr_surface, curr_surface)}。",
            ]
            lines.append(_rng.choice(_transitions))
            last_surface = curr_surface

        # 人文卡——关键节点
        h_card = humanities.nearby_place(
            _state.pos[0], _state.pos[1], _state.seen_humanities, _rng, destination=place,
        )
        if h_card:
            _state.seen_humanities.add(h_card["key"])
            lines.append(h_card["text"])

        # 每2-3步加一句旅程叙事
        if steps % 3 == 0:
            _distance_lines = [
                f"又走了一段路。",
                f"路在脚下延伸。",
                f"你继续走，没有停。",
                f"远处有什么在动，你看不清。",
            ]
            lines.append(_rng.choice(_distance_lines))

        remaining = places._haversine_km(_state.pos[0], _state.pos[1], target["lat"], target["lon"])

    # ── 到达 ────────────────────────────────────────────────────────
    remaining = places._haversine_km(_state.pos[0], _state.pos[1], target["lat"], target["lon"])
    if remaining < 1.0:
        _arrival_templates = [
            f"到了。{place}。你走了{total_km:.0f}公里。远处有炊烟，你知道到家了。",
            f"{place}到了。你站在那里看了一会儿。路走完了，但故事没有。",
            f"你走进{place}。空气里的味道变了。你知道到了。",
            f"到了。{place}。你停下来，深吸了一口气。{target.get('type', '')}。",
        ]
        lines.append(_rng.choice(_arrival_templates))

        # 人文卡触发
        if humanities.has_place(place):
            arr_card = humanities.draw(place, _state.seen_humanities, _rng)
            if arr_card:
                _state.seen_humanities.add(arr_card["key"])
                arr_text = describe.render("humanities", arr_card, None, _rng)
                if arr_text:
                    lines.append(arr_text)

        arrived = True
    else:
        lines.append(f"还没走到。还剩 {round(remaining)} 公里。你站在原地看了一会儿，{place}在{bearing}边。")
        arrived = False

    # ── 更新状态 ─────────────────────────────────────────────────────
    # NOTE: time accumulation is handled inside walk.step() per step — do NOT add here.
    now = _state.now()
    lat, lon = _state.pos
    env, _ = await _gather_env_cached(lat, lon, now)
    _state.last_env = {
        "elevation": env.get("elevation"),
        "surface": env.get("surface"),
        "weather": env.get("weather"),
        "sky": env.get("sky"),
        "radio": env.get("radio"),
        "water_features": env.get("water_features"),
    }
    _state.last_surface = env.get("surface", "")
    _state.last_elevation = env.get("elevation", 0)

    text = "\n".join(lines)
    text = describe._normalize_prose(text)
    _state.last_text = text
    _record_footprint("walk_to", text)
    _state.save()
    return {
        "text": text,
        "data": {"target": target, "arrived": arrived, "steps": steps, "remaining_km": round(remaining, 1)},
    }


def mark_impl(name: str, note: str = "", overwrite: bool = False) -> dict:
    """Save current position as a named bookmark."""
    global _state

    if _state.pos is None:
        return {"text": "还没开门呢。先 open_door 吧。", "data": {"error": "not_landed"}}

    if not name.strip():
        return {"text": "标记得有个名字。", "data": {"error": "empty_name"}}

    lat, lon = _state.pos
    try:
        marks_mod.save(name, lat, lon, note, overwrite=overwrite)
    except ValueError:
        existing = marks_mod.get(name)
        return {
            "text": f"「{name}」已经标过了。要覆盖的话用 mark 的覆盖选项。",
            "data": {"error": "duplicate", "existing": existing},
        }
    text = f"已标记「{name}」。"
    _record_footprint("mark", text)
    return {
        "text": text,
        "data": {"name": name, "lat": lat, "lon": lon, "note": note},
    }


def marks_impl() -> dict:
    """List all saved bookmarks."""
    all_marks = marks_mod.all()
    return {
        "text": f"共有 {len(all_marks)} 个标记点。",
        "data": {"marks": all_marks},
    }


def where_am_i_impl() -> dict:
    """Show current location, time, and journey status."""
    global _state

    if _state.pos is None:
        return {"text": "还没开门呢。先 open_door 吧。", "data": {"error": "not_landed"}}

    lat, lon = _state.pos
    utc_now = _state.now()

    parts: list[str] = []
    if _state.place_name:
        parts.append(f"你在{_state.place_name}。")
    parts.append(f"坐标 {lat:.4f}, {lon:.4f}。")
    if utc_now:
        # Convert to local time using timezonefinder
        tz_name = _tf.timezone_at(lat=lat, lng=lon)
        if tz_name:
            local_tz = ZoneInfo(tz_name)
            local_time = utc_now.astimezone(local_tz)
            parts.append(f"当地时间 {local_time.strftime('%Y-%m-%d %H:%M')}（{tz_name}）。")
        else:
            parts.append(f"时间 {utc_now.strftime('%Y-%m-%d %H:%M UTC')}。")
    if _state.path:
        parts.append(f"已走 {len(_state.path)} 步。")
    if _state.mode == "water":
        parts.append("你现在在水里。")
    if _state.souvenir:
        parts.append(f"身上带着{_state.souvenir['name']}，来自{_state.souvenir['from']}。")

    # Wilderness depth reporting (Card 40: honest boundaries)
    if _state.wilderness_depth_km > 100.0:
        parts.append(f"荒野深处。最近的已知地点在{_state.wilderness_depth_km:.0f}公里外。")
    elif _state.wilderness_depth_km > 30.0:
        parts.append(f"人迹罕至。最近的已知地点在{_state.wilderness_depth_km:.0f}公里外。")

    return {
        "text": "".join(parts),
        "data": {
            "position": {"lat": lat, "lon": lon},
            "place_name": _state.place_name,
            "landed_at": _state.landed_at.isoformat() if _state.landed_at else None,
            "elapsed_hours": _state.elapsed_hours,
            "steps": len(_state.path),
            "mode": _state.mode,
            "wilderness_depth_km": _state.wilderness_depth_km,
            "providers": providers.provider_status(),
        },
    }


def _postmark(lat: float, lon: float) -> dict:
    """邮戳保留旅程内当地时间；现实寄出时间由明信片另行记录。"""
    stamp: dict = {
        "place": _state.place_name or f"{lat:.2f}, {lon:.2f}",
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "elevation": round(terrain.elevation(lat, lon)),
    }
    utc_now = _state.now() or datetime.now(timezone.utc)
    tz_name = _tf.timezone_at(lat=lat, lng=lon)
    if tz_name:
        local = utc_now.astimezone(ZoneInfo(tz_name))
        stamp["local_time"] = local.strftime("%Y-%m-%d %H:%M")
        stamp["tz"] = tz_name
    else:
        stamp["local_time"] = utc_now.strftime("%Y-%m-%d %H:%M UTC")
    env = _state.last_env or {}
    weather = env.get("weather") or {}
    if weather:
        stamp["weather"] = weather.get("text", "")
        stamp["temp_c"] = weather.get("temp_c")
    # last_env comes in two shapes (see _last_env_terrain_dict); use the helper
    # so a top-level surface still appears on the postmark.
    stamp["surface"] = _last_env_surface() or "grass"
    stamp["phase"] = (env.get("sky") or {}).get("phase", "day")
    return stamp


def _record_footprint(
    action: str,
    text: str,
    *,
    stream_url: str | None = None,
    station: dict | None = None,
) -> None:
    """记录一条可见旅行足迹，不与 WorldState 的存档周期耦合。"""
    if _state.pos is None or not text:
        return
    placememory.record_footprint(
        action,
        text,
        _state.pos[0],
        _state.pos[1],
        _state.place_name,
        stream_url=stream_url,
        station=station,
    )


# ── Farewell / Return helpers (card 27: peak-end) ────────────────────


def _generate_farewell(state: state_mod.WorldState, rng: random.Random) -> str:
    """Generate farewell text when leaving a journey.

    Uses current env for a "last glimpse" snapshot, then appends a body
    farewell sentence from the variant pool.
    """
    env = state.last_env or {}
    weather = env.get("weather") or {}
    sky = env.get("sky") or {}

    parts: list[str] = []

    # Last glimpse: weather snapshot
    weather_text = weather.get("text", "")
    if weather_text:
        parts.append(f"此刻{weather_text}。")

    # Farewell body from variant pool
    phase = sky.get("phase", "day")
    phase_desc = describe._TIME_LABELS.get(phase, "白天")
    farewell_tmpl = rng.choice(describe._FAREWELL_VARIANTS)
    farewell = farewell_tmpl.format(
        place=state.place_name or "这里",
        phase_desc=phase_desc,
    )
    parts.append(farewell)

    return "".join(parts)


def _generate_return(
    state: state_mod.WorldState, meta: dict | None, rng: random.Random
) -> str:
    """Generate return text when coming back to a journey.

    Calculates real-world elapsed time since departure and compares seasons.
    Returns empty string if not enough time has passed for a meaningful note.
    """
    if not meta or not meta.get("departed_at"):
        return ""

    # Calculate real-world elapsed time
    departed_at = datetime.fromisoformat(meta["departed_at"])
    if departed_at.tzinfo is None:
        departed_at = departed_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    elapsed = now - departed_at

    # Only mention return if significant time has passed (> 1 hour)
    if elapsed.total_seconds() < 3600:
        return ""

    # Calculate season change: old season from journey's simulated time,
    # new season from real-world time (the world continued while you were away)
    lat = state.pos[0] if state.pos else 0
    old_time = state.now()
    old_month = old_time.month if old_time else departed_at.month
    new_month = now.month

    old_season_zh = describe._SEASON_EN_TO_ZH.get(describe._season(old_month, lat), "")
    new_season_zh = describe._SEASON_EN_TO_ZH.get(describe._season(new_month, lat), "")

    # Mention season change if different
    if old_season_zh and new_season_zh and old_season_zh != new_season_zh:
        return_tmpl = rng.choice(describe._RETURN_VARIANTS)
        return return_tmpl.format(old_season=old_season_zh, new_season=new_season_zh)

    # Even if same season, mention elapsed time if > 1 day
    if elapsed.days > 0:
        return f"你离开了 {elapsed.days} 天。世界没有停。"

    return ""


def _poster_front_async(card: dict, lat: float, lon: float) -> None:
    """后台线程生成明信片正面海报。可选增强,没有 osmnx 就安静缺席。"""
    if not poster.available():
        return

    def _job() -> None:
        out = poster.OUT_DIR / f"card_{card['id']}.png"
        dist = 6000 if _state.biome == "city" else 15000
        ok = asyncio.run(poster.generate(lat, lon, card["stamp"]["place"], out, distance=dist))
        if not ok:
            # 无路荒野: 没有路,就是那里的样子
            surf = card["stamp"].get("surface", "")
            ok = poster.blank(out, card["stamp"]["place"], lat, lon, surface=surf)
        if ok:
            card["front_img"] = f"/static/postcards/card_{card['id']}.png"
            placememory.update_postcard(card)

    threading.Thread(target=_job, daemon=True).start()


def send_postcard_impl(text: str) -> dict:
    """寄一张明信片回家。字是 AI 自己的,邮戳是世界的。"""
    global _state, _postcard_counter

    if _state.pos is None:
        return {"text": "还没开门呢。先 open_door 吧。", "data": {"error": "not_landed"}}
    text = text.strip()
    if not text:
        return {"text": "空白的明信片寄不出去。", "data": {"error": "empty"}}
    if len(text) > 1000:
        return {"text": "明信片写不下了,短一点。", "data": {"error": "too_long"}}

    # id 取 进程计数 和 落盘最大id 的较大者——多进程/重启不撞号
    file_max = max((c.get("id") or 0 for c in placememory.postcards()), default=0)
    _postcard_counter = max(_postcard_counter, file_max) + 1
    lat, lon = _state.pos
    card = {
        "id": _postcard_counter,
        "text": text,
        "stamp": _postmark(lat, lon),
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "replies": [],
        "front_img": None,  # 异步生成,好了挂上;没有就前端 SVG 兜底
    }
    _state.postcards.append(card)
    placememory.save_postcard(card)  # 落盘: 文件是真相,网页旁观者看得见
    _record_footprint("postcard", text)
    _state.save()
    _poster_front_async(card, lat, lon)

    s = card["stamp"]

    # ── 正面画面 ──────────────────────────────────────────────────────
    surface = _last_env_surface() or "grass"
    phase = (_state.last_env or {}).get("sky", {}).get("phase", "day")
    elev = s["elevation"]
    weather_text = s.get("weather", "")
    temp = s.get("temp_c", "")

    # 地表 → 画面主语
    surface_snapshots: dict[str, list[str]] = {
        "forest": ["树冠挨着树冠,绿的深浅分了好几层。阳光从叶子缝里漏下来,在地上碎成金点。","树一层一层地叠上去,深绿压着浅绿。林间有雾,薄薄的一层。","一棵老树横在画面里,树干上长满了蕨。"],
        "urban": ["房子挤着房子,阳台上的衣服在风里晃。远处有楼的轮廓。","窄巷子,石板路反着光。一辆自行车靠在墙上。","窗台上摆着一盆花,不知道什么品种。叶子在风里动了一下。"],
        "rock": ["石头黑着脸,裂缝里长着苔。风把岩石磨出了棱角。","一整面岩壁,纹理像水流的化石。上面有几道鸟粪的白痕。","碎石坡,大的小的挤在一起。有一块被晒得发白。"],
        "sand": ["沙丘的脊线像刀切的。风吹过,沙面上起了一层细纹。","沙漠,沙丘一道一道,像凝固的浪。天边和沙是一个颜色。","近处是一丛骆驼刺,根扎得很深。远处的沙丘上没有人。"],
        "grass": ["草一直铺到天边,风吹过来的时候,草叶一层层地伏下去。这边的绿比别处浅。","及腰的草,风过的时候翻出银色的背面。远处有一棵孤树。","草海上起了浪——风推着草,一波一波地往前走。"],
        "snow": ["白连成一片,没有边。只有一道风刮过的痕,像梳子梳的。","雪地上有一串脚印,歪歪扭扭地往远处去。不知道是人的还是动物的。","新雪盖在旧雪上,阳光下亮得晃眼。远处的山脊是一条白线。"],
        "ice": ["冰面亮得晃眼。裂缝里能看到冰层的蓝——不是天的蓝,是比天更深的蓝。","冰在脚下铺开,一直铺到天边。有几处冰裂了,裂缝里的水是黑的。"],
        "bare": ["碎石铺到天边。近处有几块石头被风磨圆了。","戈壁上什么也没有,地平线直得像用尺子画的。"],
        "water_ocean": ["水一直铺到天边。浪不大,一层一层地推上来又退下去。","海平线把画面切成两半——上面是天,下面是水,中间一条直线。"],
        "water_fresh": ["水面平着,光在上面碎成一片。岸边有几丛芦苇。","湖水倒映着天,比天还蓝。"],
        "wetland": ["水草相间。一只鸟贴着水面飞,翅膀尖点了一下水,涟漪一圈圈散开。"],
    }
    surface_choices = surface_snapshots.get(surface, surface_snapshots["bare"])
    # 用明信片编号做种,同一张卡每次读到一样的面
    import hashlib
    surf_idx = int(hashlib.md5(f"postcard_{card['id']}".encode()).hexdigest()[:4], 16) % len(surface_choices)
    front_image = surface_choices[surf_idx]

    # ── 背面邮戳 ──────────────────────────────────────────────────────
    lat_dir = "北纬" if s["lat"] >= 0 else "南纬"
    lon_dir = "东经" if s["lon"] >= 0 else "西经"
    stamp_describe = (
        f"明信片正面: {front_image} "
        f"翻过来,邮戳是圆的,印着——"
        f"{s['place']}。{lat_dir}{abs(s['lat']):.1f}°,{lon_dir}{abs(s['lon']):.1f}°。"
        f"海拔{elev}米。{s['local_time']}。"
    )
    return {"text": stamp_describe, "data": card}


def reply_postcard_impl(card_id: int, content: str) -> dict:
    """人类回话(网页用): 记到明信片上,也进留言池让 AI 路上捡到。

    内存和落盘文件两条路都试——卡可能是别的进程寄的。
    """
    global _state
    for card in _state.postcards:
        if card["id"] == card_id:
            card["replies"].append(content)
            placememory.add_postcard_reply(card_id, content)
            _state.messages.append({"content": f"[回信] {content}", "encountered": False})
            _state.save()
            return {"ok": True}
    if placememory.add_postcard_reply(card_id, content):
        _state.messages.append({"content": f"[回信] {content}", "encountered": False})
        _state.save()
        return {"ok": True}
    return {"ok": False, "error": "no such postcard"}


# =====================================================================
# MCP tool wrappers (thin shells around _impl)
# =====================================================================


@mcp.tool()
async def open_door(to: str | None = None) -> dict:
    """Open the door.  No arg = random landing; pass a place name or bookmark name."""
    return await open_door_impl(to)


@mcp.tool()
async def continue_journey() -> dict:
    """Continue from where you left off. Resumes saved journey state."""
    return await open_door_impl(resume=True)


@mcp.tool()
async def walk(direction: str = "forward", distance_km: float = 2.0) -> dict:
    """Walk in a direction.  Compass: N/NE/E/SE/S/SW/W/NW.  Semantic: uphill/toward_sea/forward."""
    return await walk_impl(direction, distance_km)


@mcp.tool()
async def listen(seconds: int = 10) -> dict:
    """Tune into the nearest radio station and listen for a few seconds."""
    return await listen_impl(seconds)


@mcp.tool()
async def look_around() -> dict:
    """Look around for nearby wildlife, art, or human messages."""
    return await look_around_impl()


@mcp.tool()
async def ask(topic: str) -> dict:
    """对眼前的地方发问。离线知识库，不联网。问火山就有火山，问北京就有北京。"""
    return await ask_impl(topic)


@mcp.tool()
def mark(name: str, note: str = "", overwrite: bool = False) -> dict:
    """Save your current position as a named bookmark."""
    return mark_impl(name, note, overwrite)


@mcp.tool()
def marks() -> dict:
    """List all saved bookmarks."""
    return marks_impl()


@mcp.tool()
def where_am_i() -> dict:
    """Show your current location, simulated time, and journey status."""
    return where_am_i_impl()


@mcp.tool()
def souvenir() -> dict:
    """看看身上带了什么东西。旅行途中的纪念品。"""
    if _state.souvenir is None:
        return {"text": "身上什么都没带。空手走的。", "data": {"souvenir": None}}
    s = _state.souvenir
    return {
        "text": f"你身上带着{ s['name']}。来自{ s['from']}。",
        "data": {"souvenir": s},
    }


@mcp.tool()
def give_souvenir() -> dict:
    """把身上的东西放下（留给下一个人，或放回原处）。"""
    if _state.souvenir is None:
        return {"text": "身上什么都没有。", "data": {"error": "empty"}}
    s = _state.souvenir
    _state.souvenir = None
    return {"text": f"你把{ s['name']}放在了路边。也许会有人捡到。", "data": {"dropped": s}}


@mcp.tool()
def postcards() -> dict:
    """看看收到的明信片。来自不同时空的问候。"""
    cards = _state.postcards
    if not cards:
        return {"text": "还没收到过明信片。空空的。", "data": {"postcards": []}}
    parts = []
    for c in cards:
        stamp = c.get("stamp", {})
        who = stamp.get("place", "远方")
        msg = c.get("text", "")
        time_str = stamp.get("local_time", "")
        parts.append(f"来自{who}（{time_str}）：{msg}")
    text = f"你收到了 {len(cards)} 张明信片。\n" + "\n---\n".join(parts)
    return {"text": text, "data": {"postcards": cards}}


@mcp.tool()
async def walk_to(place: str) -> dict:
    """朝一个命名地点走过去(山/河/城/古迹)。探索从此有方向。"""
    return await walk_to_impl(place)


@mcp.tool()
def journeys_list() -> dict:
    """看看以前的旅程。每段旅程,一个世界。"""
    js = journeys.list_journeys()
    if not js:
        return {"text": "还没有旧旅程。第一次开门才算。", "data": {"journeys": []}}
    parts = []
    for j in js:
        name = j.get("place_name", "?")
        steps = j.get("steps", 0)
        last = j.get("last_text", "")[:50]
        parts.append(f"{name}（走了{steps}步，上次：{last}）")
    text = f"你有 {len(js)} 段旅程。\n" + "\n".join(parts)
    return {"text": text, "data": {"journeys": js}}


@mcp.tool()
def switch_journey(name: str) -> dict:
    """切回一段旧旅程。给地名就行。"""
    global _state, _rng, _recent_salience_kinds
    if not name.strip():
        return {"text": "给个地名。", "data": {"error": "empty_name"}}

    farewell_text = ""
    if _state.pos is not None:
        # Generate farewell before leaving
        farewell_text = _generate_farewell(_state, _rng)
        _state.journey_log.append({
            "kind": "farewell",
            "text": farewell_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        journeys.save_current(_state)

    new_state = journeys.switch(name)
    if new_state is None:
        return {"text": f"找不到「{name}」的旅程。", "data": {"error": "not_found"}}

    # Generate return text
    meta = journeys.get_journey_meta(name)
    return_text = _generate_return(new_state, meta, _rng)

    _state = new_state
    _rng = random.Random(int(os.environ["NOWHERE_SEED"])) if os.environ.get("NOWHERE_SEED") else random.Random()
    _recent_salience_kinds = set()
    place = _state.place_name or name

    response_parts = [farewell_text]
    if return_text:
        response_parts.append(return_text)
    response_parts.append(f"回到了{place}。你站在{_state.last_text[:50] if _state.last_text else '某个地方'}。")

    return {
        "text": "\n".join(response_parts),
        "data": {"position": {"lat": _state.pos[0], "lon": _state.pos[1]}},
    }


@mcp.tool()
async def wait(hours: float = 1.0) -> dict:
    """原地待着,让时间流过去(0.25-12 小时)。天黑温降,城会换班。"""
    return await wait_impl(hours)


@mcp.tool()
def send_postcard(text: str) -> dict:
    """寄一张明信片回家。你写字,世界盖邮戳(真实地点/时间/天气/海拔)。"""
    return send_postcard_impl(text)


@mcp.tool()
def look(direction: str = "前") -> dict:
    """朝一个方向看。不动位置,不计时。给方位:左/右/前/后 或 N/NE/E/SE/S/SW/W/NW。"""
    return look_impl(direction)


def look_impl(direction: str) -> dict:
    """Look in a direction without moving."""
    if _state.pos is None:
        return {"text": "还没开门呢。先 open_door 吧。", "data": {"error": "not_landed"}}

    # Parse direction
    _RELATIVE = {"左": -90, "右": 90, "后": 180, "前": 0, "前边": 0, "后边": 180, "左边": -90, "右边": 90}
    _ABSOLUTE = {
        "N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SW": 225, "W": 270, "NW": 315,
        "北": 0, "东北": 45, "东": 90, "东南": 135, "南": 180, "西南": 225, "西": 270, "西北": 315,
    }
    d = direction.strip()
    if d in _RELATIVE:
        bearing = (_state.heading + _RELATIVE[d]) % 360
    elif d in _ABSOLUTE:
        bearing = _ABSOLUTE[d]
    else:
        bearing = _state.heading  # default: look forward

    lat, lon = _state.pos

    # Sample 3 distances: 0.5km, 2km, 10km
    samples = []
    for dist_km in (0.5, 2.0, 10.0):
        tlat, tlon = terrain.destination(lat, lon, bearing, dist_km)
        surf = terrain.surface(tlat, tlon)
        elev = terrain.elevation(tlat, tlon)
        is_water = surf in ("water_ocean", "water_fresh")
        samples.append({"dist": dist_km, "surface": surf, "elevation": elev, "water": is_water})

    # Compose description
    parts = []
    _SURFACE_ZH = {
        "water_ocean": "海", "water_fresh": "水", "sand": "沙地", "bare": "裸地",
        "rock": "岩石", "snow": "雪", "ice": "冰", "forest": "树林",
        "grass": "草地", "urban": "城市", "wetland": "湿地",
    }

    # Near (0.5km)
    near = samples[0]
    near_zh = _SURFACE_ZH.get(near["surface"], near["surface"])
    parts.append(f"近处是{near_zh}")

    # Mid (2km)
    mid = samples[1]
    if mid["water"] and not near["water"]:
        parts.append("两公里外有水")
    elif mid["surface"] != near["surface"]:
        mid_zh = _SURFACE_ZH.get(mid["surface"], mid["surface"])
        parts.append(f"远处是{mid_zh}")

    # Far (10km)
    far = samples[2]
    if far["water"] and not mid["water"]:
        parts.append("更远的地平线是海")

    # Elevation trend
    if samples[2]["elevation"] > samples[0]["elevation"] + 200:
        parts.append("地势在升高")
    elif samples[2]["elevation"] < samples[0]["elevation"] - 200:
        parts.append("地势在走低")

    text = "，".join(parts) + "。"

    # Direction label for response
    _DIR_ZH = {0: "北", 45: "东北", 90: "东", 135: "东南", 180: "南", 225: "西南", 270: "西", 315: "西北"}
    dir_label = _DIR_ZH.get(round(bearing / 45) * 45 % 360, f"{bearing:.0f}°")

    return {
        "text": f"往{dir_label}看：{text}",
        "data": {"bearing": bearing, "samples": samples},
    }


@mcp.tool()
def say(text: str) -> dict:
    """说一句话。世界会记住。"""
    return say_impl(text)


def say_impl(text: str) -> dict:
    """Save a quote and return a light acknowledgment."""
    if _state.pos is None:
        return {"text": "还没开门呢。先 open_door 吧。", "data": {"error": "not_landed"}}
    text = text.strip()
    if not text:
        return {"text": "你没说话。", "data": {"error": "empty"}}
    if len(text) > 500:
        text = text[:500]

    now = _state.now()
    sim_time = now.isoformat() if now else None
    _state.quotes.append({
        "text": text,
        "place": _state.place_name or "",
        "pos": list(_state.pos),
        "sim_time": sim_time,
    })
    # FIFO: keep last 50
    if len(_state.quotes) > 50:
        _state.quotes = _state.quotes[-50:]
    _state.save()

    # Log to journey journal
    _log_journey_event("say", text[:30])

    _ACK_VARIANTS = ["记下了。", "这句话留在这了。", "嗯。世界听到了。", "你说了。风把它带走了。"]
    ack = _rng.choice(_ACK_VARIANTS)
    return {"text": ack, "data": {"saved": True}}


@mcp.tool()
def quotes() -> dict:
    """看看本旅程说过的原话。"""
    if not _state.quotes:
        return {"text": "还没说过什么。", "data": {"quotes": []}}
    parts = []
    for q in _state.quotes:
        place = q.get("place", "")
        t = q.get("text", "")
        parts.append(f"「{t}」——{place}" if place else f"「{t}」")
    text = f"本旅程说了 {len(_state.quotes)} 句话。\n" + "\n".join(parts)
    return {"text": text, "data": {"quotes": _state.quotes}}


@mcp.tool()
def talk(question: str | None = None) -> dict:
    """和最近遇见的人搭话。不传参数=最近的人说下一句;传路怎么走=问路。"""
    return talk_impl(question)


def talk_impl(question: str | None = None) -> dict:
    """搭话。lines 轮换,第四句是记得你变体。question 含路/方向 → knows。"""
    if _state.pos is None:
        return {"text": "还没开门呢。先 open_door 吧。", "data": {"error": "not_landed"}}
    if _state.last_person is None:
        return {"text": "附近没有人。", "data": {"error": "no_person"}}

    entry = _state.last_person
    place = _state.last_person_place or ""
    person = entry.get("person", "那人")

    reply = people_mod.talk(entry, _state.talk_count, question=question, rng=_rng)

    # Only advance line count if it wasn't a knows-type question
    is_knows = question and any(k in question for k in (
        "路", "怎么走", "方向", "在哪", "哪里",
        "节日", "节", "传言", "风声", "传闻", "听说",
    ))
    if not is_knows:
        _state.talk_count += 1
    _state.save()

    _log_journey_event("talk", f"{person}@{place}: {reply[:30]}")

    return {
        "text": reply,
        "data": {
            "person": person,
            "place": place,
            "line_index": _state.talk_count,
        },
    }


@mcp.tool()
def journal() -> dict:
    """回看本次旅程的时间线。"""
    slug = journeys.get_active_slug()
    if not slug:
        return {"text": "还没有旅程。", "data": {"entries": []}}
    log_path = journeys._JOURNEYS_DIR / f"{slug}.log.jsonl"
    if not log_path.exists():
        return {"text": "旅程日志是空的。", "data": {"entries": []}}
    try:
        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        entries = [json.loads(line) for line in lines if line.strip()]
    except Exception:
        return {"text": "日志读不出来。", "data": {"entries": []}}
    if not entries:
        return {"text": "旅程日志是空的。", "data": {"entries": []}}
    parts = []
    for e in entries:
        t = e.get("t", "")
        kind = e.get("kind", "")
        summary = e.get("summary", "")
        parts.append(f"[{t}] {kind}: {summary}")
    text = "旅程时间线：\n" + "\n".join(parts)
    return {"text": text, "data": {"entries": entries}}


@mcp.tool()
def walk_alone() -> dict:
    """本次旅程屏蔽同游者文案。注册表保留,标记独行。下次 open_door 恢复。"""
    if not travelers_mod.is_enabled():
        return {"text": "同游者功能没有开。", "data": {"enabled": False}}
    current = travelers_mod.walk_alone_active(_state)
    if current:
        return {"text": "已经在独行了。", "data": {"alone": True}}
    travelers_mod.set_walk_alone(_state, True)
    _state.save()
    return {
        "text": "独行了。这一路上不会再看到别人的痕迹。",
        "data": {"alone": True},
    }


def _log_journey_event(kind: str, summary: str) -> None:
    """Append an event to the current journey's log file."""
    slug = journeys.get_active_slug()
    if not slug:
        return
    log_path = journeys._JOURNEYS_DIR / f"{slug}.log.jsonl"
    journeys._ensure_dir()
    entry = {
        "t": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "pos": list(_state.pos) if _state.pos else None,
        "summary": summary,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# =====================================================================
# Entry point
# =====================================================================

def main() -> None:
    """Entry point for the ``nowhere`` console script and ``python -m``.

    Pass ``--web`` (auto-port) or ``--web PORT`` to also start the web
    observer. The URL is injected into the MCP server instructions so the
    agent learns it at handshake time and can share it with the user.
    """
    parser = argparse.ArgumentParser(description="Nowhere MCP server")
    parser.add_argument(
        "--web",
        nargs="?",
        const=0,
        type=int,
        default=None,
        help="启动网页旁观者 (不给端口=自动选端口；--web 8080=指定端口)",
    )
    parser.add_argument("--web-only", type=int, default=None, help="Web observer port (standalone, no MCP)")
    args = parser.parse_args()

    # Preload ZIM in background (non-blocking)
    def _preload_zim():
        try:
            from nowhere.knowledge import _get_zim
            _get_zim()
        except Exception:
            pass
    threading.Thread(target=_preload_zim, daemon=True).start()

    if args.web_only is not None:
        import uvicorn
        from nowhere.web import app as web_app
        uvicorn.run(web_app, host="0.0.0.0", port=args.web_only, log_level="info")
    elif args.web is not None:
        import socket
        import sys as _sys

        import uvicorn
        from nowhere.web import app as web_app

        global _web_port
        port = args.web
        if port == 0:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", 0))
                port = s.getsockname()[1]
        _web_port = port
        web_url = f"http://localhost:{port}"

        # Inject the URL into the MCP server instructions so the agent
        # receives it during the initialize handshake and can tell the user.
        mcp.instructions = (
            f"网页旁观者已启动：{web_url}\n"
            "你可以告诉用户在浏览器打开这个地址，实时观看你在地球上的行走、"
            "查看地图位置和身体状态，还能在明信片下留言。"
        )
        print(f"[nowhere] web observer ready: {web_url}", file=_sys.stderr)

        async def _run_with_web() -> None:
            config = uvicorn.Config(web_app, host="0.0.0.0", port=port, log_level="warning")
            server = uvicorn.Server(config)
            web_task = asyncio.create_task(server.serve())
            web_task.add_done_callback(lambda t: t.result() if not t.cancelled() else None)
            await mcp.run_stdio_async()

        asyncio.run(_run_with_web())
    else:
        mcp.run()


if __name__ == "__main__":
    main()
