"""Task 7: 幽灵索引清理"""
import os, sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\84989\Desktop\nowhere_repo")

import pathlib

DATA_DIR = pathlib.Path(r"C:\Users\84989\Desktop\nowhere_repo\nowhere\data")

PHANTOMS = ["南极磷虾", "墨西哥湾流", "深海热泉", "珊瑚礁", "黑潮"]

print(f"=== Task 7: 幽灵索引清理 ===\n")

# 1. Check explorable_index.json
index_path = DATA_DIR / "explorable_index.json"
index_data = json.loads(index_path.read_text(encoding="utf-8"))
index_places = index_data.get("places", {})
index_names = set(index_places.keys())

print(f"1. explorable_index.json:")
for p in PHANTOMS:
    exists = p in index_names
    print(f"   {p}: {'EXISTS' if exists else 'NOT FOUND'}")

# 2. Check localcolor.json (+ regional files)
lc_path = DATA_DIR / "localcolor.json"
lc_data = json.loads(lc_path.read_text(encoding="utf-8")) if lc_path.exists() else {}

# Also check regional files
for fname in ["localcolor_china.json", "localcolor_japan_korea_sea.json",
              "localcolor_americas_africa_oceania.json"]:
    p = DATA_DIR / fname
    if p.exists():
        regional = json.loads(p.read_text(encoding="utf-8"))
        for k, v in regional.items():
            if k not in lc_data:
                lc_data[k] = v

lc_names = set(lc_data.keys())
print(f"\n2. localcolor.json (all regional files):")
for p in PHANTOMS:
    exists = p in lc_names
    if exists:
        card_count = len(lc_data[p]) if isinstance(lc_data[p], list) else 1
        print(f"   {p}: EXISTS ({card_count} cards)")
    else:
        print(f"   {p}: NOT FOUND")

# 3. Check humanities.json
h_path = DATA_DIR / "humanities.json"
h_data = json.loads(h_path.read_text(encoding="utf-8")) if h_path.exists() else {}
h_places = h_data.get("places", {})
h_names = set(h_places.keys())

print(f"\n3. humanities.json:")
for p in PHANTOMS:
    exists = p in h_names
    if exists:
        entries = h_places[p]
        count = len(entries) if isinstance(entries, list) else 1
        print(f"   {p}: EXISTS ({count} entries)")
    else:
        print(f"   {p}: NOT FOUND")

# Summary
print(f"\n=== Summary ===")
for p in PHANTOMS:
    in_index = p in index_names
    in_lc = p in lc_names
    in_h = p in h_names
    is_phantom = in_index and not in_lc and not in_h
    status = "PHANTOM (index only, no data)" if is_phantom else "OK"
    if in_index and (in_lc or in_h):
        status = "OK (has data)"
    elif not in_index:
        status = "NOT IN INDEX"
    print(f"  {p}: index={'Y' if in_index else 'N'}, localcolor={'Y' if in_lc else 'N'}, humanities={'Y' if in_h else 'N'} -> {status}")

with open(r"C:\Users\84989\Desktop\nowhere_repo\_audit_task7_result.json", "w", encoding="utf-8") as f:
    results = {}
    for p in PHANTOMS:
        in_index = p in index_names
        in_lc = p in lc_names
        in_h = p in h_names
        results[p] = {
            "in_index": in_index,
            "in_localcolor": in_lc,
            "in_humanities": in_h,
            "is_phantom": in_index and not in_lc and not in_h,
        }
    json.dump(results, f, ensure_ascii=False, indent=2)
