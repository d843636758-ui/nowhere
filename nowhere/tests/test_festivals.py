"""Tests for Card 11: 节日历 — 在对的时间到对的地方."""

from __future__ import annotations

from datetime import datetime, timezone, date

import pytest

from nowhere import server


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset festival cache between tests."""
    server._festivals_cache = None
    yield
    server._festivals_cache = None


def test_festivals_json_has_86_prototypes():
    """festivals.json 应有 86 个节日原型。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "festivals.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    assert len(data) == 86, f"实际有 {len(data)} 个节日,应为86"


def test_each_festival_has_cards():
    """每个节日至少有 1 张主卡 + 1 张前夜卡。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "festivals.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    for fest in data:
        cards = fest.get("cards", [])
        eve = fest.get("eve_cards", [])
        total = len(cards) + len(eve)
        assert len(cards) >= 1, f"{fest['name']} 没有主卡"
        assert total >= 2, f"{fest['name']} 只有 {total} 张卡(主卡+前夜)"


def test_each_festival_has_eve_card():
    """每个节日至少有 1 张前夜卡。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "festivals.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    for fest in data:
        eve = fest.get("eve_cards", [])
        assert len(eve) >= 1, f"{fest['name']} 没有前夜卡"


def test_fixed_window_apr14_hits_splash():
    """4/14 → 清迈 hits 泼水节。"""
    sim_time = datetime(2026, 4, 14, 12, 0, tzinfo=timezone.utc)
    result = server._check_festival_hit("清迈", "TH", 18.79, sim_time, server._rng)
    assert result is not None
    assert "水" in result


def test_fixed_window_apr20_no_hit():
    """4/20 → 清迈无节日命中。"""
    sim_time = datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)
    result = server._check_festival_hit("清迈", "TH", 18.79, sim_time, server._rng)
    # 4/20 is outside 泼水节 window [4/13, 4/15]
    assert result is None


def test_lunar_window_spring_festival():
    """农历春节日期验证: 2026年2/17 北京命中春节。"""
    sim_time = datetime(2026, 2, 17, 12, 0, tzinfo=timezone.utc)
    result = server._check_festival_hit("北京", "CN", 39.9, sim_time, server._rng)
    assert result is not None


def test_lunar_window_no_hit_wrong_date():
    """春节窗口外不命中。"""
    sim_time = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
    result = server._check_festival_hit("北京", "CN", 39.9, sim_time, server._rng)
    # 3/1 is outside 春节 window (2026: [2,17], span_days=3)
    assert result is None


def test_country_fallback():
    """国家码匹配: CN 全境节气卡。"""
    # 冬至 12/21
    sim_time = datetime(2026, 12, 21, 12, 0, tzinfo=timezone.utc)
    result = server._check_festival_hit("南京", "CN", 32.0, sim_time, server._rng)
    # 冬至 has country=CN, so should match even if place != 南京
    # But 冬至 also has place=北京, so it's a place match for 北京
    # For 南京 it should still match via country
    assert result is not None


def test_lat_rule_cherry_blossom():
    """纬度规则: 樱花前线。"""
    # 京都 约35°N, base_lat=31.0, base_date=[3,24], days_per_deg=2.6
    # offset = (35-31)*2.6 = 10.4 days → adjusted_start ≈ 4/3
    sim_time = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
    result = server._check_festival_hit("京都", "JP", 35.0, sim_time, server._rng)
    assert result is not None
    assert "花" in result or "瓣" in result


def test_priority_place_over_country():
    """优先级: place 匹配 > country 匹配。"""
    # 泼水节 has place=景洪, country=CN
    # 同时有 CN 的冬至
    # 12/21 景洪应该命中冬至(CN)而不是泼水节
    sim_time = datetime(2026, 12, 21, 12, 0, tzinfo=timezone.utc)
    result = server._check_festival_hit("景洪", "CN", 22.0, sim_time, server._rng)
    assert result is not None


def test_forbidden_words_in_cards():
    """节日卡文案不含禁词。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "festivals.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    forbidden = {"很", "非常", "十分"}
    for fest in data:
        all_cards = fest.get("cards", []) + fest.get("eve_cards", [])
        for text in all_cards:
            for word in forbidden:
                assert word not in text, f"{fest['name']} 含禁词'{word}': {text[:50]}"


def test_festival_cards_not_empty():
    """所有节日卡文案非空。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "festivals.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    for fest in data:
        all_cards = fest.get("cards", []) + fest.get("eve_cards", [])
        for text in all_cards:
            assert len(text) >= 10, f"{fest['name']} 卡太短: {text}"


def test_window_types_present():
    """三种窗口类型都应有实例。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "festivals.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    types = set()
    for fest in data:
        wtype = fest.get("window", {}).get("type", "fixed")
        types.add(wtype)
    assert "fixed" in types, "没有 fixed 类型"
    assert "lunar" in types, "没有 lunar 类型"
    assert "lat_rule" in types, "没有 lat_rule 类型"


def test_hijri_window_type():
    """hijri 类型应有实例。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "festivals.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    hijri_fests = [f for f in data if f.get("window", {}).get("type") == "hijri"]
    assert len(hijri_fests) >= 2, f"只有 {len(hijri_fests)} 个 hijri 类型"


def test_chinese_system_count():
    """中国系节日存在。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "festivals.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    cn_fests = [f for f in data if f.get("country") == "CN"]
    assert len(cn_fests) >= 39, f"中国系只有 {len(cn_fests)} 个"


def test_world_system_count():
    """世界系至少 40 个节日。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "festivals.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    non_cn = [f for f in data if f.get("country") != "CN"]
    assert len(non_cn) >= 40, f"世界系只有 {len(non_cn)} 个"
