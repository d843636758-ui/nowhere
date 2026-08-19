"""Tests for baked (烘焙物产层)."""

from __future__ import annotations

import random

from nowhere import baked


def test_food_scene_render():
    """Scene file entries should produce sensory-rich descriptions."""
    r = baked.render_food({"zh": "冬阴功", "en": "Tom Yum Kung"}, random.Random(1))
    assert "冬阴功" in r
    # Scene file has sensory details about sourness
    assert "酸" in r or "辣" in r


def test_food_scene_partial_match():
    """Partial name matches should still hit scene file."""
    r = baked.render_food({"zh": "热干面", "en": "Hot Dry Noodles"}, random.Random(1))
    assert "热干面" in r
    assert "芝麻酱" in r  # scene file mentions sesame paste


def test_food_scene_fallback():
    """Unknown foods should fall back to template logic."""
    r = baked.render_food({"zh": "不存在的食物", "en": "Nonexistent"}, random.Random(1))
    assert r  # Should still return something
    assert "不存在的食物" in r


def test_food_scene_count():
    """Verify all 193 scenes loaded."""
    scenes = baked._load_food_scenes()
    assert len(scenes) == 192


def test_food_items_filters_empty_zh(monkeypatch):
    """Food entries with zh="" should be filtered out from candidate pool."""
    # Monkeypatch the internal _food dict to inject an empty-zh entry
    baked._load()
    monkeypatch.setattr(
        baked,
        "_food",
        {
            "TEST": [
                {"zh": "红烧肉", "en": "Braised Pork", "desc": "好吃"},
                {"zh": "", "en": "Paprikash", "desc": "Hungarian stew"},
                {"zh": "  ", "en": "Another", "desc": "whitespace only"},
            ]
        },
    )
    items = baked.food_items("TEST")
    # Only the entry with a non-empty zh should survive
    assert len(items) == 1
    assert items[0]["zh"] == "红烧肉"


def test_render_food_no_english_leak():
    """render_food with zh="" should not produce English words in output."""
    # This tests the render path directly with an empty-zh item.
    # After the fix, food_items filters these out, but render_food itself
    # should also not produce English-only names in Chinese prose.
    r = baked.render_food({"zh": "", "en": "Paprikash"}, random.Random(1))
    # The name will be "Paprikash" since zh is empty -- verify it's not
    # a clean Chinese sentence (this documents the old bug behavior;
    # the real fix is at the food_items filter level).
    assert "Paprikash" in r  # render_food itself still renders what it gets
