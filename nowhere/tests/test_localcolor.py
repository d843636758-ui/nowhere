"""Tests for localcolor (方志一叠卡)."""

from __future__ import annotations

import random

from nowhere import baked, localcolor


def test_has_place():
    assert localcolor.has_place("喀什") is True
    assert localcolor.has_place("不存在的地方") is False
    assert localcolor.has_place(None) is False


def test_draw_no_repeat_until_exhausted():
    seen: set[str] = set()
    rng = random.Random(1)
    cards = []
    while True:
        c = localcolor.draw("喀什", seen, rng)
        if c is None:
            break
        seen.add(c["key"])
        cards.append(c)
    assert len(cards) >= 8  # 一叠,不是一张
    assert localcolor.draw("喀什", seen, rng) is None  # 抽完就没了


def test_draw_unknown_place():
    assert localcolor.draw("不存在的地方", set(), random.Random(1)) is None


def test_rhythm_event_hours():
    # 喀什: 10-22 巴扎开着
    hit = localcolor.rhythm_event("喀什", 15, random.Random(1))
    assert hit is not None and "巴扎" in hit
    # 深夜 3 点无节律
    assert localcolor.rhythm_event("喀什", 3, random.Random(1)) is None
    assert localcolor.rhythm_event("不存在的地方", 12, random.Random(1)) is None


def test_nanjing_from_regional():
    """南京 comes from regional merge — has_place True and can draw a card."""
    assert localcolor.has_place("南京") is True
    card = localcolor.draw("南京", set(), random.Random(1))
    assert card is not None
    assert card["text"]


def test_handwritten_priority_over_baked():
    """卡32: 同地连抽到手写层空, 期间烘焙卡占比 <20%."""
    # 先算喀什手写卡的 key 集合 (Card layer)
    hw_keys: set[str] = set()
    for c in localcolor._load():
        if c.conditions.get("place") == "喀什" and c.meta.get("category") != "节律":
            hw_keys.add(c.id)

    seen: set[str] = set()
    rng = random.Random(42)
    baked_count = 0
    total = 0
    while True:
        card = localcolor.draw("喀什", seen, rng, country_code="CN")
        if card is None:
            break
        seen.add(card["key"])
        total += 1
        if "烘焙" in card["key"]:
            baked_count += 1
        # 手写层全部 seen 就停,不计入烘焙续抽
        if hw_keys and hw_keys.issubset(seen):
            break
    if total > 0:
        ratio = baked_count / total
        assert ratio < 0.20, f"烘焙卡占比 {ratio:.0%} 超过20% ({baked_count}/{total})"


def test_zh_empty_food_never_appears(monkeypatch):
    """卡32: zh 空的美食卡永远不会出现在抽卡结果中."""
    baked._load()
    monkeypatch.setattr(
        baked,
        "_food",
        {
            "ZZ": [
                {"zh": "红烧肉", "en": "Braised Pork", "desc": "好吃"},
                {"zh": "", "en": "paprikash", "desc": "Hungarian stew"},
                {"zh": "", "en": "túrógombóc", "desc": "cheese dumplings"},
            ]
        },
    )
    monkeypatch.setattr(baked, "_flora", {"测试无手写地": []})

    seen: set[str] = set()
    rng = random.Random(1)
    # 抽20次, 看有没有纯英文名渗入
    for _ in range(20):
        card = localcolor.draw("测试无手写地", seen, rng, country_code="ZZ")
        if card is None:
            break
        seen.add(card["key"])
        text = card["text"]
        assert "paprikash" not in text, f"纯英文名渗入: {text}"
        assert "túrógombóc" not in text, f"纯英文名渗入: {text}"


def test_no_filler_sentences_in_rendered():
    """卡32: 渲染结果不含已删除的万能尾句."""
    filler = ["在这里，吃饭不是将就的事", "名字记不住没关系，味道会替你记住"]
    rng = random.Random(7)
    for item in [
        {"zh": "小笼包", "en": "Xiaolongbao", "desc": "皮薄汤多"},
        {"zh": "不存在的食物", "en": "Fake", "desc": "测试"},
        {"zh": "烤串", "en": "Kebab", "desc": "炭火烤的"},
    ]:
        result = baked.render_food(item, rng)
        if result is not None:
            for phrase in filler:
                assert phrase not in result, f"渲染结果含万能尾句: {result}"
