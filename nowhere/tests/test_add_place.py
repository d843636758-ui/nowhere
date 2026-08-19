"""Tests for tools/add_place.py — 加城市流水线。

用 tmp 目录 mock 数据文件,不碰真实数据。
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

# 确保 tools 可导入
_REPO = pathlib.Path(__file__).resolve().parent.parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


@pytest.fixture()
def pipeline_env(tmp_path, monkeypatch):
    """搭建隔离环境: tmp 目录 + mock 数据文件。

    返回 {"repo": tmp_path, "data": data_dir, "drafts": drafts_dir,
           "lc_path": ..., "idx_path": ...}
    """
    data_dir = tmp_path / "nowhere" / "data"
    data_dir.mkdir(parents=True)
    drafts_dir = tmp_path / "drafts"
    drafts_dir.mkdir()

    lc_path = data_dir / "localcolor.json"
    idx_path = data_dir / "explorable_index.json"

    # 初始化空数据文件
    lc_path.write_text("{}", encoding="utf-8")
    idx_path.write_text('{"places": {}}', encoding="utf-8")

    # Patch 模块级路径
    import tools.add_place as ap
    monkeypatch.setattr(ap, "_REPO", tmp_path)
    monkeypatch.setattr(ap, "_DATA_DIR", data_dir)
    monkeypatch.setattr(ap, "_DRAFTS_DIR", drafts_dir)
    monkeypatch.setattr(ap, "_LC_PATH", lc_path)
    monkeypatch.setattr(ap, "_IDX_PATH", idx_path)

    return {
        "repo": tmp_path,
        "data": data_dir,
        "drafts": drafts_dir,
        "lc_path": lc_path,
        "idx_path": idx_path,
        "ap": ap,
    }


# ── Mock 函数 ────────────────────────────────────────────────────────

def _mock_geocode_ok(place: str):
    """模拟成功查到坐标。"""
    return (32.06, 118.79)  # 南京附近


def _mock_geocode_fail(place: str):
    """模拟查不到坐标。"""
    return None


def _mock_country_ok(lat: float, lon: float) -> str:
    """模拟国家码查询成功。"""
    return "CN"


def _mock_is_water_false(lat: float, lon: float) -> bool:
    return False


def _mock_is_water_true(lat: float, lon: float) -> bool:
    return True


# ── Gate 1: 坐标关 ──────────────────────────────────────────────────

def test_coordinate_gate_ok(pipeline_env):
    """正常坐标 → 通过。"""
    ap = pipeline_env["ap"]
    result = ap.gate_coordinate(
        "南京",
        _geocode_lookup=_mock_geocode_ok,
        _country_code_of=_mock_country_ok,
        _is_water=_mock_is_water_false,
    )
    assert result["ok"] is True
    assert result["lat"] == 32.06
    assert result["lon"] == 118.79
    assert result["country"] == "CN"
    assert result["is_water"] is False


def test_coordinate_gate_fail_no_geocode(pipeline_env):
    """查不到坐标 → 拦截。"""
    ap = pipeline_env["ap"]
    result = ap.gate_coordinate(
        "不存在的地方",
        _geocode_lookup=_mock_geocode_fail,
        _country_code_of=_mock_country_ok,
        _is_water=_mock_is_water_false,
    )
    assert result["ok"] is False
    assert "查不到坐标" in result["error"]


def test_coordinate_gate_fail_water(pipeline_env):
    """落在水面上 → 拦截。"""
    ap = pipeline_env["ap"]
    result = ap.gate_coordinate(
        "马里亚纳海沟",
        _geocode_lookup=_mock_geocode_ok,
        _country_code_of=_mock_country_ok,
        _is_water=_mock_is_water_true,
    )
    assert result["ok"] is False
    assert result["is_water"] is True
    assert "水面上" in result["error"]


# ── Gate 2: 实据关 ──────────────────────────────────────────────────

def test_facts_gate_creates_file(pipeline_env):
    """有 ZIM 结果 → 生成 facts 文件。"""
    ap = pipeline_env["ap"]
    path = ap.gate_facts("南京", _zim_lookup=lambda p: "南京,简称宁,是江苏省省会。")
    assert path is not None
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "南京" in content
    assert "江苏省省会" in content


def test_facts_gate_no_zim(pipeline_env):
    """ZIM 查不到 → 跳过(不报错)。"""
    ap = pipeline_env["ap"]
    path = ap.gate_facts("不存在的地方", _zim_lookup=lambda p: None)
    assert path is None


def test_facts_gate_idempotent(pipeline_env):
    """已有草稿 → 不覆盖。"""
    ap = pipeline_env["ap"]
    drafts = pipeline_env["drafts"]
    facts_path = drafts / "南京_facts.md"
    facts_path.write_text("人工编辑的内容", encoding="utf-8")

    path = ap.gate_facts("南京", _zim_lookup=lambda p: "新内容")
    assert path == facts_path
    assert facts_path.read_text(encoding="utf-8") == "人工编辑的内容"


# ── Gate 3: 模板关 ──────────────────────────────────────────────────

def test_template_gate_creates_skeleton(pipeline_env):
    """生成骨架 JSON,含五类 + 节律。"""
    ap = pipeline_env["ap"]
    path = ap.gate_template("南京")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "物产" in data
    assert "声音" in data
    assert "痕迹" in data
    assert "植被" in data
    assert "美食" in data
    assert "节律" in data
    assert "_说明" in data


def test_template_gate_idempotent(pipeline_env):
    """已有模板 → 不覆盖。"""
    ap = pipeline_env["ap"]
    drafts = pipeline_env["drafts"]
    tpl_path = drafts / "南京_cards.json"
    tpl_path.write_text('{"人工编辑": true}', encoding="utf-8")

    path = ap.gate_template("南京")
    assert path == tpl_path
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("人工编辑") is True


# ── Gate 4: 质检关 ──────────────────────────────────────────────────

def _write_valid_cards(drafts: pathlib.Path, place: str):
    """写一份合法的卡片草稿。"""
    cards = {
        "物产": ["盐水鸭的皮紧实,筷子一戳有汁水冒出来。"],
        "声音": ["秦淮河上游船的桨声,木头碰木头。"],
        "痕迹": ["明城墙的砖上刻着工匠的名字,六百年没磨掉。"],
        "植被": ["梧桐树的果子挂在枝头,风一吹掉一地。"],
        "美食": ["鸭血粉丝汤端上来,粉丝滑,鸭血嫩,汤头清。"],
        "节律": [
            {"hours": [6, 8], "text": "早市的菜贩子把青菜码成一排,水珠还在叶子上。"}
        ],
    }
    path = drafts / f"{place}_cards.json"
    path.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_check_gate_pass(pipeline_env):
    """合法卡片 → 质检通过。"""
    ap = pipeline_env["ap"]
    _write_valid_cards(pipeline_env["drafts"], "南京")
    errors = ap.gate_check(
        "南京",
        _geocode_lookup=_mock_geocode_ok,
        _country_code_of=_mock_country_ok,
        _is_water=_mock_is_water_false,
    )
    assert errors == []


def test_check_gate_forbidden_word(pipeline_env):
    """含禁词 → 质检拦截。"""
    ap = pipeline_env["ap"]
    cards = {
        "物产": ["盐水鸭非常好吃。"],  # 禁词 "非常"
        "声音": ["秦淮河上游船的桨声。"],
        "痕迹": ["明城墙的砖上刻着工匠的名字。"],
        "植被": ["梧桐树的果子挂在枝头。"],
        "美食": ["鸭血粉丝汤端上来。"],
        "节律": [],
    }
    path = pipeline_env["drafts"] / "南京_cards.json"
    path.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

    errors = ap.gate_check(
        "南京",
        _geocode_lookup=_mock_geocode_ok,
        _country_code_of=_mock_country_ok,
        _is_water=_mock_is_water_false,
    )
    assert len(errors) > 0
    assert any("非常" in e for e in errors)


def test_check_gate_forbidden_word_time_context_ok(pipeline_env):
    """时间语境里的 '十分' 不算违规。"""
    ap = pipeline_env["ap"]
    cards = {
        "物产": ["盐水鸭的皮紧实。"],
        "声音": ["秦淮河上游船的桨声。"],
        "痕迹": ["明城墙的砖上刻着工匠的名字。"],
        "植被": ["梧桐树的果子挂在枝头。"],
        "美食": ["鸭血粉丝汤端上来。"],
        "节律": [
            {"hours": [14, 16], "text": "下午两点十分,阳光照在城墙上。"}  # "十分"在时间里
        ],
    }
    path = pipeline_env["drafts"] / "南京_cards.json"
    path.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

    errors = ap.gate_check(
        "南京",
        _geocode_lookup=_mock_geocode_ok,
        _country_code_of=_mock_country_ok,
        _is_water=_mock_is_water_false,
    )
    # "十分"在时间语境中,不应被标记
    forbidden_errors = [e for e in errors if "十分" in e]
    assert len(forbidden_errors) == 0


def test_check_gate_rhythm_hours_invalid(pipeline_env):
    """hours 起>=止 → 质检拦截。"""
    ap = pipeline_env["ap"]
    cards = {
        "物产": ["盐水鸭的皮紧实。"],
        "声音": ["秦淮河上游船的桨声。"],
        "痕迹": ["明城墙的砖上刻着工匠的名字。"],
        "植被": ["梧桐树的果子挂在枝头。"],
        "美食": ["鸭血粉丝汤端上来。"],
        "节律": [
            {"hours": [22, 1], "text": "深夜的秦淮河。"}  # 跨午夜应用[22,24]
        ],
    }
    path = pipeline_env["drafts"] / "南京_cards.json"
    path.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

    errors = ap.gate_check(
        "南京",
        _geocode_lookup=_mock_geocode_ok,
        _country_code_of=_mock_country_ok,
        _is_water=_mock_is_water_false,
    )
    assert any("hours" in e and "起>=止" in e for e in errors)


def test_check_gate_no_cards_file(pipeline_env):
    """模板不存在 → 质检拦截。"""
    ap = pipeline_env["ap"]
    errors = ap.gate_check(
        "南京",
        _geocode_lookup=_mock_geocode_ok,
        _country_code_of=_mock_country_ok,
        _is_water=_mock_is_water_false,
    )
    assert any("不存在" in e for e in errors)


# ── Gate 5: 合并关 ──────────────────────────────────────────────────

def test_merge_gate_full_flow(pipeline_env):
    """完整合并流程: 写入 localcolor + explorable_index。"""
    ap = pipeline_env["ap"]
    _write_valid_cards(pipeline_env["drafts"], "南京")

    errors = ap.gate_merge(
        "南京",
        _geocode_lookup=_mock_geocode_ok,
        _country_code_of=_mock_country_ok,
        _is_water=_mock_is_water_false,
        _skip_tests=True,
    )
    assert errors == []

    # 验证 localcolor.json
    lc = json.loads(pipeline_env["lc_path"].read_text(encoding="utf-8"))
    assert "南京" in lc
    assert "物产" in lc["南京"]
    assert len(lc["南京"]["物产"]) == 1

    # 验证 explorable_index.json
    idx = json.loads(pipeline_env["idx_path"].read_text(encoding="utf-8"))
    assert "南京" in idx["places"]
    assert idx["places"]["南京"]["lat"] == 32.06
    assert idx["places"]["南京"]["layers"]["localcolor"] is True


def test_merge_gate_key_conflict(pipeline_env):
    """键冲突 → 红字停。"""
    ap = pipeline_env["ap"]
    # 先往 localcolor 写入一个已有地名
    lc = {"南京": {"物产": ["已有数据"]}}
    pipeline_env["lc_path"].write_text(
        json.dumps(lc, ensure_ascii=False), encoding="utf-8"
    )

    _write_valid_cards(pipeline_env["drafts"], "南京")
    errors = ap.gate_merge(
        "南京",
        _geocode_lookup=_mock_geocode_ok,
        _country_code_of=_mock_country_ok,
        _is_water=_mock_is_water_false,
        _skip_tests=True,
    )
    assert any("键冲突" in e for e in errors)

    # 验证原数据未被覆盖
    lc_after = json.loads(pipeline_env["lc_path"].read_text(encoding="utf-8"))
    assert lc_after["南京"]["物产"] == ["已有数据"]


def test_merge_gate_empty_cards_blocked(pipeline_env):
    """全是占位符 → 拒绝合并。"""
    ap = pipeline_env["ap"]
    cards = {
        "物产": ["【请填写】当地能摸到、看到、吃到的实物。1-3句散文。"],
        "声音": ["【请填写】当地特有的声音。1-3句散文。"],
        "痕迹": ["【请填写】时间留下的印记。1-3句散文。"],
        "植被": ["【请填写】当地植物。1-3句散文。"],
        "美食": ["【请填写】当地食物。1-3句散文。"],
        "节律": [],
    }
    path = pipeline_env["drafts"] / "南京_cards.json"
    path.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

    errors = ap.gate_merge(
        "南京",
        _geocode_lookup=_mock_geocode_ok,
        _country_code_of=_mock_country_ok,
        _is_water=_mock_is_water_false,
        _skip_tests=True,
    )
    assert any("占位符" in e for e in errors)


# ── 幂等 ────────────────────────────────────────────────────────────

def test_already_exists(pipeline_env):
    """已有地名 → check_already_exists 返回 True。"""
    ap = pipeline_env["ap"]
    assert ap.check_already_exists("南京") is False

    lc = {"南京": {"物产": ["test"]}}
    pipeline_env["lc_path"].write_text(
        json.dumps(lc, ensure_ascii=False), encoding="utf-8"
    )
    assert ap.check_already_exists("南京") is True


# ── 禁词假阳性过滤 ──────────────────────────────────────────────────

def test_is_time_context():
    """时间语境检测。"""
    import tools.add_place as ap

    # "下午两点十分" 里的 "十分" 应被识别为时间语境
    # 下=0 午=1 两=2 点=3 十=4 分=5  → pos=4
    text1 = "下午两点十分,阳光照在城墙上"
    pos1 = text1.index("十分")
    assert ap._is_time_context(text1, "十分", pos1) is True
    # "十分壮观" 里的 "十分" 不是时间语境
    text2 = "城墙十分壮观"
    pos2 = text2.index("十分")
    assert ap._is_time_context(text2, "十分", pos2) is False
    # "凌晨三点" 里的 "三" 是时间语境
    text3 = "凌晨三点,街上没人"
    pos3 = text3.index("三")
    assert ap._is_time_context(text3, "三", pos3) is True


# ── 禁词质检完整测试 ────────────────────────────────────────────────

def test_check_catches_all_forbidden_words(pipeline_env):
    """质检能抓出所有禁词。"""
    ap = pipeline_env["ap"]
    for word in ap._FORBIDDEN_WORDS:
        cards = {
            "物产": [f"这里{word}特别。"],
            "声音": ["安静。"],
            "痕迹": ["旧的。"],
            "植被": ["绿色的。"],
            "美食": ["好吃的。"],
            "节律": [],
        }
        path = pipeline_env["drafts"] / "南京_cards.json"
        path.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

        errors = ap.gate_check(
            "南京",
            _geocode_lookup=_mock_geocode_ok,
            _country_code_of=_mock_country_ok,
            _is_water=_mock_is_water_false,
        )
        forbidden_errors = [e for e in errors if word in e and "禁词" in e]
        assert len(forbidden_errors) > 0, f"禁词「{word}」未被抓出"
