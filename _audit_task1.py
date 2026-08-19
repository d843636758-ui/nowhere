"""Task 1: Card 32 - 拉普兰12连抽"""
import os, sys, json
os.environ["NOWHERE_SEED"] = "42"
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\84989\Desktop\nowhere_repo")

import random
from nowhere import localcolor

rng = random.Random(42)
seen = set()
results = []

for i in range(1, 13):
    card = localcolor.draw("拉普兰", seen, rng)
    if card is None:
        results.append({"draw": i, "card": None, "category": None, "key": None, "handwritten": None})
        continue
    seen.add(card["key"])
    # Determine handwritten vs baked: handwritten keys don't start with "拉普兰/烘焙"
    is_baked = card["key"].startswith("拉普兰/烘焙") or "/烘焙" in card["key"]
    is_handwritten = not is_baked
    results.append({
        "draw": i,
        "category": card["category"],
        "key": card["key"],
        "text_preview": card["text"][:60],
        "handwritten": is_handwritten,
        "baked": is_baked,
    })

# Count
hw_count = sum(1 for r in results if r.get("handwritten"))
baked_count = sum(1 for r in results if r.get("baked"))
hw_in_first_6 = sum(1 for r in results[:6] if r.get("handwritten"))

print(f"=== Task 1: 拉普兰 12 draws ===")
print(f"Total handwritten: {hw_count}")
print(f"Total baked: {baked_count}")
print(f"Handwritten in first 6: {hw_in_first_6}")
print(f"Assertion (all handwritten in first 6): {'PASS' if hw_count <= 6 and hw_in_first_6 == hw_count else 'FAIL'}")
for r in results:
    print(f"  Draw {r['draw']}: cat={r.get('category')}, hw={r.get('handwritten')}, key={r.get('key')}, text={r.get('text_preview','N/A')}")

# Save raw results
with open(r"C:\Users\84989\Desktop\nowhere_repo\_audit_task1_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
