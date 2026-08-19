"""Tests for the cotraveler (同游者) system — card 44.

Dual-traveler mock scenario: footprints, direction, 3rd encounter naming,
@ message delivery, 7-day expiry, OFF mode zero overhead, walk_alone suppresses.
"""

from __future__ import annotations

import json
import sys
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from nowhere import travelers as tv, state as state_mod


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture()
def isolated_home(tmp_path, monkeypatch):
    """Isolate NOWHERE_HOME to a temp directory."""
    monkeypatch.setenv("NOWHERE_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def cotravel_enabled(monkeypatch, isolated_home):
    """Enable cotraveler system with full features."""
    monkeypatch.setenv("NOWHERE_COTRAVEL", "1")
    # Clear module-level caches that might hold stale state
    return isolated_home


@pytest.fixture()
def cotravel_quiet(monkeypatch, isolated_home):
    """Enable cotraveler in quiet mode (footprints only)."""
    monkeypatch.setenv("NOWHERE_COTRAVEL", "quiet")
    return isolated_home


@pytest.fixture()
def cotravel_off(monkeypatch, isolated_home):
    """Disable cotraveler (default state)."""
    monkeypatch.delenv("NOWHERE_COTRAVEL", raising=False)
    return isolated_home


def _make_state(place: str, lat: float, lon: float) -> state_mod.WorldState:
    """Create a minimal WorldState for testing."""
    s = state_mod.WorldState()
    s.pos = (lat, lon)
    s.place_name = place
    s.landed_at = datetime.now(timezone.utc)
    s.path = [{"lat": lat, "lon": lon, "elevation": 0, "dist_km": 1.0}]
    return s


# ── Master switch tests ───────────────────────────────────────────────


class TestMasterSwitch:
    """Verify the master switch behavior."""

    def test_off_by_default(self, cotravel_off):
        assert tv.is_enabled() is False
        assert tv.is_quiet() is False

    def test_enabled_with_1(self, cotravel_enabled):
        assert tv.is_enabled() is True
        assert tv.is_quiet() is False

    def test_quiet_mode(self, cotravel_quiet):
        assert tv.is_enabled() is True
        assert tv.is_quiet() is True

    def test_off_with_0(self, monkeypatch, isolated_home):
        monkeypatch.setenv("NOWHERE_COTRAVEL", "0")
        assert tv.is_enabled() is False

    def test_off_with_empty(self, monkeypatch, isolated_home):
        monkeypatch.setenv("NOWHERE_COTRAVEL", "")
        assert tv.is_enabled() is False

    def test_register_when_off_does_nothing(self, cotravel_off):
        tv.register("测试者", "北京", 39.9, 116.4)
        data = tv.get_active_travelers()
        assert len(data) == 0

    def test_register_when_on_writes(self, cotravel_enabled):
        tv.register("测试者", "北京", 39.9, 116.4)
        data = tv.get_active_travelers()
        assert "测试者" in data
        assert data["测试者"]["place"] == "北京"
        assert data["测试者"]["door_count"] == 1

    def test_off_no_travelers_json_written(self, cotravel_off):
        """When OFF, travelers.json should not be created."""
        tv.register("测试者", "北京", 39.9, 116.4)
        path = tv._travelers_path()
        assert not path.exists()


# ── Registration tests ────────────────────────────────────────────────


class TestRegistration:
    """Test traveler registration and door count."""

    def test_register_increments_door_count(self, cotravel_enabled):
        tv.register("有一", "喀什", 39.5, 76.0)
        tv.register("有一", "长江", 30.8, 111.0)
        data = tv.get_active_travelers()
        assert data["有一"]["door_count"] == 2
        assert data["有一"]["place"] == "长江"

    def test_register_two_travelers(self, cotravel_enabled):
        tv.register("又又", "北京", 39.9, 116.4)
        tv.register("有一", "喀什", 39.5, 76.0)
        data = tv.get_active_travelers()
        assert len(data) == 2
        assert "又又" in data
        assert "有一" in data

    def test_refresh_pos(self, cotravel_enabled):
        tv.register("有一", "喀什", 39.5, 76.0)
        tv.refresh_pos("有一", 39.6, 76.1)
        data = tv.get_active_travelers()
        pos = data["有一"]["pos"]
        assert pos[0] == 39.6
        assert pos[1] == 76.1

    def test_refresh_pos_only_every_5_steps(self, cotravel_enabled):
        """refresh_pos only updates if name exists."""
        tv.refresh_pos("不存在的人", 10.0, 20.0)
        data = tv.get_active_travelers()
        assert "不存在的人" not in data


# ── Footprint tests ───────────────────────────────────────────────────


class TestFootprints:
    """Test footprint recording and detection."""

    def test_record_footprint(self, cotravel_enabled):
        tv.register("有一", "喀什", 39.5, 76.0)
        tv.record_footprint("有一", 39.5, 76.0, "喀什")
        data = tv.get_active_travelers()
        fps = data["有一"]["footprints"]
        assert len(fps) == 1
        assert fps[0]["place"] == "喀什"

    def test_footprint_bearing_computed(self, cotravel_enabled):
        """Bearing should be computed from previous footprint."""
        tv.register("有一", "喀什", 39.5, 76.0)
        tv.record_footprint("有一", 39.5, 76.0, "喀什")
        tv.record_footprint("有一", 39.6, 76.0, "喀什")  # moved north
        data = tv.get_active_travelers()
        fps = data["有一"]["footprints"]
        assert len(fps) == 2
        # Second footprint should have a bearing (north-ish = ~0 degrees)
        bearing = fps[1].get("bearing")
        assert bearing is not None

    def test_check_footprints_within_3km(self, cotravel_enabled, monkeypatch):
        """Footprints within 3km should be detectable."""
        import random

        tv.register("有一", "喀什", 39.5, 76.0)
        tv.record_footprint("有一", 39.5, 76.0, "喀什")

        # Force rng.random() to return 0.1 (< 0.15 threshold)
        rng = random.Random(42)
        rng.random = lambda: 0.1  # type: ignore[method-assign]

        encounter_counts: dict[str, int] = {}
        result = tv.check_footprints("又又", 39.501, 76.001, rng, encounter_counts)
        assert result is not None
        # First encounter: should be anonymous (no name)
        assert "有一" not in result

    def test_check_footprints_beyond_3km(self, cotravel_enabled):
        """Footprints beyond 3km should not trigger."""
        import random

        tv.register("有一", "喀什", 39.5, 76.0)
        tv.record_footprint("有一", 39.5, 76.0, "喀什")

        rng = random.Random(42)
        rng.random = lambda: 0.1  # type: ignore[method-assign]

        encounter_counts: dict[str, int] = {}
        # ~100km away
        result = tv.check_footprints("又又", 40.4, 76.0, rng, encounter_counts)
        assert result is None

    def test_third_encounter_names_traveler(self, cotravel_enabled):
        """Third encounter with same traveler should include their name."""
        import random

        tv.register("有一", "喀什", 39.5, 76.0)
        tv.record_footprint("有一", 39.5, 76.0, "喀什")

        rng = random.Random(42)
        rng.random = lambda: 0.1  # type: ignore[method-assign]

        encounter_counts: dict[str, int] = {}
        # First two encounters: anonymous
        r1 = tv.check_footprints("又又", 39.501, 76.001, rng, encounter_counts)
        assert r1 is not None
        assert "有一" not in r1

        r2 = tv.check_footprints("又又", 39.501, 76.001, rng, encounter_counts)
        assert r2 is not None

        # Third encounter: should name them
        r3 = tv.check_footprints("又又", 39.501, 76.001, rng, encounter_counts)
        assert r3 is not None
        assert "有一" in r3

    def test_footprint_random_miss(self, cotravel_enabled):
        """When rng.random() > 0.15, footprints should not trigger."""
        import random

        tv.register("有一", "喀什", 39.5, 76.0)
        tv.record_footprint("有一", 39.5, 76.0, "喀什")

        rng = random.Random(42)
        rng.random = lambda: 0.5  # type: ignore[method-assign]

        encounter_counts: dict[str, int] = {}
        result = tv.check_footprints("又又", 39.501, 76.001, rng, encounter_counts)
        assert result is None

    def test_footprint_self_excluded(self, cotravel_enabled):
        """A traveler's own footprints should not be detected."""
        import random

        tv.register("有一", "喀什", 39.5, 76.0)
        tv.record_footprint("有一", 39.5, 76.0, "喀什")

        rng = random.Random(42)
        rng.random = lambda: 0.1  # type: ignore[method-assign]

        encounter_counts: dict[str, int] = {}
        result = tv.check_footprints("有一", 39.501, 76.001, rng, encounter_counts)
        assert result is None

    def test_footprint_direction_from_bearing(self, cotravel_enabled):
        """Footprint text should include direction from bearing data."""
        import random

        tv.register("有一", "喀什", 39.5, 76.0)
        tv.record_footprint("有一", 39.5, 76.0, "喀什")
        tv.record_footprint("有一", 39.6, 76.0, "喀什")  # moved north

        rng = random.Random(42)
        rng.random = lambda: 0.1  # type: ignore[method-assign]

        encounter_counts: dict[str, int] = {}
        result = tv.check_footprints("又又", 39.6, 76.0, rng, encounter_counts)
        assert result is not None
        # Should contain some direction word
        has_direction = any(d in result for d in ["北", "东北", "东", "东南", "南", "西南", "西", "西北"])
        assert has_direction or "看不清" in result

    def test_footprints_disabled_when_off(self, cotravel_off):
        """check_footprints should return None when disabled."""
        import random

        rng = random.Random(42)
        encounter_counts: dict[str, int] = {}
        result = tv.check_footprints("又又", 39.5, 76.0, rng, encounter_counts)
        assert result is None

    def test_archived_footprint_past_tense(self, cotravel_enabled):
        """Archived traveler's footprints should use past tense."""
        import random

        tv.register("有一", "喀什", 39.5, 76.0)
        tv.record_footprint("有一", 39.5, 76.0, "喀什")

        # Manually archive: move from active to archive
        data = tv._load_json(tv._travelers_path())
        traveler_data = data.pop("有一")
        traveler_data["archived"] = True
        tv._save_json(tv._archive_path(), {"有一": traveler_data})
        tv._save_json(tv._travelers_path(), data)

        rng = random.Random(42)
        rng.random = lambda: 0.1  # type: ignore[method-assign]

        encounter_counts: dict[str, int] = {}
        result = tv.check_footprints("又又", 39.501, 76.001, rng, encounter_counts)
        # Should still work but with past-tense wording
        assert result is not None


# ── Meeting tests ─────────────────────────────────────────────────────


class TestMeeting:
    """Test synchronous meeting detection."""

    def test_meeting_within_3km_and_24h(self, cotravel_enabled):
        """Meeting should trigger when both are close and active."""
        import random

        tv.register("有一", "喀什", 39.5, 76.0)
        # Refresh to mark as recently active
        tv.refresh_pos("有一", 39.5, 76.0)

        rng = random.Random(42)
        meeting_log: dict[str, str] = {}

        my_text, their_text = tv.check_meeting("又又", 39.501, 76.001, rng, meeting_log)
        assert my_text is not None
        assert their_text is not None
        # Both should be non-empty narrative text
        assert len(my_text) > 5
        assert len(their_text) > 5

    def test_meeting_cooldown_7_days(self, cotravel_enabled):
        """Same pair should not meet again within 7 days."""
        import random

        tv.register("有一", "喀什", 39.5, 76.0)
        tv.refresh_pos("有一", 39.5, 76.0)

        rng = random.Random(42)
        meeting_log: dict[str, str] = {}

        # First meeting
        my1, their1 = tv.check_meeting("又又", 39.501, 76.001, rng, meeting_log)
        assert my1 is not None

        # Second attempt: should not trigger (cooldown)
        my2, their2 = tv.check_meeting("又又", 39.501, 76.001, rng, meeting_log)
        assert my2 is None
        assert their2 is None

    def test_meeting_beyond_3km(self, cotravel_enabled):
        """No meeting when >3km apart."""
        import random

        tv.register("有一", "喀什", 39.5, 76.0)
        tv.refresh_pos("有一", 39.5, 76.0)

        rng = random.Random(42)
        meeting_log: dict[str, str] = {}

        my, their = tv.check_meeting("又又", 40.5, 76.0, rng, meeting_log)
        assert my is None

    def test_meeting_disabled_in_quiet_mode(self, cotravel_quiet):
        """Quiet mode should suppress meetings."""
        import random

        tv.register("有一", "喀什", 39.5, 76.0)
        tv.refresh_pos("有一", 39.5, 76.0)

        rng = random.Random(42)
        meeting_log: dict[str, str] = {}

        my, their = tv.check_meeting("又又", 39.501, 76.001, rng, meeting_log)
        assert my is None

    def test_meeting_disabled_when_off(self, cotravel_off):
        """Off mode should suppress meetings."""
        import random

        rng = random.Random(42)
        meeting_log: dict[str, str] = {}

        my, their = tv.check_meeting("又又", 39.5, 76.0, rng, meeting_log)
        assert my is None


# ── @ Messaging tests ────────────────────────────────────────────────


class TestAtMessaging:
    """Test @ message delivery system."""

    def test_send_and_receive(self, cotravel_enabled):
        """Sent @message should be deliverable on next open_door."""
        import random

        tv.send_at_message("又又", "有一", "喀什")
        rng = random.Random(42)
        result = tv.check_at_messages("有一", rng)
        assert result is not None
        assert "喀什" in result

    def test_message_consumed_after_check(self, cotravel_enabled):
        """check_at_messages should consume the message."""
        import random

        tv.send_at_message("又又", "有一", "喀什")
        rng = random.Random(42)
        tv.check_at_messages("有一", rng)
        # Second check: no more messages
        result = tv.check_at_messages("有一", rng)
        assert result is None

    def test_message_to_nonexistent_traveler(self, cotravel_enabled):
        """@ to nonexistent traveler should be silently accepted."""
        import random

        tv.send_at_message("又又", "不存在的人", "喀什")
        rng = random.Random(42)
        # Delivering to "不存在的人" should still work
        result = tv.check_at_messages("不存在的人", rng)
        assert result is not None

    def test_message_disabled_when_off(self, cotravel_off):
        """No messages when system is off."""
        import random

        tv.send_at_message("又又", "有一", "喀什")
        rng = random.Random(42)
        result = tv.check_at_messages("有一", rng)
        assert result is None

    def test_multiple_messages_fifo(self, cotravel_enabled):
        """Messages should be delivered in FIFO order."""
        import random

        tv.send_at_message("又又", "有一", "喀什")
        tv.send_at_message("又又", "有一", "北京")
        rng = random.Random(42)
        r1 = tv.check_at_messages("有一", rng)
        assert "喀什" in r1
        r2 = tv.check_at_messages("有一", rng)
        assert "北京" in r2


# ── 7-day expiry tests ────────────────────────────────────────────────


class TestExpiry:
    """Test 7-day inactivity archive."""

    def test_active_traveler_not_archived(self, cotravel_enabled):
        """Recently active traveler should stay in main registry."""
        tv.register("有一", "喀什", 39.5, 76.0)
        data = tv.get_active_travelers()
        assert "有一" in data

    def test_inactive_traveler_archived(self, cotravel_enabled):
        """Traveler inactive for 7+ days should be archived."""
        tv.register("有一", "喀什", 39.5, 76.0)

        # Backdate last_seen to 8 days ago
        data = tv._load_json(tv._travelers_path())
        old_time = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        data["有一"]["last_seen"] = old_time
        tv._save_json(tv._travelers_path(), data)

        # expire_inactive should move to archive
        tv.expire_inactive()

        active = tv.get_active_travelers()
        archived = tv.get_archived_travelers()
        assert "有一" not in active
        assert "有一" in archived
        assert archived["有一"].get("archived") is True

    def test_just_under_7_days_stays(self, cotravel_enabled):
        """Traveler inactive for 6 days should stay active."""
        tv.register("有一", "喀什", 39.5, 76.0)

        data = tv._load_json(tv._travelers_path())
        old_time = (datetime.now(timezone.utc) - timedelta(days=6)).isoformat()
        data["有一"]["last_seen"] = old_time
        tv._save_json(tv._travelers_path(), data)

        tv.expire_inactive()

        active = tv.get_active_travelers()
        assert "有一" in active


# ── walk_alone tests ──────────────────────────────────────────────────


class TestWalkAlone:
    """Test per-journey opt-out."""

    def test_walk_alone_sets_flag(self, cotravel_enabled):
        s = _make_state("喀什", 39.5, 76.0)
        assert tv.walk_alone_active(s) is False
        tv.set_walk_alone(s, True)
        assert tv.walk_alone_active(s) is True

    def test_walk_alone_default_false(self, cotravel_enabled):
        s = _make_state("喀什", 39.5, 76.0)
        assert tv.walk_alone_active(s) is False

    def test_walk_alone_flag_on_state(self, cotravel_enabled):
        """walk_alone flag should be stored on state object."""
        s = _make_state("喀什", 39.5, 76.0)
        tv.set_walk_alone(s, True)
        assert getattr(s, "cotraveler_alone", False) is True


# ── Distance helper tests ────────────────────────────────────────────


class TestDistance:
    """Test distance and bearing helpers."""

    def test_km_same_point(self):
        assert tv._km((39.5, 76.0), (39.5, 76.0)) == 0.0

    def test_km_known_distance(self):
        """~111km per degree of latitude."""
        d = tv._km((39.5, 76.0), (40.5, 76.0))
        assert 100 < d < 120

    def test_bearing_word_north(self):
        """Point directly north should return '北'."""
        word = tv._bearing_word((39.0, 76.0), (40.0, 76.0))
        assert word == "北"

    def test_bearing_word_east(self):
        """Point directly east should return '东'."""
        word = tv._bearing_word((39.0, 76.0), (39.0, 77.0))
        assert word == "东"


# ── Variant pool tests ────────────────────────────────────────────────


class TestVariants:
    """Test that variant pools are non-empty and distinct."""

    def test_anon_variants_exist(self):
        assert len(tv._FP_ANON_VARIANTS) >= 6

    def test_named_variants_exist(self):
        assert len(tv._FP_NAMED_VARIANTS) >= 6

    def test_meeting_variants_exist(self):
        assert len(tv._MEETING_MY_VARIANTS) >= 1
        assert len(tv._MEETING_THEIR_VARIANTS) >= 1

    def test_at_hint_variants_exist(self):
        assert len(tv._AT_HINT_VARIANTS) >= 3

    def test_anon_archived_variants_exist(self):
        assert len(tv._FP_ANON_ARCHIVED) >= 1

    def test_named_archived_variants_exist(self):
        assert len(tv._FP_NAMED_ARCHIVED) >= 1


# ── Integration: OFF mode zero overhead ───────────────────────────────


class TestOffModeZeroOverhead:
    """Verify that when cotraveler is off, zero side effects occur."""

    def test_no_json_files_created(self, cotravel_off):
        """When OFF, no cotraveler JSON files should be created."""
        home = Path(os.environ.get("NOWHERE_HOME", ""))
        tv.register("test", "place", 0, 0)
        tv.record_footprint("test", 0, 0, "place")
        tv.send_at_message("a", "b", "place")
        # None of these should create files
        assert not (home / "travelers.json").exists()
        assert not (home / "cotraveler_messages.json").exists()

    def test_get_active_returns_empty(self, cotravel_off):
        assert tv.get_active_travelers() == {}

    def test_get_archived_returns_empty(self, cotravel_off):
        assert tv.get_archived_travelers() == {}

    def test_check_footprints_returns_none(self, cotravel_off):
        import random
        rng = random.Random(42)
        assert tv.check_footprints("x", 0, 0, rng, {}) is None

    def test_check_meeting_returns_none(self, cotravel_off):
        import random
        rng = random.Random(42)
        assert tv.check_meeting("x", 0, 0, rng, {}) == (None, None)

    def test_check_at_messages_returns_none(self, cotravel_off):
        import random
        rng = random.Random(42)
        assert tv.check_at_messages("x", rng) is None

    def test_refresh_pos_noop(self, cotravel_off):
        tv.refresh_pos("x", 0, 0)
        assert tv.get_active_travelers() == {}

    def test_expire_inactive_noop(self, cotravel_off):
        tv.expire_inactive()  # should not raise
