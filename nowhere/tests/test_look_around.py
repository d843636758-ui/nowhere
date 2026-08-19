"""Tests for Card 38: look_around no longer has '往回走' movement verbs."""

from __future__ import annotations

import asyncio
import random
from unittest.mock import AsyncMock, patch

from nowhere import server
from nowhere.state import WorldState


def _setup_state():
    """Reset server state for testing look_around."""
    server._state = WorldState()
    server._state.pos = (35.0, 139.0)
    server._state.place_name = "TestPlace"
    server._state.landed_at = __import__("datetime").datetime(2026, 7, 15, 10, 0, 0,
                                                              tzinfo=__import__("datetime").timezone.utc)
    server._state.elapsed_hours = 1.0
    server._state.biome = "grass"
    server._rng = random.Random(42)


def test_look_around_never_contains_wanghui():
    """look_around output must never contain '往回走' or '回到'."""
    _setup_state()

    with patch.object(server, "localcolor") as mock_lc, \
         patch.object(server, "life") as mock_life, \
         patch.object(server, "art") as mock_art:
        mock_lc.draw.return_value = None
        mock_life.nearby = AsyncMock(return_value=None)
        mock_art.match = AsyncMock(return_value=None)

        result = asyncio.run(server.look_around_impl())

    text = result["text"]
    assert "往回走" not in text, f"Found '往回走' in look_around output: {text}"
    assert "回到" not in text, f"Found '回到' in look_around output: {text}"


def test_look_around_no_movement_verbs():
    """look_around output must not contain walking movement verbs."""
    _setup_state()

    with patch.object(server, "localcolor") as mock_lc, \
         patch.object(server, "life") as mock_life, \
         patch.object(server, "art") as mock_art:
        mock_lc.draw.return_value = None
        mock_life.nearby = AsyncMock(return_value=None)
        mock_art.match = AsyncMock(return_value=None)

        result = asyncio.run(server.look_around_impl())

    text = result["text"]
    # Should not contain "走了" (walking movement)
    assert "走了" not in text, f"Found movement verb '走了' in look_around: {text}"


def test_look_around_uses_static_verbs():
    """look_around opening should use static observation verbs, not movement."""
    _setup_state()

    with patch.object(server, "localcolor") as mock_lc, \
         patch.object(server, "life") as mock_life, \
         patch.object(server, "art") as mock_art:
        mock_lc.draw.return_value = None
        mock_life.nearby = AsyncMock(return_value=None)
        mock_art.match = AsyncMock(return_value=None)

        result = asyncio.run(server.look_around_impl())

    text = result["text"]
    # Should contain one of the static verbs
    static_verbs = ["目光投向", "视线落在", "你看向", "你望向", "你面朝"]
    has_static = any(v in text for v in static_verbs)
    assert has_static, f"Expected a static observation verb in: {text[:100]}"


def test_look_around_different_closings():
    """Two look_around calls with different seeds should produce different text."""
    texts = []
    for seed in [42, 123]:
        server._state = WorldState()
        server._state.pos = (35.0, 139.0)
        server._state.place_name = "TestPlace"
        server._state.landed_at = __import__("datetime").datetime(
            2026, 7, 15, 10, 0, 0,
            tzinfo=__import__("datetime").timezone.utc)
        server._state.elapsed_hours = 1.0
        server._state.biome = "grass"
        server._rng = random.Random(seed)

        with patch.object(server, "localcolor") as mock_lc, \
             patch.object(server, "life") as mock_life, \
             patch.object(server, "art") as mock_art:
            mock_lc.draw.return_value = None
            mock_life.nearby = AsyncMock(return_value=None)
            mock_art.match = AsyncMock(return_value=None)

            result = asyncio.run(server.look_around_impl())
        texts.append(result["text"])

    # With different seeds, the text should differ (different direction, verb, closing)
    assert texts[0] != texts[1], "Two look_around calls with different seeds produced identical text"
