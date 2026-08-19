"""Walk action registry -- Card 48.

Each if-block in walk_impl becomes an Action with should() + render().
Order = priority (节日/纪念日 > 时间轴 > 常规遭遇).
No event bus -- synchronous two-step (判断 + 渲染).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


# ── Context ─────────────────────────────────────────────────────────


@dataclass
class WalkContext:
    """All state an Action might need. Built once per walk step."""

    state: Any  # WorldState
    env: dict
    rng: random.Random
    step_result: dict
    lat: float
    lon: float
    now: datetime | None
    bearing: float | None
    semantic: str | None
    local_dt: Any  # datetime in local timezone, or None
    tz_name: str | None
    water_features: list[dict]
    is_deep_wilderness: bool
    wilderness_depth: float
    encounter_multiplier: float
    env_cached: bool
    prev_env: dict | None = None
    # Mutable inter-action state
    mishap_fired: bool = False


# ── Protocol ────────────────────────────────────────────────────────


class Action(Protocol):
    """A walk narrative slot."""

    name: str

    def should(self, ctx: WalkContext) -> bool: ...
    def render(self, ctx: WalkContext) -> str | None: ...


# ── Concrete Actions ────────────────────────────────────────────────


class RhythmAction:
    """立志节律: 这座城此刻正在发生的事 (季节门控)."""

    name = "rhythm"

    def should(self, ctx: WalkContext) -> bool:
        return ctx.local_dt is not None

    def render(self, ctx: WalkContext) -> str | None:
        from nowhere import localcolor

        place = ctx.state.place_name
        ld = ctx.local_dt
        rhythm = localcolor.rhythm_event(
            place, ld.hour, ctx.rng, ld.month,
            recent=ctx.state.recent_scenes,
            weekday=ld.weekday(),
        )
        return rhythm


class TimeaxisAction:
    """六根时间轴(Card 46): 最多2层,优先级排序."""

    name = "timeaxis"

    def should(self, ctx: WalkContext) -> bool:
        return ctx.now is not None and not ctx.env_cached

    def render(self, ctx: WalkContext) -> str | None:
        from nowhere.server import _compute_timeaxes

        layers = _compute_timeaxes(
            ctx.now, ctx.lat, ctx.lon,
            ctx.state.biome or "",
            ctx.env.get("sky", {}).get("phase", "day"),
            ctx.env.get("weather", {}).get("precip", "none"),
            ctx.water_features,
            ctx.state.seen_humanities,
            ctx.rng,
        )
        parts: list[str] = []
        recent_set = set(ctx.state.recent_scenes)
        for ta in layers:
            if ta["text"] not in recent_set:
                parts.append(ta["text"])
                ctx.state.recent_scenes.append(ta["text"])
        return "\n".join(parts) if parts else None


class HumanitiesAction:
    """人文卡: 走到附近触发(非随机)."""

    name = "humanities"

    def should(self, ctx: WalkContext) -> bool:
        return True

    def render(self, ctx: WalkContext) -> str | None:
        from nowhere import describe, humanities, placememory

        card = humanities.nearby_place(
            ctx.lat, ctx.lon, ctx.state.seen_humanities, ctx.rng,
        )
        if not card:
            return None
        ctx.state.seen_humanities.add(card["key"])
        placememory.save_seen_humanities(ctx.state.seen_humanities)
        text = describe.render("humanities", card, None, ctx.rng)
        if not text:
            return None
        if card.get("category") == "人物":
            name = card.get("ref", {}).get("name", "")
            text += f"\n{name}。这名字你记下了。ask 能问出更多。"
        return text


class PersonAction:
    """卡中人遇见: walk 落在该地 5km 内 -> sight."""

    name = "person"

    def should(self, ctx: WalkContext) -> bool:
        return not ctx.state.person_encountered_this_walk

    def render(self, ctx: WalkContext) -> str | None:
        from nowhere import people as people_mod

        local_month = ctx.local_dt.month if ctx.local_dt else (ctx.now.month if ctx.now else 7)
        hit = people_mod.find_nearby_person(
            ctx.lat, ctx.lon, local_month, ctx.state.seen_people, ctx.rng,
        )
        if not hit:
            return None
        ctx.state.person_encountered_this_walk = True
        ctx.state.last_person = hit["data"]
        ctx.state.last_person_place = hit["place"]
        ctx.state.talk_count = 0
        ctx.state.seen_people.add(f"{hit['place']}/{hit['person']}")
        return hit["sight"]


class MishapAction:
    """意外层(Card 28): 3% per step, 10-step cooldown."""

    name = "mishap"

    def should(self, ctx: WalkContext) -> bool:
        return True

    def render(self, ctx: WalkContext) -> str | None:
        from nowhere.server import _try_mishap

        result = _try_mishap(ctx.env, ctx.rng)
        if result:
            ctx.mishap_fired = True
            return result["text"]
        return None


class MishapEchoAction:
    """意外回声: 50% chance next step echoes last mishap."""

    name = "mishap_echo"

    def should(self, ctx: WalkContext) -> bool:
        return not ctx.mishap_fired

    def render(self, ctx: WalkContext) -> str | None:
        from nowhere.server import _try_mishap_echo

        return _try_mishap_echo(ctx.rng)


class EncounterAction:
    """File-based encounter: density-adjusted 25% chance."""

    name = "encounter"

    def should(self, ctx: WalkContext) -> bool:
        return ctx.rng.random() < 0.25 * ctx.encounter_multiplier

    def render(self, ctx: WalkContext) -> str | None:
        from nowhere import encounters, notebook_mod

        enc = encounters.draw_encounter(
            ctx.state.biome or "", ctx.lat, ctx.lon, ctx.rng,
            place_name=ctx.state.place_name or "",
        )
        if not enc:
            return None
        # Card 43: fauna notebook hook
        try:
            fauna_name = enc.split("。")[0].split(",")[0].split("，")[0].strip()
            skip_city = False
            for cp in ("巴黎", "伦敦", "东京", "纽约", "上海", "北京", "罗马", "柏林"):
                if fauna_name.startswith(cp):
                    skip_city = True
                    break
            if fauna_name and not skip_city:
                nb_env = dict(ctx.env) if ctx.env else {}
                nb_env["_dt"] = ctx.now
                notebook_mod.record_with_env(
                    "fauna", fauna_name, ctx.state.place_name or "", nb_env, ctx.lat,
                )
        except Exception:
            pass
        return enc


class MessageAction:
    """30% chance to encounter a message from another traveler."""

    name = "message"

    def should(self, ctx: WalkContext) -> bool:
        return bool(ctx.state.messages) and ctx.rng.random() < 0.3 * ctx.encounter_multiplier

    def render(self, ctx: WalkContext) -> str | None:
        from nowhere import describe
        from nowhere.server import _strip_code_markers

        msg = ctx.rng.choice(list(ctx.state.messages))
        content = msg["content"] if isinstance(msg, dict) else msg
        if isinstance(msg, dict):
            msg["encountered"] = True
        content = _strip_code_markers(str(content))
        return describe.render("message", {"content": content}, None, ctx.rng)


class WildernessEventAction:
    """Deep wilderness: 10+ steps, 5% procedural flesh event."""

    name = "wilderness_event"

    def should(self, ctx: WalkContext) -> bool:
        return (
            ctx.is_deep_wilderness
            and len(ctx.state.path) >= 10
            and ctx.rng.random() < 0.05
        )

    def render(self, ctx: WalkContext) -> str | None:
        from nowhere.server import _WILDERNESS_FLESH_EVENTS

        return ctx.rng.choice(_WILDERNESS_FLESH_EVENTS)


class RiverAction:
    """Along-river narrative: detect flow alignment."""

    name = "river"

    def should(self, ctx: WalkContext) -> bool:
        return any(f.get("type") == "river" for f in ctx.water_features)

    def render(self, ctx: WalkContext) -> str | None:
        from nowhere.server import _compute_river_direction, _river_alignment_text

        river_dir = _compute_river_direction(ctx.water_features, ctx.lat, ctx.lon)
        return _river_alignment_text(ctx.bearing, river_dir, ctx.rng) or None


# ── Post-compose Actions (append to prose, not sections) ────────────


class SouvenirAction:
    """Natural souvenir pickup: 15% (25% first step)."""

    name = "souvenir"

    def should(self, ctx: WalkContext) -> bool:
        chance = 0.5 if len(ctx.state.path) <= 1 else 0.3
        return ctx.state.souvenir is None and ctx.rng.random() < chance

    def render(self, ctx: WalkContext) -> str | None:
        from nowhere.server import _pick_souvenir

        souvenir = _pick_souvenir(ctx.lat, ctx.lon, ctx.env, ctx.rng)
        if souvenir:
            ctx.state.souvenir = souvenir
            return souvenir["desc"]
        return None


class FestivalChaseAction:
    """Card 42: Festival chase wind mention -- 10% per walk, once per journey."""

    name = "festival_chase"

    def should(self, ctx: WalkContext) -> bool:
        return (
            not ctx.state.errand_festival_mentioned_this_journey
            and ctx.rng.random() < 0.10
        )

    def render(self, ctx: WalkContext) -> str | None:
        from nowhere.server import _check_festival_chase

        text = _check_festival_chase(ctx.lat, ctx.lon, ctx.now)
        if text:
            ctx.state.errand_festival_mentioned_this_journey = True
        return text


class CotravelerAction:
    """Cotraveler: footprints + meeting + pos refresh."""

    name = "cotraveler"

    def should(self, ctx: WalkContext) -> bool:
        from nowhere import travelers as travelers_mod

        return (
            travelers_mod.is_enabled()
            and not travelers_mod.walk_alone_active(ctx.state)
        )

    def render(self, ctx: WalkContext) -> str | None:
        import os
        from nowhere import travelers as travelers_mod

        traveler_name = os.environ.get("NOWHERE_TRAVELER_NAME", "").strip() or "网线那头的人"
        lat, lon = ctx.lat, ctx.lon
        prose_parts: list[str] = []

        # Refresh pos every 5 steps
        if ctx.state.walk_step_counter % 5 == 0:
            travelers_mod.refresh_pos(traveler_name, lat, lon)
        # Record footprint
        travelers_mod.record_footprint(traveler_name, lat, lon, ctx.state.place_name or "")
        # Check other travelers' footprints
        from nowhere.server import _cotraveler_encounter_counts, _cotraveler_meeting_log

        fp_text = travelers_mod.check_footprints(
            traveler_name, lat, lon, ctx.rng, _cotraveler_encounter_counts,
        )
        if fp_text:
            prose_parts.append(fp_text)
        # Check meeting (full mode only)
        if not travelers_mod.is_quiet():
            my_meet, _their_meet = travelers_mod.check_meeting(
                traveler_name, lat, lon, ctx.rng, _cotraveler_meeting_log,
            )
            if my_meet:
                prose_parts.append(my_meet)
        return "\n".join(prose_parts) if prose_parts else None


class WaterFeaturesAction:
    """Water features + SST + marine life rendering."""

    name = "water_features"

    def should(self, ctx: WalkContext) -> bool:
        return bool(ctx.water_features)

    def render(self, ctx: WalkContext) -> str | None:
        import asyncio
        from nowhere import describe, notebook_mod, water

        parts: list[str] = []
        lat, lon = ctx.lat, ctx.lon
        now = ctx.now
        env = ctx.env

        # Water feature description
        water_text = describe.render(
            "water_features", ctx.water_features, None, ctx.rng,
            biome=ctx.state.biome or "", elevation=env.get("elevation", 0),
        )
        if water_text:
            parts.append(water_text)
        # Card 43: water notebook hook
        try:
            wn = ctx.water_features[0].get("name", "") if ctx.water_features else ""
            if wn:
                nb_env = dict(env) if env else {}
                nb_env["_dt"] = now
                notebook_mod.record_with_env("water", wn, ctx.state.place_name or "", nb_env, lat)
        except Exception:
            pass

        # SST
        try:
            sst = asyncio.get_event_loop().run_until_complete(
                asyncio.wait_for(water.sea_surface_temp(lat, lon), timeout=8.0)
            )
            if sst is not None:
                parts.append(water.describe_sst(sst, ctx.rng))
        except Exception:
            pass

        # Marine life (30% chance)
        if ctx.rng.random() < 0.3:
            try:
                m = asyncio.get_event_loop().run_until_complete(
                    asyncio.wait_for(water.marine_life(lat, lon, ctx.rng), timeout=8.0)
                )
                if m:
                    parts.append(f"{m['common_name']}。{m['distance_m']}米外。{m['scene']}")
            except Exception:
                pass

        # Along-river narrative
        if any(f.get("type") == "river" for f in ctx.water_features):
            from nowhere.server import _compute_river_direction, _river_alignment_text

            river_dir = _compute_river_direction(ctx.water_features, lat, lon)
            rtext = _river_alignment_text(ctx.bearing, river_dir, ctx.rng)
            if rtext:
                parts.append(rtext)

        return "\n".join(parts) if parts else None


# ── Registries ──────────────────────────────────────────────────────

# Pre-compose: feed into sections list. Order = priority.
ACTIONS: list[Action] = [
    RhythmAction(),        # 节日/纪念日 (highest)
    TimeaxisAction(),      # 时间轴
    HumanitiesAction(),    # 人文卡
    PersonAction(),        # 卡中人遇见
    MishapAction(),        # 意外层
    MishapEchoAction(),    # 意外回声 (depends on mishap)
    EncounterAction(),     # 文件遭遇
    MessageAction(),       # 消息遭遇
    WildernessEventAction(),  # 荒深事件
    RiverAction(),         # 河流叙事
    WaterFeaturesAction(), # 水文 + SST + 海洋生物
]

# Post-compose: append to prose string.
POST_ACTIONS: list[Action] = [
    FestivalChaseAction(), # 节日追风
    SouvenirAction(),      # 纪念品
    CotravelerAction(),    # 同游者
]
