"""构建时管线: 校验 + 拆分 + 写门禁产物。

设计原则(Noel Llopis, Game Developer Magazine 2004):
  问题在构建时解决,不在运行时解决。运行时不过滤。

用法:
  python tools/build_scenes.py          # 全量构建
  python tools/build_scenes.py --check  # 只校验不输出
"""

from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

# ── Paths ─────────────────────────────────────────────────────────────
_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SRC_DIR = _ROOT / "nowhere" / "data" / "scenes_src"
_OUT_DIR = _ROOT / "nowhere" / "data"

# ── Registries ────────────────────────────────────────────────────────
WATER_TYPES = {"river", "lake", "dock", "waterfall", "stream", "ocean", "pond"}
DISCOVERY_TYPES = {"forest", "mountain", "desert", "ocean", "polar",
                   "city", "universal", "grassland", "rainforest", "wetland"}
VALID_TYPES = WATER_TYPES | DISCOVERY_TYPES
VALID_BIOMES = {"tundra", "desert", "coast", "mountain", "rainforest",
                "grassland", "city", "any", "forest"}

# Biome compatibility: which types are allowed in each biome
# "any" in source means the card works everywhere
_BIOME_COMPAT: dict[str, set[str]] = {
    "tundra":     {"river", "lake", "waterfall", "stream", "pond"},
    "desert":     {"river", "lake", "waterfall", "stream", "pond"},
    "coast":      {"river", "lake", "waterfall", "stream", "dock", "ocean", "pond"},
    "mountain":   {"river", "lake", "waterfall", "stream", "pond"},
    "rainforest": {"river", "lake", "waterfall", "stream", "pond"},
    "grassland":  {"river", "lake", "waterfall", "stream", "pond"},
    "city":       {"river", "lake", "waterfall", "stream", "dock", "pond"},
    "forest":     {"river", "lake", "waterfall", "stream", "pond"},
}

# ── Forbidden words ───────────────────────────────────────────────────
_FORBIDDEN_WORDS = {"很", "非常", "十分", "巨大", "美丽"}
_VAGUE_WORDS = {"一些", "很多", "仿佛", "好像", "似乎", "有点"}

# False positive patterns: (word, suffix_that_makes_it_ok)
_FALSE_POSITIVE_CONTEXTS = {
    "十分": {"钟", "之"},  # 十分钟 = 10 minutes, 十分之一 = one tenth
}


class BuildError(Exception):
    """Raised when validation fails."""


def _validate_card(card: dict, idx: int, src_name: str) -> list[str]:
    """Validate a single card. Returns list of error strings."""
    errors: list[str] = []
    prefix = f"{src_name}[{idx}]"

    # Required fields
    for field in ("text", "type", "biomes"):
        if field not in card:
            errors.append(f"{prefix}: missing required field '{field}'")

    text = card.get("text", "")
    ctype = card.get("type", "")
    biomes = card.get("biomes", [])

    # Type in registry
    if ctype and ctype not in VALID_TYPES:
        errors.append(f"{prefix}: unknown type '{ctype}' (valid: {sorted(VALID_TYPES)})")

    # Biomes in registry
    for b in biomes:
        if b not in VALID_BIOMES:
            errors.append(f"{prefix}: unknown biome '{b}' (valid: {sorted(VALID_BIOMES)})")

    # Forbidden words (with false-positive context filtering)
    for word in _FORBIDDEN_WORDS:
        idx = text.find(word)
        while idx >= 0:
            end = idx + len(word)
            suffix = text[end:end + 1] if end < len(text) else ""
            if word in _FALSE_POSITIVE_CONTEXTS and suffix in _FALSE_POSITIVE_CONTEXTS[word]:
                idx = text.find(word, end)
                continue
            errors.append(f"{prefix}: forbidden word '{word}' in text")
            break

    # Vague words
    for word in _VAGUE_WORDS:
        if word in text:
            errors.append(f"{prefix}: vague word '{word}' in text")

    # Empty text
    if not text.strip():
        errors.append(f"{prefix}: empty text")

    return errors


def _load_and_validate(src_path: pathlib.Path) -> tuple[list[dict], list[str]]:
    """Load a source JSON file and validate all cards. Returns (cards, errors)."""
    if not src_path.exists():
        return [], [f"Source file not found: {src_path}"]

    try:
        data = json.loads(src_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [], [f"JSON parse error in {src_path}: {e}"]

    if not isinstance(data, list):
        return [], [f"Expected list in {src_path}, got {type(data).__name__}"]

    all_errors: list[str] = []
    src_name = src_path.stem

    for i, card in enumerate(data):
        all_errors.extend(_validate_card(card, i, src_name))

    # Duplicate detection within type
    seen_by_type: dict[str, dict[str, int]] = {}
    for i, card in enumerate(data):
        ctype = card.get("type", "")
        text = card.get("text", "")
        if ctype not in seen_by_type:
            seen_by_type[ctype] = {}
        if text in seen_by_type[ctype]:
            all_errors.append(
                f"{src_name}[{i}]: duplicate text in type '{ctype}' "
                f"(first at [{seen_by_type[ctype][text]}])"
            )
        else:
            seen_by_type[ctype][text] = i

    return data, all_errors


def _card_usable_in_biome(card: dict, biome: str) -> bool:
    """Check if a card is usable in the given biome."""
    biomes = card.get("biomes", ["any"])
    if "any" in biomes:
        return True
    return biome in biomes


def _build_water(cards: list[dict]) -> dict[str, list[str]]:
    """Split water cards into biome-specific product files.

    Returns dict of {filename_without_ext: [lines]}.
    """
    # Collect all biomes that appear in cards
    all_biomes: set[str] = set()
    for card in cards:
        for b in card.get("biomes", ["any"]):
            if b == "any":
                all_biomes.update(_BIOME_COMPAT.keys())
            else:
                all_biomes.add(b)

    products: dict[str, list[str]] = {}

    # Per-type files
    for ctype in sorted(VALID_TYPES):
        lines = [c["text"] for c in cards if c.get("type") == ctype]
        if lines:
            products[f"scene_water_{ctype}"] = sorted(lines)

    # Per-biome files
    for biome in sorted(all_biomes):
        allowed_types = _BIOME_COMPAT.get(biome, set())
        lines = []
        for card in cards:
            if card.get("type") not in allowed_types:
                continue
            if _card_usable_in_biome(card, biome):
                lines.append(card["text"])
        if lines:
            products[f"scene_water_{biome}"] = sorted(set(lines))

    return products


def _build_discovery(cards: list[dict]) -> dict[str, list[str]]:
    """Split discovery cards into biome-specific product files.

    Returns dict of {filename_without_ext: [lines]}.
    """
    # Collect all biomes
    all_biomes: set[str] = set()
    for card in cards:
        for b in card.get("biomes", ["any"]):
            if b == "any":
                all_biomes.update(_BIOME_COMPAT.keys())
            else:
                all_biomes.add(b)

    products: dict[str, list[str]] = {}

    # Per-type files
    for dtype in sorted(set(c.get("type", "") for c in cards)):
        lines = [c["text"] for c in cards if c.get("type") == dtype]
        if lines:
            products[f"scene_discovery_{dtype}"] = sorted(lines)

    # Per-biome files
    for biome in sorted(all_biomes):
        lines = []
        for card in cards:
            if _card_usable_in_biome(card, biome):
                lines.append(card["text"])
        if lines:
            products[f"scene_discovery_{biome}"] = sorted(set(lines))

    return products


def _write_products(products: dict[str, list[str]], out_dir: pathlib.Path) -> int:
    """Write product files. Returns count of files written."""
    count = 0
    for name, lines in sorted(products.items()):
        fp = out_dir / f"{name}.txt"
        fp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        count += 1
    return count


def build(check_only: bool = False) -> tuple[int, list[str]]:
    """Main build entry point.

    Returns (files_written_or_checked, errors).
    """
    all_errors: list[str] = []
    all_products: dict[str, list[str]] = {}

    # ── Load and validate water ──
    water_path = _SRC_DIR / "water.json"
    water_cards, water_errors = _load_and_validate(water_path)
    all_errors.extend(water_errors)

    # ── Load and validate discovery ──
    disc_path = _SRC_DIR / "discovery.json"
    disc_cards, disc_errors = _load_and_validate(disc_path)
    all_errors.extend(disc_errors)

    if all_errors:
        return 0, all_errors

    # ── Build products ──
    water_products = _build_water(water_cards)
    disc_products = _build_discovery(disc_cards)
    all_products.update(water_products)
    all_products.update(disc_products)

    if check_only:
        # Print summary
        _print_summary(water_cards, disc_cards, all_products)
        return len(all_products), []

    # ── Write products ──
    count = _write_products(all_products, _OUT_DIR)
    _print_summary(water_cards, disc_cards, all_products)
    return count, []


def _print_summary(water: list[dict], disc: list[dict], products: dict[str, list[str]]) -> None:
    """Print build summary."""
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"=== Build Scenes Summary ===")
    print(f"Water source cards: {len(water)}")
    wc = Counter(c.get("type", "?") for c in water)
    for t in sorted(wc):
        print(f"  {t}: {wc[t]}")
    print(f"Discovery source cards: {len(disc)}")
    dc = Counter(c.get("type", "?") for c in disc)
    for t in sorted(dc):
        print(f"  {t}: {dc[t]}")
    print(f"Product files: {len(products)}")
    for name in sorted(products):
        print(f"  {name}.txt: {len(products[name])} lines")


def main() -> None:
    """CLI entry point."""
    sys.stdout.reconfigure(encoding="utf-8")
    check_only = "--check" in sys.argv

    count, errors = build(check_only=check_only)

    if errors:
        print(f"\n=== ERRORS ({len(errors)}) ===", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)

    if check_only:
        print(f"\nCheck passed. {count} product files would be generated.")
    else:
        print(f"\nBuild complete. {count} product files written.")


if __name__ == "__main__":
    main()
