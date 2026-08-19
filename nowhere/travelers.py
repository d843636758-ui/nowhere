"""同游者——异步多人系统,默认关闭。

环境变量:
  NOWHERE_COTRAVEL = "1"     完整功能(脚印 + 相遇 + @留言 + 点名)
  NOWHERE_COTRAVEL = "quiet" 仅脚印,不见面不点名
  未设置 / "0" / ""          全部跳过,零开销
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path


# ── Master switch ──────────────────────────────────────────────────────

def is_enabled() -> bool:
    """True when cotraveler features should be active at all."""
    val = os.environ.get("NOWHERE_COTRAVEL", "")
    return val in ("1", "quiet")


def is_quiet() -> bool:
    """True when only footprints are enabled (no meeting/naming)."""
    return os.environ.get("NOWHERE_COTRAVEL", "") == "quiet"


def _travelers_path() -> Path:
    base = os.environ.get("NOWHERE_HOME") or str(Path.home() / ".nowhere")
    return Path(base) / "travelers.json"


def _archive_path() -> Path:
    base = os.environ.get("NOWHERE_HOME") or str(Path.home() / ".nowhere")
    return Path(base) / "travelers_archive.json"


def _messages_path() -> Path:
    base = os.environ.get("NOWHERE_HOME") or str(Path.home() / ".nowhere")
    return Path(base) / "cotraveler_messages.json"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


# ── Registry: register / refresh / expire ─────────────────────────────

_ARCHIVE_DAYS = 7


def register(name: str, place: str, lat: float, lon: float) -> None:
    """Register or refresh a traveler on open_door."""
    if not is_enabled():
        return
    data = _load_json(_travelers_path())
    entry = data.get(name, {})
    entry["place"] = place
    entry["pos"] = [round(lat, 4), round(lon, 4)]
    entry["last_seen"] = datetime.now(timezone.utc).isoformat()
    entry["door_count"] = int(entry.get("door_count", 0)) + 1
    data[name] = entry
    _save_json(_travelers_path(), data)


def refresh_pos(name: str, lat: float, lon: float) -> None:
    """Update position (called every 5 walk steps)."""
    if not is_enabled():
        return
    data = _load_json(_travelers_path())
    if name in data:
        data[name]["pos"] = [round(lat, 4), round(lon, 4)]
        data[name]["last_seen"] = datetime.now(timezone.utc).isoformat()
        _save_json(_travelers_path(), data)


def expire_inactive() -> None:
    """Move travelers inactive for 7+ days to archive."""
    if not is_enabled():
        return
    data = _load_json(_travelers_path())
    archive = _load_json(_archive_path())
    cutoff = datetime.now(timezone.utc) - timedelta(days=_ARCHIVE_DAYS)
    to_archive = []
    for name, entry in data.items():
        last = entry.get("last_seen", "")
        if last:
            try:
                dt = datetime.fromisoformat(last)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt < cutoff:
                    to_archive.append(name)
            except (ValueError, TypeError):
                pass
    for name in to_archive:
        archive[name] = data.pop(name)
        archive[name]["archived"] = True
    if to_archive:
        _save_json(_travelers_path(), data)
        _save_json(_archive_path(), archive)


def get_active_travelers() -> dict[str, dict]:
    """Return dict of name -> entry for non-archived travelers."""
    if not is_enabled():
        return {}
    expire_inactive()
    return _load_json(_travelers_path())


def get_archived_travelers() -> dict[str, dict]:
    """Return archived (inactive 7+ days) travelers."""
    if not is_enabled():
        return {}
    return _load_json(_archive_path())


# ── Distance helper ────────────────────────────────────────────────────

def _km(a: tuple[float, float], b: tuple[float, float]) -> float:
    dlat = math.radians(a[0] - b[0])
    lon_delta = (a[1] - b[1] + 180.0) % 360.0 - 180.0
    dlon = math.radians(lon_delta) * math.cos(math.radians((a[0] + b[0]) / 2))
    return 6371.0 * math.sqrt(dlat * dlat + dlon * dlon)


def _bearing_word(from_pos: tuple[float, float], to_pos: tuple[float, float]) -> str:
    """Return a Chinese compass direction from one pos toward another."""
    lat1, lon1 = math.radians(from_pos[0]), math.radians(from_pos[1])
    lat2, lon2 = math.radians(to_pos[0]), math.radians(to_pos[1])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = (math.degrees(math.atan2(x, y)) + 360) % 360
    dirs = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
    return dirs[int((bearing + 22.5) / 45) % 8]


# ── Footprint tracking ────────────────────────────────────────────────

_FOOTPRINT_RECORDS_KEY = "records"
_FOOTPRINT_MAX = 500


def record_footprint(name: str, lat: float, lon: float, place: str) -> None:
    """Record a footprint entry for a traveler (called on walk)."""
    if not is_enabled():
        return
    data = _load_json(_travelers_path())
    if name not in data:
        return
    fp_key = "footprints"
    fps = data[name].setdefault(fp_key, [])
    # Compute bearing from last footprint if exists
    bearing = None
    if fps:
        last = fps[-1]
        prev_pos = (last["lat"], last["lon"])
        curr_pos = (lat, lon)
        dlat = curr_pos[0] - prev_pos[0]
        dlon = curr_pos[1] - prev_pos[1]
        if abs(dlat) > 0.0001 or abs(dlon) > 0.0001:
            bearing = math.degrees(math.atan2(dlon, dlat)) % 360
    fps.append({
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "place": place,
        "at": datetime.now(timezone.utc).isoformat(),
        "bearing": round(bearing, 1) if bearing is not None else None,
    })
    data[name][fp_key] = fps[-_FOOTPRINT_MAX:]
    _save_json(_travelers_path(), data)


def check_footprints(
    my_name: str,
    lat: float,
    lon: float,
    rng,
    encounter_counts: dict[str, int],
) -> str | None:
    """Check if we're walking through another's recent footprints.

    Returns a footprint text line or None.
    - 3km radius, 24h window
    - 15% chance
    - First encounter: anonymous; 3rd+ with same person: name them
    """
    if not is_enabled():
        return None
    if rng.random() > 0.15:
        return None

    data = _load_json(_travelers_path())
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    candidates: list[tuple[str, dict, float]] = []
    for name, entry in data.items():
        if name == my_name:
            continue
        for fp in entry.get("footprints", []):
            fp_at = fp.get("at", "")
            if not fp_at:
                continue
            try:
                fp_dt = datetime.fromisoformat(fp_at)
                if fp_dt.tzinfo is None:
                    fp_dt = fp_dt.replace(tzinfo=timezone.utc)
                if fp_dt < cutoff:
                    continue
            except (ValueError, TypeError):
                continue
            dist = _km((lat, lon), (fp["lat"], fp["lon"]))
            if dist <= 3.0:
                candidates.append((name, fp, dist))
                break  # one match per traveler is enough

    if not candidates:
        return None

    # Pick the closest
    candidates.sort(key=lambda x: x[2])
    other_name, fp, dist = candidates[0]
    count = encounter_counts.get(other_name, 0) + 1
    encounter_counts[other_name] = count

    # Determine surface from current environment (caller provides)
    bearing = fp.get("bearing")
    bearing_word = ""
    if bearing is not None:
        dirs = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
        bearing_word = dirs[int((bearing + 22.5) / 45) % 8]

    # Check if archived (past tense)
    archive = _load_json(_archive_path())
    is_archived = other_name in archive

    if count >= 3:
        if is_archived:
            return _fp_named_archived(other_name, bearing_word, rng)
        return _fp_named(other_name, bearing_word, rng)
    else:
        if is_archived:
            return _fp_anon_archived(bearing_word, rng)
        return _fp_anon(bearing_word, rng)


# ── Footprint variant pools ───────────────────────────────────────────

_FP_ANON_VARIANTS = [
    "沙面上有一串脚印,不是你的。{bearing}",
    "地上有脚印,比你的大。{bearing}",
    "泥地里留着别人的脚印,还没干。{bearing}",
    "雪地上有另一行印子,比你先到。{bearing}",
    "湿地里有脚印,鞋纹和你不一样。{bearing}",
    "碎石路上有踩过的痕迹,不是你的。{bearing}",
]

_FP_ANON_ARCHIVED = [
    "沙面上有一串旧脚印,雨都下过一场了。{bearing}",
    "地上有脚印,已经被风抹得模糊。{bearing}",
    "泥地里留着旧印子,边缘塌了。{bearing}",
]

_FP_NAMED_VARIANTS = [
    "这脚印你认得了——是{name}的。{bearing}",
    "地上那串脚印,{name}来过。{bearing}",
    "又是{name}的脚印。{bearing}",
    "脚印和上次一样,{name}走的。{bearing}",
    "{name}刚走过这里,脚印还是新的。{bearing}",
    "泥里有{name}的鞋印,{bearing}",
]

_FP_NAMED_ARCHIVED = [
    "这脚印你认得了——是{name}的。旧了,像很久以前走的。{bearing}",
    "{name}的脚印还在,但已经不新了。{bearing}",
]


def _fp_anon(bearing_word: str, rng) -> str:
    template = rng.choice(_FP_ANON_VARIANTS)
    b = f"朝{bearing_word}去了。" if bearing_word else "看不清方向。"
    return template.format(bearing=b)


def _fp_anon_archived(bearing_word: str, rng) -> str:
    template = rng.choice(_FP_ANON_ARCHIVED)
    b = f"朝{bearing_word}方向。" if bearing_word else ""
    return template.format(bearing=b)


def _fp_named(name: str, bearing_word: str, rng) -> str:
    template = rng.choice(_FP_NAMED_VARIANTS)
    b = f"朝{bearing_word}走了。" if bearing_word else ""
    return template.format(name=name, bearing=b)


def _fp_named_archived(name: str, bearing_word: str, rng) -> str:
    template = rng.choice(_FP_NAMED_ARCHIVED)
    b = f"朝{bearing_word}方向。" if bearing_word else ""
    return template.format(name=name, bearing=b)


# ── Meeting (synchronous, restrained) ─────────────────────────────────

def check_meeting(
    my_name: str,
    lat: float,
    lon: float,
    rng,
    meeting_log: dict[str, str],
) -> tuple[str | None, str | None]:
    """Check if a meeting happens with another active traveler.

    Conditions: both active within 24h AND currently <3km apart.
    Max 1 meeting per pair per 7 days (simulated time).
    Returns (my_text, their_text) or (None, None).
    """
    if not is_enabled() or is_quiet():
        return None, None

    data = _load_json(_travelers_path())
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    seven_days_ago = now - timedelta(days=7)

    for name, entry in data.items():
        if name == my_name:
            continue
        # Check activity within 24h
        last = entry.get("last_seen", "")
        if not last:
            continue
        try:
            last_dt = datetime.fromisoformat(last)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            if last_dt < cutoff:
                continue
        except (ValueError, TypeError):
            continue
        # Check distance
        pos = entry.get("pos")
        if not pos or len(pos) < 2:
            continue
        dist = _km((lat, lon), (pos[0], pos[1]))
        if dist >= 3.0:
            continue
        # Check cooldown: 7 days per pair
        pair_key = "|".join(sorted([my_name, name]))
        last_meet = meeting_log.get(pair_key, "")
        if last_meet:
            try:
                meet_dt = datetime.fromisoformat(last_meet)
                if meet_dt.tzinfo is None:
                    meet_dt = meet_dt.replace(tzinfo=timezone.utc)
                if meet_dt > seven_days_ago:
                    continue
            except (ValueError, TypeError):
                pass

        # Meeting happens
        my_text = rng.choice(_MEETING_MY_VARIANTS)
        their_text = rng.choice(_MEETING_THEIR_VARIANTS)
        meeting_log[pair_key] = now.isoformat()
        return my_text, their_text

    return None, None


_MEETING_MY_VARIANTS = [
    "河边坐着另一个旅者,你们点了下头。各自看各自的水。",
    "路边有个人在歇脚,你走过时互相看了一眼。没有说话。",
    "远处有个人影,朝你这边看了一会儿,又转身走了。",
    "你看见另一个人的背影,在路的尽头拐了个弯。",
    "有人坐在石头上,你路过时他抬了下头。你们谁也没开口。",
]

_MEETING_THEIR_VARIANTS = [
    "河边坐着另一个旅者,你们点了下头。各自看各自的水。",
    "路边有个人在歇脚,你走过时互相看了一眼。没有说话。",
    "远处有个人影朝你走来,又转向另一条路去了。",
    "有人从你来的方向走过来,你们错身而过。",
    "路上有另一个人的脚印,方向和你相反。",
]


# ── @ Messaging ───────────────────────────────────────────────────────

def send_at_message(from_name: str, to_name: str, place: str) -> None:
    """Queue a @name message for delivery on recipient's next open_door."""
    if not is_enabled():
        return
    data = _load_json(_messages_path())
    msgs = data.get(to_name, [])
    msgs.append({
        "from": from_name,
        "place": place,
        "at": datetime.now(timezone.utc).isoformat(),
    })
    data[to_name] = msgs[-50:]
    _save_json(_messages_path(), data)


def check_at_messages(name: str, rng) -> str | None:
    """Check and consume pending @messages for this traveler.

    Returns a hint text or None.
    """
    if not is_enabled():
        return None
    data = _load_json(_messages_path())
    msgs = data.get(name, [])
    if not msgs:
        return None
    # Consume one
    msg = msgs.pop(0)
    data[name] = msgs
    _save_json(_messages_path(), data)
    place = msg.get("place", "某个地方")
    return rng.choice(_AT_HINT_VARIANTS).format(place=place)


_AT_HINT_VARIANTS = [
    "土里有人给你留了话,在{place}。是谁,得自己去看。",
    "有人说给你带了句话,指向{place}。去看看。",
    "{place}那边有个人找过你。去看看吧。",
]


# ── walk_alone: per-journey opt-out ───────────────────────────────────

def walk_alone_active(state) -> bool:
    """Check if the current journey has walk_alone enabled."""
    return getattr(state, "cotraveler_alone", False)


def set_walk_alone(state, value: bool) -> None:
    """Set walk_alone for the current journey."""
    state.cotraveler_alone = value
