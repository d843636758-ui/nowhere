"""Test that all 329 pool.json landing points resolve to correct surface type.

Card 26: land destinations must not land on water.
Water destinations (大堡礁/北大西洋/死海/里海) are exempt.
"""

from __future__ import annotations

import sys

import pytest

from nowhere.landing import (
    _WATER_DESTINATIONS,
    _load_pool,
    nudge_if_water,
    _pool_surface_for,
)

# ── helpers ──────────────────────────────────────────────────────────

_pool = _load_pool()

# Build a set of (name_hint) that are known water destinations
_WATER_NAMES: set[str] = set(_WATER_DESTINATIONS)


# ── tests ────────────────────────────────────────────────────────────


class TestPoolSurfaceLookup:
    """Verify that pool entries with 'surface' field are found by lookup."""

    def test_known_water_entries_have_pool_surface(self):
        """大堡礁/死海/里海 should resolve via pool, not grid."""
        for name in ("大堡礁", "死海", "里海"):
            entry = next(e for e in _pool if e["name_hint"] == name)
            s = _pool_surface_for(entry["lat"], entry["lon"])
            assert s is not None, f"{name}: pool lookup returned None"
            assert s.startswith("water"), f"{name}: expected water, got {s}"

    def test_jerusalem_has_pool_surface(self):
        """Jerusalem (fixed coords) must resolve to urban via pool."""
        entry = next(e for e in _pool if e["name_hint"] == "耶路撒冷")
        s = _pool_surface_for(entry["lat"], entry["lon"])
        assert s == "urban", f"Jerusalem pool surface: {s}"


class TestNudgeIfWater:
    """Test the nudge logic for known problem spots."""

    @pytest.mark.parametrize(
        "name,lat,lon,biome",
        [
            ("耶路撒冷", 31.7767, 35.2345, "city"),
            ("贝鲁特", 33.8938, 35.5018, "city"),
            ("惠灵顿", -41.2865, 174.7762, "city"),
            ("新西兰", -40.9006, 174.886, "city"),
            ("珍珠港", 21.3445, -157.9747, "city"),
            ("阿皮亚", -13.8333, -171.75, "city"),
        ],
    )
    def test_former_water_landings_now_land(self, name, lat, lon, biome):
        """These 6 destinations were landing in water; they must not now."""
        result = nudge_if_water(lat, lon, name, biome)
        assert not result.get("water_landing"), (
            f"{name} still marked as water_landing"
        )

    def test_water_destinations_stay_water(self):
        """Water destinations should NOT be nudged away."""
        water_spots = [
            ("大堡礁", -18.2871, 147.6992, "coast"),
            ("死海", 31.5, 35.5, "desert"),
            ("里海", 41.0, 51.0, "coast"),
        ]
        for name, lat, lon, biome in water_spots:
            result = nudge_if_water(lat, lon, name, biome)
            assert not result.get("water_landing"), (
                f"{name}: water destination should not be marked water_landing"
            )
            # Water destinations should keep original coords
            assert result["lat"] == pytest.approx(lat, abs=0.01)
            assert result["lon"] == pytest.approx(lon, abs=0.01)

    def test_land_point_unchanged(self):
        """A clear land point (富士山) should not be moved."""
        result = nudge_if_water(35.3606, 138.7274, "富士山", "mountain")
        assert result["lat"] == 35.3606
        assert result["lon"] == 138.7274
        assert "water_landing" not in result


class TestAllPoolEntries:
    """Parametrized test: every pool entry must not land on water."""

    @pytest.mark.parametrize(
        "entry",
        _pool,
        ids=[e.get("name_hint", f"idx_{i}") for i, e in enumerate(_pool)],
    )
    def test_entry_not_water_landing(self, entry):
        """Each pool entry must resolve to non-water (unless intentional)."""
        name = entry.get("name_hint", "")
        lat, lon = entry["lat"], entry["lon"]
        biome = entry.get("biome", "")

        if name in _WATER_NAMES:
            pytest.skip(f"{name} is an intentional water destination")

        result = nudge_if_water(lat, lon, name, biome)
        assert not result.get("water_landing"), (
            f"{name} ({lat}, {lon}) biome={biome} resolves to water_landing"
        )
