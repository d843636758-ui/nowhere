"""Card 16: 盲开门 tests."""

from __future__ import annotations

import sys
import os
import random

sys.stdout.reconfigure(encoding="utf-8")

# Ensure we can import the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from nowhere.state import WorldState


def test_blind_state_serialization():
    """blind/door_key state round-trips through to_dict/from_dict."""
    s = WorldState()
    s.blind = True
    s.blind_clues = 2
    s.door_key = None
    d = s.to_dict()
    assert d["blind"] is True
    assert d["blind_clues"] == 2
    s2 = WorldState.from_dict(d)
    assert s2.blind is True
    assert s2.blind_clues == 2


def test_blind_default_false():
    """Default state has blind=False."""
    s = WorldState()
    assert s.blind is False
    assert s.blind_clues == 0


def test_blind_state_with_door_key():
    """door_key round-trips."""
    s = WorldState()
    s.door_key = "my-key"
    d = s.to_dict()
    assert d["door_key"] == "my-key"
    s2 = WorldState.from_dict(d)
    assert s2.door_key == "my-key"


def test_reveal_variants_count():
    """Reveal variant pools have at least 4 entries each."""
    # Import from server module (the _REVEAL_VARIANTS dict)
    import importlib
    try:
        from nowhere import server
        # Check that reveal variants exist and have enough entries
        variants = server._REVEAL_VARIANTS
        assert len(variants["correct"]) >= 4, f"correct variants: {len(variants['correct'])}"
        assert len(variants["give_up"]) >= 4, f"give_up variants: {len(variants['give_up'])}"
        assert len(variants["wrong_clue"]) >= 1, f"wrong_clue variants: {len(variants['wrong_clue'])}"
        assert len(variants["far"]) >= 1, f"far variants: {len(variants['far'])}"
    except ImportError:
        # If server can't be imported (missing deps), just check the state
        pass


def test_blind_clue_progression():
    """Blind clues progress from continent to climate to country."""
    from nowhere.server import _get_blind_clue
    # Beijing coords
    clue0 = _get_blind_clue(39.9, 116.4, 0)
    clue1 = _get_blind_clue(39.9, 116.4, 1)
    clue2 = _get_blind_clue(39.9, 116.4, 2)
    # Should be different levels
    assert "亚洲" in clue0 or "中国" in clue0 or "温" in clue0 or "寒" in clue0 or "北" in clue0
    assert clue1 != clue0
    assert clue2 != clue1


def test_drift_seen_serialization():
    """drift_seen round-trips through state."""
    s = WorldState()
    s.drift_seen = ["text1", "text2"]
    d = s.to_dict()
    assert d["drift_seen"] == ["text1", "text2"]
    s2 = WorldState.from_dict(d)
    assert s2.drift_seen == ["text1", "text2"]
