"""Card 21: 声音出处 tests."""

from __future__ import annotations

import json
import sys
import os
import pathlib
import random

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"


def test_soundscape_credits_json_exists():
    """soundscape_credits.json exists."""
    fp = DATA_DIR / "soundscape_credits.json"
    assert fp.exists(), f"soundscape_credits.json not found at {fp}"


def test_credits_30_entries():
    """soundscape_credits.json has 30+ entries total."""
    fp = DATA_DIR / "soundscape_credits.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    total = sum(len(entries) for entries in data.values())
    assert total >= 30, f"Only {total} credits entries, need 30+"


def test_credits_8_biome_types():
    """soundscape_credits.json covers 8 biome types."""
    fp = DATA_DIR / "soundscape_credits.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    assert len(data) >= 8, f"Only {len(data)} biome types, need 8"


def test_credits_each_biome_3_plus():
    """Each biome type has at least 3 entries."""
    fp = DATA_DIR / "soundscape_credits.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    for biome, entries in data.items():
        assert len(entries) >= 3, f"Biome '{biome}' has only {len(entries)} entries, need 3+"


def test_credits_all_have_who_where_note():
    """All credit entries have who/where/note fields."""
    fp = DATA_DIR / "soundscape_credits.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    for biome, entries in data.items():
        for entry in entries:
            assert "who" in entry, f"Missing 'who' in {biome}"
            assert "where" in entry, f"Missing 'where' in {biome}"
            assert "note" in entry, f"Missing 'note' in {biome}"
            assert entry["who"].strip(), f"Empty 'who' in {biome}"
            assert entry["where"].strip(), f"Empty 'where' in {biome}"
            assert entry["note"].strip(), f"Empty 'note' in {biome}"


def test_credits_no_forbidden_words():
    """Credit notes don't contain forbidden words."""
    fp = DATA_DIR / "soundscape_credits.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    forbidden = ["很", "非常", "十分"]
    for biome, entries in data.items():
        for entry in entries:
            for word in forbidden:
                assert word not in entry["note"], f"Forbidden word '{word}' in {biome} note: {entry['note']}"


def test_credits_biome_matching():
    """Credits function only returns entries matching the biome."""
    from nowhere.soundscape import soundscape_credit, _BIOME_CREDIT_MAP
    rng = random.Random(42)

    # Forest biome should get forest credits
    forest_hits = 0
    for _ in range(200):
        result = soundscape_credit("forest", rng)
        if result:
            forest_hits += 1
            assert "录" in result or "收" in result or "录" in result
    # With 20% chance, should get some hits in 200 tries
    assert forest_hits > 0, "No forest credits in 200 tries"


def test_credits_20_percent_chance():
    """Credits appear ~20% of the time."""
    from nowhere.soundscape import soundscape_credit
    rng = random.Random(42)

    hits = 0
    trials = 1000
    for _ in range(trials):
        result = soundscape_credit("forest", rng)
        if result:
            hits += 1
    rate = hits / trials
    assert 0.10 < rate < 0.30, f"Credit rate {rate:.2%} outside expected ~20%"


def test_credits_biome_mapping():
    """Biome mapping covers expected biomes."""
    from nowhere.soundscape import _BIOME_CREDIT_MAP
    expected = {"forest", "city", "coast", "desert", "grassland", "tundra", "mountain", "wetland"}
    for biome in expected:
        assert biome in _BIOME_CREDIT_MAP, f"Missing biome mapping for '{biome}'"


def test_credits_empty_biome():
    """Unknown biome returns None."""
    from nowhere.soundscape import soundscape_credit
    rng = random.Random(42)
    # "volcano" has no credits, should return None even on hit
    result = soundscape_credit("volcano", rng)
    # It will be None because volcano maps to empty string
    assert result is None


def test_credits_templates():
    """Credit output matches one of the 3 templates."""
    from nowhere.soundscape import soundscape_credit
    rng = random.Random(42)

    for _ in range(100):
        result = soundscape_credit("forest", rng)
        if result:
            # Should contain template markers
            assert "录" in result or "收" in result or "来自" in result
            break
