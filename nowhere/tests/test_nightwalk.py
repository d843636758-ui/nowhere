"""Tests for night navigation (Card 14)."""
from __future__ import annotations

import random
import pytest

from nowhere import describe


def test_north_mid_lat_polar_star():
    """Mid-latitude north: polar star variants appear."""
    rng = random.Random(42)
    results = set()
    for _ in range(100):
        text = describe.render_night_nav(40.0, 0.5, "night", 7, rng)
        if text:
            results.add(text)
    assert any("北" in r or "星" in r or "银河" in r for r in results)


def test_southern_cross():
    """South lat < -10: Southern Cross, no polar star."""
    rng = random.Random(42)
    results = set()
    for _ in range(100):
        text = describe.render_night_nav(-30.0, 0.5, "night", 7, rng)
        if text:
            results.add(text)
    assert any("南十字" in r for r in results)
    assert not any("北极星" in r for r in results)


def test_full_moon_variant():
    """moon_phase > 0.8: full moon pool."""
    rng = random.Random(42)
    results = set()
    for _ in range(100):
        text = describe.render_night_nav(40.0, 0.9, "night", 7, rng)
        if text:
            results.add(text)
    assert any("满月" in r or "月光" in r or "月亮" in r for r in results)


def test_no_moon_variant():
    """moon_phase < 0.2: no moon pool."""
    rng = random.Random(42)
    results = set()
    for _ in range(100):
        text = describe.render_night_nav(40.0, 0.1, "night", 7, rng)
        if text:
            results.add(text)
    assert any("没月亮" in r or "黑" in r or "星" in r for r in results)


def test_polar_night():
    """|lat|>66 in winter months: polar night pool."""
    rng = random.Random(42)
    results = set()
    for _ in range(100):
        text = describe.render_night_nav(70.0, 0.5, "night", 12, rng)
        if text:
            results.add(text)
    assert any("极夜" in r or "太阳不上来" in r for r in results)


def test_low_lat_no_head():
    """Low latitude (10-30) should not say '头顶'."""
    rng = random.Random(42)
    for _ in range(100):
        text = describe.render_night_nav(15.0, 0.5, "night", 7, rng)
        if text:
            assert "头顶" not in text, f"Low lat should not say '头顶': {text}"


def test_day_returns_none():
    """Day phase returns None."""
    rng = random.Random(42)
    assert describe.render_night_nav(40.0, 0.5, "day", 7, rng) is None


def test_equator_returns_none():
    """Near equator (-10 to 10) returns None."""
    rng = random.Random(42)
    assert describe.render_night_nav(5.0, 0.5, "night", 7, rng) is None


def test_variant_total_count():
    """Total variant count is 21."""
    pools = [
        describe._NIGHT_NAV_POLAR_LOW,
        describe._NIGHT_NAV_POLAR_MID,
        describe._NIGHT_NAV_POLAR_HIGH,
        describe._NIGHT_NAV_POLAR_UNIVERSAL,
        describe._NIGHT_NAV_SOUTHERN,
        describe._NIGHT_NAV_FULL_MOON,
        describe._NIGHT_NAV_NO_MOON,
        describe._NIGHT_NAV_POLAR_NIGHT,
    ]
    total = sum(len(p) for p in pools)
    assert total == 21


def test_no_forbidden_words():
    """No forbidden words in any variant."""
    pools = [
        describe._NIGHT_NAV_POLAR_LOW,
        describe._NIGHT_NAV_POLAR_MID,
        describe._NIGHT_NAV_POLAR_HIGH,
        describe._NIGHT_NAV_POLAR_UNIVERSAL,
        describe._NIGHT_NAV_SOUTHERN,
        describe._NIGHT_NAV_FULL_MOON,
        describe._NIGHT_NAV_NO_MOON,
        describe._NIGHT_NAV_POLAR_NIGHT,
    ]
    for pool in pools:
        for text in pool:
            for word in ("很", "非常", "十分"):
                assert word not in text, f"Forbidden word '{word}' in: {text}"


def test_high_lat_polar_night_southern():
    """Southern hemisphere polar night (lat < -66, winter months)."""
    rng = random.Random(42)
    results = set()
    for _ in range(100):
        text = describe.render_night_nav(-70.0, 0.5, "night", 6, rng)
        if text:
            results.add(text)
    assert any("极夜" in r or "太阳不上来" in r for r in results)


def test_north_low_lat():
    """Low latitude (10-30) gets low-lat specific variant."""
    rng = random.Random(42)
    results = set()
    for _ in range(200):
        text = describe.render_night_nav(20.0, 0.5, "night", 7, rng)
        if text:
            results.add(text)
    # Should contain at least one low-lat specific text
    assert any("地平线" in r for r in results)
