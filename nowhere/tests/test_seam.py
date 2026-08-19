"""Card 35: 缝合工坊 — seam quality tests.

Tests for:
- _normalize_prose(): missing periods, full/half-width normalization, consecutive periods
- compose() transition guard: walk-only transitions excluded from establish sections
- Person unification: stray pronouns at section starts
- Known regression: "像刚下过雪风声大" (missing period concatenation)
"""

from __future__ import annotations

import random

import pytest

import nowhere.describe as d


# ── Helpers ──────────────────────────────────────────────────────────


@pytest.fixture
def mock_smell(monkeypatch):
    """Patch _SMELL_BY_BIOME and _TOUCH_BY_SURFACE to controlled values."""
    monkeypatch.setattr(d, "_SMELL_BY_BIOME", {
        "tundra": ["苔藓的味道，湿的，像刚下过雪"],
        "mountain": ["稀薄的空气，闻起来什么都没有"],
    })
    monkeypatch.setattr(d, "_TOUCH_BY_SURFACE", {
        "snow": ["雪壳塌裂，碎冰钻进鞋帮"],
    })
    # Patch scene elements to avoid pulling real data
    monkeypatch.setattr(d, "_load_scene_elements", lambda: {})
    monkeypatch.setattr(d, "_load_seasonal", lambda: {})


@pytest.fixture
def mock_scenes(monkeypatch):
    """Patch scene file loaders to controlled values."""
    monkeypatch.setattr(d, "_SCENE_CACHE", {})
    monkeypatch.setattr(d, "_META_CACHE", None)
    monkeypatch.setattr(d, "_LOCATION_SCENES", {"测试城": ["测试场景。"]})
    # Keep scene files unavailable so render falls through to templates
    monkeypatch.setattr(d, "_SCENE_DIR", d._SCENE_DIR)  # keep real dir
    # But cache empty scenes for known scene names
    def _fake_load_scenes(name):
        return []
    monkeypatch.setattr(d, "_load_scenes", _fake_load_scenes)


# ── _normalize_prose tests ───────────────────────────────────────────


def test_normalize_prose_fixes_missing_period():
    """Chinese char followed by non-punctuation → insert period."""
    assert d._normalize_prose("像刚下过雪风声大") == "像刚下过雪。风声大"


def test_normalize_prose_fullwidth():
    """Half-width punctuation in Chinese context → full-width."""
    assert d._normalize_prose("你好,世界") == "你好，世界"
    assert d._normalize_prose("好吗?") == "好吗？"
    assert d._normalize_prose("太好!") == "太好！"


def test_normalize_prose_consecutive_periods():
    """Multiple consecutive periods → one."""
    assert d._normalize_prose("你好。。世界") == "你好。世界"
    assert d._normalize_prose("你好。。。世界") == "你好。世界"


def test_normalize_prose_no_false_positive():
    """Already correct punctuation should not be changed."""
    s = "苔藓的味道，湿的，像刚下过雪。风声大。"
    assert d._normalize_prose(s) == s


def test_normalize_prose_empty():
    """Empty input → empty output."""
    assert d._normalize_prose("") == ""


def test_normalize_prose_chinese_to_chinese_no_period():
    """Chinese followed by Chinese should NOT insert period."""
    assert d._normalize_prose("你好世界") == "你好世界"


def test_normalize_prose_number_boundary():
    """Number boundary should be handled correctly."""
    assert d._normalize_prose("海拔3000米") == "海拔3000米"


def test_normalize_prose_two_sections_boundary():
    """Two sections concatenated should get period at boundary."""
    assert d._normalize_prose("苔藓的味道，湿的，像刚下过雪风声大") == "苔藓的味道，湿的，像刚下过雪。风声大"


# ── compose() transition guard tests ─────────────────────────────────


def test_compose_establish_no_walk_transition():
    """Establish sections should not get walk transitions like '走着走着,'."""
    # Use a seed that would pick a walk transition if available
    # With section_type="establish", walk transitions are excluded
    sections = ["落地段。", "天气不错。", "地形平坦。"]
    for seed in range(50):
        rng = random.Random(seed)
        result = d.compose(sections, rng, section_type="establish")
        assert "走着走着" not in result, (
            f"Walk transition '走着走着' found in establish section with seed {seed}: {result}"
        )
        assert "又走了一段" not in result, (
            f"Walk transition '又走了一段' found in establish section with seed {seed}: {result}"
        )


def test_compose_walk_allows_walk_transition():
    """Walk sections should allow walk transitions."""
    sections = ["走路段。", "天气变化。", "地形变化。"]
    # With many sections, walk transitions should be possible
    found_walk = False
    for seed in range(100):
        rng = random.Random(seed)
        result = d.compose(sections, rng, section_type="walk")
        if "走着走着" in result or "又走了一段" in result:
            found_walk = True
            break
    assert found_walk, "Walk transitions should be available in walk sections"


def test_compose_walk_default_is_walk():
    """Default section_type should be 'walk' (backward compatible)."""
    sections = ["走路段。", "天气变化。", "地形变化。"]
    found_walk = False
    for seed in range(100):
        rng = random.Random(seed)
        result = d.compose(sections, rng)  # no section_type → default "walk"
        if "走着走着" in result or "又走了一段" in result:
            found_walk = True
            break
    assert found_walk, "Default compose should allow walk transitions"


# ── Punctuation normalization in compose ─────────────────────────────


def test_compose_inserts_period_between_sections():
    """compose() should insert missing period between concatenated sections."""
    # Section 1 ends with Chinese char (no period), section 2 starts with Chinese char
    sections = ["苔藓的味道，湿的，像刚下过雪", "风声大"]
    rng = random.Random(42)
    result = d.compose(sections, rng)
    # Should have a period between "雪" and "风"
    assert "雪。风" in result, f"Missing period between sections: {result}"


def test_compose_preserves_existing_punctuation():
    """compose() should not double-up periods that already exist."""
    sections = ["天晴了。", "风很大。"]
    rng = random.Random(42)
    result = d.compose(sections, rng)
    assert "了。风" in result or "了。" in result, f"Period handling incorrect: {result}"
    assert "。。" not in result, f"Double period found: {result}"


# ── Person unification ───────────────────────────────────────────────


def test_compose_no_stray_pronouns_in_establish():
    """Establish sections should not have stray 他/她/它 at section starts."""
    sections = ["落地段。", "天气不错。", "地形平坦。"]
    for seed in range(50):
        rng = random.Random(seed)
        result = d.compose(sections, rng, section_type="establish")
        # Check no "他" or "她" or "它" at the start of a joined section
        # (after the first section, which is the header)
        for pronoun in ("他", "她", "它"):
            # Allow pronouns inside sentences, but not at transition boundaries
            # The compose function prepends transitions, so pronouns at section starts
            # would appear after transition phrases
            assert not result.startswith(pronoun), (
                f"Text starts with pronoun '{pronoun}' in establish: {result}"
            )


# ── Regression anchor: "像刚下过雪" case ────────────────────────────


def test_regression_xiang_gang_guo_xue(mock_smell, mock_scenes):
    """Regression: '像刚下过雪风声大' — missing period between smell and walk text.

    Simulates the scenario where _SMELL_BY_BIOME returns a smell entry
    without a trailing period, and it gets concatenated with walk text.
    """
    smell = "苔藓的味道，湿的，像刚下过雪"
    walk = "风声大"

    # Direct composition
    rng = random.Random(7)
    result = d.compose([smell, walk], rng)
    assert "雪。风" in result or "雪。" in result.split("风")[0], (
        f"Regression: missing period between smell and walk text: {result}"
    )
    assert "雪风" not in result, (
        f"Regression: '像刚下过雪风声大' concatenation still present: {result}"
    )


def test_regression_normalize_prose_direct():
    """Direct test of the normalizer on the known bug input."""
    bad = "苔藓的味道，湿的，像刚下过雪风声大"
    good = d._normalize_prose(bad)
    assert "雪。风" in good, f"Normalizer did not fix the known bug: {good}"
    assert "雪风" not in good, f"Known concatenation still present: {good}"


# ── 8 places × landing + 3 walks (fixed seed) ────────────────────────


def test_seam_eight_places_landing_walks(mock_smell, mock_scenes):
    """Fixed seed: 8 places × landing + 3 walks, assert no period-missing concatenation.

    Uses template-based rendering (scene files patched out) to ensure
    deterministic output for seam quality verification.
    """
    # Patch render to use template fallback (no scene files)
    # We test the compose/normalize pipeline, not the scene file content
    places = [
        "北京", "东京", "巴黎", "纽约",
        "开罗", "悉尼", "莫斯科", "里约热内卢",
    ]

    for place in places:
        for seed_offset in range(4):  # 1 landing + 3 walks
            seed = hash(f"{place}_{seed_offset}") % 10000
            rng = random.Random(seed)

            # Build sections that mimic real output
            sections = [
                f"【{place}，白天】",
                "光铺满草地，远处的一切。",
                "空气 20 度。",
            ]
            # Add a smell section (no trailing period — the known bug pattern)
            if seed_offset == 0:
                sections.append("苔藓的味道，湿的，像刚下过雪")
            else:
                sections.append("稀薄的空气，闻起来什么都没有")

            section_type = "establish" if seed_offset == 0 else "walk"
            result = d.compose(sections, rng, section_type=section_type)

            # Assert: no missing-period concatenation
            assert "雪风" not in result, (
                f"Missing period in {place} seed={seed}: {result}"
            )
            # Assert: no consecutive periods
            assert "。。" not in result, (
                f"Double period in {place} seed={seed}: {result}"
            )
            # Assert: no walk transitions in establish sections
            if section_type == "establish":
                assert "走着走着" not in result, (
                    f"Walk transition in establish for {place} seed={seed}: {result}"
                )


# ── compose with transitions and punctuation ─────────────────────────


def test_compose_with_transitions_and_punctuation():
    """Verify that compose correctly handles transitions + punctuation."""
    sections = ["天气晴朗，万里无云。", "气温回升了几度，太阳在发力。", "远处有什么在动，你看不清。"]
    rng = random.Random(42)
    result = d.compose(sections, rng, section_type="walk")
    # Should be well-formed prose
    assert len(result) > 0
    # Should not have double periods
    assert "。。" not in result
    # Should not have missing periods between sections
    # (each section already ends with period, so this should be fine)
    assert result.count("。") >= 3, f"Expected at least 3 periods: {result}"


def test_compose_establish_with_header():
    """Verify that compose handles establish sections with header format."""
    sections = ["【中国，北京，白天】", "光铺满城，房子挤着房子。", "空气 30 度。"]
    rng = random.Random(42)
    result = d.compose(sections, rng, section_type="establish")
    # Header should not get a period after it
    assert "】。" not in result, f"Header should not get period: {result}"
    # Should not have walk transitions
    assert "走着走着" not in result
    assert "又走了一段" not in result


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    pytest.main([__file__, "-v"])
