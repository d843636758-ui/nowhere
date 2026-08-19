"""Task 3+4: Card 37+39 - 长江5步 + 复读检查"""
import os, sys, json, re
os.environ["NOWHERE_SEED"] = "42"
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\84989\Desktop\nowhere_repo")

import asyncio, random
from nowhere import server as srv

WATER_KEYWORDS = ["水", "江", "河", "潮", "浪", "湖", "溪", "海", "渡", "岸", "滩", "波"]

async def run():
    # open_door to 长江
    door_result = await srv.open_door_impl(to="长江")
    door_text = door_result.get("text", "")
    print(f"Door text (first 120): {door_text[:120]}")

    step_texts = []
    # Walk 5 steps North
    for i in range(5):
        result = await srv.walk_impl("N")
        text = result.get("text", "")
        step_texts.append(text)
        print(f"\n--- Step {i+1} ---")
        print(f"Text (first 200): {text[:200]}")

    # Task 3: Check water content in each step
    print(f"\n=== Task 3: 长江5步 water presence ===")
    water_results = []
    for i, text in enumerate(step_texts):
        has_water = any(kw in text for kw in WATER_KEYWORDS)
        water_results.append(has_water)
        print(f"  Step {i+1}: water={'YES' if has_water else 'NO'} | keywords found: {[kw for kw in WATER_KEYWORDS if kw in text]}")

    all_have_water = all(water_results)
    print(f"Assertion (all 5 steps have water): {'PASS' if all_have_water else 'FAIL'}")

    # Task 4: Repetition check
    print(f"\n=== Task 4: 长江5步复读检查 ===")

    # Check radio station text repetition
    radio_texts = []
    for text in step_texts:
        # Extract radio-related text (simplified: look for 台/电台/频率/MHz/FM/AM
        radio_match = re.findall(r'[^。\n]*(?:电台|频率|MHz|FM|AM|广播|收音)[^。\n]*[。]?', text)
        radio_texts.extend(radio_match)

    # Check for repeated exact sentences
    all_sentences = []
    for text in step_texts:
        sentences = re.split(r'[。\n]', text)
        all_sentences.extend([s.strip() for s in sentences if s.strip()])

    # Count "同时," usage
    tongshi_count = sum(1 for s in all_sentences if s.startswith("同时,") or s.startswith("同时，"))
    tongshi_pct = tongshi_count / len(all_sentences) * 100 if all_sentences else 0

    # Find repeated sentences
    from collections import Counter
    sentence_counts = Counter(all_sentences)
    repeated = {s: c for s, c in sentence_counts.items() if c > 1}

    print(f"  Radio texts found: {len(radio_texts)}")
    print(f"  Total sentences: {len(all_sentences)}")
    print(f"  '同时,' count: {tongshi_count} ({tongshi_pct:.1f}%)")
    print(f"  Repeated sentences: {repeated}")

    radio_ok = len(radio_texts) <= 2
    touch_ok = not any(c > 1 for s, c in repeated.items() if "触" in s or "摸" in s or "碰" in s)
    tongshi_ok = tongshi_pct < 30

    print(f"  Radio <=2: {'PASS' if radio_ok else 'FAIL'}")
    print(f"  No repeated touch: {'PASS' if touch_ok else 'FAIL'}")
    print(f"  同时, <30%: {'PASS' if tongshi_ok else 'FAIL'}")
    print(f"  Overall: {'PASS' if radio_ok and touch_ok and tongshi_ok else 'FAIL'}")

    with open(r"C:\Users\84989\Desktop\nowhere_repo\_audit_task3_4_result.json", "w", encoding="utf-8") as f:
        json.dump({
            "door_text": door_text[:200],
            "step_texts": step_texts,
            "water_results": water_results,
            "all_have_water": all_have_water,
            "radio_texts": radio_texts,
            "tongshi_count": tongshi_count,
            "tongshi_pct": tongshi_pct,
            "repeated_sentences": repeated,
        }, f, ensure_ascii=False, indent=2)

asyncio.run(run())
