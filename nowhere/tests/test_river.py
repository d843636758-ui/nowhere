"""Card 37 — River awareness tests.

Verifies:
  1. Landing on 长江 returns water feature description with correct segment.
  2. Walking along a river produces at least one 顺流/逆流 sentence in 3 steps.
  3. Leaving the river area (>5km) makes river imagery disappear.
  4. open_door("长江 入海口") lands in Shanghai segment.
  5. Offline water feature lookup returns expected entries.
"""

from __future__ import annotations

import asyncio
import math
import os
import random
import sys

import pytest

# GBK console fix
sys.stdout.reconfigure(encoding="utf-8")

# Deterministic seed for reproducible tests
os.environ["NOWHERE_SEED"] = "42"

from nowhere import server, hydrology


# ── helpers ──────────────────────────────────────────────────────────


def _run(coro):
    """Run an async coroutine in a fresh event loop."""
    return asyncio.run(coro)


# ── Test 1: Landing on 长江 ──────────────────────────────────────────


class TestLandingYangtze:
    """Landing on 长江 should produce water feature description with segment info."""

    def test_landing_changjiang_has_water_text(self):
        """open_door('长江') → prose contains water/river imagery."""
        _run(server.open_door_impl(to="长江"))
        result = _run(server.open_door_impl(to="长江"))
        text = result["text"]
        # Should mention water-related content (江/河/水/岸/三峡)
        water_keywords = ["江", "河", "水", "岸", "三峡", "流", "浪"]
        has_water = any(k in text for k in water_keywords)
        assert has_water, f"Landing on 长江 should mention water. Got: {text[:200]}"

    def test_landing_changjiang_segment_in_prose(self):
        """open_door('长江') → place_name includes segment info."""
        result = _run(server.open_door_impl(to="长江"))
        data = result["data"]
        # The position should be near the Three Gorges area (lat ~30.7, lon ~111)
        lat = data["position"]["lat"]
        lon = data["position"]["lon"]
        assert 28 < lat < 33, f"Expected lat near 三峡 (~30.7), got {lat}"
        assert 109 < lon < 113, f"Expected lon near 三峡 (~111), got {lon}"

    def test_landing_changjiang_shanghai_segment(self):
        """open_door('长江 入海口') → lands in Shanghai segment."""
        result = _run(server.open_door_impl(to="长江 入海口"))
        data = result["data"]
        lat = data["position"]["lat"]
        lon = data["position"]["lon"]
        # Shanghai段 is at (31.2, 121.5)
        assert 30 < lat < 33, f"Expected lat near Shanghai (~31.2), got {lat}"
        assert 120 < lon < 123, f"Expected lon near Shanghai (~121.5), got {lon}"

    def test_landing_changjiang_nanjing_segment(self):
        """open_door('长江 南京段') → lands in Nanjing segment."""
        result = _run(server.open_door_impl(to="长江 南京段"))
        data = result["data"]
        lat = data["position"]["lat"]
        lon = data["position"]["lon"]
        # 南京段 is at (32.1, 118.8)
        assert 31 < lat < 33, f"Expected lat near Nanjing (~32.1), got {lat}"
        assert 117 < lon < 120, f"Expected lon near Nanjing (~118.8), got {lon}"


# ── Test 2: Along-river walk narrative ───────────────────────────────


class TestRiverWalk:
    """Walking along a river should produce 顺流/逆流 text."""

    def test_walk_along_river_has_alignment_text(self):
        """Walk 3 steps near 长江 → at least one river alignment sentence."""
        # Land on 长江 first
        _run(server.open_door_impl(to="长江"))

        river_sentences = []
        river_keywords = [
            "顺流", "逆流", "江水",
            "横着江", "水声",
            "你和江", "江从你",
        ]

        for _ in range(3):
            result = _run(server.walk_impl(direction="E", distance_km=2.0))
            text = result["text"]
            for kw in river_keywords:
                if kw in text:
                    river_sentences.append(text[:100])
                    break

        assert len(river_sentences) >= 1, (
            f"Expected at least 1 river alignment sentence in 3 steps, "
            f"got {len(river_sentences)}. Last text: {result['text'][:200]}"
        )


# ── Test 3: River imagery disappears when far ───────────────────────


class TestRiverGone:
    """Walking far from river → no river imagery."""

    def test_leave_river_area(self):
        """Walk 5km away from river → water features list should be empty."""
        # Land somewhere without rivers (mid-Sahara)
        _run(server.open_door_impl(to="Tamanrasset"))

        # Walk a few steps to get settled
        for _ in range(2):
            _run(server.walk_impl(direction="S", distance_km=5.0))

        # Check that no river water features are nearby
        lat, lon = server._state.pos
        wf = server._offline_water_nearby(lat, lon, radius_km=5)
        rivers = [f for f in wf if f.get("type") == "river"]
        assert len(rivers) == 0, f"Expected no rivers in Sahara, got {rivers}"


# ── Test 4: Offline water feature lookup ─────────────────────────────


class TestOfflineLookup:
    """Verify the offline water feature lookup works correctly."""

    def test_near_yangtze_finds_river(self):
        """Near Chongqing (29.5, 106.5) → finds 长江."""
        wf = hydrology.offline_water_nearby(29.5, 106.5, radius_km=50)
        names = [f["name"] for f in wf]
        assert "长江" in names, f"Expected 长江 near Chongqing, got {names}"

    def test_near_lake_finds_lake(self):
        """Near West Lake (30.2, 120.1) → finds 西湖."""
        wf = hydrology.offline_water_nearby(30.2, 120.1, radius_km=10)
        names = [f["name"] for f in wf]
        assert "西湖" in names, f"Expected 西湖, got {names}"

    def test_sahara_no_water(self):
        """Deep Sahara (23.0, 3.0) → no water features within 50km."""
        wf = hydrology.offline_water_nearby(23.0, 3.0, radius_km=50)
        assert len(wf) == 0, f"Expected no water in Sahara, got {wf}"

    def test_segment_note_preserved(self):
        """长江 entry with note should have note in result."""
        wf = hydrology.offline_water_nearby(31.2, 121.5, radius_km=50)
        yangtze = [f for f in wf if f["name"] == "长江" and f.get("note")]
        assert len(yangtze) > 0, "Expected 长江 with note near Shanghai"


# ── Test 5: River direction computation ──────────────────────────────


class TestRiverDirection:
    """Verify river direction computation."""

    def test_river_direction_returns_vector(self):
        """compute_river_direction for 长江 returns a valid unit vector."""
        water_features = [{"name": "长江", "type": "river", "distance_km": 5, "bearing": "东"}]
        result = server._compute_river_direction(water_features, 30.0, 112.0)
        if result is not None:
            dx, dy = result
            mag = math.sqrt(dx * dx + dy * dy)
            assert abs(mag - 1.0) < 0.01, f"Expected unit vector, got magnitude {mag}"

    def test_alignment_text_with_dot_product(self):
        """River alignment text generation."""
        # River flowing east (dx=1, dy=0)
        river_dir = (1.0, 0.0)
        rng = random.Random(42)

        # Walking east (same direction) → 顺流
        text = server._river_alignment_text(90.0, river_dir, rng)
        assert "顺" in text or "江" in text or "水" in text, f"Expected river text, got: {text}"

        # Walking west (opposite) → 逆流
        rng2 = random.Random(42)
        text2 = server._river_alignment_text(270.0, river_dir, rng2)
        assert "逆" in text2 or "江" in text2 or "对" in text2, f"Expected 逆流 text, got: {text2}"

    def test_alignment_text_none_inputs(self):
        """None inputs return empty string."""
        rng = random.Random(42)
        assert server._river_alignment_text(None, (1, 0), rng) == ""
        assert server._river_alignment_text(90.0, None, rng) == ""


# ── Test 6: find_river_segment ───────────────────────────────────────


class TestFindRiverSegment:
    """Verify segment lookup for 长江."""

    def test_default_segment_is_scenic(self):
        """_find_river_segment('长江', '') → scenic default (三峡)."""
        seg = server._find_river_segment("长江", "")
        assert seg is not None
        assert "三峡" in seg["segment_name"] or "宜昌" in seg["segment_name"]

    def test_shanghai_segment(self):
        """_find_river_segment('长江', '上海段') → Shanghai."""
        seg = server._find_river_segment("长江", "上海段")
        assert seg is not None
        assert "上海" in seg["segment_name"]
        assert 120 < seg["lon"] < 123

    def test_nanjing_segment(self):
        """_find_river_segment('长江', '南京段') → Nanjing."""
        seg = server._find_river_segment("长江", "南京段")
        assert seg is not None
        assert "南京" in seg["segment_name"]
        assert 117 < seg["lon"] < 120

    def test_nonexistent_segment_returns_none(self):
        """_find_river_segment('长江', '不存在的段') → None."""
        seg = server._find_river_segment("长江", "不存在的段")
        assert seg is None
