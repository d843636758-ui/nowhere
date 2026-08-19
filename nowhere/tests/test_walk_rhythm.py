"""Tests for Card 39: walk rhythm — radio cooldown, touch dedup, glue words, direction gating."""

from __future__ import annotations

import asyncio
import random
from unittest.mock import AsyncMock, MagicMock, patch

from nowhere import server
from nowhere.state import WorldState


def _make_step_result(bearing=0, dist_km=2.0, surface="grass"):
    """Create a mock walk.step return value."""
    return {
        "dist_km": dist_km,
        "new_surface": surface,
        "slope_deg": 0,
        "elevation_delta": 0,
        "blocked": False,
        "no_gain": False,
    }


def _make_env(radio=None, surface="grass"):
    """Create a mock environment dict."""
    return {
        "elevation": 100,
        "surface": surface,
        "weather": {"temp_c": 20, "feels_c": 20, "wind_ms": 3, "text": "晴", "precip": "none"},
        "sky": {"phase": "day", "sun_alt": 45},
        "radio": radio,
        "water_features": [],
    }


def _setup_state():
    """Reset server state for walk testing."""
    server._state = WorldState()
    server._state.pos = (35.0, 139.0)
    server._state.place_name = "TestPlace"
    server._state.landed_at = __import__("datetime").datetime(
        2026, 7, 15, 10, 0, 0,
        tzinfo=__import__("datetime").timezone.utc)
    server._state.elapsed_hours = 1.0
    server._state.biome = "grass"
    server._state.last_surface = "grass"
    server._state.radio_steps_since = 999
    server._state.walk_step_counter = 0
    server._rng = random.Random(42)
    server._recent_salience_kinds = set()


def test_walk_10_steps_radio_cooldown():
    """Fixed seed 10 steps: radio appears at most 2 times (cooldown = 5 steps)."""
    _setup_state()

    radio = {"name": "TestFM", "genre": "pop", "stream_url": "http://test"}
    env = _make_env(radio=radio)

    step_texts = []

    with patch.object(server, "walk_mod") as mock_walk, \
         patch.object(server, "_gather_env_cached", new_callable=AsyncMock) as mock_env, \
         patch.object(server, "country") as mock_country, \
         patch.object(server, "terrain") as mock_terrain, \
         patch.object(server, "water") as mock_water, \
         patch.object(server, "encounters") as mock_enc, \
         patch.object(server, "localcolor") as mock_lc, \
         patch.object(server, "humanities") as mock_hum, \
         patch.object(server, "placememory") as mock_pm:

        mock_walk.step.return_value = _make_step_result()
        mock_walk._bearing_from_path.return_value = 0.0
        mock_env.return_value = (env, False)
        mock_country.country_code_of.return_value = "JP"
        mock_terrain.elevation.return_value = 100
        mock_terrain.surface.return_value = "grass"
        mock_water.sea_surface_temp = AsyncMock(return_value=None)
        mock_water.marine_life = AsyncMock(return_value=None)
        mock_enc.draw_encounter.return_value = None
        mock_lc.draw.return_value = None
        mock_lc.rhythm_event.return_value = None
        mock_hum.nearby_place.return_value = None

        for i in range(10):
            result = asyncio.run(server.walk_impl("N", 2.0))
            step_texts.append(result["text"])

    radio_count = sum(
        1 for t in step_texts
        if "TestFM" in t or "电台" in t or "收音机" in t or "播" in t
    )
    assert radio_count <= 2, f"Radio appeared {radio_count} times in 10 steps (expected <= 2)"


def test_walk_10_steps_no_repeated_touch():
    """Fixed seed 10 steps: no touch sentence repeats within the walk."""
    _setup_state()

    env = _make_env()

    step_texts = []

    with patch.object(server, "walk_mod") as mock_walk, \
         patch.object(server, "_gather_env_cached", new_callable=AsyncMock) as mock_env, \
         patch.object(server, "country") as mock_country, \
         patch.object(server, "terrain") as mock_terrain, \
         patch.object(server, "water") as mock_water, \
         patch.object(server, "encounters") as mock_enc, \
         patch.object(server, "localcolor") as mock_lc, \
         patch.object(server, "humanities") as mock_hum, \
         patch.object(server, "placememory") as mock_pm:

        mock_walk.step.return_value = _make_step_result()
        mock_walk._bearing_from_path.return_value = 0.0
        mock_env.return_value = (env, False)
        mock_country.country_code_of.return_value = "JP"
        mock_terrain.elevation.return_value = 100
        mock_terrain.surface.return_value = "grass"
        mock_water.sea_surface_temp = AsyncMock(return_value=None)
        mock_water.marine_life = AsyncMock(return_value=None)
        mock_enc.draw_encounter.return_value = None
        mock_lc.draw.return_value = None
        mock_lc.rhythm_event.return_value = None
        mock_hum.nearby_place.return_value = None

        for i in range(10):
            result = asyncio.run(server.walk_impl("N", 2.0))
            step_texts.append(result["text"])

    # Check that no touch sentence from the pool appears more than once
    from nowhere.describe import _TOUCH_BY_SURFACE
    touch_pool = _TOUCH_BY_SURFACE.get("grass", [])
    for touch_sent in touch_pool:
        count = sum(1 for t in step_texts if touch_sent in t)
        assert count <= 1, f"Touch sentence '{touch_sent}' appeared {count} times"


def test_walk_glue_word_variation():
    """'同时,' should be less than 30% of non-empty transitions in 10 steps."""
    _setup_state()

    env = _make_env()

    step_texts = []

    with patch.object(server, "walk_mod") as mock_walk, \
         patch.object(server, "_gather_env_cached", new_callable=AsyncMock) as mock_env, \
         patch.object(server, "country") as mock_country, \
         patch.object(server, "terrain") as mock_terrain, \
         patch.object(server, "water") as mock_water, \
         patch.object(server, "encounters") as mock_enc, \
         patch.object(server, "localcolor") as mock_lc, \
         patch.object(server, "humanities") as mock_hum, \
         patch.object(server, "placememory") as mock_pm:

        mock_walk.step.return_value = _make_step_result()
        mock_walk._bearing_from_path.return_value = 0.0
        mock_env.return_value = (env, False)
        mock_country.country_code_of.return_value = "JP"
        mock_terrain.elevation.return_value = 100
        mock_terrain.surface.return_value = "grass"
        mock_water.sea_surface_temp = AsyncMock(return_value=None)
        mock_water.marine_life = AsyncMock(return_value=None)
        mock_enc.draw_encounter.return_value = None
        mock_lc.draw.return_value = None
        mock_lc.rhythm_event.return_value = None
        mock_hum.nearby_place.return_value = None

        for i in range(10):
            result = asyncio.run(server.walk_impl("N", 2.0))
            step_texts.append(result["text"])

    # Count glue words across all step texts
    all_transitions = ["同时,", "头顶上,", "风里,", "远处,", "走着走着,",
                       "这会儿,", "紧接着,", "没过多会儿,"]
    total_glue = 0
    tongshi_count = 0
    for t in step_texts:
        for tr in all_transitions:
            cnt = t.count(tr)
            total_glue += cnt
            if tr == "同时,":
                tongshi_count += cnt

    if total_glue > 0:
        ratio = tongshi_count / total_glue
        assert ratio < 0.30, f"'同时,' ratio is {ratio:.1%} ({tongshi_count}/{total_glue}), expected < 30%"
    # If total_glue == 0, that's fine (no transitions at all)


def test_walk_direction_sentences_limited():
    """Direction sentences ('你继续往X走') should appear at most 3 times in 10 steps."""
    _setup_state()

    env = _make_env()

    step_texts = []

    with patch.object(server, "walk_mod") as mock_walk, \
         patch.object(server, "_gather_env_cached", new_callable=AsyncMock) as mock_env, \
         patch.object(server, "country") as mock_country, \
         patch.object(server, "terrain") as mock_terrain, \
         patch.object(server, "water") as mock_water, \
         patch.object(server, "encounters") as mock_enc, \
         patch.object(server, "localcolor") as mock_lc, \
         patch.object(server, "humanities") as mock_hum, \
         patch.object(server, "placememory") as mock_pm:

        mock_walk.step.return_value = _make_step_result()
        mock_walk._bearing_from_path.return_value = 0.0
        mock_env.return_value = (env, False)
        mock_country.country_code_of.return_value = "JP"
        mock_terrain.elevation.return_value = 100
        mock_terrain.surface.return_value = "grass"
        mock_water.sea_surface_temp = AsyncMock(return_value=None)
        mock_water.marine_life = AsyncMock(return_value=None)
        mock_enc.draw_encounter.return_value = None
        mock_lc.draw.return_value = None
        mock_lc.rhythm_event.return_value = None
        mock_hum.nearby_place.return_value = None

        for i in range(10):
            result = asyncio.run(server.walk_impl("N", 2.0))
            step_texts.append(result["text"])

    # Count direction sentences
    dir_count = sum(1 for t in step_texts if "你继续往" in t)
    assert dir_count <= 3, f"Direction sentences appeared {dir_count} times (expected <= 3)"


def test_radio_cooldown_state_field():
    """radio_steps_since should be in state and persist."""
    s = WorldState()
    assert hasattr(s, "radio_steps_since")
    assert s.radio_steps_since == 999  # starts high so first walk sees radio
    assert hasattr(s, "walk_step_counter")
    assert s.walk_step_counter == 0
