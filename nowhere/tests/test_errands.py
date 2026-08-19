"""Tests for Card 42: 差事发生器 (errand system).

Covers:
  - Letter lifecycle: pick up → deliver → journal entry
  - Treasure chain: 2 legs + terminal (3rd leg empty)
  - Festival chase: wind mention within window
  - Letter-in-wait text
  - Suspend/transfer legal
"""

from __future__ import annotations

import json
import math
import random
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# ── GBK console fix ─────────────────────────────────────────────────
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Ensure the package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from nowhere import errands, state as state_mod


# ═══════════════════════════════════════════════════════════════════
# Letter data
# ═══════════════════════════════════════════════════════════════════


class TestLetterData:
    """errands_letters.json has 20 letters with required fields."""

    def test_load_letters(self):
        letters = errands._load_letters()
        assert len(letters) == 20

    def test_letter_fields(self):
        for letter in errands._load_letters():
            assert "sender" in letter, f"Missing sender in {letter}"
            assert "recipient" in letter, f"Missing recipient in {letter}"
            assert "hint" in letter, f"Missing hint in {letter}"
            assert "text" in letter, f"Missing text in {letter}"
            # hint should be a feature description, not a place name
            assert len(letter["hint"]) > 0


# ═══════════════════════════════════════════════════════════════════
# Letter lifecycle
# ═══════════════════════════════════════════════════════════════════


class TestLetterLifecycle:
    """Full letter lifecycle: pick up → carry → deliver → journal."""

    def test_pick_letter(self):
        rng = random.Random(42)
        letter = errands.pick_letter(rng)
        assert letter is not None
        assert "sender" in letter
        assert "text" in letter

    def test_take_letter(self):
        sim_time = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)
        letter = errands._load_letters()[0]
        errand = errands.take_letter(letter, sim_time)
        assert errand["kind"] == "letter"
        assert errand["sender"] == letter["sender"]
        assert errand["hint"] == letter["hint"]
        assert errand["text"] == letter["text"]
        assert errand["taken_at"] == sim_time.isoformat()

    def test_check_delivery_at_destination(self):
        """Within 5km of a matching place → delivery succeeds."""
        errand = {
            "kind": "letter",
            "hint": "海边守灯塔",
            "sender": "于尔根",
        }
        # Place coords with a place very close to pos
        pos = (30.0, 120.0)
        place_coords = {"灯塔镇": (30.01, 120.01)}  # ~1.5km away
        matched = errands.check_delivery(pos, errand, place_coords, radius_km=5.0)
        assert matched == "灯塔镇"

    def test_check_delivery_too_far(self):
        """Beyond 5km → no match."""
        errand = {
            "kind": "letter",
            "hint": "海边守灯塔",
            "sender": "于尔根",
        }
        pos = (30.0, 120.0)
        place_coords = {"灯塔镇": (31.0, 121.0)}  # ~140km away
        matched = errands.check_delivery(pos, errand, place_coords, radius_km=5.0)
        assert matched is None

    def test_build_delivery_journal_same_day(self):
        errand = {"sender": "于尔根"}
        taken_at = datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc).isoformat()
        delivered_at = datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc)
        entry = errands.build_delivery_journal(errand, "灯塔镇", taken_at, delivered_at)
        assert "于尔根" in entry
        assert "灯塔镇" in entry
        assert "当天" in entry

    def test_build_delivery_journal_late(self):
        errand = {"sender": "于尔根"}
        taken_at = datetime(2026, 7, 10, 10, 0, tzinfo=timezone.utc).isoformat()
        delivered_at = datetime(2026, 7, 20, 14, 0, tzinfo=timezone.utc)
        entry = errands.build_delivery_journal(errand, "灯塔镇", taken_at, delivered_at)
        assert "10天" in entry

    def test_errand_hint_line_letter(self):
        errand = {"kind": "letter", "hint": "海边守灯塔"}
        line = errands.errand_hint_line(errand)
        assert "信" in line
        assert "海边守灯塔" in line

    def test_errand_hint_line_none(self):
        assert errands.errand_hint_line(None) == ""


# ═══════════════════════════════════════════════════════════════════
# Treasure chain
# ═══════════════════════════════════════════════════════════════════


class TestTreasureChain:
    """Treasure chain: create → advance 2 legs → terminal."""

    def test_create_chain(self):
        rng = random.Random(42)
        note = "去三江并流的地方,石头比水硬"
        pos = (30.0, 120.0)
        sim_time = datetime(2026, 7, 15, tzinfo=timezone.utc)
        chain = errands.create_chain(note, pos, sim_time, rng)
        assert chain["kind"] == "chain"
        assert chain["leg"] == 1
        assert chain["note"] == note
        assert "id" in chain

    def test_advance_chain(self):
        rng = random.Random(42)
        chain = errands.create_chain("test", (0, 0), datetime.now(timezone.utc), rng)
        assert chain["leg"] == 1

        chain2 = errands.advance_chain(chain)
        assert chain2["leg"] == 2

        chain3 = errands.advance_chain(chain2)
        assert chain3["leg"] == 3

    def test_chain_terminal(self):
        rng = random.Random(42)
        chain = errands.create_chain("test", (0, 0), datetime.now(timezone.utc), rng)
        assert not errands.chain_is_terminal(chain)

        chain2 = errands.advance_chain(chain)
        assert not errands.chain_is_terminal(chain2)

        chain3 = errands.advance_chain(chain2)
        assert errands.chain_is_terminal(chain3)

    def test_chain_terminal_note(self):
        note = errands.chain_terminal_note()
        assert "空" in note or "留给" in note


# ═══════════════════════════════════════════════════════════════════
# Festival chase
# ═══════════════════════════════════════════════════════════════════


class TestFestivalChase:
    """Festival chase: wind mention within 800km/5 days."""

    def test_create_festival_rumor(self):
        text = errands.create_festival_rumor("清迈", "泼水节", 4)
        assert "4天" in text
        assert "清迈" in text
        assert "泼水节" in text

    def test_create_festival_rumor_today(self):
        text = errands.create_festival_rumor("清迈", "泼水节", 0)
        assert "今天" in text

    def test_festival_rumor_no_negative_days(self):
        text = errands.create_festival_rumor("清迈", "泼水节", -1)
        # Should still produce valid text (days_away <= 0 → today)
        assert "今天" in text


# ═══════════════════════════════════════════════════════════════════
# Letter-in-wait text
# ═══════════════════════════════════════════════════════════════════


class TestLetterInWait:
    """Letter in pack → wait text 10% weight mention."""

    def test_letter_wait_text(self):
        rng = random.Random(42)
        text = errands.letter_wait_text(rng)
        assert len(text) > 0
        # Should mention letter/信 or pack/包
        assert any(k in text for k in ("信", "包", "纸"))

    def test_letter_wait_text_variety(self):
        """Multiple calls should produce variety."""
        rng = random.Random(42)
        texts = {errands.letter_wait_text(rng) for _ in range(20)}
        assert len(texts) >= 2, f"Only {len(texts)} variants out of 20 calls"


# ═══════════════════════════════════════════════════════════════════
# State serialization
# ═══════════════════════════════════════════════════════════════════


class TestErrandState:
    """errand field round-trips through to_dict/from_dict."""

    def test_errand_none_roundtrip(self):
        s = state_mod.WorldState()
        assert s.errand is None
        d = s.to_dict()
        assert d["errand"] is None
        s2 = state_mod.WorldState.from_dict(d)
        assert s2.errand is None

    def test_errand_letter_roundtrip(self):
        s = state_mod.WorldState()
        s.errand = {
            "kind": "letter",
            "sender": "于尔根",
            "recipient_desc": "守灯塔那镇上的妹妹",
            "hint": "海边守灯塔",
            "text": "妈的病好多了。",
            "taken_at": "2026-07-15T12:00:00+00:00",
        }
        d = s.to_dict()
        s2 = state_mod.WorldState.from_dict(d)
        assert s2.errand["kind"] == "letter"
        assert s2.errand["sender"] == "于尔根"
        assert s2.errand["hint"] == "海边守灯塔"

    def test_errand_chain_roundtrip(self):
        s = state_mod.WorldState()
        s.errand = {
            "kind": "chain",
            "id": 12345,
            "leg": 2,
            "note": "去三江并流的地方",
            "origin_pos": [30.0, 120.0],
            "created_at": "2026-07-15T12:00:00+00:00",
        }
        d = s.to_dict()
        s2 = state_mod.WorldState.from_dict(d)
        assert s2.errand["kind"] == "chain"
        assert s2.errand["leg"] == 2

    def test_errand_flags_roundtrip(self):
        s = state_mod.WorldState()
        s.errand_letter_taken_this_journey = True
        s.errand_festival_mentioned_this_journey = True
        d = s.to_dict()
        s2 = state_mod.WorldState.from_dict(d)
        assert s2.errand_letter_taken_this_journey is True
        assert s2.errand_festival_mentioned_this_journey is True


# ═══════════════════════════════════════════════════════════════════
# Suspend / transfer legal
# ═══════════════════════════════════════════════════════════════════


class TestSuspendTransfer:
    """Errand persists across suspend/resume and journey switches."""

    def test_errand_persists_in_state(self):
        """Errand survives to_dict → from_dict (suspend/resume)."""
        s = state_mod.WorldState()
        s.errand = {"kind": "letter", "sender": "test", "hint": "某处"}
        d = s.to_dict()
        s2 = state_mod.WorldState.from_dict(d)
        assert s2.errand is not None
        assert s2.errand["kind"] == "letter"

    def test_errand_flags_default_false(self):
        """New state has flags defaulting to False."""
        s = state_mod.WorldState()
        assert s.errand_letter_taken_this_journey is False
        assert s.errand_festival_mentioned_this_journey is False

    def test_errand_none_on_new_state(self):
        """Brand new state has no errand."""
        s = state_mod.WorldState()
        assert s.errand is None
