"""Tests for bury/find system (Card 13)."""
from __future__ import annotations

import sys
import pytest
from datetime import datetime, timezone

from nowhere import placememory, state as state_mod


@pytest.fixture()
def isolated_home(tmp_path, monkeypatch):
    """Isolate NOWHERE_HOME to a temp directory."""
    monkeypatch.setenv("NOWHERE_HOME", str(tmp_path))
    return tmp_path


def _make_state_with_souvenir(place: str, lat: float, lon: float) -> state_mod.WorldState:
    s = state_mod.WorldState()
    s.pos = (lat, lon)
    s.place_name = place
    s.landed_at = datetime.now(timezone.utc)
    s.souvenir = {"name": "旧指南针", "from": "喀什", "desc": "铜的,指针有点卡"}
    return s


def test_buried_save_and_load(isolated_home):
    """save_buried writes to buried.json and buried_items reads it back."""
    entry = {
        "name": "旧指南针", "desc": "铜的", "from": "喀什",
        "pos": [39.47, 75.99], "buried_at": "2026-01-01T00:00:00+00:00",
        "note": "留给下一个路过的人",
    }
    placememory.save_buried(entry)
    items = placememory.buried_items()
    assert len(items) == 1
    assert items[0]["name"] == "旧指南针"
    assert items[0]["note"] == "留给下一个路过的人"


def test_buried_nearby(isolated_home):
    """buried_nearby finds items within 3km."""
    entry = {
        "name": "test", "desc": "", "from": "",
        "pos": [39.47, 75.99], "buried_at": "", "note": "",
    }
    placememory.save_buried(entry)

    # Within 3km
    nearby = placememory.buried_nearby(39.48, 75.99, radius_km=3.0)
    assert len(nearby) == 1

    # Far away (>100km)
    far = placememory.buried_nearby(40.5, 76.0, radius_km=3.0)
    assert len(far) == 0


def test_buried_fifo_100(isolated_home):
    """FIFO cap at 100 items."""
    for i in range(110):
        entry = {
            "name": f"item-{i}", "desc": "", "from": "",
            "pos": [39.47, 75.99], "buried_at": "", "note": "",
        }
        placememory.save_buried(entry)

    items = placememory.buried_items()
    assert len(items) == 100
    # First 10 should be gone
    assert items[0]["name"] == "item-10"
    assert items[-1]["name"] == "item-109"


def test_bury_variants_count():
    """All variant pools have required counts."""
    from nowhere.server import (
        _BURY_VARIANTS, _FIND_VARIANTS,
        _PUTBACK_VARIANTS, _EMPTY_BURY_VARIANTS,
    )
    assert len(_BURY_VARIANTS) == 4
    assert len(_FIND_VARIANTS) == 4
    assert len(_PUTBACK_VARIANTS) == 2
    assert len(_EMPTY_BURY_VARIANTS) == 2


def test_no_forbidden_words():
    """No forbidden words in any variant."""
    from nowhere.server import (
        _BURY_VARIANTS, _FIND_VARIANTS,
        _PUTBACK_VARIANTS, _EMPTY_BURY_VARIANTS,
    )
    for pool in [_BURY_VARIANTS, _FIND_VARIANTS, _PUTBACK_VARIANTS, _EMPTY_BURY_VARIANTS]:
        for text in pool:
            for word in ("很", "非常", "十分"):
                assert word not in text, f"Forbidden word '{word}' in: {text}"


def test_buried_entry_has_note_field(isolated_home):
    """Buried entry preserves note field."""
    entry = {
        "name": "test", "desc": "", "from": "",
        "pos": [39.47, 75.99], "buried_at": "", "note": "a note",
    }
    placememory.save_buried(entry)
    items = placememory.buried_items()
    assert items[0]["note"] == "a note"


def test_buried_empty_note(isolated_home):
    """Buried entry works with empty note."""
    entry = {
        "name": "test", "desc": "", "from": "",
        "pos": [39.47, 75.99], "buried_at": "", "note": "",
    }
    placememory.save_buried(entry)
    items = placememory.buried_items()
    assert items[0]["note"] == ""
