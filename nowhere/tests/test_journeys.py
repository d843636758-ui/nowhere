"""Tests for multi-journey system."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from nowhere import journeys, state as state_mod


@pytest.fixture()
def isolated_home(tmp_path, monkeypatch):
    """Isolate NOWHERE_HOME to a temp directory."""
    monkeypatch.setenv("NOWHERE_HOME", str(tmp_path))
    # Clear module-level caches
    journeys._JOURNEYS_DIR = tmp_path / "journeys"
    journeys._INDEX_FILE = journeys._JOURNEYS_DIR / "index.json"
    state_mod._SAVE_DIR = tmp_path
    state_mod._SAVE_FILE = tmp_path / "journey.json"
    return tmp_path


def _make_state(place: str, lat: float, lon: float, steps: int = 0) -> state_mod.WorldState:
    """Create a minimal WorldState for testing."""
    from datetime import datetime, timezone
    s = state_mod.WorldState()
    s.pos = (lat, lon)
    s.place_name = place
    s.landed_at = datetime.now(timezone.utc)
    s.path = [{"lat": lat, "lon": lon, "elevation": 0, "dist_km": 1.0}] * steps
    s.last_text = f"你在{place}走了走。"
    return s


def test_save_and_list(isolated_home):
    """save_current creates a journey file and list_journeys returns it."""
    s = _make_state("纽约", 40.71, -74.01, steps=3)
    journeys.save_current(s)

    js = journeys.list_journeys()
    assert len(js) == 1
    assert js[0]["place_name"] == "纽约"
    assert js[0]["steps"] == 3


def test_switch_by_place(isolated_home):
    """switch() can restore a journey by place name."""
    s = _make_state("布拉格", 50.08, 14.44, steps=2)
    journeys.save_current(s)

    restored = journeys.switch("布拉格")
    assert restored is not None
    assert restored.pos == (50.08, 14.44)
    assert len(restored.path) == 2


def test_two_journeys_switch(isolated_home):
    """Two journeys can coexist and be switched between."""
    s1 = _make_state("纽约", 40.71, -74.01, steps=3)
    journeys.save_current(s1)

    s2 = _make_state("布拉格", 50.08, 14.44, steps=2)
    journeys.save_current(s2)

    js = journeys.list_journeys()
    assert len(js) == 2

    # Switch back to纽约
    restored = journeys.switch("纽约")
    assert restored is not None
    assert restored.pos == (40.71, -74.01)
    assert len(restored.path) == 3


def test_switch_nonexistent(isolated_home):
    """switch() returns None for unknown journey."""
    s = _make_state("纽约", 40.71, -74.01)
    journeys.save_current(s)

    assert journeys.switch("不存在的地方") is None


def test_delete(isolated_home):
    """delete() removes a journey."""
    s = _make_state("纽约", 40.71, -74.01)
    journeys.save_current(s)

    assert len(journeys.list_journeys()) == 1
    journeys.delete("纽约")
    assert len(journeys.list_journeys()) == 0


def test_roundtrip_preserves_seen_cards(isolated_home):
    """save→switch preserves seen_cards."""
    s = _make_state("京都", 35.01, 135.77)
    s.seen_cards = {"card_a", "card_b"}
    journeys.save_current(s)

    restored = journeys.switch("京都")
    assert restored.seen_cards == {"card_a", "card_b"}


def test_fuzzy_match(isolated_home):
    """switch() fuzzy-matches place name."""
    s = _make_state("拉普兰", 68.0, 25.0)
    journeys.save_current(s)

    # Should match with partial name
    restored = journeys.switch("拉普")
    assert restored is not None
    assert restored.pos == (68.0, 25.0)
