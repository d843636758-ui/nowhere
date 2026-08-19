"""Task 2: Card 35 - 渲染链探针 (lite: 3 places x 5 walks)"""
import os, sys, json, re
os.environ["NOWHERE_SEED"] = "42"
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\84989\Desktop\nowhere_repo")

import asyncio, random
from nowhere import server as srv

PLACES = ["京都", "长江", "巴黎"]

async def run():
    all_texts = []
    issues = []

    for place in PLACES:
        try:
            door_result = await srv.open_door_impl(to=place)
            text = door_result.get("text", "")
            all_texts.append(("open_door", place, text))
        except Exception as e:
            issues.append(f"open_door({place}) CRASH: {e}")
            continue

        for step_i in range(5):
            try:
                walk_result = await srv.walk_impl("N")
                text = walk_result.get("text", "")
                all_texts.append(("walk", f"{place}/step{step_i+1}", text))
            except Exception as e:
                issues.append(f"walk({place}, step {step_i}) CRASH: {e}")
                break

    # Scan all output text
    combined = "\n".join(t for _, _, t in all_texts)

    # Check 1: placeholder {xxx}
    placeholders = re.findall(r'\{[a-z_]+\}', combined)
    if placeholders:
        issues.append(f"placeholders found: {set(placeholders)}")

    # Check 2: double periods 。。
    double_periods = combined.count("。。")
    if double_periods > 0:
        issues.append(f"double periods (。。): {double_periods}")

    # Check 3: None leaks
    none_leaks = len(re.findall(r'\bNone\b', combined))
    if none_leaks > 0:
        issues.append(f"None leaks: {none_leaks}")

    # Check 4: forbidden words
    for word in ["很", "非常", "十分"]:
        count = combined.count(word)
        if count > 0:
            issues.append(f"forbidden word '{word}': {count} occurrences")

    # Check 5: punctuation mixing
    mixed = len(re.findall(r'[。！？][.,!?]|[，、][,]', combined))
    if mixed > 0:
        issues.append(f"mixed punctuation: {mixed}")

    print(f"=== Task 2: 渲染链探针 ===")
    print(f"Total text segments: {len(all_texts)}")
    print(f"Total characters: {len(combined)}")
    print(f"Total issues: {len(issues)}")
    print(f"Assertion (0 issues): {'PASS' if len(issues) == 0 else 'FAIL'}")
    for iss in issues:
        print(f"  ISSUE: {iss}")

    with open(r"C:\Users\84989\Desktop\nowhere_repo\_audit_task2_result.json", "w", encoding="utf-8") as f:
        json.dump({"issues": issues, "text_count": len(all_texts), "char_count": len(combined)}, f, ensure_ascii=False, indent=2)

asyncio.run(run())
