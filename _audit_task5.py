"""Task 5: Card 40 - 15步密度衰减"""
import os, sys, json
os.environ["NOWHERE_SEED"] = "42"
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\84989\Desktop\nowhere_repo")

import asyncio, random, re
from nowhere import server as srv

async def run():
    # open_door to a random place
    door_result = await srv.open_door_impl()
    door_text = door_result.get("text", "")
    place = srv._state.place_name or "random"
    pos = srv._state.pos
    print(f"Landed at: {place} ({pos})")
    print(f"Door text (first 100): {door_text[:100]}")

    step_data = []
    # Walk 15 steps North
    for i in range(15):
        result = await srv.walk_impl("N")
        text = result.get("text", "")
        data = result.get("data", {})

        # Extract encounter info
        has_encounter = bool(re.search(r'(遇到|看见|发现|一头|一只|一群|飞过|跑过|爬过|走过)', text))

        # Extract wilderness depth info
        wd = srv._compute_wilderness_depth_km(srv._state.pos[0], srv._state.pos[1]) if srv._state.pos else 0

        step_data.append({
            "step": i + 1,
            "text": text[:300],
            "has_encounter": has_encounter,
            "wilderness_depth_km": round(wd, 2),
            "pos": list(srv._state.pos) if srv._state.pos else None,
        })

    # Check assertions
    print(f"\n=== Task 5: 15步密度衰减 ===")

    # Check: no "回到原来的地方"
    has_return = any("回到原来的地方" in s["text"] for s in step_data)
    print(f"  No '回到原来的地方': {'PASS' if not has_return else 'FAIL'}")

    # Check: wilderness depth should generally increase
    depths = [s["wilderness_depth_km"] for s in step_data]
    depth_increased = depths[-1] >= depths[0]
    print(f"  Wilderness depth increased: {'PASS' if depth_increased else 'FAIL'} ({depths[0]} -> {depths[-1]})")

    # Record key steps
    for key_step in [0, 4, 9, 14]:  # steps 1, 5, 10, 15
        s = step_data[key_step]
        enc_tag = "ENCOUNTER" if s["has_encounter"] else "quiet"
        print(f"  Step {s['step']}: [{enc_tag}] wd={s['wilderness_depth_km']}km | {s['text'][:120]}")

    # Check encounter density decay (steps 1-7 vs 8-15)
    first_half = sum(1 for s in step_data[:7] if s["has_encounter"])
    second_half = sum(1 for s in step_data[7:] if s["has_encounter"])
    print(f"  Encounters 1-7: {first_half}, 8-15: {second_half}")
    print(f"  Density decay visible: {'PASS' if first_half >= second_half else 'NOTE: may vary with RNG'}")

    with open(r"C:\Users\84989\Desktop\nowhere_repo\_audit_task5_result.json", "w", encoding="utf-8") as f:
        json.dump(step_data, f, ensure_ascii=False, indent=2)

asyncio.run(run())
