"""Multi-journey management for nowhere.

Stores each journey as a separate JSON file under ~/.nowhere/journeys/.
An index.json tracks the active journey and metadata for all journeys.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
from datetime import datetime, timezone
from typing import Any

from nowhere.state import WorldState

_JOURNEYS_DIR = pathlib.Path(
    os.environ.get("NOWHERE_HOME") or str(pathlib.Path.home() / ".nowhere")
) / "journeys"
_INDEX_FILE = _JOURNEYS_DIR / "index.json"


def _slug(place_name: str) -> str:
    """Normalize place name to a filesystem-safe slug."""
    s = place_name.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^\w一-鿿-]", "", s)
    return s or "unknown"


def _ensure_dir() -> None:
    _JOURNEYS_DIR.mkdir(parents=True, exist_ok=True)


def _load_index() -> dict:
    """Load or initialize the journey index."""
    if _INDEX_FILE.exists():
        try:
            return json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"active": None, "journeys": []}


def _save_index(index: dict) -> None:
    """Persist the journey index."""
    _ensure_dir()
    _INDEX_FILE.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _journey_path(slug: str) -> pathlib.Path:
    return _JOURNEYS_DIR / f"{slug}.json"


def save_current(state: WorldState) -> None:
    """Save the current state as a journey file and update the index."""
    _ensure_dir()
    place = state.place_name or "unknown"
    slug = _slug(place)
    path = _journey_path(slug)

    # Save state
    data = state.to_dict()
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Update index
    index = _load_index()
    now_iso = datetime.now(timezone.utc).isoformat()

    # Find existing entry
    existing = None
    for j in index["journeys"]:
        if j["slug"] == slug:
            existing = j
            break

    if existing:
        existing["last_active"] = now_iso
        existing["departed_at"] = now_iso
        existing["steps"] = len(state.path)
        existing["last_text"] = (state.last_text or "")[:50]
    else:
        index["journeys"].append({
            "slug": slug,
            "place_name": place,
            "landed_at": state.landed_at.isoformat() if state.landed_at else now_iso,
            "last_active": now_iso,
            "departed_at": now_iso,
            "steps": len(state.path),
            "last_text": (state.last_text or "")[:50],
        })

    index["active"] = slug
    _save_index(index)


def list_journeys() -> list[dict]:
    """List all saved journeys with metadata."""
    index = _load_index()
    return index.get("journeys", [])


def get_active_slug() -> str | None:
    """Return the active journey slug, or None."""
    return _load_index().get("active")


def switch(slug_or_place: str) -> WorldState | None:
    """Switch to a journey by slug or place name. Returns WorldState or None."""
    index = _load_index()
    target = _slug(slug_or_place)

    # Try exact slug match first
    for j in index["journeys"]:
        if j["slug"] == target:
            return _load_journey(j["slug"], index)

    # Try fuzzy match (place_name contains query)
    slug_or_lower = slug_or_place.strip().lower()
    for j in index["journeys"]:
        if slug_or_lower in j.get("place_name", "").lower():
            return _load_journey(j["slug"], index)

    return None


def get_journey_meta(slug_or_place: str) -> dict | None:
    """Return index metadata for a journey, or None if not found."""
    index = _load_index()
    target = _slug(slug_or_place)

    # Try exact slug match first
    for j in index["journeys"]:
        if j["slug"] == target:
            return j

    # Try fuzzy match (place_name contains query)
    slug_or_lower = slug_or_place.strip().lower()
    for j in index["journeys"]:
        if slug_or_lower in j.get("place_name", "").lower():
            return j

    return None


def _load_journey(slug: str, index: dict) -> WorldState | None:
    """Load a journey file and set it as active."""
    path = _journey_path(slug)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        state = WorldState.from_dict(data)
        index["active"] = slug
        _save_index(index)
        return state
    except Exception:
        return None


def delete(slug: str) -> bool:
    """Delete a journey file. Returns True if deleted."""
    path = _journey_path(slug)
    if path.exists():
        path.unlink()
    index = _load_index()
    index["journeys"] = [j for j in index["journeys"] if j["slug"] != slug]
    if index["active"] == slug:
        index["active"] = None
    _save_index(index)
    return True
