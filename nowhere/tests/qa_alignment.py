"""Card 23: 风俗/内容错配体检 — 八亚种审计脚本(只量不修)。

Usage:
    cd C:\\Users\\84989\\Desktop\\nowhere_repo
    python nowhere/tests/qa_alignment.py

输出: qa_alignment_report.md (仓库根)
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import sys

# GBK console fix
sys.stdout.reconfigure(encoding="utf-8")

_REPO = pathlib.Path(__file__).resolve().parent.parent.parent
_DATA = _REPO / "nowhere" / "data"
_REPORT = _REPO / "qa_alignment_report.md"

# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _haversine_km(a_lat, a_lon, b_lat, b_lon):
    lat1, lon1, lat2, lon2 = map(math.radians, (a_lat, a_lon, b_lat, b_lon))
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def _load_json(fp: pathlib.Path):
    if not fp.exists():
        return {}
    return json.loads(fp.read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════════════════
# 1. Cultural Region Rectangles (文化区矩形)
# ═══════════════════════════════════════════════════════════════════════

# Copy of describe.py _REGION_MAP
_DESCRIBE_REGION_MAP = [
    (43, 50, 5, 18, "alpine"),
    (35, 70, -15, 40, "europe"),
    (45, 70, 20, 180, "russia"),
    (20, 55, 73, 145, "east_asia"),
    (-10, 25, 90, 155, "southeast_asia"),
    (5, 35, 60, 100, "south_asia"),
    (10, 45, 25, 65, "middle_east"),
    (-35, 37, -20, 55, "africa"),
    (10, 70, -170, -50, "north_america"),
    (-55, 15, -85, -35, "south_america"),
    (-50, 0, 110, 180, "oceania"),
    (66, 90, -180, 180, "arctic"),
]


def _describe_region(lat, lon):
    for lat_min, lat_max, lon_min, lon_max, region in _DESCRIBE_REGION_MAP:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return region
    return "any"


# Copy of encounters.py _region_for
def _encounter_region(lat, lon):
    if lat > 60 or lat < -60:
        return "polar"
    if -35 <= lat <= 32 and -20 <= lon <= 55:
        return "africa"
    if 35 <= lat <= 55 and 26 <= lon <= 60:
        return "asia"
    if 0 <= lat <= 55 and 60 <= lon <= 150:
        return "asia"
    if -55 <= lat <= 70 and -170 <= lon <= -30:
        return "americas"
    if -50 <= lat <= 0 and 110 <= lon <= 180:
        return "oceania"
    if 35 <= lat <= 72 and -15 <= lon <= 40:
        return "europe"
    return "natural"


# 200 world cities: (name_zh, lat, lon, expected_region_for_describe, expected_encounter_region)
# expected = None means "any region is acceptable"
CITIES_200 = [
    # ---- Known 5 must-be-✗ ----
    ("第比利斯", 41.72, 44.78, "europe", "asia"),       # Caucasus: not middle_east
    ("埃里温", 40.18, 44.51, "europe", "asia"),          # Caucasus: not middle_east
    ("阿拉木图", 43.24, 76.95, "central_asia", "asia"),  # not east_asia
    ("加德满都", 27.70, 85.32, "south_asia", "asia"),     # not east_asia
    ("雷克雅未克", 64.13, -21.90, "europe", "polar"),     # not any
    # ---- Europe ----
    ("巴黎", 48.86, 2.35, "europe", "europe"),
    ("伦敦", 51.51, -0.13, "europe", "europe"),
    ("柏林", 52.52, 13.41, "europe", "europe"),
    ("罗马", 41.90, 12.50, "europe", "europe"),
    ("马德里", 40.42, -3.70, "europe", "europe"),
    ("里斯本", 38.72, -9.14, "europe", "europe"),
    ("阿姆斯特丹", 52.37, 4.90, "europe", "europe"),
    ("维也纳", 48.21, 16.37, "europe", "europe"),
    ("布拉格", 50.08, 14.44, "europe", "europe"),
    ("华沙", 52.23, 21.01, "europe", "europe"),
    ("雅典", 37.98, 23.73, "europe", "europe"),
    ("莫斯科", 55.76, 37.62, "russia", "europe"),
    ("圣彼得堡", 59.93, 30.32, "russia", "europe"),
    ("赫尔辛基", 60.17, 24.94, "europe", "europe"),
    ("斯德哥尔摩", 59.33, 18.07, "europe", "europe"),
    ("奥斯陆", 59.91, 10.75, "europe", "europe"),
    ("哥本哈根", 55.68, 12.57, "europe", "europe"),
    ("都柏林", 53.35, -6.26, "europe", "europe"),
    ("布鲁塞尔", 50.85, 4.35, "europe", "europe"),
    ("苏黎世", 47.38, 8.54, "europe", "europe"),
    ("慕尼黑", 48.14, 11.58, "europe", "europe"),
    ("巴塞罗那", 41.39, 2.17, "europe", "europe"),
    ("米兰", 45.46, 9.19, "europe", "europe"),
    ("那不勒斯", 40.85, 14.27, "europe", "europe"),
    ("佛罗伦萨", 43.77, 11.25, "europe", "europe"),
    ("威尼斯", 45.44, 12.34, "europe", "europe"),
    ("爱丁堡", 55.95, -3.19, "europe", "europe"),
    ("布达佩斯", 47.50, 19.04, "europe", "europe"),
    ("克拉科夫", 50.06, 19.94, "europe", "europe"),
    ("萨格勒布", 45.81, 15.98, "europe", "europe"),
    ("贝尔格莱德", 44.79, 20.47, "europe", "europe"),
    ("索非亚", 42.70, 23.32, "europe", "europe"),
    ("布加勒斯特", 44.43, 26.10, "europe", "europe"),
    ("基辅", 50.45, 30.52, "europe", "europe"),
    ("里加", 56.95, 24.11, "europe", "europe"),
    ("塔林", 59.44, 24.75, "europe", "europe"),
    ("维尔纽斯", 54.69, 25.28, "europe", "europe"),
    ("杜布罗夫尼克", 42.65, 18.09, "europe", "europe"),
    # ---- Middle East ----
    ("伊斯坦布尔", 41.01, 28.98, "europe", "europe"),  # Western side
    ("安卡拉", 39.93, 32.85, "middle_east", "asia"),
    ("德黑兰", 35.69, 51.39, "middle_east", "asia"),
    ("巴格达", 33.31, 44.37, "middle_east", "asia"),
    ("利雅得", 24.71, 46.68, "middle_east", "asia"),
    ("迪拜", 25.20, 55.27, "middle_east", "asia"),
    ("多哈", 25.29, 51.53, "middle_east", "asia"),
    ("贝鲁特", 33.89, 35.50, "middle_east", "asia"),
    ("安曼", 31.95, 35.93, "middle_east", "asia"),
    ("耶路撒冷", 31.77, 35.23, "middle_east", "asia"),
    ("马斯喀特", 23.59, 58.54, "middle_east", "asia"),
    ("科威特城", 29.38, 47.99, "middle_east", "asia"),
    ("大马士革", 33.51, 36.29, "middle_east", "asia"),
    # ---- East Asia ----
    ("北京", 39.90, 116.40, "east_asia", "asia"),
    ("上海", 31.23, 121.47, "east_asia", "asia"),
    ("东京", 35.68, 139.69, "east_asia", "asia"),
    ("首尔", 37.57, 126.98, "east_asia", "asia"),
    ("大阪", 34.69, 135.50, "east_asia", "asia"),
    ("京都", 35.01, 135.77, "east_asia", "asia"),
    ("台北", 25.03, 121.57, "east_asia", "asia"),
    ("香港", 22.32, 114.17, "east_asia", "asia"),
    ("澳门", 22.20, 113.55, "east_asia", "asia"),
    ("广州", 23.13, 113.26, "east_asia", "asia"),
    ("成都", 30.57, 104.07, "east_asia", "asia"),
    ("西安", 34.26, 108.94, "east_asia", "asia"),
    ("杭州", 30.27, 120.15, "east_asia", "asia"),
    ("重庆", 29.56, 106.55, "east_asia", "asia"),
    ("武汉", 30.59, 114.31, "east_asia", "asia"),
    ("南京", 32.06, 118.80, "east_asia", "asia"),
    ("深圳", 22.54, 114.06, "east_asia", "asia"),
    ("乌兰巴托", 47.89, 106.91, "east_asia", "asia"),
    ("平壤", 39.02, 125.75, "east_asia", "asia"),
    # ---- Southeast Asia ----
    ("曼谷", 13.76, 100.50, "southeast_asia", "asia"),
    ("河内", 21.03, 105.85, "southeast_asia", "asia"),
    ("胡志明", 10.82, 106.63, "southeast_asia", "asia"),
    ("新加坡", 1.35, 103.82, "southeast_asia", "asia"),
    ("雅加达", -6.21, 106.85, "southeast_asia", "asia"),
    ("马尼拉", 14.60, 120.98, "southeast_asia", "asia"),
    ("吉隆坡", 3.14, 101.69, "southeast_asia", "asia"),
    ("金边", 11.56, 104.92, "southeast_asia", "asia"),
    ("仰光", 16.87, 96.20, "southeast_asia", "asia"),
    ("万象", 17.97, 102.63, "southeast_asia", "asia"),
    ("岘港", 16.05, 108.22, "southeast_asia", "asia"),
    ("暹粒", 13.36, 103.86, "southeast_asia", "asia"),
    ("巴厘岛", -8.34, 115.09, "southeast_asia", "asia"),
    # ---- South Asia ----
    ("孟买", 19.08, 72.88, "south_asia", "asia"),
    ("德里", 28.61, 77.21, "south_asia", "asia"),
    ("新德里", 28.61, 77.23, "south_asia", "asia"),
    ("科伦坡", 6.93, 79.86, "south_asia", "asia"),
    ("达卡", 23.81, 90.41, "south_asia", "asia"),
    ("卡拉奇", 24.86, 67.01, "south_asia", "asia"),
    ("伊斯兰堡", 33.69, 73.04, "south_asia", "asia"),
    ("拉合尔", 31.55, 74.35, "south_asia", "asia"),
    ("瓦拉纳西", 25.32, 83.01, "south_asia", "asia"),
    ("加尔各答", 22.57, 88.36, "south_asia", "asia"),
    ("班加罗尔", 12.97, 77.59, "south_asia", "asia"),
    ("廷布", 27.47, 89.64, "south_asia", "asia"),
    # ---- Africa ----
    ("开罗", 30.04, 31.24, "africa", "africa"),
    ("开普敦", -33.93, 18.42, "africa", "africa"),
    ("内罗毕", -1.29, 36.82, "africa", "africa"),
    ("拉各斯", 6.52, 3.38, "africa", "africa"),
    ("约翰内斯堡", -26.20, 28.05, "africa", "africa"),
    ("马拉喀什", 31.63, -8.01, "africa", "africa"),
    ("卡萨布兰卡", 33.57, -7.59, "africa", "africa"),
    ("亚的斯亚贝巴", 9.02, 38.75, "africa", "africa"),
    ("达累斯萨拉姆", -6.79, 39.28, "africa", "africa"),
    ("阿克拉", 5.56, -0.19, "africa", "africa"),
    ("达喀尔", 14.69, -17.44, "africa", "africa"),
    ("的黎波里", 32.90, 13.18, "africa", "africa"),
    ("突尼斯", 36.81, 10.17, "africa", "africa"),
    ("阿尔及尔", 36.75, 3.04, "africa", "africa"),
    ("金沙萨", -4.44, 15.27, "africa", "africa"),
    ("亚历山大", 31.20, 29.92, "africa", "africa"),
    ("桑给巴尔", -6.17, 39.19, "africa", "africa"),
    # ---- Americas ----
    ("纽约", 40.71, -74.01, "north_america", "americas"),
    ("洛杉矶", 34.05, -118.24, "north_america", "americas"),
    ("芝加哥", 41.88, -87.63, "north_america", "americas"),
    ("旧金山", 37.77, -122.42, "north_america", "americas"),
    ("华盛顿", 38.91, -77.04, "north_america", "americas"),
    ("迈阿密", 25.76, -80.19, "north_america", "americas"),
    ("休斯敦", 29.76, -95.37, "north_america", "americas"),
    ("多伦多", 43.65, -79.38, "north_america", "americas"),
    ("温哥华", 49.28, -123.12, "north_america", "americas"),
    ("蒙特利尔", 45.50, -73.57, "north_america", "americas"),
    ("墨西哥城", 19.43, -99.13, "north_america", "americas"),
    ("哈瓦那", 23.11, -82.37, "north_america", "americas"),
    ("波哥大", 4.71, -74.07, "south_america", "americas"),
    ("利马", -12.05, -77.04, "south_america", "americas"),
    ("圣地亚哥", -33.45, -70.67, "south_america", "americas"),
    ("布宜诺斯艾利斯", -34.60, -58.38, "south_america", "americas"),
    ("里约", -22.91, -43.17, "south_america", "americas"),
    ("圣保罗", -23.55, -46.63, "south_america", "americas"),
    ("亚松森", -25.26, -57.58, "south_america", "americas"),
    ("蒙得维的亚", -34.88, -56.17, "south_america", "americas"),
    ("乌斯怀亚", -54.80, -68.30, "south_america", "americas"),
    ("基多", -0.18, -78.47, "south_america", "americas"),
    ("加拉加斯", 10.48, -66.90, "south_america", "americas"),
    ("危地马拉城", 14.63, -90.51, "north_america", "americas"),
    ("巴拿马城", 8.98, -79.52, "north_america", "americas"),
    # ---- Oceania ----
    ("悉尼", -33.87, 151.21, "oceania", "oceania"),
    ("墨尔本", -37.81, 144.96, "oceania", "oceania"),
    ("奥克兰", -36.85, 174.76, "oceania", "oceania"),
    ("惠灵顿", -41.29, 174.78, "oceania", "oceania"),
    ("珀斯", -31.95, 115.86, "oceania", "oceania"),
    ("布里斯班", -27.47, 153.03, "oceania", "oceania"),
    ("基督城", -43.53, 172.64, "oceania", "oceania"),
    ("苏瓦", -18.14, 178.44, "oceania", "oceania"),
    ("莫尔兹比港", -9.48, 147.15, "oceania", "oceania"),
    # ---- Russia / Central Asia ----
    ("新西伯利亚", 55.04, 82.93, "russia", "asia"),
    ("叶卡捷琳堡", 56.84, 60.60, "russia", "asia"),
    ("符拉迪沃斯托克", 43.12, 131.87, "russia", "asia"),
    ("塔什干", 41.30, 69.28, "middle_east", "asia"),
    ("比什凯克", 42.87, 74.59, "east_asia", "asia"),
    ("杜尚别", 38.56, 68.77, "middle_east", "asia"),
    ("阿什哈巴德", 37.95, 58.38, "middle_east", "asia"),
    # ---- Edge cases / borders ----
    ("安塔利亚", 36.90, 30.70, "middle_east", "asia"),
    ("伊兹密尔", 38.42, 27.14, "europe", "europe"),  # lon 27.14 in europe rect
    ("塞浦路斯", 35.13, 33.38, "middle_east", "asia"),  # lon 33.38 middle_east
    ("克里特岛", 35.24, 24.47, "europe", "europe"),
    ("西西里", 37.60, 14.01, "europe", "europe"),
    ("法鲁", 37.02, -7.94, "europe", "europe"),
    ("直布罗陀", 36.14, -5.35, "europe", "europe"),
    # ---- Polar / Arctic ----
    ("朗伊尔城", 78.22, 15.63, "arctic", "polar"),
    ("特罗姆瑟", 69.65, 18.96, "arctic", "polar"),
    ("摩尔曼斯克", 68.97, 33.07, "arctic", "polar"),
    ("安克雷奇", 61.22, -149.90, "arctic", "polar"),
    # ---- Southern hemisphere extras ----
    ("约翰内斯堡2", -26.20, 28.05, "africa", "africa"),
    ("利隆圭", -13.96, 33.77, "africa", "africa"),
    ("马普托", -25.97, 32.57, "africa", "africa"),
    ("温得和克", -22.56, 17.08, "africa", "africa"),
    ("努美阿", -22.28, 166.46, "oceania", "oceania"),
    # ---- More Asian edge ----
    ("喀什", 39.47, 75.99, "east_asia", "asia"),        # lon 75.99: south_asia? east_asia?
    ("乌鲁木齐", 43.83, 87.62, "east_asia", "asia"),
    ("拉萨", 29.65, 91.10, "east_asia", "asia"),         # lon 91: southeast_asia?
    ("兰州", 36.06, 103.83, "east_asia", "asia"),
    ("哈尔滨", 45.80, 126.53, "east_asia", "asia"),
    ("敦煌", 40.14, 94.66, "east_asia", "asia"),
    # ---- More edge ----
    ("特拉维夫", 32.07, 34.78, "middle_east", "asia"),
    ("阿布扎比", 24.45, 54.37, "middle_east", "asia"),
    ("马尔代夫", 4.17, 73.51, "south_asia", "asia"),
    ("斯里兰卡", 6.93, 79.86, "south_asia", "asia"),
    ("不丹", 27.47, 89.64, "south_asia", "asia"),
    ("尼泊尔", 27.70, 85.32, "south_asia", "asia"),
]


def audit_1_region_rectangles():
    """Sub-type 1: Cultural Region Rectangles."""
    mismatches = []
    known_five = []

    for name, lat, lon, expected_d, expected_e in CITIES_200:
        actual_d = _describe_region(lat, lon)
        actual_e = _encounter_region(lat, lon)

        issues = []

        # Check describe.py region vs expected
        if expected_d and actual_d != expected_d:
            issues.append(f"describe: got {actual_d}, expected {expected_d}")

        # Check encounters.py region vs expected
        if expected_e and actual_e != expected_e:
            issues.append(f"encounters: got {actual_e}, expected {expected_e}")

        # Check two systems disagree with each other
        d_to_e_map = {
            "europe": "europe", "middle_east": "asia", "east_asia": "asia",
            "southeast_asia": "asia", "south_asia": "asia", "africa": "africa",
            "north_america": "americas", "south_america": "americas",
            "oceania": "oceania", "russia": "europe", "arctic": "polar",
            "any": None, "alpine": "europe", "central_asia": "asia",
        }
        expected_encounter = d_to_e_map.get(actual_d)
        if expected_encounter and actual_e != expected_encounter:
            issues.append(f"两套不一致: describe={actual_d} vs encounters={actual_e}")

        if issues:
            entry = {"city": name, "lat": lat, "lon": lon,
                     "describe": actual_d, "encounters": actual_e,
                     "issues": issues}
            mismatches.append(entry)
            if name in ("第比利斯", "埃里温", "阿拉木图", "加德满都", "雷克雅未克"):
                known_five.append(entry)

    return mismatches, known_five


# ═══════════════════════════════════════════════════════════════════════
# 2. Place Name Key Drift (地名键漂移)
# ═══════════════════════════════════════════════════════════════════════

def audit_2_key_drift():
    """Sub-type 2: Cross-reference keys across data files."""
    lc_main = _load_json(_DATA / "localcolor.json")
    lc_china = _load_json(_DATA / "localcolor_china.json")
    lc_japan = _load_json(_DATA / "localcolor_japan_korea_sea.json")
    lc_americas = _load_json(_DATA / "localcolor_americas_africa_oceania.json")

    hum_raw = _load_json(_DATA / "humanities.json")
    hum_places = hum_raw.get("places", {})
    hum_aliases = hum_raw.get("aliases", {})
    hum_films = _load_json(_DATA / "humanities_films.json")
    hum_historical = _load_json(_DATA / "humanities_historical.json")

    idx = _load_json(_DATA / "explorable_index.json")
    idx_places = idx.get("places", {})

    # Merge all localcolor keys
    lc_all = set(lc_main.keys())
    for regional in [lc_china, lc_japan, lc_americas]:
        lc_all.update(regional.keys())

    # Merge all humanities keys
    hum_all = set(hum_places.keys())
    for regional in [hum_films, hum_historical]:
        if "places" in regional and isinstance(regional["places"], dict):
            hum_all.update(regional["places"].keys())
        else:
            for k in regional.keys():
                if not k.startswith("_"):
                    hum_all.add(k)

    # Index keys (exclude region-level entries like "africa", "asia" etc.)
    region_tags = {"africa", "americas", "art", "asia", "europe", "natural", "polar"}
    idx_keys = set(k for k in idx_places.keys() if k not in region_tags)

    findings = []

    # A) Keys in index but not in any data source
    idx_no_lc = idx_keys - lc_all - hum_all
    for k in sorted(idx_no_lc):
        entry = idx_places.get(k, {})
        has_layer = entry.get("layers", {})
        if has_layer.get("localcolor") or has_layer.get("humanities"):
            findings.append({
                "type": "索引有但数据无",
                "key": k,
                "detail": f"explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到",
                "severity": "实锤",
            })

    # B) Keys in data but not in index
    data_no_idx = (lc_all | hum_all) - idx_keys
    for k in sorted(data_no_idx):
        findings.append({
            "type": "数据有但索引无",
            "key": k,
            "detail": f"localcolor/humanities 有卡, 但 explorable_index 没收录",
            "severity": "可疑",
        })

    # C) Alias vs actual key conflicts
    for alias, canonical in hum_aliases.items():
        if canonical not in hum_all:
            findings.append({
                "type": "别名指向不存在的键",
                "key": alias,
                "detail": f"alias {alias} -> {canonical}, 但 {canonical} 不在 humanities places 里",
                "severity": "实锤",
            })

    # D) Near-duplicate keys (manual check list)
    all_keys = lc_all | hum_all | idx_keys
    # Common drift patterns
    drift_patterns = [
        ("喀什", "喀什地区"), ("喀什", "Kashgar"),
        ("凤凰", "凤凰古城"),
        ("敦煌", "Dunhuang"),
        ("丽江", "Lijiang"),
    ]
    for a, b in drift_patterns:
        if a in all_keys and b in all_keys:
            findings.append({
                "type": "疑似一地多名",
                "key": f"{a} / {b}",
                "detail": f"两个键可能指向同一地方, 需人工确认",
                "severity": "人审",
            })

    return findings


# ═══════════════════════════════════════════════════════════════════════
# 3. Country Code Boundary Errors (国家码边界错)
# ═══════════════════════════════════════════════════════════════════════

def audit_3_country_codes():
    """Sub-type 3: food_by_country key vs city country_code_of."""
    food = _load_json(_DATA / "food_by_country.json")
    findings = []

    # Overseas territories that need human review
    overseas = {
        "RE": "留尼汪 (法国海外省)",
        "PF": "法属波利尼西亚",
        "HK": "香港 (中国特别行政区)",
        "MO": "澳门 (中国特别行政区)",
        "GP": "瓜德罗普 (法国海外省)",
        "PR": "波多黎各 (美国领地)",
        "NC": "新喀里多尼亚 (法国海外属地)",
        "GI": "直布罗陀 (英国海外领地)",
        "XK": "科索沃 (争议地位)",
        "DD": "东德 (已不存在)",
        "GL": "格陵兰 (丹麦自治领)",
    }

    for cc, desc in overseas.items():
        if cc in food:
            items = food[cc]
            zh_names = [i.get("zh", "") or i.get("en", "") for i in items[:3]]
            findings.append({
                "type": "海外领地/争议地区",
                "code": cc,
                "detail": f"{desc}: food_by_country 有 {len(items)} 道菜 ({', '.join(zh_names[:3])})",
                "severity": "人审",
            })

    # Flag empty zh entries (card 5 overlap)
    empty_zh_count = 0
    empty_zh_samples = []
    for cc, items in food.items():
        for item in items:
            if not item.get("zh", "").strip():
                empty_zh_count += 1
                if len(empty_zh_samples) < 20:
                    empty_zh_samples.append(f"{cc}: {item.get('en', '?')}")

    if empty_zh_count > 0:
        findings.append({
            "type": "zh空串条目",
            "code": "多国",
            "detail": f"共 {empty_zh_count} 条食物 zh 为空串, 渲染时会混入英文菜名",
            "severity": "实锤",
        })

    # DD (East Germany) is anachronistic
    if "DD" in food:
        findings.append({
            "type": "已不存在的国家码",
            "code": "DD",
            "detail": f"东德(DD)已不存在, food_by_country 有 {len(food['DD'])} 道菜",
            "severity": "实锤",
        })

    return findings, empty_zh_samples


# ═══════════════════════════════════════════════════════════════════════
# 4. Calendar Drift (历法漂移)
# ═══════════════════════════════════════════════════════════════════════

def audit_4_calendar():
    """Sub-type 4: Hardcoded religious dates and hemisphere issues."""
    findings = []

    # Load all localcolor and humanities data for text scanning
    all_texts = []

    # localcolor files
    for fname in ["localcolor.json", "localcolor_china.json",
                   "localcolor_japan_korea_sea.json",
                   "localcolor_americas_africa_oceania.json"]:
        data = _load_json(_DATA / fname)
        for place, entry in data.items():
            for cat in ("物产", "声音", "痕迹", "美食", "节律", "感受", "植被"):
                items = entry.get(cat, [])
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, str):
                            all_texts.append((place, cat, item))
                        elif isinstance(item, dict):
                            all_texts.append((place, cat, item.get("text", "")))
                elif isinstance(items, str):
                    all_texts.append((place, cat, items))

    # humanities files
    for fname in ["humanities.json", "humanities_films.json",
                   "humanities_historical.json"]:
        raw = _load_json(_DATA / fname)
        places = raw.get("places", raw)
        for place, entry in places.items():
            if place.startswith("_"):
                continue
            if not isinstance(entry, dict):
                continue
            for cat in ("事件", "人物", "作品"):
                cards = entry.get(cat, [])
                if isinstance(cards, list):
                    for card in cards:
                        if isinstance(card, dict):
                            all_texts.append((place, cat, card.get("text", "")))

    # Islamic calendar keywords (hardcoded month = always wrong for some year)
    islamic_keywords = ["斋月", "开斋节", "古尔邦节", "宰牲节", "圣纪节"]
    # Chinese calendar keywords
    chinese_calendar = ["春节", "藏历新年", "中秋", "端午", "清明", "重阳"]
    # Southern hemisphere Christmas = snow issue
    southern_christmas_kw = ["圣诞", "雪花", "雪人", "白色圣诞"]

    for place, cat, text in all_texts:
        if not text:
            continue

        # Islamic holidays with hardcoded month references
        for kw in islamic_keywords:
            if kw in text:
                # Check if there's a month number nearby
                month_match = re.search(r'(\d{1,2})月', text)
                if month_match:
                    findings.append({
                        "type": "伊斯兰历硬编码月份",
                        "place": place,
                        "cat": cat,
                        "text": text[:80],
                        "detail": f"提到 {kw} 且有 {month_match.group(0)}, 伊斯兰历每年偏移~11天",
                        "severity": "实锤",
                    })
                else:
                    findings.append({
                        "type": "伊斯兰历节日提及",
                        "place": place,
                        "cat": cat,
                        "text": text[:80],
                        "detail": f"提到 {kw}, 需确认是否有硬编码日期",
                        "severity": "人审",
                    })

    # Southern hemisphere winter wonderland
    southern_cities = ["悉尼", "墨尔本", "奥克兰", "惠灵顿", "开普敦",
                       "布宜诺斯艾利斯", "乌斯怀亚", "珀斯", "布里斯班",
                       "约翰内斯堡", "圣地亚哥", "莫尔兹比港"]
    for place, cat, text in all_texts:
        if not text:
            continue
        if place in southern_cities:
            for kw in southern_christmas_kw:
                if kw in text and ("雪" in text or "冬" in text):
                    findings.append({
                        "type": "南半球冬季节日错配",
                        "place": place,
                        "cat": cat,
                        "text": text[:80],
                        "detail": f"南半球12月是夏天, 但文案有 '{kw}' + 雪/冬意象",
                        "severity": "可疑",
                    })

    return findings


# ═══════════════════════════════════════════════════════════════════════
# 5. City Point vs Scenic Area (城市点 vs 景区面)
# ═══════════════════════════════════════════════════════════════════════

# Known scenic spots with coordinates
SCENIC_SPOTS = {
    "漓江": (25.27, 110.29),
    "黄山": (30.13, 118.17),
    "天池": (42.0, 128.05),       # 长白山天池
    "天山天池": (43.87, 88.12),
    "富士山": (35.36, 138.73),
    "玉龙雪山": (27.10, 100.18),
    "九寨沟": (33.26, 103.92),
    "张家界": (29.12, 110.43),
    "泰山": (36.25, 117.10),
    "华山": (34.48, 110.09),
    "峨眉山": (29.52, 103.33),
    "五台山": (39.02, 113.57),
    "鼓浪屿": (24.44, 118.07),
    "西湖": (30.24, 120.14),
    "诺日朗瀑布": (33.26, 103.92),
    "珍珠滩": (33.26, 103.92),
    "五彩池": (33.26, 103.92),
    "亚龙湾": (18.21, 109.60),
    "鹿回头": (18.24, 109.51),
    "丹翠雨林": (-16.07, 145.42),
    "火地岛": (-54.80, -68.30),
    "乞力马扎罗": (-3.07, 37.35),
    "比格尔海峡": (-54.80, -68.30),
}

# City center coords (approximate)
CITY_CENTERS = {
    "桂林": (25.27, 110.29),
    "黄山市": (29.71, 118.31),
    "长白山": (42.0, 128.05),
    "乌鲁木齐": (43.83, 87.62),
    "丽江": (26.87, 100.23),
    "张家界市": (29.12, 110.43),
    "泰安": (36.20, 117.08),
    "渭南": (34.50, 109.51),
    "峨眉山市": (29.52, 103.33),
    "忻州": (38.42, 112.73),
    "厦门": (24.48, 118.09),
    "杭州": (30.27, 120.15),
    "三亚": (18.25, 109.51),
    "乌斯怀亚": (-54.80, -68.30),
    "凯恩斯": (-16.92, 145.78),
    "乞力马扎罗": (-3.07, 37.35),
    "桂林市": (25.27, 110.29),
}


def audit_5_city_vs_scenic():
    """Sub-type 5: localcolor cards mentioning scenic spots far from city center."""
    findings = []

    # Load all localcolor data
    all_data = {}
    for fname in ["localcolor.json", "localcolor_china.json",
                   "localcolor_japan_korea_sea.json",
                   "localcolor_americas_africa_oceania.json"]:
        data = _load_json(_DATA / fname)
        all_data.update(data)

    for place, entry in all_data.items():
        # Collect all text for this place
        texts = []
        for cat in ("物产", "声音", "痕迹", "美食", "感受", "植被"):
            items = entry.get(cat, [])
            if isinstance(items, list):
                texts.extend([i if isinstance(i, str) else i.get("text", "") for i in items])
            elif isinstance(items, str):
                texts.append(items)

        full_text = " ".join(texts)

        for spot_name, (spot_lat, spot_lon) in SCENIC_SPOTS.items():
            if spot_name in full_text:
                # Find city center
                city_lat, city_lon = None, None
                if place in CITY_CENTERS:
                    city_lat, city_lon = CITY_CENTERS[place]
                else:
                    # Try to get from explorable_index
                    idx = _load_json(_DATA / "explorable_index.json")
                    entry_idx = idx.get("places", {}).get(place, {})
                    if "lat" in entry_idx and "lon" in entry_idx:
                        city_lat = entry_idx["lat"]
                        city_lon = entry_idx["lon"]

                if city_lat is not None and city_lon is not None:
                    dist = _haversine_km(city_lat, city_lon, spot_lat, spot_lon)
                    if dist > 50:
                        findings.append({
                            "type": "景区远离城市落点",
                            "place": place,
                            "spot": spot_name,
                            "distance_km": round(dist, 1),
                            "detail": f"'{place}' 卡提到 '{spot_name}', 但距离城市落点 {round(dist,1)}km",
                            "severity": "可疑" if dist < 200 else "实锤",
                        })

    return findings


# ═══════════════════════════════════════════════════════════════════════
# 6. Species/Vegetation Distribution (物种/植被超分布)
# ═══════════════════════════════════════════════════════════════════════

# Coarse distribution rules
TROPICAL_KEYWORDS = ["椰子", "棕榈", "芭蕉", "热带", "芒果", "榴莲", "红树林",
                     "橡胶", "可可", "咖啡", "香蕉", "菠萝", "槟榔"]
MOUNTAIN_KEYWORDS = ["雪松", "冷杉", "云杉", "落叶松", "杜鹃", "高山", "雪线"]
ARCTIC_KEYWORDS = ["驯鹿", "北极熊", "苔原", "极光", "冰川"]
DESERT_KEYWORDS = ["仙人掌", "骆驼", "沙棘", "胡杨"]


def _get_place_latlon(place, idx_data):
    """Get lat/lon from explorable_index."""
    entry = idx_data.get("places", {}).get(place, {})
    return entry.get("lat"), entry.get("lon")


def audit_6_species():
    """Sub-type 6: Species/vegetation out of expected distribution."""
    findings = []
    idx = _load_json(_DATA / "explorable_index.json")

    # Check flora_by_place
    flora = _load_json(_DATA / "flora_by_place.json")
    for place, items in flora.items():
        lat, lon = _get_place_latlon(place, idx)
        if lat is None:
            continue

        abs_lat = abs(lat)
        for item in items:
            zh_name = item.get("zh", "")
            if not zh_name:
                continue

            # Tropical species at high latitude
            if abs_lat > 35:
                for kw in TROPICAL_KEYWORDS:
                    if kw in zh_name:
                        findings.append({
                            "type": "热带物种超分布",
                            "place": place,
                            "species": zh_name,
                            "lat": lat,
                            "detail": f"纬度 {lat}, 但 flora 有热带物种 '{zh_name}'",
                            "severity": "可疑",
                        })
                        break

            # Arctic species at low latitude
            if abs_lat < 45:
                for kw in ARCTIC_KEYWORDS:
                    if kw in zh_name:
                        findings.append({
                            "type": "极地物种超分布",
                            "place": place,
                            "species": zh_name,
                            "lat": lat,
                            "detail": f"纬度 {lat}, 但 flora 有极地物种 '{zh_name}'",
                            "severity": "可疑",
                        })
                        break

    # Check localcolor text for species mentions
    all_data = {}
    for fname in ["localcolor.json", "localcolor_china.json",
                   "localcolor_japan_korea_sea.json",
                   "localcolor_americas_africa_oceania.json"]:
        data = _load_json(_DATA / fname)
        all_data.update(data)

    for place, entry in all_data.items():
        lat, lon = _get_place_latlon(place, idx)
        if lat is None:
            continue

        abs_lat = abs(lat)
        texts = []
        for cat in ("物产", "声音", "痕迹", "美食", "感受", "植被"):
            items = entry.get(cat, [])
            if isinstance(items, list):
                texts.extend([i if isinstance(i, str) else i.get("text", "") for i in items])
            elif isinstance(items, str):
                texts.append(items)
        full_text = " ".join(texts)

        if abs_lat > 30:
            for kw in TROPICAL_KEYWORDS:
                if kw in full_text:
                    findings.append({
                        "type": "热带意象超分布",
                        "place": place,
                        "species": kw,
                        "lat": lat,
                        "detail": f"纬度 {lat}, 但 localcolor 文案含热带词 '{kw}'",
                        "severity": "人审",
                    })
                    break

    return findings


# ═══════════════════════════════════════════════════════════════════════
# 7. Era Anachronisms (时代错)
# ═══════════════════════════════════════════════════════════════════════

ERA_WORDS = [
    "绿皮火车", "供销社", "公社", "粮票", "BP机", "传呼机",
    "大哥大", "拨号上网", "56K", "录像带", "VCD", "DVD",
    "黑白电视", "收音机", "半导体", "蜂窝煤", "煤球炉",
    "公共汽车票", "月票", "饭票", "布票", "工业券",
    "知青", "上山下乡", "大跃进", "人民公社", "生产队",
    "工分", "集体户", "插队",
]

# These may be intentional nostalgia — flag for human review
INTENTIONAL_NOSTALGIA = ["绿皮火车", "收音机", "蜂窝煤", "知青"]


def audit_7_anachronisms():
    """Sub-type 7: Scan for era-specific words."""
    findings = []

    # Scan all data files
    sources = []
    for fname in ["localcolor.json", "localcolor_china.json",
                   "localcolor_japan_korea_sea.json",
                   "localcolor_americas_africa_oceania.json",
                   "humanities.json", "humanities_films.json",
                   "humanities_historical.json"]:
        fp = _DATA / fname
        if not fp.exists():
            continue
        text = fp.read_text(encoding="utf-8")
        sources.append((fname, text))

    for fname, text in sources:
        for word in ERA_WORDS:
            # Find all occurrences with context
            for m in re.finditer(re.escape(word), text):
                start = max(0, m.start() - 30)
                end = min(len(text), m.end() + 30)
                context = text[start:end].replace("\n", " ").strip()

                severity = "人审" if word in INTENTIONAL_NOSTALGIA else "可疑"
                findings.append({
                    "type": "时代词",
                    "file": fname,
                    "word": word,
                    "context": context[:80],
                    "detail": f"文件 {fname} 含时代词 '{word}'",
                    "severity": severity,
                })

    # Deduplicate by word+file
    seen = set()
    deduped = []
    for f in findings:
        key = (f["word"], f["file"])
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    return deduped


# ═══════════════════════════════════════════════════════════════════════
# 8. AI-Fabricated Facts (AI编的事实)
# ═══════════════════════════════════════════════════════════════════════

# Patterns for specific numbers in Chinese text
FACT_PATTERNS = [
    (r'(\d{1,4})\s*年', "年份"),
    (r'(\d{1,6})\s*(?:米|公尺)', "距离/海拔"),
    (r'(\d{1,6})\s*(?:公里|千米)', "距离"),
    (r'(\d{1,4})\s*(?:度|°)', "温度/角度"),
    (r'(\d{1,6})\s*(?:人|万人口)', "人口/人数"),
    (r'(\d{1,6})\s*(?:平方米|平方公里|亩)', "面积"),
    (r'(\d{1,4})\s*(?:元|块|美元|欧元|日元)', "价格"),
    (r'(\d{1,3})\s*级', "等级"),
    (r'(\d{1,6})\s*卷', "卷数"),
    (r'(\d{1,6})\s*篇', "篇数"),
    (r'(\d{1,6})\s*个', "个数"),
    (r'(\d{1,6})\s*座', "座数"),
    (r'(\d{1,6})\s*根', "根数"),
]


def _try_zim_lookup(topic: str) -> str | None:
    """Try to look up a topic in the ZIM file. Returns extract or None."""
    zim_path = _DATA / "packs" / "wikipedia_zh_mini.zim"
    if not zim_path.exists():
        return None
    try:
        from zimply.zimply import ZIMFile
        zim = ZIMFile(str(zim_path), encoding="utf-8")
        # Try to find article
        for ns in ["C", "A"]:
            try:
                article = zim[ns][topic]
                if article:
                    # Strip HTML roughly
                    text = re.sub(r'<[^>]+>', '', str(article))
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text[:500]
            except (KeyError, Exception):
                continue
        # Try search
        try:
            results = zim.search(topic)
            if results:
                first = results[0]
                ns = first.namespace if hasattr(first, 'namespace') else 'C'
                url = first.url if hasattr(first, 'url') else str(first)
                try:
                    article = zim.get_article(ns, url)
                    text = re.sub(r'<[^>]+>', '', str(article))
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text[:500]
                except Exception:
                    pass
        except Exception:
            pass
    except Exception:
        pass
    return None


def audit_8_fabricated_facts():
    """Sub-type 8: Find cards with specific numbers, sample 10% for ZIM cross-check."""
    findings = []
    all_cards = []

    # Collect all cards with their text
    for fname in ["localcolor.json", "localcolor_china.json",
                   "localcolor_japan_korea_sea.json",
                   "localcolor_americas_africa_oceania.json"]:
        data = _load_json(_DATA / fname)
        for place, entry in data.items():
            for cat in ("物产", "声音", "痕迹", "美食", "感受", "植被"):
                items = entry.get(cat, [])
                if isinstance(items, list):
                    for i, item in enumerate(items):
                        text = item if isinstance(item, str) else item.get("text", "")
                        if text:
                            all_cards.append((place, cat, i, text, fname))
                elif isinstance(items, str) and items:
                    all_cards.append((place, cat, 0, items, fname))

    for fname in ["humanities.json", "humanities_films.json",
                   "humanities_historical.json"]:
        raw = _load_json(_DATA / fname)
        places = raw.get("places", raw)
        for place, entry in places.items():
            if place.startswith("_") or not isinstance(entry, dict):
                continue
            for cat in ("事件", "人物", "作品"):
                cards = entry.get(cat, [])
                if isinstance(cards, list):
                    for i, card in enumerate(cards):
                        if isinstance(card, dict):
                            text = card.get("text", "")
                            if text:
                                all_cards.append((place, cat, i, text, fname))

    # Find cards with specific numbers
    cards_with_numbers = []
    for place, cat, idx, text, fname in all_cards:
        for pattern, kind in FACT_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                cards_with_numbers.append({
                    "place": place, "cat": cat, "idx": idx,
                    "text": text, "file": fname,
                    "numbers": [(m, kind) for m in matches],
                })
                break  # one match per card is enough

    # Sample 10% for ZIM check
    import random
    rng = random.Random(42)
    sample_size = max(1, len(cards_with_numbers) // 10)
    sample = rng.sample(cards_with_numbers, min(sample_size, len(cards_with_numbers)))

    for card in sample:
        # Try to extract a lookup topic from the card
        text = card["text"]
        place = card["place"]

        # Try ZIM lookup
        zim_result = _try_zim_lookup(place)

        # Extract key claims
        claims = []
        for pattern, kind in FACT_PATTERNS:
            for m in re.finditer(pattern, text):
                num = m.group(1)
                # Get surrounding context
                start = max(0, m.start() - 10)
                end = min(len(text), m.end() + 10)
                ctx = text[start:end]
                claims.append(f"{kind}: {num} ({ctx})")

        if zim_result:
            # Check if any numbers appear in ZIM result
            for num_str, kind in card["numbers"]:
                if num_str in zim_result:
                    pass  # Confirmed
                else:
                    findings.append({
                        "type": "ZIM未确认的数字",
                        "place": place,
                        "cat": card["cat"],
                        "text": text[:80],
                        "detail": f"数字 {num_str} ({kind}) 未在维基百科 '{place}' 条目中找到",
                        "severity": "人审",
                    })
        else:
            findings.append({
                "type": "ZIM查不到该地",
                "place": place,
                "cat": card["cat"],
                "text": text[:80],
                "detail": f"维基百科无 '{place}' 条目, 无法交叉验证 ({'; '.join(claims[:3])})",
                "severity": "人审",
            })

    # Summary stats
    summary = {
        "total_cards": len(all_cards),
        "cards_with_numbers": len(cards_with_numbers),
        "sampled": len(sample),
        "findings": len(findings),
    }

    return findings, summary


# ═══════════════════════════════════════════════════════════════════════
# Report generation
# ═══════════════════════════════════════════════════════════════════════

def generate_report():
    """Run all 8 audits and generate report."""
    lines = []
    lines.append("# QA Alignment Report (Card 23)")
    lines.append("")
    lines.append("生成时间: 2026-08-20")
    lines.append("脚本: nowhere/tests/qa_alignment.py")
    lines.append("原则: 只量不修")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── 1. Region Rectangles ──
    print("[1/8] 审计文化区矩形...")
    mismatches, known_five = audit_1_region_rectangles()
    lines.append("## 1. 文化区矩形 (Cultural Region Rectangles)")
    lines.append("")
    lines.append(f"总检测城市: {len(CITIES_200)}")
    lines.append(f"错配数: {len(mismatches)}")
    lines.append(f"已知5实锤复现: {len(known_five)}/5")
    lines.append("")

    if known_five:
        lines.append("### 已知5实锤 (必须全部复现为 ✗)")
        lines.append("")
        for e in known_five:
            lines.append(f"- ✗ **{e['city']}** ({e['lat']}, {e['lon']}): describe={e['describe']}, encounters={e['encounters']}")
            for issue in e["issues"]:
                lines.append(f"  - {issue}")
        lines.append("")

    other = [m for m in mismatches if m not in known_five]
    if other:
        lines.append(f"### 其他错配 ({len(other)} 个)")
        lines.append("")
        for e in other:
            lines.append(f"- **{e['city']}** ({e['lat']}, {e['lon']}): describe={e['describe']}, encounters={e['encounters']}")
            for issue in e["issues"]:
                lines.append(f"  - {issue}")
        lines.append("")

    # ── 2. Key Drift ──
    print("[2/8] 审计地名键漂移...")
    drift = audit_2_key_drift()
    lines.append("## 2. 地名键漂移 (Place Name Key Drift)")
    lines.append("")
    lines.append(f"总发现: {len(drift)}")
    lines.append("")

    by_type = {}
    for f in drift:
        by_type.setdefault(f["type"], []).append(f)

    for t, items in sorted(by_type.items()):
        lines.append(f"### {t} ({len(items)})")
        lines.append("")
        for item in items:
            lines.append(f"- [{item['severity']}] **{item['key']}**: {item['detail']}")
        lines.append("")

    # ── 3. Country Codes ──
    print("[3/8] 审计国家码边界...")
    cc_findings, empty_zh_samples = audit_3_country_codes()
    lines.append("## 3. 国家码边界错 (Country Code Boundary Errors)")
    lines.append("")
    lines.append(f"总发现: {len(cc_findings)}")
    lines.append("")

    for f in cc_findings:
        lines.append(f"- [{f['severity']}] **{f['code']}** ({f['type']}): {f['detail']}")
    lines.append("")

    if empty_zh_samples:
        lines.append("### zh空串样例 (前20)")
        lines.append("")
        for s in empty_zh_samples:
            lines.append(f"- {s}")
        lines.append("")

    # ── 4. Calendar Drift ──
    print("[4/8] 审计历法漂移...")
    cal = audit_4_calendar()
    lines.append("## 4. 历法漂移 (Calendar Drift)")
    lines.append("")
    lines.append(f"总发现: {len(cal)}")
    lines.append("")

    for f in cal:
        lines.append(f"- [{f['severity']}] **{f['place']}** ({f['cat']}): {f['detail']}")
        if f.get("text"):
            lines.append(f"  - 文案: \"{f['text']}\"")
    lines.append("")

    # ── 5. City vs Scenic ──
    print("[5/8] 审计城市点vs景区面...")
    scenic = audit_5_city_vs_scenic()
    lines.append("## 5. 城市点 vs 景区面 (City Point vs Scenic Area)")
    lines.append("")
    lines.append(f"总发现: {len(scenic)}")
    lines.append("")

    for f in scenic:
        lines.append(f"- [{f['severity']}] **{f['place']}** 提到 **{f['spot']}**: 距离城市落点 {f['distance_km']}km")
    lines.append("")

    # ── 6. Species ──
    print("[6/8] 审计物种/植被超分布...")
    species = audit_6_species()
    lines.append("## 6. 物种/植被超分布 (Species/Vegetation Distribution)")
    lines.append("")
    lines.append(f"总发现: {len(species)}")
    lines.append("")

    for f in species:
        lines.append(f"- [{f['severity']}] **{f['place']}**: {f['detail']}")
    lines.append("")

    # ── 7. Anachronisms ──
    print("[7/8] 审计时代错...")
    anachronisms = audit_7_anachronisms()
    lines.append("## 7. 时代错 (Era Anachronisms)")
    lines.append("")
    lines.append(f"总发现: {len(anachronisms)}")
    lines.append("")

    for f in anachronisms:
        lines.append(f"- [{f['severity']}] **{f['word']}** in {f['file']}: {f['detail']}")
        lines.append(f"  - 上下文: \"{f['context']}\"")
    lines.append("")

    # ── 8. AI Facts ──
    print("[8/8] 审计AI编的事实...")
    ai_facts, ai_summary = audit_8_fabricated_facts()
    lines.append("## 8. AI编的事实 (AI-Fabricated Facts)")
    lines.append("")
    lines.append(f"总卡数: {ai_summary['total_cards']}")
    lines.append(f"含具体数字的卡: {ai_summary['cards_with_numbers']}")
    lines.append(f"抽样验证: {ai_summary['sampled']}")
    lines.append(f"发现问题: {ai_summary['findings']}")
    lines.append("")

    for f in ai_facts:
        lines.append(f"- [{f['severity']}] **{f['place']}** ({f['cat']}): {f['detail']}")
        lines.append(f"  - 文案: \"{f['text']}\"")
    lines.append("")

    # ── Summary ──
    lines.append("---")
    lines.append("")
    lines.append("## 总结与优先级建议")
    lines.append("")

    total = (len(mismatches) + len(drift) + len(cc_findings) + len(cal)
             + len(scenic) + len(species) + len(anachronisms) + len(ai_facts))

    lines.append(f"**总发现数: {total}**")
    lines.append("")
    lines.append("| 亚种 | 发现数 | 最高严重度 |")
    lines.append("|------|--------|-----------|")
    lines.append(f"| 1. 文化区矩形 | {len(mismatches)} | {'实锤' if known_five else '可疑'} |")
    lines.append(f"| 2. 地名键漂移 | {len(drift)} | 实锤 |")
    lines.append(f"| 3. 国家码边界 | {len(cc_findings)} | 实锤 |")
    lines.append(f"| 4. 历法漂移 | {len(cal)} | {'实锤' if any(f['severity']=='实锤' for f in cal) else '可疑'} |")
    lines.append(f"| 5. 城市vs景区 | {len(scenic)} | {'实锤' if any(f['severity']=='实锤' for f in scenic) else '可疑'} |")
    lines.append(f"| 6. 物种超分布 | {len(species)} | 可疑 |")
    lines.append(f"| 7. 时代错 | {len(anachronisms)} | 可疑 |")
    lines.append(f"| 8. AI编事实 | {len(ai_facts)} | 人审 |")
    lines.append("")
    lines.append("### 建议修复优先级")
    lines.append("")
    lines.append("1. **文化区矩形** (实锤): describe.py `_REGION_MAP` 和 encounters.py `_region_for` 的矩形定义冲突, 高加索/中亚/南亚边界错最多。修矩形是第一优先。")
    lines.append("2. **国家码边界** (实锤): food_by_country.json 的 DD(东德) 条目必须删; 574 条 zh 空串会导致英文菜名混入中文散文。")
    lines.append("3. **地名键漂移** (实锤): 凤凰/凤凰古城等重复键需合并; 索引与数据文件的键需对齐。")
    lines.append("4. **历法漂移** (实锤): 伊斯兰历节日的硬编码月份必须改用动态计算。")
    lines.append("5. **城市vs景区** (可疑): 景区卡需确认城市落点是否合理, 或调整落点坐标。")
    lines.append("6. **物种超分布** (可疑): 需人工二审, 部分可能是数据源本身的分布记录。")
    lines.append("7. **时代错** (人审): 部分可能是故意怀旧, 需人工判断哪些保留哪些删。")
    lines.append("8. **AI编事实** (人审): 需更完整的 ZIM 交叉验证, 当前样本量有限。")
    lines.append("")

    report = "\n".join(lines)
    _REPORT.write_text(report, encoding="utf-8")
    print(f"\n报告已生成: {_REPORT}")
    print(f"总发现: {total}")

    return total


if __name__ == "__main__":
    generate_report()
