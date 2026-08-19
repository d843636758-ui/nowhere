"""Tests for Card 10: 痕迹链 — 世界在你离开后继续过日子."""

from __future__ import annotations

import pytest

from nowhere import placememory


@pytest.fixture(autouse=True)
def _tmp_home(tmp_path, monkeypatch):
    """绝不碰生产 ~/.nowhere——重定向到 tmp。"""
    monkeypatch.setenv("NOWHERE_HOME", str(tmp_path))


def test_traces_json_has_10_places():
    """traces.json 应有 10 个地点。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "traces.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    assert len(data) == 10


def test_each_place_has_3_stages():
    """每个地点应有 3 个阶段。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "traces.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    for place, info in data.items():
        assert len(info["stages"]) == 3, f"{place} 应有 3 个阶段"


def test_has_trace_known_place():
    """已知地点应有痕迹链。"""
    assert placememory.has_trace("喀什") is True
    assert placememory.has_trace("威尼斯") is True


def test_has_trace_unknown_place():
    """未知地点应无痕迹链。"""
    assert placememory.has_trace("不存在的地方") is False


def test_three_visits_different_texts():
    """同地三次落地,三段文本按序出现且不同。"""
    t1 = placememory.get_trace_text("喀什")
    t2 = placememory.get_trace_text("喀什")
    t3 = placememory.get_trace_text("喀什")
    assert t1 != t2 != t3
    assert t1 is not None
    assert t2 is not None
    assert t3 is not None


def test_fourth_visit_capped():
    """第四次落地=第三段(封顶)。"""
    placememory.get_trace_text("喀什")
    placememory.get_trace_text("喀什")
    placememory.get_trace_text("喀什")
    t4 = placememory.get_trace_text("喀什")
    t3_again = placememory.get_trace_text("喀什")
    # After 3 advances, stage is capped at 2 (last stage)
    # t4 should be stage 2 text (same as t3)
    # t3_again should also be stage 2 text
    assert t4 == t3_again


def test_no_chain_place_returns_none():
    """无链地回退正常——返回 None。"""
    assert placememory.get_trace_text("火星") is None


def test_stage_persists(tmp_path, monkeypatch):
    """stage 持久化进 placememory。"""
    monkeypatch.setenv("NOWHERE_HOME", str(tmp_path))
    placememory.get_trace_text("京都")
    # Read the raw file to verify persistence
    import json
    stages_file = tmp_path / "trace_stages.json"
    assert stages_file.exists()
    data = json.loads(stages_file.read_text(encoding="utf-8"))
    assert data["京都"] == 1


def test_stage_advances_correctly():
    """stage 按正确顺序推进。"""
    assert placememory.get_trace_stage("敦煌") == 0
    placememory.get_trace_text("敦煌")
    assert placememory.get_trace_stage("敦煌") == 1
    placememory.get_trace_text("敦煌")
    assert placememory.get_trace_stage("敦煌") == 2
    placememory.get_trace_text("敦煌")
    # Capped at 2
    assert placememory.get_trace_stage("敦煌") == 2


def test_all_10_places_have_traces():
    """所有 10 个地点都有痕迹链。"""
    places = ["喀什", "威尼斯", "敦煌", "京都", "瓦尔帕莱索",
              "德纳利", "里斯本", "大城", "巴格达", "哈尔滨"]
    for p in places:
        assert placememory.has_trace(p) is True
        text = placememory.get_trace_text(p)
        assert text is not None
        assert len(text) > 10


def test_forbidden_words_in_traces():
    """痕迹链文案不含禁词。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "traces.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    forbidden = {"很", "非常", "十分"}
    for place, info in data.items():
        for i, text in enumerate(info["stages"]):
            for word in forbidden:
                assert word not in text, f"{place} 阶段{i} 含禁词'{word}': {text}"


def test_trace_texts_not_empty():
    """所有痕迹链文案非空且有实质内容。"""
    import json
    import pathlib
    fp = pathlib.Path(__file__).resolve().parent.parent / "data" / "traces.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    for place, info in data.items():
        for i, text in enumerate(info["stages"]):
            assert len(text) >= 10, f"{place} 阶段{i} 文案太短: {text}"
