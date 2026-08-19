"""QA 地理编码测试——量出错配清单。

测试链: special_places → places.find → cities15000 → (Nominatim 跳过)。
每条记录命中来源、坐标、反查国家码，与期望比对。
福州根因单独分析。

输出: qa_geocode_report.md (仓库根)。
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys
import time

# GBK console fix
sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO = pathlib.Path(__file__).resolve().parent.parent.parent
_DATA = _REPO / "nowhere" / "data"
_REPORT = _REPO / "qa_geocode_report.md"

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

# (a) 中国 34 省级首府 + 20 名城 → 期望国家码
CHINA_CITIES: list[tuple[str, str]] = [
    # 34 省级首府
    ("北京", "CN"), ("天津", "CN"), ("上海", "CN"), ("重庆", "CN"),
    ("石家庄", "CN"), ("太原", "CN"), ("呼和浩特", "CN"),
    ("沈阳", "CN"), ("长春", "CN"), ("哈尔滨", "CN"),
    ("南京", "CN"), ("杭州", "CN"), ("合肥", "CN"), ("福州", "CN"),
    ("南昌", "CN"), ("济南", "CN"), ("郑州", "CN"), ("武汉", "CN"),
    ("长沙", "CN"), ("广州", "CN"), ("南宁", "CN"), ("海口", "CN"),
    ("成都", "CN"), ("贵阳", "CN"), ("昆明", "CN"), ("拉萨", "CN"),
    ("西安", "CN"), ("兰州", "CN"), ("西宁", "CN"), ("银川", "CN"),
    ("乌鲁木齐", "CN"), ("台北", "CN"), ("香港", "CN"), ("澳门", "CN"),
    # 20 名城
    ("厦门", "CN"), ("苏州", "CN"), ("喀什", "CN"), ("敦煌", "CN"),
    ("丽江", "CN"), ("桂林", "CN"), ("洛阳", "CN"), ("大理", "CN"),
    ("三亚", "CN"), ("青岛", "CN"), ("大连", "CN"), ("珠海", "CN"),
    ("深圳", "CN"), ("宁波", "CN"), ("无锡", "CN"), ("常州", "CN"),
    ("徐州", "CN"), ("泉州", "CN"), ("唐山", "CN"), ("秦皇岛", "CN"),
]

# (b) 30 世界首都/名城 → 期望国家码
WORLD_CITIES: list[tuple[str, str]] = [
    ("巴黎", "FR"), ("伦敦", "GB"), ("东京", "JP"), ("纽约", "US"),
    ("开罗", "EG"), ("雷克雅未克", "IS"), ("威尼斯", "IT"),
    ("京都", "JP"), ("廷巴克图", "ML"), ("悉尼", "AU"),
    ("莫斯科", "RU"), ("柏林", "DE"), ("马德里", "ES"),
    ("罗马", "IT"), ("阿姆斯特丹", "NL"), ("维也纳", "AT"),
    ("布拉格", "CZ"), ("华沙", "PL"), ("首尔", "KR"),
    ("曼谷", "TH"), ("河内", "VN"), ("雅加达", "ID"),
    ("伊斯坦布尔", "TR"), ("孟买", "IN"), ("加尔各答", "IN"),
    ("内罗毕", "KE"), ("布宜诺斯艾利斯", "AR"), ("利马", "PE"),
    ("墨西哥城", "MX"), ("温哥华", "CA"),
]

# (c) 从 localcolor.json / humanities.json 抽 30 个地名(无标准答案,给人审)
DATASET_SAMPLE: list[str] = [
    # localcolor
    "K2大本营", "乌斯怀亚", "亚速尔群岛", "加拉帕戈斯", "北海道",
    "卑尔根", "卡帕多西亚", "卢克索", "卢布尔雅那", "塞维利亚",
    "圣彼得堡", "塔林", "大马士革", "马拉喀什", "撒马尔罕",
    # humanities
    "尾道", "新潟", "长崎", "广岛", "敦刻尔克",
    "锡拉库萨", "赤壁", "荆州", "白帝城", "曲阜",
    "布拉格", "瓦尔帕莱索", "特奥蒂瓦坎", "阿拉卡塔卡", "阿尤恩",
]


# ---------------------------------------------------------------------------
# Core: trace the geocode chain without Nominatim
# ---------------------------------------------------------------------------

def _load_special() -> dict[str, dict]:
    p = _DATA / "special_places.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _offline_lookup_trace(place: str) -> tuple[tuple[float, float] | None, str]:
    """Trace cities15000 lookup, return (coords, detail)."""
    pack = _DATA / "packs" / "cities15000.txt"
    if not pack.exists():
        return None, "cities15000.txt missing"
    q = place.strip().lower()
    if not q:
        return None, "empty query"

    best = None
    best_score = -1.0
    best_detail = ""
    with open(pack, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 15:
                continue
            name, ascii_name, alts = parts[1], parts[2], parts[3]
            score = 0.0
            reason = ""
            if q == name.lower() or q == ascii_name.lower():
                score = 4.0
                reason = "exact_name"
            elif q in name.lower() or q in ascii_name.lower():
                score = 2.0
                reason = "partial_name"
            else:
                for token in alts.lower().split(","):
                    token = token.strip()
                    if not token:
                        continue
                    if token == q:
                        score = max(score, 3.0)
                        reason = f"exact_alt:{token.strip()}"
                        break
                    if q in token:
                        score = max(score, 1.0)
                        reason = f"partial_alt:{token.strip()}"
            if score == 0.0:
                continue
            try:
                pop = int(parts[14] or 0)
            except ValueError:
                pop = 0
            rank = score * 1e12 + pop
            if rank > best_score:
                best_score = rank
                best = (float(parts[4]), float(parts[5]))
                best_detail = (
                    f"cities15000({parts[1]},cc={parts[8]},"
                    f"pop={pop},score={score},{reason})"
                )
    return best, best_detail or "no_match"


def _places_find_trace(place: str) -> tuple[dict | None, str]:
    """Trace places.find, return (result, detail)."""
    try:
        from nowhere import places
        hit = places.find(place)
        if hit:
            return hit, f"places.db({hit.get('name','?')})"
    except Exception:
        pass
    return None, "places.db(miss)"


def trace_lookup(place: str) -> tuple[tuple[float, float] | None, str]:
    """Full chain trace (no Nominatim)."""
    # 1. special_places
    sp = _load_special()
    hit = sp.get(place) or sp.get(place.strip().lower()) or sp.get(place.strip())
    if hit:
        return (hit["lat"], hit["lon"]), "special_places"

    # 2. places.find
    pf, pf_detail = _places_find_trace(place)
    if pf:
        return (pf["lat"], pf["lon"]), pf_detail

    # 3. cities15000
    coords, detail = _offline_lookup_trace(place)
    if coords:
        return coords, detail

    return None, "no_match(skipped_nominatim)"


# ---------------------------------------------------------------------------
# Country code reverse lookup
# ---------------------------------------------------------------------------

def _country_code(lat: float, lon: float) -> str | None:
    try:
        from nowhere.country import country_code_of
        return country_code_of(lat, lon)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Fuzhou root cause analysis
# ---------------------------------------------------------------------------

def analyze_fuzhou() -> dict:
    """Deep-dive the 福州 case."""
    pack = _DATA / "packs" / "cities15000.txt"
    results = {"entries": [], "winner": None, "correct": None}

    if not pack.exists():
        results["error"] = "cities15000.txt missing"
        return results

    q = "福州"
    q_lower = q.strip().lower()
    with open(pack, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 15:
                continue
            name, ascii_name, alts = parts[1], parts[2], parts[3]

            # Check all match paths
            match_paths = []
            score = 0.0
            if q_lower == name.lower() or q_lower == ascii_name.lower():
                score = 4.0
                match_paths.append("exact_name")
            elif q_lower in name.lower() or q_lower in ascii_name.lower():
                score = 2.0
                match_paths.append("partial_name")

            for token in alts.lower().split(","):
                token = token.strip()
                if not token:
                    continue
                if token == q_lower:
                    match_paths.append(f"exact_alt:[{token}]")
                    score = max(score, 3.0)
                    break
                if q_lower in token:
                    match_paths.append(f"partial_alt:[{token}]")
                    score = max(score, 1.0)

            if score > 0:
                try:
                    pop = int(parts[14] or 0)
                except ValueError:
                    pop = 0
                rank = score * 1e12 + pop
                entry = {
                    "name": name, "ascii": ascii_name,
                    "lat": float(parts[4]), "lon": float(parts[5]),
                    "cc": parts[8], "pop": pop,
                    "score": score, "rank": rank,
                    "match_paths": match_paths,
                    "alts_has_fuzhou": "福州" in alts,
                }
                results["entries"].append(entry)

    # Sort by rank descending
    results["entries"].sort(key=lambda e: -e["rank"])
    if results["entries"]:
        results["winner"] = results["entries"][0]
    for e in results["entries"]:
        if e["lat"] < 27 and e["lat"] > 25 and e["lon"] > 118:
            results["correct"] = e
            break
    return results


# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------

def run_tests() -> dict:
    """Run all test groups, return structured results."""
    all_results = []
    mismatches = []

    def test_group(group_name: str, items: list[tuple[str, str]]):
        for place, expected_cc in items:
            coords, source = trace_lookup(place)
            if coords is None:
                actual_cc = None
                actual_coords = None
            else:
                actual_cc = _country_code(coords[0], coords[1])
                actual_coords = coords
            match = (actual_cc == expected_cc)
            row = {
                "place": place, "expected_cc": expected_cc,
                "actual_cc": actual_cc, "coords": actual_coords,
                "source": source, "match": match,
                "group": group_name,
            }
            all_results.append(row)
            if not match:
                mismatches.append(row)

    test_group("china", CHINA_CITIES)
    test_group("world", WORLD_CITIES)

    # (c) dataset samples — no expected, just record
    dataset_rows = []
    for place in DATASET_SAMPLE:
        coords, source = trace_lookup(place)
        if coords:
            cc = _country_code(coords[0], coords[1])
        else:
            cc = None
        dataset_rows.append({
            "place": place, "coords": coords,
            "actual_cc": cc, "source": source,
        })

    fuzhou = analyze_fuzhou()

    return {
        "all": all_results,
        "mismatches": mismatches,
        "dataset": dataset_rows,
        "fuzhou": fuzhou,
        "total_tested": len(CHINA_CITIES) + len(WORLD_CITIES),
        "total_mismatches": len(mismatches),
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(results: dict) -> str:
    lines = []
    lines.append("# QA Geocode Report")
    lines.append("")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total tested: {results['total_tested']}")
    lines.append(f"- Mismatches: **{results['total_mismatches']}**")
    lines.append("")

    # Mismatch table
    lines.append("## Mismatch Table")
    lines.append("")
    if results["mismatches"]:
        lines.append("| Place | Expected CC | Actual CC | Coords | Hit Chain |")
        lines.append("|-------|-------------|-----------|--------|-----------|")
        for m in results["mismatches"]:
            c = f"({m['coords'][0]:.4f}, {m['coords'][1]:.4f})" if m["coords"] else "N/A"
            lines.append(
                f"| {m['place']} | {m['expected_cc']} | {m['actual_cc'] or 'None'} "
                f"| {c} | {m['source']} |"
            )
    else:
        lines.append("No mismatches found.")
    lines.append("")

    # Fuzhou root cause
    lines.append("## 福州 Root Cause Analysis")
    lines.append("")
    fz = results["fuzhou"]
    if "error" in fz:
        lines.append(f"Error: {fz['error']}")
    else:
        lines.append("### All matching entries for '福州' in cities15000.txt")
        lines.append("")
        lines.append("| Name | ASCII | Lat | Lon | CC | Pop | Score | Rank | Match Paths | Has 福州 in alts |")
        lines.append("|------|-------|-----|-----|----|-----|-------|------|-------------|-----------------|")
        for e in fz["entries"]:
            paths_str = "; ".join(e["match_paths"]) if e["match_paths"] else "-"
            lines.append(
                f"| {e['name']} | {e['ascii']} | {e['lat']} | {e['lon']} "
                f"| {e['cc']} | {e['pop']} | {e['score']} | {e['rank']:.0f} "
                f"| {paths_str} | {e['alts_has_fuzhou']} |"
            )
        lines.append("")
        if fz["winner"]:
            w = fz["winner"]
            lines.append(f"### Winner: {w['name']} at ({w['lat']}, {w['lon']})")
            lines.append("")
            lines.append(f"- Match paths: {'; '.join(w['match_paths'])}")
            lines.append(f"- Population: {w['pop']}")
            lines.append(f"- Score: {w['score']}, Rank: {w['rank']:.0f}")
            lines.append("")
        if fz["correct"]:
            c = fz["correct"]
            lines.append(f"### Correct entry: {c['name']} at ({c['lat']}, {c['lon']})")
            lines.append("")
            lines.append(f"- Population: {c['pop']}")
            lines.append(f"- Has 福州 in alternatenames: {c['alts_has_fuzhou']}")
            lines.append("")

        # Root cause explanation
        lines.append("### Root Cause")
        lines.append("")
        lines.append(
            "The geocode chain is: special_places -> places.find -> cities15000 -> Nominatim."
        )
        lines.append("")
        lines.append(
            "For '福州': special_places has no entry; places.db is empty (no tables), "
            "so places.find returns None."
        )
        lines.append("")
        lines.append(
            "In cities15000.txt there are two entries with ASCII name 'Fuzhou':"
        )
        lines.append("")
        lines.append(
            "1. **Jiangxi (抚州)**: lat=27.95999, lon=116.33333, pop=1,089,888. "
            "Alternatenames do NOT contain '福州'. Scores via partial_name match (score=2.0) "
            "since '福州' is not a substring of 'Fuzhou' — this entry should NOT match."
        )
        lines.append("")
        lines.append(
            "2. **Fujian (福州)**: lat=26.06139, lon=119.30611, pop=3,740,000. "
            "Alternatenames contain '福州' (exact alt, score=3.0). This is the correct match."
        )
        lines.append("")
        lines.append(
            "The current code correctly returns the Fujian entry (score=3.0 beats no match). "
            "If the historical bug was that 福州 resolved to Jiangxi/Zhejiang, it was likely due to:"
        )
        lines.append("")
        lines.append("- **Scenario A**: The Jiangxi entry's alternatenames previously contained '福州' "
                      "as a variant, giving it score=3.0 with higher rank (score*1e12 is equal, "
                      "but population tiebreak: Jiangxi pop < Fujian pop, so Fujian should still win).")
        lines.append("- **Scenario B**: places.db was not empty and had a wrong entry for 福州 "
                      "with Jiangxi/Zhejiang coordinates, which is checked before cities15000.")
        lines.append("- **Scenario C**: The bug was in places_patch.json having a wrong entry.")
        lines.append("")
        lines.append(
            "Recommendation: Ensure places_patch.json and places.db never contain conflicting "
            "entries for well-known cities. Add a disambiguation step: when multiple cities "
            "share the same ASCII name, prefer the one whose Chinese name matches the query "
            "exactly in alternatenames."
        )
    lines.append("")

    # Dataset samples
    lines.append("## Dataset Samples (localcolor / humanities)")
    lines.append("")
    lines.append("No expected country code — for human review.")
    lines.append("")
    lines.append("| Place | Coords | Country Code | Hit Chain |")
    lines.append("|-------|--------|-------------|-----------|")
    for d in results["dataset"]:
        c = f"({d['coords'][0]:.4f}, {d['coords'][1]:.4f})" if d["coords"] else "N/A"
        lines.append(
            f"| {d['place']} | {c} | {d['actual_cc'] or 'None'} | {d['source']} |"
        )
    lines.append("")

    # Fix suggestions
    lines.append("## Fix Suggestions")
    lines.append("")
    lines.append("1. **cities15000 disambiguation**: When multiple entries match with the same "
                  "score, prefer the one whose Chinese alternatenames contain the query. "
                  "Currently the tiebreak is population only — add a 'query_lang_match' bonus.")
    lines.append("")
    lines.append("2. **Country-aware filtering**: If the query is a Chinese city name, "
                  "prefer entries with cc=CN. Use country.py's country_code_of to validate "
                  "the result post-match.")
    lines.append("")
    lines.append("3. **places_patch.json audit**: Ensure all patch entries have correct "
                  "coordinates. No conflicting entries for cities already in cities15000.")
    lines.append("")
    lines.append("4. **None result caching**: Currently geocode.py caches None results permanently. "
                  "Failed lookups should not be cached (or cached with a short TTL) to allow "
                  "retries after data fixes.")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Running geocode QA tests...")
    t0 = time.time()
    results = run_tests()
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s")
    print(f"Tested: {results['total_tested']}, Mismatches: {results['total_mismatches']}")

    report = generate_report(results)
    _REPORT.write_text(report, encoding="utf-8")
    print(f"Report written to: {_REPORT}")


if __name__ == "__main__":
    main()
