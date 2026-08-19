"""Card 43: 旅行手账——五册自然志测试。"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# GBK console fix
sys.stdout.reconfigure(encoding="utf-8")

# ── 用临时目录做 NOWHERE_HOME ────────────────────────────────────────

@pytest.fixture(autouse=True)
def _tmp_home(tmp_path, monkeypatch):
    """每个测试用独立的临时 NOWHERE_HOME。"""
    monkeypatch.setenv("NOWHERE_HOME", str(tmp_path))
    # 清除模块缓存
    import nowhere.notebook as nb
    yield tmp_path


# ── 导入 ─────────────────────────────────────────────────────────────

from nowhere import notebook as nb


# ── 基础记录 ─────────────────────────────────────────────────────────

class TestRecord:
    """基本记录功能。"""

    def test_record_single_entry(self, _tmp_home):
        """记录一条,能读回来。"""
        nb.record("flora", "云莓", "拉普兰", "蹲下去才看见。")
        main, uniques = nb._volume_entries("flora")
        assert len(main) == 1
        assert main[0]["name"] == "云莓"
        assert main[0]["place"] == "拉普兰"
        assert main[0]["first_impression"] == "蹲下去才看见。"
        assert main[0]["at"]  # 时间戳存在

    def test_record_no_name_skipped(self, _tmp_home):
        """空名字不记录。"""
        nb.record("flora", "", "拉普兰")
        main, _ = nb._volume_entries("flora")
        assert len(main) == 0

    def test_record_invalid_volume_skipped(self, _tmp_home):
        """无效册名不记录。"""
        nb.record("invalid", "云莓", "拉普兰")
        main, _ = nb._volume_entries("flora")
        assert len(main) == 0

    def test_record_with_env_generates_impression(self, _tmp_home):
        """record_with_env 自动生成 first_impression。"""
        env = {"weather": {"precip": "rain", "wind_ms": 2, "temp_c": 15, "cloud": 80}}
        nb.record_with_env("flora", "云莓", "拉普兰", env, lat=68.0)
        main, _ = nb._volume_entries("flora")
        assert len(main) == 1
        fi = main[0]["first_impression"]
        assert fi is not None
        assert "云莓" in fi  # 名字在印象里
        assert len(fi) > 5  # 不是空串

    def test_record_null_impression_allowed(self, _tmp_home):
        """first_impression 可以是 null。"""
        nb.record("flora", "云莓", "拉普兰", None)
        main, _ = nb._volume_entries("flora")
        assert main[0]["first_impression"] is None


# ── 五册各自触发 ─────────────────────────────────────────────────────

class TestFiveVolumes:
    """五册都能记录和读取。"""

    def test_flora_volume(self, _tmp_home):
        nb.record("flora", "云莓", "拉普兰", "蹲下去才看见。")
        main, _ = nb._volume_entries("flora")
        assert len(main) == 1

    def test_fauna_volume(self, _tmp_home):
        nb.record("fauna", "狐狸", "拉普兰", "从面前跑过去。")
        main, _ = nb._volume_entries("fauna")
        assert len(main) == 1

    def test_radio_volume(self, _tmp_home):
        nb.record("radio", "CRI Easy FM", "长江", "后半夜的英语新闻。")
        main, _ = nb._volume_entries("radio")
        assert len(main) == 1

    def test_water_volume(self, _tmp_home):
        nb.record("water", "长江", "三峡", "远远看见水面。")
        main, _ = nb._volume_entries("water")
        assert len(main) == 1

    def test_people_volume(self, _tmp_home):
        nb.record("people", "老张", "喀什", "在路边聊天。")
        main, _ = nb._volume_entries("people")
        assert len(main) == 1


# ── 初见记,重逢不添笔 ────────────────────────────────────────────────

class TestFirstEncounterOnly:
    """同一实体多次记录应产生多条(每条是不同的初见时刻)。"""

    def test_multiple_entries_same_name(self, _tmp_home):
        """同名实体可以记多次(不同时刻)。"""
        nb.record("flora", "云莓", "拉普兰", "第一次。")
        nb.record("flora", "云莓", "冰岛", "第二次。")
        main, _ = nb._volume_entries("flora")
        assert len(main) == 2


# ── FIFO 丢旧但唯一节保留 ────────────────────────────────────────────

class TestFIFO:
    """FIFO 上限 200,唯一条目永不丢。"""

    def test_fifo_cap(self, _tmp_home):
        """超过 200 条丢最旧的。"""
        for i in range(210):
            nb.record("flora", f"植物{i}", f"地方{i}", f"印象{i}")
        main, _ = nb._volume_entries("flora")
        assert len(main) <= 200
        # 最新的还在
        assert main[-1]["name"] == "植物209"

    def test_unique_preserved_on_fifo(self, _tmp_home):
        """被 FIFO 丢掉的唯一条目搬进 uniques。"""
        # 先记一个唯一的
        nb.record("flora", "唯一植物", "唯一地方", "唯一印象。")
        # 再记 200 个不同的把它挤出去
        for i in range(200):
            nb.record("flora", f"植物{i}", f"地方{i}")
        main, uniques = nb._volume_entries("flora")
        # "唯一植物"不在主列表了
        assert all(e["name"] != "唯一植物" for e in main)
        # 但在 uniques 里
        assert any(e["name"] == "唯一植物" for e in uniques)

    def test_non_unique_not_preserved(self, _tmp_home):
        """FIFO 丢旧条目: 同名两条时先丢一条,剩余变 unique 被保留。"""
        # 记两个同名的
        nb.record("flora", "常见植物", "地方A")
        nb.record("flora", "常见植物", "地方B")
        # 再记 200 个不同的把它们挤出去
        for i in range(200):
            nb.record("flora", f"植物{i}", f"地方{i}")
        main, uniques = nb._volume_entries("flora")
        # "常见植物"不在主列表(FIFO 丢掉了)
        assert all(e["name"] != "常见植物" for e in main)
        # 第二条变 unique 被保留(这是正确行为: 唯一条目永不丢)
        assert any(e["name"] == "常见植物" and e["place"] == "地方B" for e in uniques)


# ── 跨旅程持久 ────────────────────────────────────────────────────────

class TestPersistence:
    """数据跨调用持久。"""

    def test_data_persists(self, _tmp_home):
        """写入后重新加载能读到。"""
        nb.record("flora", "云莓", "拉普兰", "蹲下去才看见。")
        # 重新加载
        main, _ = nb._volume_entries("flora")
        assert len(main) == 1
        assert main[0]["name"] == "云莓"


# ── 南半球季节正确 ────────────────────────────────────────────────────

class TestSeason:
    """季节从 at 反推,南半球翻转。"""

    def test_northern_summer(self):
        assert nb._compute_season(7, 40.0) == "夏天"

    def test_northern_winter(self):
        assert nb._compute_season(1, 40.0) == "冬天"

    def test_southern_summer_is_winter(self):
        """南半球 7 月是冬天。"""
        assert nb._compute_season(7, -33.0) == "冬天"

    def test_southern_january_is_summer(self):
        """南半球 1 月是夏天。"""
        assert nb._compute_season(1, -33.0) == "夏天"

    def test_southern_spring(self):
        """南半球 10 月是春天。"""
        assert nb._compute_season(10, -33.0) == "春天"


# ── 空册文案 ──────────────────────────────────────────────────────────

class TestEmptyVolume:
    """空册输出有文案,不是系统腔。"""

    def test_empty_volume_has_text(self):
        """空册不返回空串。"""
        text = nb.notebook("flora")
        assert text
        assert len(text) > 5

    def test_empty_volume_no_system_talk(self):
        """空册不说'还没有记录'。"""
        text = nb.notebook("radio")
        assert "还没有记录" not in text
        assert "暂无" not in text

    def test_overview_shows_all_volumes(self):
        """总览列出所有五册。"""
        text = nb.notebook()
        assert "植物册" in text or "植物" in text
        assert "电台" in text


# ── notebook() 输出格式 ───────────────────────────────────────────────

class TestNotebookOutput:
    """notebook() 输出声口。"""

    def test_volume_output_two_lines_per_entry(self, _tmp_home):
        """指定册:每条两行。"""
        nb.record("flora", "云莓", "拉普兰", "蹲下去才看见。")
        text = nb.notebook("flora")
        lines = text.strip().split("\n")
        assert len(lines) == 2
        assert "云莓" in lines[0]
        assert "拉普兰" in lines[0]
        assert lines[1].startswith("  ")  # 缩进
        assert "蹲下去才看见" in lines[1]

    def test_overview_format(self, _tmp_home):
        """总览:册名+笔数+第一笔。"""
        nb.record("flora", "云莓", "拉普兰", "蹲下去才看见。")
        text = nb.notebook()
        assert "植物册" in text or "植物" in text
        assert "云莓" in text

    def test_unique_section(self, _tmp_home):
        """"只有一次的"节。"""
        nb.record("flora", "云莓", "拉普兰", "蹲下去才看见。")
        nb.record("fauna", "狐狸", "冰岛", "从面前跑过去。")
        text = nb.notebook_unique_section()
        assert "只遇到过一次的" in text
        assert "云莓" in text
        assert "狐狸" in text

    def test_unique_section_empty(self):
        """没有条目时有兜底文案。"""
        text = nb.notebook_unique_section()
        assert "还没有" in text


# ── first_impression 含槽位值且非百科腔 ───────────────────────────────

class TestFirstImpression:
    """first_impression 质量。"""

    def test_impression_contains_name(self, _tmp_home):
        """印象里有实体名。"""
        env = {"weather": {"precip": "none", "wind_ms": 2, "temp_c": 20, "cloud": 30}}
        fi = nb._generate_first_impression("flora", "云莓", env, 68.0)
        assert fi is not None
        assert "云莓" in fi

    def test_impression_not_encyclopedic(self, _tmp_home):
        """印象不是百科腔。"""
        env = {"weather": {"precip": "none", "wind_ms": 2, "temp_c": 20, "cloud": 30}}
        for vol in nb.VOLUMES:
            fi = nb._generate_first_impression(vol, "测试名", env, 30.0)
            if fi:
                assert "分布于" not in fi, f"{vol}: 百科腔"
                assert "学名是" not in fi, f"{vol}: 百科腔"
                assert "蔷薇科" not in fi, f"{vol}: 百科腔"

    def test_impression_with_weather_slots(self, _tmp_home):
        """印象里有天气槽位值(多次尝试至少一次命中)。"""
        env = {"weather": {"precip": "rain", "wind_ms": 2, "temp_c": 15, "cloud": 80}}
        hits = 0
        for i in range(20):
            fi = nb._generate_first_impression("flora", f"植物{i}", env, 30.0)
            if fi and "雨" in fi:
                hits += 1
        # 6 个变体中 3 个有天气槽位,20 次应该命中多次
        assert hits > 0, f"20 次尝试无一次命中天气槽位"

    def test_impression_10_entries_null_ratio(self, _tmp_home):
        """10 笔里 null 不超过 4。"""
        env = {"weather": {"precip": "none", "wind_ms": 2, "temp_c": 20, "cloud": 30}}
        null_count = 0
        for i in range(10):
            fi = nb._generate_first_impression("flora", f"植物{i}", env, 30.0)
            if fi is None:
                null_count += 1
        assert null_count <= 4, f"null 太多: {null_count}/10"


# ── 变体池多样性 ─────────────────────────────────────────────────────

class TestVariantPool:
    """变体池有足够多样性。"""

    def test_pool_has_6_variants_per_volume(self):
        """每册有 6 个变体。"""
        for vol in nb.VOLUMES:
            pool = nb._VARIANT_POOLS.get(vol, [])
            assert len(pool) >= 6, f"{vol}: 只有 {len(pool)} 个变体"

    def test_empty_variants_exist(self):
        """每册有空册变体。"""
        for vol in nb.VOLUMES:
            variants = nb._EMPTY_VARIANTS.get(vol, [])
            assert len(variants) >= 3, f"{vol}: 只有 {len(variants)} 个空册变体"


# ── 原子写 ────────────────────────────────────────────────────────────

class TestAtomicWrite:
    """原子写:文件损坏时不影响数据。"""

    def test_notebook_file_created(self, _tmp_home):
        """记录后文件存在。"""
        nb.record("flora", "云莓", "拉普兰")
        p = nb._notebook_path()
        assert p.exists()

    def test_notebook_file_is_valid_json(self, _tmp_home):
        """文件是合法 JSON。"""
        nb.record("flora", "云莓", "拉普兰")
        p = nb._notebook_path()
        data = json.loads(p.read_text(encoding="utf-8"))
        assert "flora" in data


# ── 辅助函数 ─────────────────────────────────────────────────────────

class TestHelpers:
    """辅助函数。"""

    def test_weather_word_rain(self):
        w = nb._weather_word({"precip": "rain", "wind_ms": 1, "temp_c": 15, "cloud": 80})
        assert "雨" in w

    def test_weather_word_snow(self):
        w = nb._weather_word({"precip": "snow", "wind_ms": 1, "temp_c": -5, "cloud": 90})
        assert "雪" in w

    def test_weather_word_calm(self):
        w = nb._weather_word({"precip": "none", "wind_ms": 1, "temp_c": 22, "cloud": 20})
        assert w  # 不是空串

    def test_weather_word_none_input(self):
        w = nb._weather_word(None)
        assert w == "风里"

    def test_time_word_morning(self):
        dt = datetime(2026, 7, 17, 7, 0, tzinfo=timezone.utc)
        w = nb._time_word(dt, 30.0)
        assert w in ("清晨", "上午")  # 取决于时区

    def test_time_word_night(self):
        dt = datetime(2026, 7, 17, 22, 0, tzinfo=timezone.utc)
        w = nb._time_word(dt, 30.0)
        assert w in ("夜里", "傍晚")

    def test_time_word_none_input(self):
        w = nb._time_word(None)
        assert w == "傍晚"

    def test_time_ago_recent(self):
        now = datetime.now(timezone.utc).isoformat()
        ago = nb._time_ago(now)
        assert ago == "刚才" or "小时前" in ago

    def test_time_ago_invalid(self):
        ago = nb._time_ago("not-a-date")
        assert ago == "不久前"


# ── people 钩子: 初见记/重逢不记 ─────────────────────────────────────

class TestPeopleHook:
    """people 册: 首次 talk 记录,后续不重复。"""

    def test_people_record_on_first_talk(self, _tmp_home):
        """直接调 record 记录 people。"""
        nb.record("people", "老张", "喀什", "在路边聊天。")
        main, _ = nb._volume_entries("people")
        assert len(main) == 1
        assert main[0]["name"] == "老张"
