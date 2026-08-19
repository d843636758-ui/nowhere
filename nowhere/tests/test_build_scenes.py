"""Tests for tools/build_scenes.py — build-time content pipeline."""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

# Add tools/ to path so we can import build_scenes
_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT / "tools"))
import build_scenes


# ── Validation tests ──────────────────────────────────────────────────


def test_missing_field_rejected():
    """Card missing required field must be caught."""
    cards = [{"text": "test", "type": "river"}]  # missing biomes
    errors = build_scenes._validate_card(cards[0], 0, "test")
    assert any("biomes" in e for e in errors)


def test_invalid_type_rejected():
    """Unknown type must be caught."""
    card = {"text": "test", "type": "invalid_type", "biomes": ["any"]}
    errors = build_scenes._validate_card(card, 0, "test")
    assert any("type" in e for e in errors)


def test_invalid_biome_rejected():
    """Unknown biome must be caught."""
    card = {"text": "test", "type": "river", "biomes": ["invalid_biome"]}
    errors = build_scenes._validate_card(card, 0, "test")
    assert any("biome" in e for e in errors)


def test_forbidden_word_rejected():
    """Card with forbidden word must be caught."""
    card = {"text": "这里的风景很美", "type": "river", "biomes": ["any"]}
    errors = build_scenes._validate_card(card, 0, "test")
    assert any("forbidden" in e for e in errors)


def test_vague_word_rejected():
    """Card with vague word must be caught."""
    card = {"text": "好像有什么东西", "type": "river", "biomes": ["any"]}
    errors = build_scenes._validate_card(card, 0, "test")
    assert any("vague" in e for e in errors)


def test_empty_text_rejected():
    """Card with empty text must be caught."""
    card = {"text": "", "type": "river", "biomes": ["any"]}
    errors = build_scenes._validate_card(card, 0, "test")
    assert any("empty" in e for e in errors)


def test_valid_card_passes():
    """Valid card must have no errors."""
    card = {"text": "水凉得刺骨", "type": "stream", "biomes": ["any"],
            "author": "hand"}
    errors = build_scenes._validate_card(card, 0, "test")
    assert errors == []


def test_false_positive_context_allowed():
    """'十分钟' should not trigger forbidden word '十分'."""
    card = {"text": "你走了十分钟", "type": "river", "biomes": ["any"]}
    errors = build_scenes._validate_card(card, 0, "test")
    assert not any("forbidden" in e for e in errors)


def test_duplicate_text_rejected():
    """Duplicate text within same type must be caught."""
    cards = [
        {"text": "水凉", "type": "stream", "biomes": ["any"]},
        {"text": "水凉", "type": "stream", "biomes": ["any"]},
    ]
    # Use _load_and_validate on a temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                     delete=False, encoding="utf-8") as f:
        json.dump(cards, f)
        f.flush()
        _, errors = build_scenes._load_and_validate(pathlib.Path(f.name))
    assert any("duplicate" in e for e in errors)


# ── Build output tests ────────────────────────────────────────────────


def test_tundra_water_no_dock():
    """Tundra water product must not contain dock scenes."""
    pool = build_scenes._build_water(_load_water_src())
    tundra = pool.get("scene_water_tundra", [])
    assert tundra, "No tundra water scenes"
    for line in tundra:
        assert "码头" not in line, f"Tundra has dock: {line!r}"


def test_coast_water_has_dock():
    """Coast water product must contain dock scenes."""
    pool = build_scenes._build_water(_load_water_src())
    coast = pool.get("scene_water_coast", [])
    assert any("码头" in line for line in coast), "Coast missing dock"


def test_dock_type_single_line():
    """Dock type file must have exactly 1 line (1 dock card)."""
    pool = build_scenes._build_water(_load_water_src())
    dock = pool.get("scene_water_dock", [])
    assert len(dock) == 1, f"Dock has {len(dock)} lines, expected 1"


def test_water_product_count_matches_source():
    """Total unique lines across all water biome files must match source count."""
    src = _load_water_src()
    pool = build_scenes._build_water(src)
    # All source texts should appear in at least one biome file
    all_product_texts = set()
    for lines in pool.values():
        all_product_texts.update(lines)
    src_texts = {c["text"] for c in src}
    assert src_texts <= all_product_texts, (
        f"Missing texts: {src_texts - all_product_texts}"
    )


def test_discovery_biome_files_nonempty():
    """Each biome's discovery file must be nonempty."""
    src = _load_discovery_src()
    pool = build_scenes._build_discovery(src)
    for biome in ("forest", "desert", "mountain", "coast", "tundra", "city"):
        key = f"scene_discovery_{biome}"
        assert key in pool, f"Missing {key}"
        assert len(pool[key]) >= 8, f"{key} has only {len(pool[key])} lines"


def test_full_build_produces_files(tmp_path):
    """Full build must produce product files."""
    # Patch output dir to tmp
    old_out = build_scenes._OUT_DIR
    build_scenes._OUT_DIR = tmp_path
    try:
        count, errors = build_scenes.build(check_only=False)
        assert not errors, f"Build errors: {errors}"
        assert count > 0
        # Check some files exist
        assert (tmp_path / "scene_water_tundra.txt").exists()
        assert (tmp_path / "scene_water_coast.txt").exists()
        assert (tmp_path / "scene_discovery_forest.txt").exists()
    finally:
        build_scenes._OUT_DIR = old_out


def test_full_build_no_forbidden_words(tmp_path):
    """Build output must contain no forbidden words."""
    old_out = build_scenes._OUT_DIR
    build_scenes._OUT_DIR = tmp_path
    try:
        build_scenes.build(check_only=False)
        for fp in tmp_path.glob("scene_*.txt"):
            content = fp.read_text(encoding="utf-8")
            for word in build_scenes._FORBIDDEN_WORDS:
                # Check with false-positive context
                idx = content.find(word)
                while idx >= 0:
                    end = idx + len(word)
                    suffix = content[end:end + 1] if end < len(content) else ""
                    if (word in build_scenes._FALSE_POSITIVE_CONTEXTS and
                            suffix in build_scenes._FALSE_POSITIVE_CONTEXTS[word]):
                        idx = content.find(word, end)
                        continue
                    assert False, f"Forbidden word '{word}' in {fp.name}"
    finally:
        build_scenes._OUT_DIR = old_out


# ── Helpers ───────────────────────────────────────────────────────────


def _load_water_src() -> list[dict]:
    fp = _ROOT / "nowhere" / "data" / "scenes_src" / "water.json"
    return json.loads(fp.read_text(encoding="utf-8"))


def _load_discovery_src() -> list[dict]:
    fp = _ROOT / "nowhere" / "data" / "scenes_src" / "discovery.json"
    return json.loads(fp.read_text(encoding="utf-8"))
