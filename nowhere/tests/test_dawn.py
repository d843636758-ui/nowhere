"""Card 19: 黎明合唱 tests."""

from __future__ import annotations

import json
import sys
import os
import pathlib
import random

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"


def test_dawn_chorus_json_exists():
    """dawn_chorus.json exists."""
    fp = DATA_DIR / "dawn_chorus.json"
    assert fp.exists(), f"dawn_chorus.json not found at {fp}"


def test_dawn_chorus_12_cards():
    """dawn_chorus.json has exactly 12 cards (3 groups x 4)."""
    fp = DATA_DIR / "dawn_chorus.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    assert len(data) == 3, f"Expected 3 biome groups, got {len(data)}"
    for group, cards in data.items():
        assert len(cards) == 4, f"Group '{group}' has {len(cards)} cards, expected 4"


def test_dawn_chorus_biome_groups():
    """dawn_chorus.json has forest/city/water groups."""
    fp = DATA_DIR / "dawn_chorus.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    assert "forest" in data
    assert "city" in data
    assert "water" in data


def test_dawn_chorus_no_forbidden_words():
    """Dawn chorus cards don't contain forbidden words."""
    fp = DATA_DIR / "dawn_chorus.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    forbidden = ["很", "非常", "十分"]
    for group, cards in data.items():
        for card in cards:
            for word in forbidden:
                assert word not in card, f"Forbidden word '{word}' in {group}: {card}"


def test_dawn_chorus_intensity_mapping():
    """Dawn chorus maps sun_alt to correct intensity index."""
    from nowhere.soundscape import dawn_chorus
    rng = random.Random(42)

    # sun_alt = -6.0 → first card (index 0, 一只)
    result = dawn_chorus("forest", -6.0, rng)
    assert result is not None
    assert result == "先是一只,在很远的树上。然后是第二只,近了。"

    # sun_alt = -0.5 → last card (index 3, 满)
    result = dawn_chorus("forest", -0.5, rng)
    assert result is not None
    assert "天亮了" in result or "井底" in result


def test_dawn_chorus_outside_window():
    """Dawn chorus returns None outside -6..0 window."""
    from nowhere.soundscape import dawn_chorus
    rng = random.Random(42)

    # sun_alt = 30 (daytime) → None
    assert dawn_chorus("forest", 30.0, rng) is None
    # sun_alt = -10 (deep night) → None
    assert dawn_chorus("forest", -10.0, rng) is None


def test_dawn_chorus_biome_fallback():
    """Unknown biome falls back to city group."""
    from nowhere.soundscape import dawn_chorus
    rng = random.Random(42)

    result = dawn_chorus("desert", -3.0, rng)
    # Should still return something (falls back to city)
    assert result is not None


def test_dawn_chorus_all_biomes():
    """Each biome group returns cards during the window."""
    from nowhere.soundscape import dawn_chorus
    rng = random.Random(42)

    for biome in ("forest", "city", "water"):
        result = dawn_chorus(biome, -3.0, rng)
        assert result is not None, f"No dawn chorus for {biome} at sun_alt=-3"
        assert len(result) > 5
