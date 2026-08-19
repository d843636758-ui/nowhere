"""Tests for say/quotes/journal system (card 8)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import pytest

from nowhere import journeys, state as state_mod


@pytest.fixture()
def isolated_home(tmp_path, monkeypatch):
    """Isolate NOWHERE_HOME to a temp directory."""
    monkeypatch.setenv("NOWHERE_HOME", str(tmp_path))
    journeys._JOURNEYS_DIR = tmp_path / "journeys"
    journeys._INDEX_FILE = journeys._JOURNEYS_DIR / "index.json"
    state_mod._SAVE_DIR = tmp_path
    state_mod._SAVE_FILE = tmp_path / "journey.json"
    return tmp_path


def _make_state(place: str, lat: float, lon: float) -> state_mod.WorldState:
    s = state_mod.WorldState()
    s.pos = (lat, lon)
    s.place_name = place
    s.landed_at = datetime.now(timezone.utc)
    s.last_text = f"你在{place}。"
    return s


def test_say_saves_quote(isolated_home):
    """say saves a quote with place name."""
    import nowhere.server as srv
    original = srv._state
    srv._state = _make_state("京都", 35.01, 135.77)
    try:
        r = srv.say_impl("这句话留下")
        assert "记下了" in r["text"] or "留在这" in r["text"] or "听到了" in r["text"] or "带走了" in r["text"]
        assert len(srv._state.quotes) == 1
        assert srv._state.quotes[0]["text"] == "这句话留下"
        assert srv._state.quotes[0]["place"] == "京都"
    finally:
        srv._state = original


def test_quotes_lists_quotes(isolated_home):
    """quotes() lists saved quotes."""
    import nowhere.server as srv
    original = srv._state
    srv._state = _make_state("布拉格", 50.08, 14.44)
    try:
        srv.say_impl("第一句")
        srv.say_impl("第二句")
        r = srv.quotes()
        assert "2" in r["text"]
        assert "第一句" in r["text"]
        assert "第二句" in r["text"]
    finally:
        srv._state = original


def test_quotes_empty(isolated_home):
    """quotes() with no quotes returns empty message."""
    import nowhere.server as srv
    original = srv._state
    srv._state = _make_state("纽约", 40.71, -74.01)
    try:
        r = srv.quotes()
        assert "还没说过" in r["text"]
    finally:
        srv._state = original


def test_say_empty_text(isolated_home):
    """say with empty text returns error."""
    import nowhere.server as srv
    original = srv._state
    srv._state = _make_state("测试", 0, 0)
    try:
        r = srv.say_impl("")
        assert "没说话" in r["text"]
    finally:
        srv._state = original


def test_quotes_fifo_50(isolated_home):
    """quotes beyond 50 are dropped (FIFO)."""
    import nowhere.server as srv
    original = srv._state
    srv._state = _make_state("测试", 0, 0)
    try:
        for i in range(55):
            srv.say_impl(f"第{i}句")
        assert len(srv._state.quotes) == 50
        assert srv._state.quotes[0]["text"] == "第5句"  # first 5 dropped
    finally:
        srv._state = original


def test_say_roundtrip(isolated_home):
    """quotes survive save/load."""
    import nowhere.server as srv
    original = srv._state
    srv._state = _make_state("京都", 35.01, 135.77)
    try:
        srv.say_impl("记住这句话")
        d = srv._state.to_dict()
        restored = state_mod.WorldState.from_dict(d)
        assert len(restored.quotes) == 1
        assert restored.quotes[0]["text"] == "记住这句话"
    finally:
        srv._state = original
