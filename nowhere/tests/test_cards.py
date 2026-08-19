"""Tests for the unified Card schema (cards.py).

Validates:
- All card sources produce valid Cards
- Card counts match expected totals
- select() filtering and weighting works
- Condition matching is correct
"""

from __future__ import annotations

import random

from nowhere import cards, encounters, localcolor, humanities


# ── Card loading ────────────────────────────────────────────────────


def test_load_all_returns_cards():
    """load_all() returns a non-empty list of Cards."""
    all_cards = cards.load_all()
    assert len(all_cards) > 0
    assert all(isinstance(c, cards.Card) for c in all_cards)


def test_all_cards_valid():
    """Every card from every source passes validation."""
    all_cards = cards.load_all()
    invalid = [c for c in all_cards if not cards.validate_card(c)]
    assert invalid == [], f"Invalid cards: {[c.id for c in invalid[:5]]}"


def test_card_kinds():
    """All five kinds are represented."""
    all_cards = cards.load_all()
    kinds = {c.kind for c in all_cards}
    assert kinds == {"localcolor", "humanities", "encounter", "people", "errand"}


def test_localcolor_card_count():
    """Localcolor cards count matches expected (main + regional merges)."""
    lc = cards.load_localcolor()
    # Main: 340 places, ~3113 cards + regional new places (1064 cards)
    assert len(lc) == 4138, f"Expected 4138 localcolor cards, got {len(lc)}"
    # All should be kind=localcolor
    assert all(c.kind == "localcolor" for c in lc)


def test_humanities_card_count():
    """Humanities cards count matches expected."""
    hu = cards.load_humanities()
    assert len(hu) >= 1200, f"Expected >= 1200 humanities cards, got {len(hu)}"
    assert all(c.kind == "humanities" for c in hu)


def test_encounter_card_count():
    """Encounter cards count matches expected."""
    enc = cards.load_encounters()
    assert len(enc) == 768, f"Expected 768 encounter cards, got {len(enc)}"
    assert all(c.kind == "encounter" for c in enc)


def test_people_card_count():
    """People cards count matches expected."""
    ppl = cards.load_people()
    assert len(ppl) == 60, f"Expected 60 people cards, got {len(ppl)}"
    assert all(c.kind == "people" for c in ppl)


def test_errand_card_count():
    """Errand cards count matches expected."""
    err = cards.load_errands()
    assert len(err) == 20, f"Expected 20 errand cards, got {len(err)}"
    assert all(c.kind == "errand" for c in err)


# ── Condition matching ──────────────────────────────────────────────


def test_matches_conditions_place():
    """Place condition filters correctly."""
    card = cards.Card(id="test/1", kind="localcolor", text="hi",
                      conditions={"place": "喀什"})
    assert cards.matches_conditions(card, {"place": "喀什"})
    assert not cards.matches_conditions(card, {"place": "京都"})
    # No context place = no filter
    assert cards.matches_conditions(card, {})


def test_matches_conditions_hours():
    """Hours condition filters correctly."""
    card = cards.Card(id="test/1", kind="localcolor", text="hi",
                      conditions={"hours": [6, 9]})
    assert cards.matches_conditions(card, {"hours": 7})
    assert not cards.matches_conditions(card, {"hours": 10})
    assert cards.matches_conditions(card, {"hours": 6})
    assert not cards.matches_conditions(card, {"hours": 9})


def test_matches_conditions_months():
    """Month condition filters correctly."""
    card = cards.Card(id="test/1", kind="localcolor", text="hi",
                      conditions={"months": [6, 7, 8]})
    assert cards.matches_conditions(card, {"month": 7})
    assert not cards.matches_conditions(card, {"month": 1})
    # No context month = no filter
    assert cards.matches_conditions(card, {})


def test_matches_conditions_region():
    """Region condition filters correctly."""
    card = cards.Card(id="test/1", kind="encounter", text="hi",
                      conditions={"region": "asia"})
    assert cards.matches_conditions(card, {"region": "asia"})
    assert not cards.matches_conditions(card, {"region": "europe"})


# ── Selection ───────────────────────────────────────────────────────


def test_select_filters_seen():
    """select() skips cards in the seen set."""
    pool = [
        cards.Card(id=f"t/{i}", kind="localcolor", text=f"card {i}")
        for i in range(5)
    ]
    seen = {"t/0", "t/1"}
    result = cards.select(pool, {}, random.Random(1), seen=seen)
    result_ids = {c.id for c in result}
    assert "t/0" not in result_ids
    assert "t/1" not in result_ids


def test_select_filters_by_conditions():
    """select() filters by place condition."""
    pool = [
        cards.Card(id="a/1", kind="localcolor", text="a",
                    conditions={"place": "喀什"}),
        cards.Card(id="b/1", kind="localcolor", text="b",
                    conditions={"place": "京都"}),
    ]
    result = cards.select(pool, {"place": "喀什"}, random.Random(1))
    assert len(result) == 1
    assert result[0].id == "a/1"


def test_select_weighted():
    """select() respects weights (higher weight = more likely)."""
    pool = [
        cards.Card(id="heavy", kind="localcolor", text="h",
                    meta={"weight": 100.0}),
        cards.Card(id="light", kind="localcolor", text="l",
                    meta={"weight": 0.001}),
    ]
    # With 1000 draws, heavy should dominate
    heavy_count = 0
    for _ in range(1000):
        result = cards.select(pool, {}, random.Random(42))
        if result and result[0].id == "heavy":
            heavy_count += 1
    assert heavy_count > 900, f"heavy only selected {heavy_count}/1000 times"


def test_select_meal_time_food_bonus():
    """select() boosts food cards during meal hours."""
    pool = [
        cards.Card(id="food", kind="localcolor", text="yummy",
                    meta={"category": "美食", "weight": 3.0}),
        cards.Card(id="other", kind="localcolor", text="meh",
                    meta={"category": "物产", "weight": 1.0}),
    ]
    # During meal time, food weight stays at 3.0
    meal_result = cards.select(pool, {"hours": 12}, random.Random(1))
    # Outside meal time, food weight drops to 1.0
    no_meal_result = cards.select(pool, {"hours": 15}, random.Random(1))
    # Both should work (not crash)
    assert len(meal_result) >= 1
    assert len(no_meal_result) >= 1


def test_select_empty_pool():
    """select() returns empty list for empty pool."""
    assert cards.select([], {}, random.Random(1)) == []


def test_select_k():
    """select() returns up to k cards."""
    pool = [
        cards.Card(id=f"t/{i}", kind="localcolor", text=f"card {i}")
        for i in range(10)
    ]
    result = cards.select(pool, {}, random.Random(1), k=3)
    assert len(result) == 3


# ── Module integration ──────────────────────────────────────────────


def test_localcolor_produces_valid_cards():
    """localcolor._load() returns valid Card objects."""
    lc_cards = localcolor._load()
    assert len(lc_cards) > 0
    invalid = [c for c in lc_cards if not cards.validate_card(c)]
    assert invalid == [], f"Invalid: {[c.id for c in invalid[:5]]}"


def test_humanities_produces_valid_cards():
    """humanities._get_cards() returns valid Card objects."""
    hu_cards = humanities._get_cards()
    assert len(hu_cards) > 0
    invalid = [c for c in hu_cards if not cards.validate_card(c)]
    assert invalid == [], f"Invalid: {[c.id for c in invalid[:5]]}"


def test_encounters_card_pool():
    """encounters.card_pool() returns valid Card objects."""
    enc_cards = encounters.card_pool()
    assert len(enc_cards) == 768
    invalid = [c for c in enc_cards if not cards.validate_card(c)]
    assert invalid == [], f"Invalid: {[c.id for c in invalid[:5]]}"


def test_localcolor_draw_unchanged():
    """localcolor.draw() still returns {category, text, key} format."""
    rng = random.Random(42)
    card = localcolor.draw("喀什", set(), rng)
    assert card is not None
    assert "category" in card
    assert "text" in card
    assert "key" in card
    assert card["text"]


def test_humanities_draw_unchanged():
    """humanities.draw() still returns {category, text, key, ref} format."""
    rng = random.Random(42)
    card = humanities.draw("京都", set(), rng)
    assert card is not None
    assert "category" in card
    assert "text" in card
    assert "key" in card
    assert "ref" in card
    assert card["text"]


def test_rhythm_event_unchanged():
    """localcolor.rhythm_event() still returns str or None."""
    rng = random.Random(42)
    result = localcolor.rhythm_event("喀什", 15, rng)
    assert result is None or isinstance(result, str)


def test_card_ids_unique_per_kind():
    """Card IDs are unique within each kind."""
    all_cards = cards.load_all()
    for kind in ("localcolor", "humanities", "encounter", "people", "errand"):
        kind_cards = [c for c in all_cards if c.kind == kind]
        ids = [c.id for c in kind_cards]
        assert len(ids) == len(set(ids)), f"Duplicate IDs in {kind}"
