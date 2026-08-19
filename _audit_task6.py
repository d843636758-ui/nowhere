"""Task 6: Probe clamp 期望值更新"""
import os, sys, json
os.environ["NOWHERE_SEED"] = "42"
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\84989\Desktop\nowhere_repo")

from nowhere import walk as walk_mod

print(f"=== Task 6: Probe clamp 期望值更新 ===")

# Read current _DIST_MIN from walk.py
dist_min = walk_mod._DIST_MIN
dist_max = walk_mod._DIST_MAX
print(f"  Current _DIST_MIN = {dist_min}")
print(f"  Current _DIST_MAX = {dist_max}")

# Check what qa_probe.py expects
# probe_2_4 at line 364: expects dist_min >= 0.2
qa_expects_min = 0.2
qa_expects_max = 5.0

print(f"\n  qa_probe.py expects: dist_min >= {qa_expects_min}, dist_max <= {qa_expects_max}")
print(f"  Actual: _DIST_MIN = {dist_min}, _DIST_MAX = {dist_max}")

# Run the actual clamp test
from nowhere.state import WorldState
from datetime import datetime, timezone

s = WorldState()
s.pos = (40.0, 116.0)
s.landed_at = datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc)
s.elapsed_hours = 0.0
s.path.append({"lat": 40.0, "lon": 116.0, "elevation": 50, "dist_km": 0})

# Test min clamp
result_min = walk_mod.step(s, 0.0, None, 0.01)
dist_min_actual = result_min.get("dist_km", 0)
clamped_min = result_min.get("clamped", False)

# Reset
s = WorldState()
s.pos = (40.0, 116.0)
s.landed_at = datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc)
s.elapsed_hours = 0.0
s.path.append({"lat": 40.0, "lon": 116.0, "elevation": 50, "dist_km": 0})

# Test max clamp
result_max = walk_mod.step(s, 0.0, None, 100.0)
dist_max_actual = result_max.get("dist_km", 0)
clamped_max = result_max.get("clamped", False)

print(f"\n  Test results:")
print(f"    step(0.01) -> dist={dist_min_actual}, clamped={clamped_min}")
print(f"    step(100)  -> dist={dist_max_actual}, clamped={clamped_max}")

# Determine needed fix
old_expected = f"dist_min >= {qa_expects_min}"
new_expected = f"dist_min >= {dist_min}"

needs_update = dist_min_actual < qa_expects_min
print(f"\n  qa_probe.py check 'dist_min >= 0.2':")
print(f"    Old expected: {old_expected}")
print(f"    New expected: {new_expected}")
print(f"    Actual min clamp result: {dist_min_actual}")
print(f"    Needs qa_probe update: {'YES' if needs_update else 'NO'}")

if needs_update:
    print(f"\n  RECOMMENDATION: Update qa_probe.py line 386:")
    print(f"    OLD: min_ok = dist_min >= 0.2 and clamped_min")
    print(f"    NEW: min_ok = dist_min >= {dist_min} and clamped_min")
    print(f"    Also update line 389 expected text:")
    print(f"    OLD: dist_min>=0.2, dist_max<=5.0")
    print(f"    NEW: dist_min>={dist_min}, dist_max<={dist_max}")
    print(f"    And line 393: _DIST_MIN={dist_min}, _DIST_MAX={dist_max}")

with open(r"C:\Users\84989\Desktop\nowhere_repo\_audit_task6_result.json", "w", encoding="utf-8") as f:
    json.dump({
        "current_dist_min": dist_min,
        "current_dist_max": dist_max,
        "qa_expects_min": qa_expects_min,
        "qa_expects_max": qa_expects_max,
        "actual_min_clamp": dist_min_actual,
        "actual_max_clamp": dist_max_actual,
        "needs_update": needs_update,
        "old_expected": old_expected,
        "new_expected": new_expected,
    }, f, ensure_ascii=False, indent=2)
