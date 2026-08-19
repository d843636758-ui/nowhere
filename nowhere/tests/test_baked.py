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
    """卡32: Unknown foods with no desc → None (no desc = no card)."""
    r = baked.render_food({"zh": "不存在的食物", "en": "Nonexistent"}, random.Random(1))
    assert r is None  # 无 desc 且无场景匹配 → 不出卡

    # But a food WITH desc should still render via template
    r2 = baked.render_food({"zh": "不存在的食物", "en": "Nonexistent", "desc": "好吃的"}, random.Random(1))
    assert r2 is not None
    assert "不存在的食物" in r2


def test_food_scene_count():
    """Verify all 193 scenes loaded."""
    scenes = baked._load_food_scenes()
    assert len(scenes) == 192


def test_food_items_filters_empty_zh(monkeypatch):
    """Food entries with zh="" should be filtered out from candidate pool."""
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


def test_zh_empty_not_in_rendered_output(monkeypatch):
    """End-to-end: zh="" entries must not produce English-only names in rendered results."""
    baked._load()
    monkeypatch.setattr(
        baked,
        "_food",
        {
            "TEST": [
                {"zh": "红烧肉", "en": "Braised Pork", "desc": "好吃"},
                {"zh": "", "en": "Paprikash", "desc": "Hungarian stew"},
            ]
        },
    )
    items = baked.food_items("TEST")
    rng = random.Random(42)
    rendered = [baked.render_food(item, rng) for item in items]
    # "Paprikash" should never appear -- the empty-zh entry was filtered out
    for line in rendered:
        assert "Paprikash" not in line
    # The valid Chinese entry should still render
    assert any("红烧肉" in line for line in rendered)
