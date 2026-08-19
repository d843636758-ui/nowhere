"""Salience ranking — pick the top-3 things the body should report.

Score = 0.5*delta + 0.3*novelty + 0.2*(1-body_distance).

Card 53: gravity dimension — heavy places warp the salience field.
  - 重地 5km 内: humanities 置顶(×2.5), 轻浮内容降级(×0.3)
  - 不是删除轻浮内容,是让它们在重力场里变轻

Only the top 3 survive; the rest stay silent in the data attachment.
"""

from __future__ import annotations

import random

_INTENT_MAP: dict[str, dict[str, float]] = {
    "孤独": {"life": 0.5, "radio": 0.5, "sky": 1.5, "terrain": 1.5, "weather": 1.5},
    "安静": {"life": 0.5, "radio": 0.5, "sky": 1.5, "terrain": 1.5, "weather": 1.5},
    "热闹": {"life": 1.5, "radio": 1.5, "water_features": 1.2, "sky": 0.7},
    "人": {"life": 1.5, "radio": 1.5, "water_features": 1.2, "sky": 0.7},
    "水": {"water": 1.5, "water_features": 1.5},
    "海": {"water": 1.5, "water_features": 1.5},
    "古老": {"humanities": 1.5},
    "历史": {"humanities": 1.5},
    "吃": {"localcolor": 2.0},
    "美食": {"localcolor": 2.0},
    "食物": {"localcolor": 2.0},
}

# ── Card 53: gravity — 重力场系数 ─────────────────────────────────────
# 重地 5km 内, humanities 置顶; 轻浮内容降级。
_GRAVITY_HEAVY_BOOST: float = 2.5     # humanities kind boost
_GRAVITY_LIGHT_DEMOTE: float = 0.3    # radio / localcolor demote
_GRAVITY_LIGHT_KINDS: set[str] = {"radio", "localcolor"}


def rank(
    candidates: list[dict],
    rng: random.Random,
    recent_kinds: set[str] | None = None,
    intent: str | None = None,
    heavy_nearby: bool = False,
) -> list[dict]:
    """Rank candidates by salience and return the top 3.

    Parameters
    ----------
    candidates : list[dict]
        Each dict must have keys: kind, delta, novelty, body_distance, payload.
    rng : random.Random
        Seeded RNG for tie-breaking (reproducible).
    recent_kinds : set[str] | None
        Kinds that appeared in the previous salience result.  Novelty for
        these is multiplied by 0.1 to prevent the same kind winning every
        time when all deltas are zero.
    heavy_nearby : bool
        Card 53: True when within 5km of a heavy place (屠杀/灾难/战争遗址).
        Humanities kind gets boosted, lightweight kinds get demoted.

    Returns
    -------
    list[dict]
        Top-3 candidates sorted by score descending.  Ties broken by rng.
    """
    if not candidates:
        return []

    if recent_kinds is None:
        recent_kinds = set()

    scored = []
    for c in candidates:
        novelty = c["novelty"]
        if c["kind"] in recent_kinds:
            novelty *= 0.1
        score = (
            0.5 * c["delta"]
            + 0.3 * novelty
            + 0.2 * (1.0 - c["body_distance"])
        )
        # Intent bias (Card 12)
        if intent:
            weights = _INTENT_MAP.get(intent, {})
            score *= weights.get(c["kind"], 1.0)
        # Card 53: gravity — 重力场扭曲 salience
        if heavy_nearby:
            if c["kind"] == "humanities":
                score *= _GRAVITY_HEAVY_BOOST
            elif c["kind"] in _GRAVITY_LIGHT_KINDS:
                score *= _GRAVITY_LIGHT_DEMOTE
        scored.append((score, rng.random(), c))

    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [t[2] for t in scored[:3]]
