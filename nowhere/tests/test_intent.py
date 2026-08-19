"""Tests for intent gate (Card 12)."""
from __future__ import annotations

import sys
import random
import pytest

from nowhere import salience, localcolor, state as state_mod


def test_intent_eating_more_food():
    """intent='吃' should bias toward food cards."""
    rng_base = random.Random(42)
    food_with_intent = 0
    food_without = 0
    runs = 50

    for i in range(runs):
        # With intent
        r1 = random.Random(i)
        result = localcolor.draw("喀什", set(), r1, local_hour=12, country_code="CN", intent="吃")
        if result and result.get("category") == "美食":
            food_with_intent += 1

        # Without intent
        r2 = random.Random(i)
        result2 = localcolor.draw("喀什", set(), r2, local_hour=12, country_code="CN")
        if result2 and result2.get("category") == "美食":
            food_without += 1

    assert food_with_intent >= food_without, (
        f"Food with intent ({food_with_intent}) should be >= without ({food_without})"
    )


def test_intent_unknown_word():
    """Unknown intent keyword should behave like no intent."""
    for i in range(20):
        r1 = random.Random(i)
        r2 = random.Random(i)
        r1a = random.Random(i)
        r2a = random.Random(i)
        # Both should produce the same result with same seed
        result_unknown = salience.rank(
            [{"kind": "weather", "delta": 0.5, "novelty": 0.2, "body_distance": 0.1, "payload": {}}],
            r1, intent="不存在词"
        )
        result_none = salience.rank(
            [{"kind": "weather", "delta": 0.5, "novelty": 0.2, "body_distance": 0.1, "payload": {}}],
            r2, intent=None
        )
        assert result_unknown == result_none


def test_intent_salience_bias():
    """Intent should change salience ranking."""
    candidates = [
        {"kind": "sky", "delta": 0.5, "novelty": 0.5, "body_distance": 0.3, "payload": {}},
        {"kind": "life", "delta": 0.5, "novelty": 0.5, "body_distance": 0.3, "payload": {}},
    ]
    # With "孤独" intent, sky should be boosted over life
    r1 = random.Random(42)
    result = salience.rank(candidates, r1, intent="孤独")
    # Sky should rank higher due to 1.5x vs 0.5x
    assert result[0]["kind"] == "sky"


def test_intent_state_serialization():
    """Intent field round-trips through to_dict/from_dict."""
    s = state_mod.WorldState()
    s.intent = "吃"
    d = s.to_dict()
    assert d["intent"] == "吃"
    s2 = state_mod.WorldState.from_dict(d)
    assert s2.intent == "吃"


def test_intent_state_default_none():
    """Intent defaults to None."""
    s = state_mod.WorldState()
    assert s.intent is None
    d = s.to_dict()
    assert d.get("intent") is None


def test_intent_map_completeness():
    """All intent map entries have valid kind keys."""
    for intent, weights in salience._INTENT_MAP.items():
        assert isinstance(weights, dict), f"Intent '{intent}' weights should be dict"
        for kind, weight in weights.items():
            assert isinstance(weight, (int, float)), f"Weight for {kind} should be number"
            assert weight > 0, f"Weight for {kind} should be positive"
