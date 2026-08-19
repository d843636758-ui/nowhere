"""Tests for Card 28: mishap system.

Tests:
- 3% probability mock hit works
- No-rain env → rain mishap never triggers
- Same card doesn't repeat in one journey
- Echo appears in next step
"""

from __future__ import annotations

import random
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.stdout.reconfigure(encoding="utf-8")

from nowhere import state as state_mod
from nowhere import server


# ── Helpers ──────────────────────────────────────────────────────────


def _reset_server_state():
    """Reset server module-level state for clean test isolation."""
    server._state = state_mod.WorldState()
    server._state.pos = (40.0, 116.0)
    server._state.landed_at = None
    server._state.path = [{"lat": 40.0, "lon": 116.0, "elevation": 50, "dist_km": 2.0}]
    server._state.walk_step_counter = 5  # not first step
    server._mishap_last_step = -999


def _make_env(precip: str = "none", biome: str = "grassland") -> dict:
    """Create a minimal env dict for testing."""
    return {
        "elevation": 100.0,
        "surface": "grass",
        "weather": {"temp_c": 20.0, "precip": precip, "text": "晴"},
        "sky": {"phase": "day"},
    }


# ── Test: 3% probability mock hit works ─────────────────────────────


class TestMishapTrigger:
    """Test that mishaps trigger at the right probability."""

    def test_mishap_fires_when_rng_below_threshold(self):
        """When rng.random() returns 0.01 (< 0.03), mishap fires."""
        _reset_server_state()
        server._state.biome = "grassland"
        server._state.walk_step_counter = 20
        server._mishap_last_step = 0  # well past cooldown

        env = _make_env()
        rng = random.Random(42)

        # Patch rng.random to always return 0.01 (below 3%)
        with patch.object(rng, 'random', return_value=0.01):
            result = server._try_mishap(env, rng)

        assert result is not None, "Mishap should fire when rng < 0.03"
        assert "tier" in result
        assert "text" in result

    def test_mishap_does_not_fire_when_rng_above_threshold(self):
        """When rng.random() returns 0.50 (> 0.03), mishap doesn't fire."""
        _reset_server_state()
        server._state.biome = "grassland"
        server._state.walk_step_counter = 20
        server._mishap_last_step = 0

        env = _make_env()
        rng = random.Random(42)

        with patch.object(rng, 'random', return_value=0.50):
            result = server._try_mishap(env, rng)

        assert result is None, "Mishap should not fire when rng > 0.03"


# ── Test: No-rain env → rain mishap never triggers ──────────────────


class TestMishapEnvConstraints:
    """Test that environment constraints are respected."""

    def test_rain_mishap_blocked_in_clear_weather(self):
        """Rain mishaps never trigger when precip is 'none'."""
        _reset_server_state()
        server._state.biome = "grassland"
        server._state.walk_step_counter = 20
        server._mishap_last_step = 0

        env = _make_env(precip="none")
        rng = random.Random(42)

        # Run 1000 attempts with forced low rng to guarantee chance roll passes
        rain_mishap_ids = {"time_rain", "time_rain_heavy"}
        seen_rain = False
        for _ in range(1000):
            server._state.mishap_seen = []  # reset seen
            with patch.object(rng, 'random', return_value=0.01):
                result = server._try_mishap(env, rng)
            if result and result["id"] in rain_mishap_ids:
                seen_rain = True
                break

        assert not seen_rain, "Rain mishap should never trigger in clear weather"

    def test_rain_mishap_fires_in_rain(self):
        """Rain mishaps can trigger when precip is 'rain'."""
        _reset_server_state()
        server._state.biome = "grassland"
        server._state.walk_step_counter = 20
        server._mishap_last_step = 0
        server._state.mishap_seen = []

        env = _make_env(precip="rain")
        rng = random.Random(42)

        # Force chance roll and pick a rain mishap
        with patch.object(rng, 'random', return_value=0.01):
            with patch.object(rng, 'choice', side_effect=lambda pool: next(
                (m for m in pool if m["id"] == "time_rain"), pool[0]
            )):
                result = server._try_mishap(env, rng)

        assert result is not None
        assert result["id"] == "time_rain"

    def test_item_mishap_blocked_in_city(self):
        """Item mishaps never trigger in city biome."""
        _reset_server_state()
        server._state.biome = "city"
        server._state.walk_step_counter = 20
        server._mishap_last_step = 0

        env = _make_env(biome="city")
        rng = random.Random(42)

        item_mishap_ids = {"item_water_leak", "item_zipper_broke",
                           "item_phone_died", "item_hat_lost",
                           "item_snack_spilled", "item_pen_leaked"}
        seen_item = False
        for _ in range(1000):
            server._state.mishap_seen = []
            with patch.object(rng, 'random', return_value=0.01):
                result = server._try_mishap(env, rng)
            if result and result["id"] in item_mishap_ids:
                seen_item = True
                break

        assert not seen_item, "Item mishap should never trigger in city"


# ── Test: Same card doesn't repeat in one journey ────────────────────


class TestMishapNoRepeat:
    """Test that each mishap card only fires once per journey."""

    def test_same_card_never_repeats(self):
        """Once a mishap is seen, it never fires again in the same journey."""
        _reset_server_state()
        server._state.biome = "grassland"
        server._state.walk_step_counter = 20
        server._mishap_last_step = 0

        env = _make_env()
        rng = random.Random(42)

        # Fire one mishap
        with patch.object(rng, 'random', return_value=0.01):
            first = server._try_mishap(env, rng)
        assert first is not None

        first_id = first["id"]
        # Reset cooldown so next attempt can fire
        server._mishap_last_step = 0

        # Try many times — the same ID should never appear
        for _ in range(500):
            server._mishap_last_step = 0
            with patch.object(rng, 'random', return_value=0.01):
                result = server._try_mishap(env, rng)
            if result:
                assert result["id"] != first_id, \
                    f"Mishap '{first_id}' fired twice in same journey"

    def test_mishap_seen_recorded_in_state(self):
        """Fired mishaps are recorded in state.mishap_seen."""
        _reset_server_state()
        server._state.biome = "grassland"
        server._state.walk_step_counter = 20
        server._mishap_last_step = 0

        env = _make_env()
        rng = random.Random(42)

        with patch.object(rng, 'random', return_value=0.01):
            result = server._try_mishap(env, rng)

        assert result is not None
        assert result["id"] in server._state.mishap_seen


# ── Test: Echo appears in next step ─────────────────────────────────


class TestMishapEcho:
    """Test that 50% echo appears after a mishap."""

    def test_echo_appear_with_50_percent_chance(self):
        """After a mishap, next call has 50% chance of echo."""
        _reset_server_state()
        server._state.mishap_seen = ["shoe_sand"]

        rng = random.Random(42)

        # With rng returning 0.3 (< 0.5), echo should fire
        with patch.object(rng, 'random', return_value=0.3):
            echo = server._try_mishap_echo(rng)

        assert echo is not None
        assert "沙" in echo or "硌" in echo  # echo for shoe_sand

    def test_echo_does_not_fire_above_threshold(self):
        """With rng > 0.5, echo should not fire."""
        _reset_server_state()
        server._state.mishap_seen = ["shoe_sand"]

        rng = random.Random(42)

        with patch.object(rng, 'random', return_value=0.8):
            echo = server._try_mishap_echo(rng)

        assert echo is None

    def test_no_echo_when_no_mishaps_seen(self):
        """No echo when no mishaps have been seen."""
        _reset_server_state()
        server._state.mishap_seen = []

        rng = random.Random(42)
        echo = server._try_mishap_echo(rng)

        assert echo is None


# ── Test: Cooldown enforcement ──────────────────────────────────────


class TestMishapCooldown:
    """Test that 10-step cooldown is enforced."""

    def test_cooldown_blocks_mishap(self):
        """Mishap won't fire within cooldown window."""
        _reset_server_state()
        server._state.biome = "grassland"
        server._state.walk_step_counter = 20
        server._mishap_last_step = 15  # only 5 steps ago, cooldown is 10

        env = _make_env()
        rng = random.Random(42)

        with patch.object(rng, 'random', return_value=0.01):
            result = server._try_mishap(env, rng)

        assert result is None, "Mishap should not fire within cooldown window"

    def test_cooldown_allows_after_enough_steps(self):
        """Mishap can fire after cooldown expires."""
        _reset_server_state()
        server._state.biome = "grassland"
        server._state.walk_step_counter = 30
        server._mishap_last_step = 15  # 15 steps ago, cooldown is 10

        env = _make_env()
        rng = random.Random(42)

        with patch.object(rng, 'random', return_value=0.01):
            result = server._try_mishap(env, rng)

        assert result is not None, "Mishap should fire after cooldown expires"


# ── Test: State effects ─────────────────────────────────────────────


class TestMishapEffects:
    """Test that mishap effects are applied correctly."""

    def test_elapsed_hours_added_for_time_mishap(self):
        """Time-tier mishaps add elapsed_hours."""
        _reset_server_state()
        server._state.biome = "grassland"
        server._state.walk_step_counter = 20
        server._mishap_last_step = 0
        server._state.elapsed_hours = 5.0

        env = _make_env(precip="rain")
        rng = random.Random(42)

        with patch.object(rng, 'random', return_value=0.01):
            with patch.object(rng, 'choice', side_effect=lambda pool: next(
                (m for m in pool if m["id"] == "time_rain"), pool[0]
            )):
                result = server._try_mishap(env, rng)

        assert result is not None
        assert server._state.elapsed_hours > 5.0, "elapsed_hours should increase"

    def test_mishap_tag_set_for_item_mishap(self):
        """Item-tier mishaps set mishap_tag."""
        _reset_server_state()
        server._state.biome = "grassland"
        server._state.walk_step_counter = 20
        server._mishap_last_step = 0

        env = _make_env()
        rng = random.Random(42)

        with patch.object(rng, 'random', return_value=0.01):
            with patch.object(rng, 'choice', side_effect=lambda pool: next(
                (m for m in pool if m["id"] == "item_water_leak"), pool[0]
            )):
                result = server._try_mishap(env, rng)

        assert result is not None
        assert server._state.mishap_tag == "thirsty"

    def test_shoe_mishap_no_state_change(self):
        """Shoe-tier mishaps have no state impact."""
        _reset_server_state()
        server._state.biome = "grassland"
        server._state.walk_step_counter = 20
        server._mishap_last_step = 0
        server._state.elapsed_hours = 5.0
        server._state.mishap_tag = None

        env = _make_env()
        rng = random.Random(42)

        with patch.object(rng, 'random', return_value=0.01):
            with patch.object(rng, 'choice', side_effect=lambda pool: next(
                (m for m in pool if m["tier"] == "shoe"), pool[0]
            )):
                result = server._try_mishap(env, rng)

        assert result is not None
        assert server._state.elapsed_hours == 5.0, "Shoe mishap should not change time"
        assert server._state.mishap_tag is None, "Shoe mishap should not set tag"


# ── Test: Mishap data integrity ─────────────────────────────────────


class TestMishapData:
    """Test that mishaps.json is well-formed."""

    def test_mishaps_load(self):
        """mishaps.json loads and has required fields."""
        mishaps = server._load_mishaps()
        assert len(mishaps) >= 20, f"Expected >=20 mishaps, got {len(mishaps)}"

        for m in mishaps:
            assert "id" in m, f"Missing 'id' in mishap: {m}"
            assert "tier" in m, f"Missing 'tier' in mishap: {m}"
            assert "text" in m, f"Missing 'text' in mishap: {m}"
            assert m["tier"] in ("shoe", "time", "path", "item"), \
                f"Unknown tier '{m['tier']}' in mishap '{m['id']}'"

    def test_all_ids_unique(self):
        """All mishap IDs are unique."""
        mishaps = server._load_mishaps()
        ids = [m["id"] for m in mishaps]
        assert len(ids) == len(set(ids)), "Duplicate mishap IDs found"

    def test_time_tier_has_elapsed(self):
        """Time-tier mishaps should have elapsed_hours."""
        mishaps = server._load_mishaps()
        for m in mishaps:
            if m["tier"] == "time":
                assert "elapsed_hours" in m, \
                    f"Time mishap '{m['id']}' missing elapsed_hours"

    def test_item_tier_has_tag(self):
        """Item-tier mishaps should have mishap_tag."""
        mishaps = server._load_mishaps()
        for m in mishaps:
            if m["tier"] == "item":
                assert "mishap_tag" in m, \
                    f"Item mishap '{m['id']}' missing mishap_tag"

    def test_requires_precip_valid(self):
        """requires.precip values are valid weather types."""
        mishaps = server._load_mishaps()
        valid_precip = {"rain", "snow", "storm", "none"}
        for m in mishaps:
            req = m.get("requires", {})
            precip = req.get("precip")
            if precip:
                assert precip in valid_precip, \
                    f"Mishap '{m['id']}' has invalid precip requirement: {precip}"
