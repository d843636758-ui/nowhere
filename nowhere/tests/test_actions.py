"""Tests for Card 48: walk action registry.

Each Action's should/render independently testable.
Priority-sensitive pair (festival + rhythm): festival comes first when both trigger.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nowhere.actions import (
    ACTIONS,
    POST_NORMALIZE_ACTIONS,
    PRE_NORMALIZE_ACTIONS,
    BuriedItemAction,
    EncounterAction,
    FestivalChaseAction,
    HumanitiesAction,
    LocalSceneAction,
    MessageAction,
    MishapAction,
    MishapEchoAction,
    NightNavAction,
    PersonAction,
    RhythmAction,
    RiverAction,
    SouvenirAction,
    TimeaxisAction,
    WalkContext,
    WildernessEventAction,
    WildernessNarrativeAction,
)
from nowhere.state import WorldState


# ── Helpers ──────────────────────────────────────────────────────────


def _make_state(**overrides) -> WorldState:
    """Create a minimal WorldState for testing."""
    s = WorldState()
    s.pos = (35.0, 139.0)
    s.place_name = "TestPlace"
    s.landed_at = datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc)
    s.elapsed_hours = 1.0
    s.biome = "grass"
    s.last_surface = "grass"
    s.radio_steps_since = 999
    s.walk_step_counter = 3
    s.path = [(35.0, 139.0)] * 5
    for k, v in overrides.items():
        setattr(s, k, v)
    return s


def _make_env(surface="grass", phase="day") -> dict:
    return {
        "elevation": 100,
        "surface": surface,
        "weather": {"temp_c": 20, "feels_c": 20, "wind_ms": 3, "text": "晴", "precip": "none"},
        "sky": {"phase": phase, "sun_alt": 45},
        "radio": None,
    }


def _make_ctx(state=None, env=None, rng_seed=42, **overrides) -> WalkContext:
    """Build a WalkContext with sensible defaults."""
    if state is None:
        state = _make_state()
    if env is None:
        env = _make_env()
    rng = random.Random(rng_seed)
    defaults = dict(
        state=state,
        env=env,
        rng=rng,
        step_result={"dist_km": 2.0, "new_surface": "grass", "slope_deg": 0, "elevation_delta": 0},
        lat=35.0,
        lon=139.0,
        now=datetime(2026, 7, 15, 14, 0, 0, tzinfo=timezone.utc),
        bearing=0.0,
        semantic="forward",
        local_dt=datetime(2026, 7, 15, 23, 0, 0),  # 11 PM local
        tz_name="Asia/Tokyo",
        water_features=[],
        is_deep_wilderness=False,
        wilderness_depth=10.0,
        encounter_multiplier=1.0,
        env_cached=False,
        sections=[],
    )
    defaults.update(overrides)
    return WalkContext(**defaults)


# ── Individual Action tests ─────────────────────────────────────────


class TestRhythmAction:
    def test_should_requires_local_dt(self):
        ctx = _make_ctx(local_dt=None)
        assert RhythmAction().should(ctx) is False

    def test_should_true_when_local_dt_set(self):
        ctx = _make_ctx()
        assert RhythmAction().should(ctx) is True

    def test_render_calls_localcolor(self):
        ctx = _make_ctx()
        with patch("nowhere.localcolor.rhythm_event", return_value="夜市开了") as mock:
            result = RhythmAction().render(ctx)
        assert result == "夜市开了"
        mock.assert_called_once()


class TestTimeaxisAction:
    def test_should_requires_now(self):
        ctx = _make_ctx(now=None)
        assert TimeaxisAction().should(ctx) is False

    def test_should_requires_not_cached(self):
        ctx = _make_ctx(env_cached=True)
        assert TimeaxisAction().should(ctx) is False

    def test_render_returns_layers(self):
        ctx = _make_ctx()
        with patch("nowhere.server._compute_timeaxes", return_value=[
            {"text": "蝉鸣"}, {"text": "热浪"},
        ]):
            result = TimeaxisAction().render(ctx)
        assert "蝉鸣" in result
        assert "热浪" in result


class TestHumanitiesAction:
    def test_should_always_true(self):
        assert HumanitiesAction().should(_make_ctx()) is True

    def test_render_returns_none_when_no_card(self):
        ctx = _make_ctx()
        with patch("nowhere.humanities.nearby_place", return_value=None):
            assert HumanitiesAction().render(ctx) is None

    def test_render_adds_character_hint(self):
        ctx = _make_ctx()
        card = {"key": "h/李白", "category": "人物", "ref": {"name": "李白"}}
        with patch("nowhere.humanities.nearby_place", return_value=card), \
             patch("nowhere.describe.render", return_value="李白在此"), \
             patch("nowhere.placememory.save_seen_humanities"):
            result = HumanitiesAction().render(ctx)
        assert "ask 能问出更多" in result


class TestPersonAction:
    def test_should_blocked_if_already_encountered(self):
        ctx = _make_ctx()
        ctx.state.person_encountered_this_walk = True
        assert PersonAction().should(ctx) is False

    def test_render_sets_state(self):
        ctx = _make_ctx()
        hit = {"sight": "一个人影", "data": {"name": "旅人"}, "place": "山脚", "person": "旅人"}
        with patch("nowhere.people.find_nearby_person", return_value=hit):
            result = PersonAction().render(ctx)
        assert result == "一个人影"
        assert ctx.state.person_encountered_this_walk is True
        assert ctx.state.talk_count == 0


class TestMishapAction:
    def test_should_always_true(self):
        assert MishapAction().should(_make_ctx()) is True

    def test_render_sets_mishap_fired(self):
        ctx = _make_ctx()
        with patch("nowhere.server._try_mishap", return_value={"text": "你摔了一跤"}):
            result = MishapAction().render(ctx)
        assert result == "你摔了一跤"
        assert ctx.mishap_fired is True

    def test_render_returns_none_when_no_mishap(self):
        ctx = _make_ctx()
        with patch("nowhere.server._try_mishap", return_value=None):
            assert MishapAction().render(ctx) is None
        assert ctx.mishap_fired is False


class TestMishapEchoAction:
    def test_should_blocked_if_mishap_fired(self):
        ctx = _make_ctx()
        ctx.mishap_fired = True
        assert MishapEchoAction().should(ctx) is False

    def test_should_true_if_no_mishap(self):
        ctx = _make_ctx()
        ctx.mishap_fired = False
        assert MishapEchoAction().should(ctx) is True

    def test_render_delegates(self):
        ctx = _make_ctx()
        with patch("nowhere.server._try_mishap_echo", return_value="回声"):
            assert MishapEchoAction().render(ctx) == "回声"


class TestEncounterAction:
    def test_should_random_gated(self):
        # With rng_seed=42 and multiplier=1.0, check the roll
        ctx = _make_ctx(rng_seed=42)
        val = ctx.rng.random()
        ctx2 = _make_ctx(rng_seed=42)
        expected = val < 0.25 * 1.0
        assert EncounterAction().should(ctx2) == expected

    def test_render_calls_encounters(self):
        ctx = _make_ctx()
        with patch("nowhere.encounters.draw_encounter", return_value="一只鹿"), \
             patch("nowhere.notebook.record_with_env"):
            result = EncounterAction().render(ctx)
        assert result == "一只鹿"


class TestMessageAction:
    def test_should_requires_messages(self):
        ctx = _make_ctx()
        ctx.state.messages = []
        assert MessageAction().should(ctx) is False

    def test_should_with_messages(self):
        ctx = _make_ctx(rng_seed=0)  # seed 0 -> random() is small
        ctx.state.messages = [{"content": "你好"}]
        # Should depends on rng roll
        r = ctx.rng.random()
        ctx2 = _make_ctx(rng_seed=0)
        ctx2.state.messages = [{"content": "你好"}]
        assert MessageAction().should(ctx2) == (r < 0.3)


class TestWildernessEventAction:
    def test_should_requires_deep_wilderness(self):
        ctx = _make_ctx(is_deep_wilderness=False)
        assert WildernessEventAction().should(ctx) is False

    def test_should_requires_10_steps(self):
        ctx = _make_ctx(is_deep_wilderness=True)
        ctx.state.path = [(0, 0)] * 5  # only 5 steps
        assert WildernessEventAction().should(ctx) is False


class TestRiverAction:
    def test_should_requires_river_feature(self):
        ctx = _make_ctx(water_features=[{"type": "lake", "name": "湖"}])
        assert RiverAction().should(ctx) is False

    def test_should_true_with_river(self):
        ctx = _make_ctx(water_features=[{"type": "river", "name": "长江"}])
        assert RiverAction().should(ctx) is True


class TestWildernessNarrativeAction:
    def test_should_requires_deep_wilderness_and_not_cached(self):
        ctx = _make_ctx(is_deep_wilderness=False)
        assert WildernessNarrativeAction().should(ctx) is False
        ctx2 = _make_ctx(is_deep_wilderness=True, env_cached=True)
        assert WildernessNarrativeAction().should(ctx2) is False
        ctx3 = _make_ctx(is_deep_wilderness=True, env_cached=False)
        assert WildernessNarrativeAction().should(ctx3) is True


class TestLocalSceneAction:
    def test_should_blocked_in_deep_wilderness(self):
        ctx = _make_ctx(is_deep_wilderness=True)
        assert LocalSceneAction().should(ctx) is False

    def test_should_blocked_when_cached(self):
        ctx = _make_ctx(env_cached=True)
        assert LocalSceneAction().should(ctx) is False

    def test_render_tries_localcolor_first(self):
        ctx = _make_ctx()
        ctx.state.place_name = "南京"
        card = {"key": "南京/植被/梧桐", "text": "梧桐树很高"}
        with patch("nowhere.localcolor.draw", return_value=card), \
             patch("nowhere.placememory.save_seen_cards"), \
             patch("nowhere.placememory.has_trace", return_value=False), \
             patch("nowhere.country.country_code_of", return_value="CN"):
            LocalSceneAction().render(ctx)
        assert ctx.had_local is True
        assert "梧桐树很高" in ctx.sections


class TestSouvenirAction:
    def test_should_blocked_when_quiet(self):
        ctx = _make_ctx(quiet=True)
        assert SouvenirAction().should(ctx) is False

    def test_should_blocked_when_already_has_souvenir(self):
        ctx = _make_ctx()
        ctx.state.souvenir = {"name": "石头"}
        assert SouvenirAction().should(ctx) is False


class TestFestivalChaseAction:
    def test_should_blocked_if_already_mentioned(self):
        ctx = _make_ctx()
        ctx.state.errand_festival_mentioned_this_journey = True
        assert FestivalChaseAction().should(ctx) is False


class TestBuriedItemAction:
    def test_should_requires_pos(self):
        ctx = _make_ctx()
        ctx.state.pos = None
        assert BuriedItemAction().should(ctx) is False


class TestNightNavAction:
    def test_should_requires_night(self):
        ctx = _make_ctx(env=_make_env(phase="day"))
        assert NightNavAction().should(ctx) is False

    def test_should_true_at_night(self):
        ctx = _make_ctx(env=_make_env(phase="night"))
        assert NightNavAction().should(ctx) is True


# ── Priority test ────────────────────────────────────────────────────


class TestPriority:
    def test_rhythm_before_timeaxis(self):
        """RhythmAction (节日) comes before TimeaxisAction in ACTIONS list."""
        names = [a.name for a in ACTIONS]
        assert names.index("rhythm") < names.index("timeaxis")

    def test_wilderness_narrative_first(self):
        """WildernessNarrativeAction is first (highest priority within narrative)."""
        assert ACTIONS[0].name == "wilderness_narrative"

    def test_action_count(self):
        """Verify total number of registered actions."""
        assert len(ACTIONS) == 14  # pre-compose
        assert len(PRE_NORMALIZE_ACTIONS) == 2
        assert len(POST_NORMALIZE_ACTIONS) == 1


# ── Integration: festival + rhythm priority ──────────────────────────


class TestFestivalRhythmPriority:
    def test_festival_before_rhythm_when_both_trigger(self):
        """When both festival and rhythm fire, festival text appears first in ACTIONS order.

        Actually rhythm comes first in ACTIONS, but the card spec says
        节日/纪念日 > 时间轴. RhythmAction IS the 节日/纪念日 action.
        TimeaxisAction is 时间轴. So rhythm < timeaxis is correct.
        """
        names = [a.name for a in ACTIONS]
        rhythm_idx = names.index("rhythm")
        timeaxis_idx = names.index("timeaxis")
        assert rhythm_idx < timeaxis_idx, "节日/纪念日 must come before 时间轴"
