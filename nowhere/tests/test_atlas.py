"""Tests for atlas (Card 15)."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

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
    s.path = [{"lat": lat, "lon": lon, "elevation": 0, "dist_km": 1.0}]
    s.last_text = f"你在{place}。"
    return s


def test_atlas_three_journeys(isolated_home):
    """3 journeys → atlas shows 3 places."""
    for place, lat, lon in [
        ("纽约", 40.71, -74.01),
        ("布拉格", 50.08, 14.44),
        ("拉普兰", 68.0, 25.0),
    ]:
        journeys.save_current(_make_state(place, lat, lon))

    result = journeys.atlas()
    assert result["places"] == 3
    assert result["continents"] >= 1
    assert result["extremes"]["north"]["name"] == "拉普兰"


def test_atlas_zero_journeys(isolated_home):
    """No journeys → places=0."""
    result = journeys.atlas()
    assert result["places"] == 0
    assert result["continents"] == 0
    assert result["extremes"] == {}


def test_atlas_extremes_correct(isolated_home):
    """Extremes are correctly identified."""
    journeys.save_current(_make_state("拉普兰", 68.0, 25.0))
    journeys.save_current(_make_state("乌斯怀亚", -54.8, -68.3))

    result = journeys.atlas()
    assert result["extremes"]["north"]["name"] == "拉普兰"
    assert result["extremes"]["south"]["name"] == "乌斯怀亚"


def test_atlas_variant_count():
    """3 atlas text variants."""
    from nowhere.server import _ATLAS_VARIANTS
    assert len(_ATLAS_VARIANTS) == 3


def test_atlas_no_forbidden_words():
    """No forbidden words in atlas variants."""
    from nowhere.server import _ATLAS_VARIANTS
    for text in _ATLAS_VARIANTS:
        for word in ("很", "非常", "十分"):
            assert word not in text, f"Forbidden word '{word}' in: {text}"


def test_atlas_continent_count(isolated_home):
    """Journeys on different continents increase continent count."""
    # NY (North America) and Prague (Europe)
    journeys.save_current(_make_state("纽约", 40.71, -74.01))
    journeys.save_current(_make_state("布拉格", 50.08, 14.44))

    result = journeys.atlas()
    assert result["places"] == 2
    assert result["continents"] >= 2
