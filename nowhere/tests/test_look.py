"""Tests for look direction and short-distance walking (card 7)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import pytest

from nowhere import state as state_mod, walk


def _make_state(lat: float, lon: float, heading: float = 0.0) -> state_mod.WorldState:
    """Create a minimal WorldState for testing."""
    s = state_mod.WorldState()
    s.pos = (lat, lon)
    s.heading = heading
    s.landed_at = datetime.now(timezone.utc)
    s.place_name = "测试点"
    return s


def test_heading_starts_at_zero():
    """New state has heading=0 (north)."""
    s = _make_state(35.0, 135.0)
    assert s.heading == 0.0


def test_heading_updates_on_walk():
    """After walking North, heading stays 0."""
    s = _make_state(35.0, 135.0)
    walk.step(s, 0, None, 2.0)  # North
    assert s.heading == 0.0


def test_heading_updates_on_east_walk():
    """After walking East, heading becomes 90."""
    s = _make_state(35.0, 135.0)
    walk.step(s, 90, None, 2.0)  # East
    assert s.heading == 90.0


def test_heading_roundtrip():
    """Heading survives save/load."""
    s = _make_state(35.0, 135.0, heading=270.0)
    d = s.to_dict()
    assert d["heading"] == 270.0
    restored = state_mod.WorldState.from_dict(d)
    assert restored.heading == 270.0


def test_short_distance_clamp():
    """Walking 0.01km clamps to 0.05km minimum."""
    s = _make_state(35.0, 135.0)
    result = walk.step(s, 0, None, 0.01)
    assert result["dist_km"] >= 0.05


def test_look_directions():
    """look_impl returns text for various directions."""
    from nowhere.server import look_impl, _state
    import nowhere.server as srv

    # Monkeypatch global state
    original = srv._state
    srv._state = _make_state(35.0, 135.0, heading=0.0)
    try:
        for d in ["前", "后", "左", "右", "N", "S", "E", "W", "北", "南"]:
            r = look_impl(d)
            assert "text" in r
            assert len(r["text"]) > 5
    finally:
        srv._state = original


def test_look_does_not_move():
    """look_impl does not change position."""
    from nowhere.server import look_impl
    import nowhere.server as srv

    original = srv._state
    srv._state = _make_state(35.0, 135.0)
    pos_before = srv._state.pos
    try:
        look_impl("左")
        assert srv._state.pos == pos_before
    finally:
        srv._state = original


def test_look_relative_direction():
    """look('左') with heading=0 should look West (270°)."""
    from nowhere.server import look_impl
    import nowhere.server as srv

    original = srv._state
    srv._state = _make_state(35.0, 135.0, heading=0.0)
    try:
        r = look_impl("左")
        assert r["data"]["bearing"] == 270.0
    finally:
        srv._state = original
