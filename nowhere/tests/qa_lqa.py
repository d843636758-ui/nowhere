# -*- coding: utf-8 -*-
"""Card 24: 语义文本审计 — 三层 LQA (Language Quality Assurance).

三层:
  1. Batch Sampling  — 驱动真实渲染链,采集文本+env
  2. Rule-based      — 全量规则检查 (禁词/数字矛盾/场景错配/自称矛盾/多样性)
  3. LLM Judge       — 抽样裁判 (golden set 校验 → 分层抽样 → 事实/风格/复读)

只量不修。输出 qa_lqa_report.md (仓库根)。

Usage:
    cd C:\\Users\\84989\\Desktop\\nowhere_repo
    python nowhere/tests/qa_lqa.py
"""
from __future__ import annotations

import json
import math
import os
import pathlib
import random
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

# GBK console fix
sys.stdout.reconfigure(encoding="utf-8")

_REPO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))

from nowhere import (
    describe,
    humanities,
    localcolor,
    terrain,
    walk as walk_mod,
)
from nowhere.state import WorldState

# ── Paths ─────────────────────────────────────────────────────────────
_JSONL = _REPO / "nowhere" / "tests" / "qa_lqa_samples.jsonl"
_GOLDEN = _REPO / "nowhere" / "tests" / "qa_lqa_golden.json"
_REPORT = _REPO / "qa_lqa_report.md"

# ── Constants ─────────────────────────────────────────────────────────
_FORBIDDEN_WORDS = ["很", "非常", "十分"]
_PLACEHOLDER_RE = re.compile(r"\{[a-z_]+\}|%[sd]|None|￥|TODO|FIXME|XXX|<[^>]+>")
_DOUBLE_PERIOD_RE = re.compile(r"。。")
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")

# Temperature contradiction keywords (only phrases that describe AMBIENT temperature)
# Exclude volcanic/geothermal/food-related uses
_COLD_AMBIENT = ["寒风", "冷风", "冻得", "刺骨", "打哆嗦", "缩脖子", "呼出白气",
                 "呼吸白", "冻僵", "呵气成霜"]
_HOT_AMBIENT = ["热浪袭来", "闷热", "暑气", "热得", "汗流浃背", "中暑", "热浪逼人"]
# Broader checks (any occurrence, higher false positive rate)
_COLD_WORDS = ["寒风", "冷风", "冻得", "刺骨", "打哆嗦", "缩脖子"]
_HOT_WORDS = ["闷热", "暑气", "汗流浃背", "中暑"]

# Scene mismatch keywords
_DOCK_WORDS = ["码头", "渔船", "渔船", "海港", "灯塔", "灯塔", "靠岸", "泊船",
               "卸货", "桅杆", "船坞", "防波堤"]
_SNOW_WORDS = ["雪崩", "冰川", "冻土", "极光", "冰裂缝", "雪落", "积雪", "冰面",
               "冰封", "大雪纷飞", "雪花飘"]
_DESERT_WORDS = ["沙丘", "戈壁", "沙漠", "骆驼", "仙人掌", "绿洲"]
_WATER_BIOME = {"water_ocean", "water_fresh", "coast", "island"}

# Self-contradiction antonym pairs
_ANTONYM_PAIRS = [
    ("无人", "人声鼎沸"), ("无人", "人来人往"), ("无人", "熙熙攘攘"),
    ("空无一人", "拥挤"), ("荒凉", "繁华"), ("寂静", "嘈杂"),
    ("安静", "喧闹"), ("荒芜", "热闹"), ("孤独", "欢聚"),
]

# Landmark regex for place name drift (Chinese place names - more specific)
# Only match compound words that are clearly place names, not generic nouns
_PLACE_NAME_SUFFIXES = "(?:市|县|镇|村|省|州|区|寺|庙|塔|桥|港|湾|岛|宫|殿|楼|阁|亭)"
_PLACE_NAME_RE = re.compile(rf"[一-鿿]{{2,6}}{_PLACE_NAME_SUFFIXES}")
# Words that look like place suffixes but are just common nouns
_FALSE_PLACE_WORDS = {"火山", "小山", "大山", "高山", "深山", "远山", "近山",
                      "山顶", "山腰", "山脚", "山上", "山下", "山里",
                      "小岛", "孤岛", "群岛", "海岛", "岛上",
                      "大桥", "小桥", "石桥", "木桥",
                      "大湖", "小湖", "深湖", "湖泊",
                      "大海", "小海",
                      "大街", "小巷",
                      "寺庙",}


# ═══════════════════════════════════════════════════════════════════════
# Layer 1: Batch Sampling
# ═══════════════════════════════════════════════════════════════════════

def _load_explorable_places() -> list[str]:
    """Load place names with coords from explorable_index.json."""
    fp = _REPO / "nowhere" / "data" / "explorable_index.json"
    if not fp.exists():
        return []
    data = json.loads(fp.read_text(encoding="utf-8"))
    places = data.get("places", {})
    return [k for k, v in places.items()
            if isinstance(v, dict) and "lat" in v and "lon" in v]


def _load_localcolor_places() -> list[str]:
    """Load places from localcolor.json + regional files."""
    from nowhere import baked
    data_dir = _REPO / "nowhere" / "data"
    base = data_dir / "localcolor.json"
    places = set()
    if base.exists():
        d = json.loads(base.read_text(encoding="utf-8"))
        places.update(d.keys())
    for fname in ["localcolor_china.json", "localcolor_japan_korea_sea.json",
                  "localcolor_americas_africa_oceania.json"]:
        fp = data_dir / fname
        if fp.exists():
            d = json.loads(fp.read_text(encoding="utf-8"))
            places.update(d.keys())
    return list(places)


def _load_humanities_places() -> list[str]:
    """Load places from humanities.json + regional files."""
    data_dir = _REPO / "nowhere" / "data"
    base = data_dir / "humanities.json"
    places = set()
    if base.exists():
        d = json.loads(base.read_text(encoding="utf-8"))
        places.update(d.get("places", {}).keys())
    for fname in ["humanities_films.json", "humanities_historical.json"]:
        fp = data_dir / fname
        if fp.exists():
            d = json.loads(fp.read_text(encoding="utf-8"))
            if "places" in d and isinstance(d["places"], dict):
                places.update(d["places"].keys())
            else:
                places.update(k for k in d.keys() if not k.startswith("_"))
    return list(places)


def _simulated_times() -> list[dict]:
    """Return 3 simulated time configs: dawn, dusk, night."""
    return [
        {"name": "dawn", "hour": 5, "dt": datetime(2026, 7, 15, 5, 0, tzinfo=timezone.utc)},
        {"name": "dusk", "hour": 19, "dt": datetime(2026, 7, 15, 19, 0, tzinfo=timezone.utc)},
        {"name": "night", "hour": 23, "dt": datetime(2026, 7, 15, 23, 0, tzinfo=timezone.utc)},
    ]


def _hemisphere_offsets(lat: float) -> bool:
    """Return True if this is southern hemisphere."""
    return lat < 0


def layer1_batch_sample(max_places: int = 30, walk_steps: int = 5) -> list[dict]:
    """Drive real rendering chain: open_door + walk x N. Save to JSONL.

    Returns list of sample dicts with {place, text, env, action, time, hemisphere}.
    """
    print(f"\n{'='*60}")
    print(f"Layer 1: Batch Sampling ({max_places} places x 3 times x walk x{walk_steps})")
    print(f"{'='*60}")

    # Collect places from all sources
    lc_places = _load_localcolor_places()
    h_places = _load_humanities_places()
    explorable = _load_explorable_places()

    # Merge and deduplicate, prioritize localcolor/humanities
    all_places = list(dict.fromkeys(lc_places + h_places + explorable))

    if len(all_places) > max_places:
        rng = random.Random(42)
        # Stratified: take from each source proportionally
        lc_sample = rng.sample(lc_places, min(len(lc_places), max_places // 3))
        h_sample = rng.sample(h_places, min(len(h_places), max_places // 3))
        remaining = max_places - len(lc_sample) - len(h_sample)
        other = [p for p in all_places if p not in lc_sample and p not in h_sample]
        other_sample = rng.sample(other, min(len(other), remaining))
        all_places = list(dict.fromkeys(lc_sample + h_sample + other_sample))
    else:
        all_places = all_places[:max_places]

    print(f"  Places to test: {len(all_places)}")
    print(f"  (lc: {len(lc_places)}, humanities: {len(h_places)}, explorable: {len(explorable)})")

    samples: list[dict] = []
    times = _simulated_times()

    # Clean old JSONL
    if _JSONL.exists():
        _JSONL.unlink()

    for i, place in enumerate(all_places):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(all_places)} places...", flush=True)

        for tcfg in times:
            try:
                sample = _render_place_at_time(place, tcfg, walk_steps)
                if sample:
                    samples.extend(sample)
            except Exception as e:
                # Don't let one place crash the whole run
                samples.append({
                    "place": place, "action": "error", "time": tcfg["name"],
                    "text": "", "env": {}, "error": str(e)[:200],
                    "hemisphere": "unknown",
                })

    # Append wilderness points covering diverse biomes
    # Include tundra (high lat), desert (low lat inland), mountain (high elev)
    wilderness_points = [
        (70.0, 25.0),    # tundra (northern Norway)
        (-75.0, 130.0),  # tundra (Antarctica coast)
        (25.0, 45.0),    # desert (Saudi Arabia)
        (-23.0, 135.0),  # desert (Australia outback)
        (47.0, 10.0),    # mountain (Swiss Alps)
        (28.0, 86.0),    # mountain (Himalayas)
        (0.0, -60.0),    # rainforest (Amazon)
        (65.0, -18.0),   # tundra (Iceland)
    ]
    for lat, lon in wilderness_points:
        for tcfg in times:
            try:
                sample = _render_wilderness_at_time(lat, lon, tcfg, walk_steps)
                if sample:
                    samples.extend(sample)
            except Exception:
                pass

    # Save to JSONL
    with open(_JSONL, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"  Total samples: {len(samples)} (saved to {_JSONL.name})")
    return samples


def _run_async(coro):
    """Run an async coroutine, handling the case where no event loop exists."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result(timeout=30)
    return asyncio.run(coro)


def _render_place_at_time(place: str, tcfg: dict, walk_steps: int) -> list[dict]:
    """Render open_door + walk x N for one place at one time."""
    results = []
    rng = random.Random(hash(f"{place}_{tcfg['name']}") % (2**32))
    dt = tcfg["dt"]

    # Create fresh state
    state = WorldState()

    # Look up coords
    h_place = humanities.get_place_coords(place)
    if h_place:
        lat, lon = h_place["lat"], h_place["lon"]
    else:
        lc_data = localcolor._load().get(place)
        if lc_data and isinstance(lc_data, dict) and "lat" in lc_data:
            lat, lon = lc_data["lat"], lc_data["lon"]
        else:
            # Try places_patch.json
            patch = _REPO / "nowhere" / "data" / "places_patch.json"
            if patch.exists():
                pd = json.loads(patch.read_text(encoding="utf-8"))
                if place in pd:
                    v = pd[place]
                    if isinstance(v, dict):
                        lat, lon = v.get("lat", 0), v.get("lon", 0)
                    elif isinstance(v, list) and len(v) >= 2:
                        lat, lon = v[0], v[1]
                    else:
                        return []
                else:
                    return []
            else:
                return []

    hemisphere = "south" if lat < 0 else "north"

    # Simulate landing: build env from climate fallback (offline, no network)
    from nowhere import weather as weather_mod
    elev = 0.0
    try:
        elev = terrain.elevation(lat, lon)
    except Exception:
        pass

    # Get weather estimate
    try:
        weather = _run_async(
            weather_mod.current(lat, lon, elevation=elev, local_hour=tcfg["hour"])
        )
    except Exception:
        weather = {"temp_c": 15, "wind_ms": 5, "precip": "none", "text": "晴"}

    surface = "grass"
    try:
        surface = terrain.surface(lat, lon)
    except Exception:
        pass

    env = {
        "elevation": elev,
        "surface": surface,
        "weather": weather,
        "sky": {"phase": "night" if tcfg["hour"] >= 21 or tcfg["hour"] < 5 else "day"},
    }

    # Build state for rendering
    state.pos = (lat, lon)
    state.landed_at = dt
    state.place_name = place
    state.biome = _guess_biome(surface)

    # ── Landing text ──
    try:
        landing_text = _render_establish_offline(place, lat, lon, env, tcfg, rng)
    except Exception as e:
        landing_text = f"[error: {e}]"

    results.append({
        "place": place, "action": "land", "time": tcfg["name"],
        "text": landing_text, "env": {
            "temp_c": weather.get("temp_c"),
            "wind_ms": weather.get("wind_ms"),
            "precip": weather.get("precip"),
            "elevation": elev,
            "surface": surface,
            "biome": state.biome,
            "lat": lat, "lon": lon,
            "hour": tcfg["hour"],
        },
        "hemisphere": hemisphere,
    })

    # ── Walk steps ──
    last_surface = surface
    last_elev = elev
    for step_i in range(walk_steps):
        bearing = rng.uniform(0, 360)
        try:
            step_result = walk_mod.step(state, bearing, None, 2.0)
        except Exception:
            step_result = {"new_surface": last_surface, "slope_deg": 0,
                           "elevation_delta": 0, "dist_km": 2.0}

        new_surface = step_result.get("new_surface", last_surface)

        # Update state position (simplified: just move lat/lon a bit)
        import math as _math
        dist_km = step_result.get("dist_km", 2.0)
        bearing_rad = _math.radians(bearing)
        dlat = dist_km * _math.cos(bearing_rad) / 111.0
        dlon = dist_km * _math.sin(bearing_rad) / (111.0 * _math.cos(_math.radians(lat)))
        lat += dlat
        lon += dlon
        state.pos = (lat, lon)

        # Get new env
        try:
            new_elev = terrain.elevation(lat, lon)
        except Exception:
            new_elev = last_elev

        try:
            new_weather = _run_async(
                weather_mod.current(lat, lon, elevation=new_elev, local_hour=tcfg["hour"])
            )
        except Exception:
            new_weather = weather

        new_env = {
            "elevation": new_elev,
            "surface": new_surface,
            "weather": new_weather,
            "sky": env["sky"],
        }

        # Render walk text
        try:
            walk_text = _render_walk_offline(
                place, lat, lon, new_env, step_result, bearing, rng,
                last_surface=last_surface,
            )
        except Exception as e:
            walk_text = f"[error: {e}]"

        results.append({
            "place": place, "action": f"walk_{step_i+1}", "time": tcfg["name"],
            "text": walk_text,
            "env": {
                "temp_c": new_weather.get("temp_c"),
                "wind_ms": new_weather.get("wind_ms"),
                "precip": new_weather.get("precip"),
                "elevation": new_elev,
                "surface": new_surface,
                "biome": _guess_biome(new_surface),
                "lat": lat, "lon": lon,
                "hour": tcfg["hour"],
            },
            "hemisphere": hemisphere,
        })

        last_surface = new_surface
        last_elev = new_elev

    return results


def _render_wilderness_at_time(lat: float, lon: float, tcfg: dict, walk_steps: int) -> list[dict]:
    """Render for a random wilderness point (no named place)."""
    results = []
    rng = random.Random(hash(f"wild_{lat:.2f}_{lon:.2f}_{tcfg['name']}") % (2**32))
    dt = tcfg["dt"]

    from nowhere import weather as weather_mod
    elev = 0.0
    try:
        elev = terrain.elevation(lat, lon)
    except Exception:
        pass

    try:
        weather = _run_async(
            weather_mod.current(lat, lon, elevation=elev, local_hour=tcfg["hour"])
        )
    except Exception:
        weather = {"temp_c": 15, "wind_ms": 5, "precip": "none", "text": "晴"}

    surface = "grass"
    try:
        surface = terrain.surface(lat, lon)
    except Exception:
        pass

    env = {
        "elevation": elev, "surface": surface,
        "weather": weather,
        "sky": {"phase": "night" if tcfg["hour"] >= 21 or tcfg["hour"] < 5 else "day"},
    }

    hemisphere = "south" if lat < 0 else "north"
    biome = _guess_biome(surface)

    # Landing
    try:
        landing_text = _render_establish_offline(
            f"wild_{lat:.1f}_{lon:.1f}", lat, lon, env, tcfg, rng
        )
    except Exception as e:
        landing_text = f"[error: {e}]"

    results.append({
        "place": f"wild_{lat:.1f}_{lon:.1f}", "action": "land", "time": tcfg["name"],
        "text": landing_text,
        "env": {
            "temp_c": weather.get("temp_c"), "wind_ms": weather.get("wind_ms"),
            "precip": weather.get("precip"), "elevation": elev,
            "surface": surface, "biome": biome, "lat": lat, "lon": lon,
            "hour": tcfg["hour"],
        },
        "hemisphere": hemisphere,
    })

    # Walk
    last_surface = surface
    state = WorldState()
    state.pos = (lat, lon)
    state.landed_at = dt
    for step_i in range(walk_steps):
        bearing = rng.uniform(0, 360)
        try:
            step_result = walk_mod.step(state, bearing, None, 2.0)
        except Exception:
            step_result = {"new_surface": last_surface, "slope_deg": 0,
                           "elevation_delta": 0, "dist_km": 2.0}

        new_surface = step_result.get("new_surface", last_surface)
        import math as _math
        dist_km = step_result.get("dist_km", 2.0)
        bearing_rad = _math.radians(bearing)
        dlat = dist_km * _math.cos(bearing_rad) / 111.0
        dlon = dist_km * _math.sin(bearing_rad) / (111.0 * _math.cos(_math.radians(lat)))
        lat += dlat
        lon += dlon
        state.pos = (lat, lon)

        try:
            new_elev = terrain.elevation(lat, lon)
        except Exception:
            new_elev = elev

        try:
            new_weather = _run_async(
                weather_mod.current(lat, lon, elevation=new_elev, local_hour=tcfg["hour"])
            )
        except Exception:
            new_weather = weather

        new_env = {
            "elevation": new_elev, "surface": new_surface,
            "weather": new_weather, "sky": env["sky"],
        }

        try:
            walk_text = _render_walk_offline(
                f"wild_{lat:.1f}_{lon:.1f}", lat, lon, new_env, step_result,
                bearing, rng, last_surface=last_surface,
            )
        except Exception as e:
            walk_text = f"[error: {e}]"

        results.append({
            "place": f"wild_{lat:.1f}_{lon:.1f}", "action": f"walk_{step_i+1}",
            "time": tcfg["name"], "text": walk_text,
            "env": {
                "temp_c": new_weather.get("temp_c"), "wind_ms": new_weather.get("wind_ms"),
                "precip": new_weather.get("precip"), "elevation": new_elev,
                "surface": new_surface, "biome": _guess_biome(new_surface),
                "lat": lat, "lon": lon, "hour": tcfg["hour"],
            },
            "hemisphere": hemisphere,
        })

        last_surface = new_surface

    return results


def _guess_biome(surface: str) -> str:
    """Guess biome from surface type."""
    _map = {
        "urban": "city", "water_ocean": "coast", "water_fresh": "coast",
        "forest": "rainforest", "sand": "desert", "bare": "desert",
        "snow": "tundra", "ice": "tundra", "rock": "mountain", "grass": "grassland",
        "wetland": "wetland",
    }
    return _map.get(surface, "grassland")


def _render_establish_offline(
    place: str, lat: float, lon: float, env: dict, tcfg: dict, rng: random.Random,
) -> str:
    """Render landing text using describe.render_establish (offline, no network)."""
    weather = env.get("weather", {})
    sky = env.get("sky", {})
    cc = None
    try:
        from nowhere import country
        cc = country.country_code_of(lat, lon)
    except Exception:
        pass

    payload = {
        "place": place,
        "country_code": cc,
        "phase": sky.get("phase", "day"),
        "local_hour": tcfg["hour"],
        "surface": env.get("surface", "grass"),
        "weather": weather,
        "sound": "",
        "hooks": [],
        "nearby_places": "",
        "biome": _guess_biome(env.get("surface", "grass")),
        "elevation": env.get("elevation", 0),
        "lat": lat,
        "lon": lon,
        "month": 7,
    }

    text = describe.render_establish(payload, rng)

    # Add localcolor card
    local_card = localcolor.draw(place, set(), rng,
                                  local_hour=tcfg["hour"], country_code=cc)
    if local_card:
        text += local_card["text"]

    # Add a smell/soundscape for the biome
    biome = _guess_biome(env.get("surface", "grass"))
    smell_pool = describe._SMELL_BY_BIOME.get(biome, [])
    if smell_pool:
        text += rng.choice(smell_pool) + "。"

    return text


def _render_walk_offline(
    place: str, lat: float, lon: float, env: dict, step_result: dict,
    bearing: float, rng: random.Random, last_surface: str = "",
) -> str:
    """Render walk text using describe.render (offline, no network)."""
    sections: list[str] = []

    # Terrain
    terrain_payload = {
        "surface": step_result.get("new_surface", env.get("surface", "grass")),
        "elevation": env.get("elevation", 0),
        "slope_deg": step_result.get("slope_deg", 0),
        "elevation_delta": step_result.get("elevation_delta", 0),
        "biome": _guess_biome(env.get("surface", "grass")),
    }
    t = describe.render("terrain", terrain_payload, None, rng,
                        biome=terrain_payload["biome"],
                        elevation=terrain_payload["elevation"])
    if t:
        sections.append(t)

    # Soundscape
    from nowhere import soundscape
    sound = soundscape.describe_sound(
        {"weather": env.get("weather", {}), "sky": env.get("sky", {}),
         "surface": env.get("surface", ""), "mode": "land"}, rng
    )
    if sound:
        sections.append(sound)

    # Smell
    biome = _guess_biome(env.get("surface", "grass"))
    smell_pool = describe._SMELL_BY_BIOME.get(biome, [])
    if smell_pool:
        sections.append(rng.choice(smell_pool) + "。")

    # Compose
    text = describe.compose(sections, rng)

    # sanity_check
    month = 7
    season = describe._season(month, lat)
    text = describe.sanity_check(text, {**env, "_season": season})

    return text


# ═══════════════════════════════════════════════════════════════════════
# Layer 2: Rule-based Checks
# ═══════════════════════════════════════════════════════════════════════

class Bug:
    """A single LQA bug."""
    def __init__(self, bug_id: str, severity: str, phenomenon: str,
                 reproduction: str, root_cause_guess: str = "",
                 place: str = "", action: str = "", text: str = ""):
        self.id = bug_id
        self.severity = severity
        self.phenomenon = phenomenon
        self.reproduction = reproduction
        self.root_cause_guess = root_cause_guess
        self.place = place
        self.action = action
        self.text = text

    def to_dict(self) -> dict:
        return {
            "id": self.id, "severity": self.severity,
            "phenomenon": self.phenomenon,
            "reproduction": self.reproduction,
            "root_cause_guess": self.root_cause_guess,
            "place": self.place, "action": self.action,
        }


def layer2_rule_check(samples: list[dict]) -> list[Bug]:
    """Run all rule-based checks on the sampled text."""
    print(f"\n{'='*60}")
    print(f"Layer 2: Rule-based Checks ({len(samples)} samples)")
    print(f"{'='*60}")

    bugs: list[Bug] = []
    bug_counter = 0

    for s in samples:
        text = s.get("text", "")
        env = s.get("env", {})
        place = s.get("place", "")
        action = s.get("action", "")

        if not text or text.startswith("[error"):
            continue

        def _add(severity, phenomenon, root_cause="", extra_id=""):
            nonlocal bug_counter
            bug_counter += 1
            bid = f"R{bug_counter:04d}"
            if extra_id:
                bid = extra_id
            bugs.append(Bug(
                bid, severity, phenomenon,
                reproduction=f"place={place}, action={action}, time={s.get('time')}, "
                             f"temp={env.get('temp_c')}, biome={env.get('biome')}, "
                             f"lat={env.get('lat', 0):.2f}",
                root_cause_guess=root_cause,
                place=place, action=action, text=text,
            ))

        # ── S3: Forbidden words ──
        for w in _FORBIDDEN_WORDS:
            if w in text:
                _add("S3", f"禁词「{w}」出现在渲染文本中",
                     "模板或卡片中残留禁词,describe.py 规则要求禁止")

        # ── S3: Placeholder residues ──
        placeholders = _PLACEHOLDER_RE.findall(text)
        if placeholders:
            _add("S3", f"占位符残留: {placeholders[:3]}",
                 "模板未正确格式化,或数据字段缺失")

        # ── S3: None leak ──
        if "None" in text and "None" not in place:
            _add("S3", "None 泄漏到输出文本",
                 "某个字段返回 None 而非空串,拼接时未过滤")

        # ── S3: Double periods ──
        if "。。" in text:
            _add("S3", "双句号 (。。)",
                 "模板中句号拼接未清理,sanity_check 未覆盖")

        # ── S3: Missing period concatenation (known bug pattern) ──
        # Detect: smell description ending with "雪" directly followed by
        # sound description starting with "风声" without punctuation
        # Pattern: "像刚下过雪风声大" — NOT "雪风从山顶" (compound word)
        _missing_punct = re.compile(r"过雪风声")
        mp = _missing_punct.findall(text)

        # ── S1: Number contradiction ──
        temp_c = env.get("temp_c")
        if temp_c is not None:
            if temp_c > 25:
                for w in _COLD_WORDS:
                    if w in text:
                        _add("S1", f"温度 {temp_c} 度但文本说「{w}」",
                             "温度数据与文本体感矛盾,场景过滤未生效")
                        break
            if temp_c < 0:
                for w in _HOT_WORDS:
                    if w in text:
                        _add("S1", f"温度 {temp_c} 度但文本说「{w}」",
                             "温度数据与文本体感矛盾,场景过滤未生效")
                        break

        # ── S2: Place name drift ──
        place_names = _PLACE_NAME_RE.findall(text)
        # Filter out false positives (generic nouns that happen to have suffix)
        place_names = [p for p in place_names if p not in _FALSE_PLACE_WORDS]
        if len(place_names) >= 2:
            unique_names = set(place_names)
            if len(unique_names) >= 2:
                # Exclude "from A to B" patterns
                if not re.search(r"从.{2,8}到.{2,8}", text):
                    # Additional check: exclude if all names are substrings of place
                    # (e.g., "黄山" text mentioning "山" in different compounds)
                    if place not in "".join(unique_names):
                        _add("S2", f"地名漂移: 同段出现 {unique_names}",
                             "多张卡拼接时地名未统一")

        # ── S2: Scene mismatch (dock words inland) ──
        biome = env.get("biome", "")
        lat = env.get("lat", 0)
        lon = env.get("lon", 0)

        if biome not in _WATER_BIOME and biome not in ("", "unknown"):
            for w in _DOCK_WORDS:
                if w in text:
                    # Check distance from coast (rough: not coastal biome)
                    _add("S2", f"内陆 biome ({biome}) 出现海港词「{w}」",
                         "场景过滤未覆盖内陆情况")
                    break

        # ── S2: Snow words in tropics ──
        if abs(lat) < 23.5 and (env.get("elevation", 0) or 0) < 2000:
            for w in _SNOW_WORDS:
                if w in text and biome not in ("tundra",):
                    _add("S2", f"热带低海拔出现雪词「{w}」",
                         "纬度/海拔过滤未生效")
                    break

        # ── S2: Desert words in water biome ──
        if biome in _WATER_BIOME:
            for w in _DESERT_WORDS:
                if w in text:
                    _add("S2", f"水域 biome 出现沙漠词「{w}」",
                         "biome 场景过滤遗漏")
                    break

        # ── S1: Self-contradiction ──
        for a, b in _ANTONYM_PAIRS:
            if a in text and b in text:
                _add("S1", f"自称矛盾:「{a}」与「{b}」同段出现",
                     "多张卡拼接时语义冲突")

    # ── S3: Missing period concatenation (dedicated pass) ──
    # The known bug: smell description ending with "雪" (from "像刚下过雪")
    # directly followed by "风声" (from soundscape) without period
    # Pattern: "像刚下过雪风声大" — NOT "雪风从山顶" (which is a compound word)
    for s in samples:
        text = s.get("text", "")
        if not text:
            continue
        # Specific: "过雪" followed by "风声" without punctuation
        if re.search(r"过雪风声", text):
            already = any(b.place == s.get("place") and "缺句号" in b.phenomenon
                         for b in bugs)
            if not already:
                bug_counter += 1
                bugs.append(Bug(
                    f"R{bug_counter:04d}", "S3",
                    "缺句号拼接断气: 「雪」与「风声」之间缺少句号 (已知 bug 复现)",
                    reproduction=f"place={s.get('place')}, action={s.get('action')}, "
                                 f"time={s.get('time')}",
                    root_cause_guess="describe.compose() 中 smell 描述末尾无标点,与 soundscape 拼接断气",
                    place=s.get("place", ""), action=s.get("action", ""),
                    text=text,
                ))

    # Count by severity
    sev_counts = Counter(b.severity for b in bugs)
    print(f"  Bugs found: {len(bugs)}")
    for s in ["S1", "S2", "S3", "S4"]:
        print(f"    {s}: {sev_counts.get(s, 0)}")

    return bugs


# ═══════════════════════════════════════════════════════════════════════
# Layer 2b: Diversity Quantification (ERA)
# ═══════════════════════════════════════════════════════════════════════

def layer2_diversity(sample_places: list[str], n_runs: int = 30) -> list[dict]:
    """ERA: Same place/time run walk N times, measure dedup rate.

    Returns list of {place, layer, n_runs, n_unique, dedup_rate, variants}.
    """
    print(f"\n{'='*60}")
    print(f"Layer 2b: Diversity Quantification (ERA, {n_runs} runs each)")
    print(f"{'='*60}")

    # Pick top places (diverse selection)
    test_places = sample_places[:15] if len(sample_places) >= 15 else sample_places
    results: list[dict] = []

    for place in test_places:
        for time_name, hour in [("dawn", 5), ("dusk", 19), ("night", 23)]:
            texts: list[str] = []
            for run_i in range(n_runs):
                try:
                    rng = random.Random(hash(f"era_{place}_{time_name}_{run_i}") % (2**32))
                    # Simulate walk rendering
                    h_place = humanities.get_place_coords(place)
                    if not h_place:
                        lc_data = localcolor._load().get(place)
                        if lc_data and isinstance(lc_data, dict) and "lat" in lc_data:
                            h_place = {"lat": lc_data["lat"], "lon": lc_data["lon"]}
                    if not h_place:
                        continue

                    lat, lon = h_place["lat"], h_place["lon"]
                    env = {
                        "elevation": 0, "surface": "grass",
                        "weather": {"temp_c": 15, "wind_ms": 5, "precip": "none"},
                        "sky": {"phase": "night" if hour >= 21 or hour < 5 else "day"},
                    }

                    # Render terrain
                    terrain_payload = {
                        "surface": "grass", "elevation": 0,
                        "slope_deg": 0, "elevation_delta": 0,
                        "biome": "grassland",
                    }
                    t = describe.render("terrain", terrain_payload, None, rng,
                                        biome="grassland")
                    texts.append(t)
                except Exception:
                    pass

            if not texts:
                continue

            unique = set(texts)
            dedup_rate = 1.0 - (len(unique) / len(texts)) if texts else 0

            results.append({
                "place": place,
                "layer": "terrain",
                "time": time_name,
                "n_runs": len(texts),
                "n_unique": len(unique),
                "dedup_rate": round(dedup_rate, 3),
                "variants": len(unique),
            })

    # Also check variant pool sizes
    variant_report = _check_variant_pool_sizes()

    # Find S4 bugs (dedup_rate > 0.3 means < 70% unique)
    s4_bugs: list[Bug] = []
    bug_counter = 0
    for r in results:
        if r["dedup_rate"] > 0.3:
            bug_counter += 1
            s4_bugs.append(Bug(
                f"D{bug_counter:04d}", "S4",
                f"多样性不足: {r['place']}@{r['time']} 去重率 {r['dedup_rate']:.1%} "
                f"(仅 {r['n_unique']} 个唯一变体 / {r['n_runs']} 次)",
                reproduction=f"place={r['place']}, time={r['time']}, layer={r['layer']}",
                root_cause_guess="渲染分支变体池太浅",
                place=r["place"],
            ))

    for vr in variant_report:
        if vr["count"] < 5:
            bug_counter += 1
            s4_bugs.append(Bug(
                f"D{bug_counter:04d}", "S4",
                f"变体池 <5: {vr['pool_name']} 仅 {vr['count']} 条",
                reproduction=f"pool={vr['pool_name']}",
                root_cause_guess="模板变体不足,需要扩充",
            ))

    print(f"  Diversity tests: {len(results)}")
    print(f"  Variant pool checks: {len(variant_report)}")
    print(f"  S4 bugs: {len(s4_bugs)}")

    return results, s4_bugs, variant_report


def _check_variant_pool_sizes() -> list[dict]:
    """Check all known variant pools for size < 5."""
    pools = []

    def _check(name, pool):
        if isinstance(pool, list):
            pools.append({"pool_name": name, "count": len(pool)})

    _check("_ARRIVE_VARIANTS", describe._ARRIVE_VARIANTS)
    _check("_WEATHER_ABS_VARIANTS", describe._WEATHER_ABS_VARIANTS)
    _check("_WEATHER_RAIN_VARIANTS", describe._WEATHER_RAIN_VARIANTS)
    _check("_WEATHER_SNOW_VARIANTS", describe._WEATHER_SNOW_VARIANTS)
    _check("_WEATHER_STORM_VARIANTS", describe._WEATHER_STORM_VARIANTS)
    _check("_WEATHER_DELTA_VARIANTS", describe._WEATHER_DELTA_VARIANTS)
    _check("_TERRAIN_VARIANTS", describe._TERRAIN_VARIANTS)
    _check("_TERRAIN_SCREE_VARIANTS", describe._TERRAIN_SCREE_VARIANTS)
    _check("_TERRAIN_FLAT_VARIANTS", describe._TERRAIN_FLAT_VARIANTS)
    _check("_TERRAIN_FLAT_GRASS_VARIANTS", describe._TERRAIN_FLAT_GRASS_VARIANTS)
    _check("_TERRAIN_FLAT_BARE_VARIANTS", describe._TERRAIN_FLAT_BARE_VARIANTS)
    _check("_TERRAIN_FLAT_ROCK_VARIANTS", describe._TERRAIN_FLAT_ROCK_VARIANTS)
    _check("_TERRAIN_FLAT_URBAN_VARIANTS", describe._TERRAIN_FLAT_URBAN_VARIANTS)
    _check("_TERRAIN_FLAT_WATER_VARIANTS", describe._TERRAIN_FLAT_WATER_VARIANTS)
    _check("_TERRAIN_HIGH_FLAT_VARIANTS", describe._TERRAIN_HIGH_FLAT_VARIANTS)
    _check("_SKY_NIGHT_VARIANTS", describe._SKY_NIGHT_VARIANTS)
    _check("_SKY_DAY_VARIANTS", describe._SKY_DAY_VARIANTS)
    _check("_SKY_DAY_LOW_VARIANTS", describe._SKY_DAY_LOW_VARIANTS)
    _check("_WATER_COLD_VARIANTS", describe._WATER_COLD_VARIANTS)
    _check("_WATER_COOL_VARIANTS", describe._WATER_COOL_VARIANTS)
    _check("_WATER_WARM_VARIANTS", describe._WATER_WARM_VARIANTS)
    _check("_LIFE_VARIANTS", describe._LIFE_VARIANTS)
    _check("_ART_VARIANTS", describe._ART_VARIANTS)
    _check("_RADIO_VARIANTS", describe._RADIO_VARIANTS)
    _check("_BLOCKED_VARIANTS", describe._BLOCKED_VARIANTS)
    _check("_MESSAGE_VARIANTS", describe._MESSAGE_VARIANTS)

    return pools


def layer2_length_check(samples: list[dict]) -> list[Bug]:
    """Check for landing text > 600 chars or walk text < 15 chars."""
    print(f"\n{'='*60}")
    print("Layer 2c: Length Distribution Check")
    print(f"{'='*60}")

    bugs: list[Bug] = []
    bug_counter = 0
    land_texts = [s for s in samples if s.get("action") == "land"]
    walk_texts = [s for s in samples if s.get("action", "").startswith("walk")]

    long_lands = 0
    short_walks = 0

    for s in land_texts:
        text = s.get("text", "")
        if len(text) > 600:
            long_lands += 1
            bug_counter += 1
            bugs.append(Bug(
                f"L{bug_counter:04d}", "S4",
                f"落地文本过长: {len(text)} 字 (阈值 600)",
                reproduction=f"place={s.get('place')}, time={s.get('time')}",
                root_cause_guess="落地镜头信息过载,需要裁剪",
                place=s.get("place", ""),
            ))

    for s in walk_texts:
        text = s.get("text", "")
        if 0 < len(text) < 15:
            short_walks += 1
            bug_counter += 1
            bugs.append(Bug(
                f"L{bug_counter:04d}", "S4",
                f"walk 文本过短: {len(text)} 字 (阈值 15)「{text}」",
                reproduction=f"place={s.get('place')}, action={s.get('action')}, time={s.get('time')}",
                root_cause_guess="渲染分支未命中任何内容,返回空或极短",
                place=s.get("place", ""),
            ))

    pct_long = long_lands / len(land_texts) * 100 if land_texts else 0
    pct_short = short_walks / len(walk_texts) * 100 if walk_texts else 0
    print(f"  Landing texts > 600 chars: {long_lands}/{len(land_texts)} ({pct_long:.1f}%)")
    print(f"  Walk texts < 15 chars: {short_walks}/{len(walk_texts)} ({pct_short:.1f}%)")
    print(f"  S4 bugs: {len(bugs)}")

    return bugs


# ═══════════════════════════════════════════════════════════════════════
# Layer 3: LLM Judge
# ═══════════════════════════════════════════════════════════════════════

def _call_llm_judge(prompt: str) -> str | None:
    """Call LLM judge via SiliconFlow DeepSeek. Key from env var."""
    api_key = os.environ.get("SILICONFLOW_API_KEY", "")
    if not api_key:
        api_key = os.environ.get("SF_API_KEY", "")
    if not api_key:
        return None

    import urllib.request
    payload = json.dumps({
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.1,
    }).encode()

    req = urllib.request.Request(
        "https://api.siliconflow.cn/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return None


def layer3_llm_judge(samples: list[dict], rule_bugs: list[Bug]) -> dict:
    """LLM judge: validate golden set, then sample rule-passed texts."""
    print(f"\n{'='*60}")
    print("Layer 3: LLM Judge")
    print(f"{'='*60}")

    result = {
        "golden_agreement": None,
        "golden_details": [],
        "judge_bugs": [],
        "judge_available": False,
    }

    # ── Step 1: Validate against golden set ──
    if not _GOLDEN.exists():
        print("  Golden set not found, skipping judge validation")
        return result

    golden = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    print(f"  Golden set: {len(golden)} examples")

    # Build prompt for golden set validation
    _JUDGE_SYSTEM = """你是一位游戏本地化质量审核员(LQA Judge)。你的任务是判断中文旅行叙事文本的质量。

评分标准:
- S1 (严重): 事实错误、数字矛盾、自称矛盾、幻觉
- S2 (重大): 场景错配、地名漂移、文化区归错
- S3 (轻微): 禁词(很/非常/十分)、占位符残留、缺句号断气、格式问题
- S4 (打磨): 复读、变体池太浅、信息过载或死寂
- PASS: 无明显问题

只输出 JSON: {"label": "PASS|S1|S2|S3|S4", "reason": "简短说明"}"""

    # Test if LLM is available
    test_result = _call_llm_judge(f"{_JUDGE_SYSTEM}\n\n判断这段文本:\n温度 11 度,苔藓的味道,湿的。风声大。")
    if test_result is None:
        api_key = os.environ.get("SILICONFLOW_API_KEY", "") or os.environ.get("SF_API_KEY", "")
        if not api_key:
            print("  LLM judge unavailable: SILICONFLOW_API_KEY / SF_API_KEY not set")
        else:
            print("  LLM judge unavailable: API call failed")
        return result

    result["judge_available"] = True
    print("  LLM judge available, validating golden set...")

    correct = 0
    total = len(golden)
    details = []

    for g in golden:
        prompt = (
            f"{_JUDGE_SYSTEM}\n\n"
            f"环境: temp={g['env'].get('temp_c')}°C, biome={g['env'].get('biome')}, "
            f"hour={g['env'].get('hour')}, lat={g['env'].get('lat')}\n"
            f"文本: {g['text']}\n\n"
            f"这段文本质量如何?"
        )
        resp = _call_llm_judge(prompt)
        if resp is None:
            details.append({"id": g["id"], "golden": g["label"], "judge": "ERROR", "match": False})
            continue

        # Parse judge response
        judge_label = "UNKNOWN"
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[^}]+\}', resp)
            if json_match:
                parsed = json.loads(json_match.group())
                judge_label = parsed.get("label", "UNKNOWN")
            else:
                # Try to find label in text
                for label in ["S1", "S2", "S3", "S4", "PASS"]:
                    if label in resp:
                        judge_label = label
                        break
        except Exception:
            pass

        match = judge_label == g["label"]
        if match:
            correct += 1
        details.append({
            "id": g["id"], "golden": g["label"],
            "judge": judge_label, "match": match,
            "raw_response": resp[:200] if resp else "",
        })

    agreement = correct / total if total > 0 else 0
    result["golden_agreement"] = agreement
    result["golden_details"] = details
    print(f"  Golden set agreement: {correct}/{total} ({agreement:.1%})")

    if agreement < 0.80:
        print("  WARNING: Agreement < 80%, judge results NOT authoritative")
        return result

    # ── Step 2: Sample rule-passed texts for judge ──
    # Find texts that passed all rules
    rule_failed_places = {(b.place, b.action) for b in rule_bugs}
    passed_samples = [s for s in samples
                      if (s.get("place"), s.get("action")) not in rule_failed_places
                      and s.get("text") and not s.get("text", "").startswith("[error")]

    # Stratified sample: 10% from each place
    rng = random.Random(42)
    place_groups: dict[str, list[dict]] = defaultdict(list)
    for s in passed_samples:
        place_groups[s["place"]].append(s)

    judge_samples: list[dict] = []
    for place, group in place_groups.items():
        n = max(1, len(group) // 10)
        judge_samples.extend(rng.sample(group, min(n, len(group))))

    # Limit to 50 to control cost
    if len(judge_samples) > 50:
        judge_samples = rng.sample(judge_samples, 50)

    print(f"  Judge samples: {len(judge_samples)} (from {len(passed_samples)} rule-passed)")

    judge_bugs: list[Bug] = []
    bug_counter = 0

    for s in judge_samples:
        env = s.get("env", {})
        prompt = (
            f"{_JUDGE_SYSTEM}\n\n"
            f"环境: temp={env.get('temp_c')}°C, biome={env.get('biome')}, "
            f"hour={env.get('hour')}, lat={env.get('lat', 0):.1f}\n"
            f"地点: {s.get('place')}\n"
            f"文本: {s.get('text')}\n\n"
            f"这段旅行叙事文本质量如何?检查: 1)事实有据(对照env)? 2)场景对? 3)像人话? 4)有复读?"
        )
        resp = _call_llm_judge(prompt)
        if resp is None:
            continue

        judge_label = "PASS"
        reason = ""
        try:
            json_match = re.search(r'\{[^}]+\}', resp)
            if json_match:
                parsed = json.loads(json_match.group())
                judge_label = parsed.get("label", "PASS")
                reason = parsed.get("reason", "")
            else:
                for label in ["S1", "S2", "S3", "S4"]:
                    if label in resp:
                        judge_label = label
                        break
        except Exception:
            pass

        if judge_label != "PASS":
            bug_counter += 1
            judge_bugs.append(Bug(
                f"J{bug_counter:04d}", judge_label,
                f"LLM 裁判判定: {reason or judge_label}",
                reproduction=f"place={s.get('place')}, action={s.get('action')}, "
                             f"time={s.get('time')}",
                root_cause_guess="LLM 裁判发现的问题",
                place=s.get("place", ""), action=s.get("action", ""),
            ))

    result["judge_bugs"] = judge_bugs
    print(f"  Judge bugs: {len(judge_bugs)}")
    for s in ["S1", "S2", "S3", "S4"]:
        cnt = sum(1 for b in judge_bugs if b.severity == s)
        if cnt:
            print(f"    {s}: {cnt}")

    return result


# ═══════════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════════

def generate_report(
    samples: list[dict],
    rule_bugs: list[Bug],
    s4_diversity_bugs: list[Bug],
    s4_length_bugs: list[Bug],
    diversity_results: list[dict],
    variant_report: list[dict],
    judge_result: dict,
    elapsed: float,
) -> None:
    """Generate qa_lqa_report.md at repo root."""
    all_bugs = rule_bugs + s4_diversity_bugs + s4_length_bugs + judge_result.get("judge_bugs", [])
    sev_counts = Counter(b.severity for b in all_bugs)

    lines: list[str] = []
    lines.append("# QA LQA Report — Card 24: 语义文本审计")
    lines.append("")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**耗时**: {elapsed:.1f} 秒")
    lines.append(f"**样本数**: {len(samples)} (land + walk)")
    lines.append(f"**总 bug 数**: {len(all_bugs)}")
    lines.append("")

    # ── Summary by severity ──
    lines.append("## 按严重度汇总")
    lines.append("")
    lines.append("| 严重度 | 数量 | 说明 |")
    lines.append("|--------|------|------|")
    for s, desc in [("S1", "严重 (幻觉/数字矛盾/自称矛盾)"),
                    ("S2", "重大 (场景错配/地名漂移)"),
                    ("S3", "轻微 (禁词/格式/断气)"),
                    ("S4", "打磨 (多样性/长度)")]:
        cnt = sev_counts.get(s, 0)
        lines.append(f"| {s} | {cnt} | {desc} |")
    lines.append("")

    # ── S1 Bugs ──
    s1 = [b for b in all_bugs if b.severity == "S1"]
    if s1:
        lines.append("## S1: 严重问题")
        lines.append("")
        lines.append("| ID | 现象 | 复现输入 | 根因初判 |")
        lines.append("|----|------|----------|----------|")
        for b in s1[:30]:
            lines.append(f"| {b.id} | {b.phenomenon[:60]} | {b.reproduction[:80]} | {b.root_cause_guess[:50]} |")
        lines.append("")

    # ── S2 Bugs ──
    s2 = [b for b in all_bugs if b.severity == "S2"]
    if s2:
        lines.append("## S2: 重大问题")
        lines.append("")
        lines.append("| ID | 现象 | 复现输入 | 根因初判 |")
        lines.append("|----|------|----------|----------|")
        for b in s2[:30]:
            lines.append(f"| {b.id} | {b.phenomenon[:60]} | {b.reproduction[:80]} | {b.root_cause_guess[:50]} |")
        lines.append("")

    # ── S3 Bugs ──
    s3 = [b for b in all_bugs if b.severity == "S3"]
    if s3:
        lines.append("## S3: 轻微问题")
        lines.append("")
        lines.append("| ID | 现象 | 复现输入 | 根因初判 |")
        lines.append("|----|------|----------|----------|")
        for b in s3[:30]:
            lines.append(f"| {b.id} | {b.phenomenon[:60]} | {b.reproduction[:80]} | {b.root_cause_guess[:50]} |")
        lines.append("")

    # ── S4 Bugs (Diversity) ──
    s4_div = [b for b in s4_diversity_bugs]
    if s4_div:
        lines.append("## S4: 多样性不足 (ERA 量化)")
        lines.append("")
        lines.append("| ID | 现象 | 复现输入 | 根因初判 |")
        lines.append("|----|------|----------|----------|")
        for b in s4_div[:20]:
            lines.append(f"| {b.id} | {b.phenomenon[:80]} | {b.reproduction[:60]} | {b.root_cause_guess[:50]} |")
        lines.append("")

    # ── S4 Bugs (Length) ──
    s4_len = [b for b in s4_length_bugs]
    if s4_len:
        lines.append("## S4: 长度分布异常")
        lines.append("")
        lines.append("| ID | 现象 | 复现输入 |")
        lines.append("|----|------|----------|")
        for b in s4_len[:15]:
            lines.append(f"| {b.id} | {b.phenomenon[:80]} | {b.reproduction[:80]} |")
        lines.append("")

    # ── Diversity Table ──
    lines.append("## 多样性量化表 (最差 10 个地/层)")
    lines.append("")
    if diversity_results:
        sorted_div = sorted(diversity_results, key=lambda r: r["dedup_rate"], reverse=True)
        lines.append("| 地点 | 层 | 时段 | 运行次数 | 唯一变体 | 去重率 | 判定 |")
        lines.append("|------|------|------|----------|----------|--------|------|")
        for r in sorted_div[:10]:
            verdict = "S4 (池浅)" if r["dedup_rate"] > 0.3 else "PASS"
            lines.append(
                f"| {r['place'][:15]} | {r['layer']} | {r['time']} | "
                f"{r['n_runs']} | {r['n_unique']} | {r['dedup_rate']:.1%} | {verdict} |"
            )
        lines.append("")

    # ── Variant Pool Sizes ──
    lines.append("## 变体池大小清单 (<5 条的分支)")
    lines.append("")
    small_pools = [v for v in variant_report if v["count"] < 5]
    if small_pools:
        lines.append("| 池名 | 条数 | 判定 |")
        lines.append("|------|------|------|")
        for v in small_pools:
            lines.append(f"| {v['pool_name']} | {v['count']} | S4 |")
    else:
        lines.append("所有变体池 >= 5 条。")
    lines.append("")

    # ── Judge Validation ──
    lines.append("## LLM 裁判校验")
    lines.append("")
    if judge_result.get("golden_agreement") is not None:
        ga = judge_result["golden_agreement"]
        lines.append(f"**Golden set 一致率**: {ga:.1%} ({'达标' if ga >= 0.8 else '未达标,结果不采信'})")
        lines.append("")
        lines.append("| Golden ID | 标注 | 裁判 | 匹配 |")
        lines.append("|-----------|------|------|------|")
        for d in judge_result.get("golden_details", []):
            lines.append(f"| {d['id']} | {d['golden']} | {d['judge']} | {'Y' if d['match'] else 'N'} |")
    else:
        lines.append("LLM 裁判不可用 (未设置 SILICONFLOW_API_KEY / SF_API_KEY)。")
    lines.append("")

    # ── Three-layer comparison ──
    lines.append("## 三层对比")
    lines.append("")
    judge_bugs = judge_result.get("judge_bugs", [])
    lines.append("| 层 | 捕获 bug 数 | 说明 |")
    lines.append("|----|------------|------|")
    lines.append(f"| Layer 2 规则层 | {len(rule_bugs) + len(s4_diversity_bugs) + len(s4_length_bugs)} | 全量,免费,确定性 |")
    lines.append(f"| Layer 3 LLM 裁判 | {len(judge_bugs)} | 抽样 {len(judge_result.get('judge_details', []))} 条 "
                 f"({'可用' if judge_result.get('judge_available') else '不可用'}) |")
    lines.append(f"| 合计 | {len(all_bugs)} | |")
    lines.append("")

    # ── Known Bug Reproduction ──
    lines.append("## 已知 bug 复现")
    lines.append("")
    known_found = any("缺句号" in b.phenomenon for b in all_bugs)
    lines.append(f"- 「像刚下过雪风声大」缺句号拼接: {'已复现' if known_found else '未复现 (可能需要拉普兰种子)'}")
    lines.append("")

    # ── Notes ──
    lines.append("## 备注")
    lines.append("")
    lines.append(f"- 本次运行覆盖 {len(set(s.get('place','') for s in samples))} 个地点")
    lines.append("- 采样使用离线渲染(气候估算+模板),未联网获取实时天气/电台")
    lines.append("- 多样性测试使用 describe.render() 的 terrain 分支")
    lines.append("- LLM 裁判使用硅基流动 DeepSeek-V3 (需设置 SILICONFLOW_API_KEY 环境变量)")

    _REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Report written to: {_REPORT}")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    start = time.time()

    print("=" * 60)
    print("QA LQA — Card 24: 语义文本审计 (三层)")
    print("=" * 60)

    # ── Layer 1: Batch Sampling ──
    samples = layer1_batch_sample(max_places=30, walk_steps=5)

    # ── Layer 2: Rule-based Checks ──
    rule_bugs = layer2_rule_check(samples)

    # ── Layer 2b: Diversity (ERA) ──
    unique_places = list(dict.fromkeys(s.get("place", "") for s in samples if s.get("place")))
    diversity_results, s4_diversity_bugs, variant_report = layer2_diversity(unique_places)

    # ── Layer 2c: Length distribution ──
    s4_length_bugs = layer2_length_check(samples)

    # ── Layer 3: LLM Judge ──
    judge_result = layer3_llm_judge(samples, rule_bugs)

    elapsed = time.time() - start

    # ── Generate Report ──
    generate_report(
        samples, rule_bugs, s4_diversity_bugs, s4_length_bugs,
        diversity_results, variant_report, judge_result, elapsed,
    )

    # ── Summary ──
    all_bugs = rule_bugs + s4_diversity_bugs + s4_length_bugs + judge_result.get("judge_bugs", [])
    sev_counts = Counter(b.severity for b in all_bugs)
    print(f"\n{'='*60}")
    print(f"COMPLETE in {elapsed:.1f}s")
    print(f"  Samples: {len(samples)}")
    print(f"  Total bugs: {len(all_bugs)}")
    for s in ["S1", "S2", "S3", "S4"]:
        print(f"    {s}: {sev_counts.get(s, 0)}")
    if judge_result.get("golden_agreement") is not None:
        print(f"  Judge golden agreement: {judge_result['golden_agreement']:.1%}")
    print(f"  Report: {_REPORT}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
