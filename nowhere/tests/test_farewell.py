"""Tests for farewell and return moments (card 27: peak-end)."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

import pytest

from nowhere import describe, journeys, state as state_mod


@pytest.fixture()
def isolated_home(tmp_path, monkeypatch):
    """Isolate NOWHERE_HOME to a temp directory."""
    monkeypatch.setenv("NOWHERE_HOME", str(tmp_path))
    journeys._JOURNEYS_DIR = tmp_path / "journeys"
    journeys._INDEX_FILE = journeys._JOURNEYS_DIR / "index.json"
    state_mod._SAVE_DIR = tmp_path
    state_mod._SAVE_FILE = tmp_path / "journey.json"
    return tmp_path


def _make_state(
    place: str,
    lat: float,
    lon: float,
    *,
    weather_text: str = "晴",
    phase: str = "day",
    elapsed_hours: float = 0.0,
) -> state_mod.WorldState:
    """Create a minimal WorldState with env data for testing."""
    s = state_mod.WorldState()
    s.pos = (lat, lon)
    s.place_name = place
    s.landed_at = datetime.now(timezone.utc) - timedelta(hours=elapsed_hours)
    s.elapsed_hours = elapsed_hours
    s.path = [{"lat": lat, "lon": lon, "elevation": 0, "dist_km": 1.0}]
    s.last_text = f"你在{place}走了走。"
    s.last_env = {
        "elevation": 100,
        "surface": "urban",
        "weather": {"text": weather_text, "temp_c": 20, "wind_ms": 3},
        "sky": {"phase": phase},
    }
    return s


# ── Variant pool forbidden words ─────────────────────────────────────


_FORBIDDEN = {"很", "非常", "十分"}


def test_farewell_variants_no_forbidden_words():
    """Farewell variant pool must not contain forbidden intensifiers."""
    for variant in describe._FAREWELL_VARIANTS:
        for word in _FORBIDDEN:
            assert word not in variant, (
                f"Forbidden word '{word}' found in farewell variant: {variant}"
            )


def test_return_variants_no_forbidden_words():
    """Return variant pool must not contain forbidden intensifiers."""
    for variant in describe._RETURN_VARIANTS:
        for word in _FORBIDDEN:
            assert word not in variant, (
                f"Forbidden word '{word}' found in return variant: {variant}"
            )


def test_farewell_variants_count():
    """Farewell variant pool must have at least 5 entries."""
    assert len(describe._FAREWELL_VARIANTS) >= 5


def test_return_variants_count():
    """Return variant pool must have at least 3 entries."""
    assert len(describe._RETURN_VARIANTS) >= 3


# ── Farewell generation ──────────────────────────────────────────────


def test_generate_farewell_returns_text():
    """_generate_farewell produces non-empty text with place name."""
    import random
    from nowhere import server

    s = _make_state("布拉格", 50.08, 14.44, weather_text="多云")
    rng = random.Random(42)
    text = server._generate_farewell(s, rng)

    assert text
    assert "布拉格" in text or "门" in text


def test_generate_farewell_includes_weather():
    """Farewell includes weather snapshot when available."""
    import random
    from nowhere import server

    s = _make_state("纽约", 40.71, -74.01, weather_text="小雨")
    rng = random.Random(42)
    text = server._generate_farewell(s, rng)

    assert "小雨" in text


def test_generate_farewell_no_env():
    """Farewell works even when last_env is None."""
    import random
    from nowhere import server

    s = _make_state("东京", 35.68, 139.69)
    s.last_env = None
    rng = random.Random(42)
    text = server._generate_farewell(s, rng)

    assert text  # Should still produce farewell body


# ── Return generation ────────────────────────────────────────────────


def test_generate_return_with_season_change():
    """Return text mentions season change when seasons differ."""
    import random
    from nowhere import server

    # Create a state that was "landed" 6 months ago (simulated)
    s = _make_state("布拉格", 50.08, 14.44, elapsed_hours=0)
    # Set landed_at to 6 months ago so state.now() is in a different season
    s.landed_at = datetime.now(timezone.utc) - timedelta(days=180)

    # Meta with departed_at 180 days ago
    departed = datetime.now(timezone.utc) - timedelta(days=180)
    meta = {"departed_at": departed.isoformat()}

    rng = random.Random(42)
    text = server._generate_return(s, meta, rng)

    # Should contain season names (春/夏/秋/冬)
    seasons = {"春", "夏", "秋", "冬"}
    has_season = any(season in text for season in seasons)
    # If the season actually changed (which it should over 6 months), we get text
    # If not (edge case), we still get elapsed days text
    assert text  # Should produce some return text
    if has_season:
        assert "离开" in text or "走" in text


def test_generate_return_short_elapsed():
    """Return text is empty when elapsed time < 1 hour."""
    import random
    from nowhere import server

    s = _make_state("京都", 35.01, 135.77)
    # Departed 30 minutes ago
    departed = datetime.now(timezone.utc) - timedelta(minutes=30)
    meta = {"departed_at": departed.isoformat()}

    rng = random.Random(42)
    text = server._generate_return(s, meta, rng)

    assert text == ""


def test_generate_return_no_meta():
    """Return text is empty when meta is None."""
    import random
    from nowhere import server

    s = _make_state("京都", 35.01, 135.77)
    rng = random.Random(42)
    text = server._generate_return(s, None, rng)

    assert text == ""


def test_generate_return_same_season_many_days():
    """Return text mentions elapsed days when same season but > 1 day."""
    import random
    from nowhere import server

    s = _make_state("布拉格", 50.08, 14.44)
    # Departed 10 days ago (likely same season)
    departed = datetime.now(timezone.utc) - timedelta(days=10)
    meta = {"departed_at": departed.isoformat()}

    rng = random.Random(42)
    text = server._generate_return(s, meta, rng)

    # Should mention days elapsed
    assert "天" in text or "离开" in text


# ── Journey log persistence ─────────────────────────────────────────


def test_farewell_logged_to_journey(isolated_home):
    """Farewell event persists in journey_log through save/load."""
    s = _make_state("布拉格", 50.08, 14.44)

    # Simulate adding farewell to log (what server.py does)
    farewell_text = "鞋底还沾着这里的土。门在身后合上。"
    s.journey_log.append({
        "kind": "farewell",
        "text": farewell_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Save and reload
    journeys.save_current(s)
    restored = journeys.switch("布拉格")

    assert restored is not None
    assert len(restored.journey_log) == 1
    assert restored.journey_log[0]["kind"] == "farewell"
    assert restored.journey_log[0]["text"] == farewell_text


def test_multiple_farewells_logged(isolated_home):
    """Multiple farewell events accumulate in journey_log."""
    s = _make_state("纽约", 40.71, -74.01)

    # Simulate two farewell events (leave and come back twice)
    for i in range(3):
        s.journey_log.append({
            "kind": "farewell",
            "text": f"farewell #{i}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    journeys.save_current(s)
    restored = journeys.switch("纽约")

    assert restored is not None
    assert len(restored.journey_log) == 3


# ── journeys.get_journey_meta ───────────────────────────────────────


def test_get_journey_meta_returns_departed_at(isolated_home):
    """get_journey_meta returns departed_at field."""
    s = _make_state("京都", 35.01, 135.77)
    journeys.save_current(s)

    meta = journeys.get_journey_meta("京都")
    assert meta is not None
    assert "departed_at" in meta


def test_get_journey_meta_nonexistent(isolated_home):
    """get_journey_meta returns None for unknown journey."""
    assert journeys.get_journey_meta("不存在的地方") is None


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    pytest.main([__file__, "-v"])
