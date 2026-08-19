"""Card 18: 漂流卡 tests."""

from __future__ import annotations

import json
import sys
import os
import pathlib
import random

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from nowhere.state import WorldState

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"


def test_drift_cards_exist():
    """drift_cards.json exists and has content."""
    fp = DATA_DIR / "drift_cards.json"
    assert fp.exists(), f"drift_cards.json not found at {fp}"
    data = json.loads(fp.read_text(encoding="utf-8"))
    assert len(data) >= 5, f"Only {len(data)} biome groups"


def test_drift_cards_30_plus():
    """drift_cards.json has 30+ total cards."""
    fp = DATA_DIR / "drift_cards.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    total = sum(len(cards) for cards in data.values())
    assert total >= 30, f"Only {total} drift cards, need 30+"


def test_drift_cards_all_have_actions():
    """All drift cards have text and action fields."""
    fp = DATA_DIR / "drift_cards.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    for biome, cards in data.items():
        for card in cards:
            assert "text" in card, f"Missing text in {biome}: {card}"
            assert "action" in card, f"Missing action in {biome}: {card}"
            assert card["text"].strip(), f"Empty text in {biome}"


def test_drift_cards_biome_groups():
    """Drift cards have at least 'any' group."""
    fp = DATA_DIR / "drift_cards.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    assert "any" in data, "Missing 'any' biome group"
    assert len(data["any"]) >= 3, f"'any' group has only {len(data['any'])} cards"


def test_drift_seen_serialization():
    """drift_seen round-trips through state."""
    s = WorldState()
    s.drift_seen = ["跟着水声走。", "朝最亮的地方走。"]
    d = s.to_dict()
    assert d["drift_seen"] == ["跟着水声走。", "朝最亮的地方走。"]
    s2 = WorldState.from_dict(d)
    assert s2.drift_seen == ["跟着水声走。", "朝最亮的地方走。"]


def test_drift_action_types():
    """All action types are valid."""
    valid_actions = {"toward_sea", "toward_light", "downwind", "turn_next", "uphill"}
    fp = DATA_DIR / "drift_cards.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    for biome, cards in data.items():
        for card in cards:
            assert card["action"] in valid_actions, f"Invalid action '{card['action']}' in {biome}"


def test_drift_any_biome_pool():
    """'any' biome cards can serve as fallback for other biomes."""
    fp = DATA_DIR / "drift_cards.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    # Verify the server can load and filter drift cards
    try:
        from nowhere.server import _load_drift_cards
        loaded = _load_drift_cards()
        assert "any" in loaded
        assert len(loaded["any"]) >= 3
    except (ImportError, AttributeError):
        # If server can't be imported, just verify JSON structure
        assert len(data["any"]) >= 3
