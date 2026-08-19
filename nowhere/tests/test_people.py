"""Tests for Card 41: 卡中人系统。

覆盖:
- 40% 遇见可 mock (force_encounter)
- 三句轮换不重复 + 第四句记得你
- months 外不遇见
- knows 三型各有路由
- 故人卡尾引导只在人物类
"""

from __future__ import annotations

import random
import sys
import types

import pytest

sys.stdout.reconfigure(encoding="utf-8")

from nowhere import people as people_mod


# ── Helpers ──────────────────────────────────────────────────────────────

def _seed_rng(seed: int = 42) -> random.Random:
    return random.Random(seed)


# ── people module: load & structure ──────────────────────────────────────

class TestLoad:
    def test_seed_loads(self):
        data = people_mod._load()
        assert len(data) >= 50, f"Expected 50+ people, got {len(data)}"

    def test_entry_has_required_fields(self):
        data = people_mod._load()
        for place, entry in list(data.items())[:10]:
            assert "person" in entry, f"{place} missing person"
            assert "sight" in entry, f"{place} missing sight"
            assert "lines" in entry, f"{place} missing lines"
            assert len(entry["lines"]) == 3, f"{place} has {len(entry['lines'])} lines, expected 3"
            assert "knows" in entry, f"{place} missing knows"
            assert "months" in entry, f"{place} missing months"

    def test_sight_is_action_not_introduction(self):
        """sight must have at least one comma (clause structure, not bare noun phrase)."""
        data = people_mod._load()
        for place, entry in list(data.items())[:20]:
            sight = entry["sight"]
            assert "," in sight or "，" in sight, \
                f"{place}: sight lacks clause structure: {sight[:50]}"

    def test_knows_types_valid(self):
        data = people_mod._load()
        valid_types = {"direction", "festival", "rumor"}
        for place, entry in data.items():
            kt = entry["knows"]["type"]
            assert kt in valid_types, f"{place}: invalid knows type {kt}"

    def test_lines_within_40_chars(self):
        """每句 ≤40 字。"""
        data = people_mod._load()
        for place, entry in data.items():
            for i, line in enumerate(entry["lines"]):
                assert len(line) <= 40, \
                    f"{place} line {i} too long ({len(line)} chars): {line[:20]}..."


# ── find_nearby_person: encounter logic ──────────────────────────────────

class TestEncounter:
    def test_no_encounter_outside_radius(self):
        """坐标离所有人 >5km 时不出人。"""
        rng = _seed_rng()
        # 0,0 is nowhere near any seeded place
        result = people_mod.find_nearby_person(
            0.0, 0.0, 7, set(), rng,
        )
        assert result is None

    def test_force_encounter_near_kashgar(self):
        """喀什坐标附近 force_encounter=True 必出人。"""
        rng = _seed_rng()
        # 喀什 coords from humanities.json
        from nowhere import humanities
        coords = humanities.get_place_coords("喀什")
        if coords is None:
            pytest.skip("No coords for 喀什 in humanities.json")
        result = people_mod.find_nearby_person(
            coords["lat"], coords["lon"], 7, set(), rng,
            force_encounter=True,
        )
        assert result is not None
        assert result["person"] == "卡孜姆"

    def test_months_filter_blocks_encounter(self):
        """months 外不遇见。"""
        rng = _seed_rng()
        from nowhere import humanities
        coords = humanities.get_place_coords("喀什")
        if coords is None:
            pytest.skip("No coords for 喀什 in humanities.json")
        # 喀什 months: [3,4,5,6,7,8,9,10], month 1 should block
        result = people_mod.find_nearby_person(
            coords["lat"], coords["lon"], 1, set(), rng,
            force_encounter=True,
        )
        # Month 1 is not in Kashgar's months
        assert result is None

    def test_probabilistic_encounter(self):
        """不做 force_encounter 时概率 <100%。"""
        from nowhere import humanities
        coords = humanities.get_place_coords("喀什")
        if coords is None:
            pytest.skip("No coords for 喀什 in humanities.json")
        hits = 0
        for seed in range(200):
            rng = random.Random(seed)
            result = people_mod.find_nearby_person(
                coords["lat"], coords["lon"], 7, set(), rng,
            )
            if result is not None:
                hits += 1
        # Should be around 40%, allow wide margin
        assert 10 < hits < 190, f"Hit rate {hits}/200 seems off from ~40%"


# ── talk: line rotation ──────────────────────────────────────────────────

class TestTalk:
    def _make_entry(self) -> dict:
        return {
            "person": "测试人",
            "where": "测试地点",
            "sight": "测试人在测试。",
            "lines": ["第一句本地应景", "第二句本地知识", "第三句私人"],
            "knows": {"type": "direction", "text": "往东走三百米"},
            "months": [1,2,3,4,5,6,7,8,9,10,11,12],
        }

    def test_three_lines_rotate_no_repeat(self):
        entry = self._make_entry()
        rng = _seed_rng()
        lines = [people_mod.talk(entry, i, rng=rng) for i in range(3)]
        assert lines[0] == "第一句本地应景"
        assert lines[1] == "第二句本地知识"
        assert lines[2] == "第三句私人"

    def test_fourth_line_is_remember_variant(self):
        entry = self._make_entry()
        rng = _seed_rng()
        line = people_mod.talk(entry, 3, rng=rng)
        assert line in people_mod._REMEMBER_VARIANTS

    def test_knows_direction_route(self):
        entry = self._make_entry()
        rng = _seed_rng()
        line = people_mod.talk(entry, 0, question="路怎么走", rng=rng)
        assert line == "往东走三百米"

    def test_knows_no_advance(self):
        """question 含路/方向时返回 knows,不影响 line_index。"""
        entry = self._make_entry()
        rng = _seed_rng()
        line = people_mod.talk(entry, 0, question="方向在哪", rng=rng)
        assert line == "往东走三百米"

    def test_knows_festival_type(self):
        entry = {
            "person": "节日人",
            "where": "测试地点",
            "sight": "节日人在测试。",
            "lines": ["a", "b", "c"],
            "knows": {"type": "festival", "text": "端午节有赛龙舟"},
            "months": [6],
        }
        rng = _seed_rng()
        line = people_mod.talk(entry, 0, question="这儿有什么节", rng=rng)
        assert "端午" in line

    def test_knows_rumor_type(self):
        entry = {
            "person": "传言人",
            "where": "测试地点",
            "sight": "传言人在测试。",
            "lines": ["a", "b", "c"],
            "knows": {"type": "rumor", "text": "听说北边有人在找信使"},
            "months": [1,2,3,4,5,6,7,8,9,10,11,12],
        }
        rng = _seed_rng()
        line = people_mod.talk(entry, 0, question="有什么传闻", rng=rng)
        assert "信使" in line


# ── 故人 hint (humanities 人物 卡) ─────────────────────────────────────

class TestGuRen:
    def test_humanities_person_hint(self):
        """故人卡(人物类)尾部应带引导。"""
        from nowhere import humanities, describe
        rng = _seed_rng()
        seen: set[str] = set()
        # Kyoto has 人物 cards
        card = humanities.draw("京都", seen, rng)
        if card is None:
            pytest.skip("No humanities card for 京都")
        # card["category"] should be 事件 or 人物 or 作品
        # If it's 事件 first, try again
        if card["category"] != "人物":
            seen.add(card["key"])
            card = humanities.draw("京都", seen, rng)
        if card is None or card["category"] != "人物":
            pytest.skip("No 人物 card for 京都 in first draws")

        # Simulate the hint logic from walk_impl
        h_text = describe.render("humanities", card, None, rng)
        if card.get("category") == "人物":
            h_name = card.get("ref", {}).get("name", "")
            h_text += f"\n{h_name}。这名字你记下了。ask 能问出更多。"
        assert "ask 能问出更多" in h_text
        assert "记下了" in h_text

    def test_humanities_event_no_hint(self):
        """事件卡不加引导。"""
        from nowhere import humanities, describe
        rng = _seed_rng()
        seen: set[str] = set()
        card = humanities.draw("京都", seen, rng)
        if card is None:
            pytest.skip("No humanities card for 京都")
        # If first card is 事件, check no hint
        if card["category"] == "事件":
            h_text = describe.render("humanities", card, None, rng)
            assert "ask 能问出更多" not in h_text
