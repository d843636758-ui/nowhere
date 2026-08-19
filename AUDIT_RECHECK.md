# AUDIT_REPORT — 7 Task Recheck

**Date**: 2026-08-20
**Seed**: NOWHERE_SEED=42
**Python**: 3.12

---

## Task 1: Card 32 — 拉普兰12连抽

**Test**: `localcolor.draw("拉普兰", seen=set(), rng)` x 12 with seed=42

**Expected**: Handwritten 4 cards all appear in first 6 draws
**Actual**: Handwritten **8** cards (not 4), all appear in draws 1-8 before any baked cards

| Draw | Category | Key | Handwritten? |
|------|----------|-----|-------------|
| 1 | 痕迹 | 拉普兰/痕迹/1 | YES |
| 2 | 物产 | 拉普兰/物产/0 | YES |
| 3 | 声音 | 拉普兰/声音/0 | YES |
| 4 | 声音 | 拉普兰/声音/1 | YES |
| 5 | 节律 | 拉普兰/节律/0 | YES |
| 6 | 节律 | 拉普兰/节律/1 | YES |
| 7 | 痕迹 | 拉普兰/痕迹/0 | YES |
| 8 | 物产 | 拉普兰/物产/1 | YES |
| 9 | 植被 | 拉普兰/烘焙植被/9 | NO (baked) |
| 10 | 植被 | 拉普兰/烘焙植被/1 | NO (baked) |
| 11 | 植被 | 拉普兰/烘焙植被/8 | NO (baked) |
| 12 | 植被 | 拉普兰/烘焙植被/6 | NO (baked) |

**Verdict**: CONDITIONAL PASS
- Tier system works correctly: all handwritten cards are drawn before any baked cards
- The assertion "4 handwritten cards" is wrong — 拉普兰 has 8 handwritten cards
- Corrected assertion: "all 8 handwritten cards appear in first 8 draws" — PASSES

---

## Task 2: Card 35 — 渲染链探针重跑

**Test**: open_door + walk x5 for 3 places (京都, 长江, 巴黎), scan for quality issues

**Expected**: 0 issues
**Actual**: **1 issue**

| Check | Result |
|-------|--------|
| Placeholders {xxx} | 0 found |
| Double periods 。。 | 0 found |
| None leaks | 0 found |
| Forbidden word '很' | **1 found** |
| Forbidden word '非常' | 0 found |
| Forbidden word '十分' | 0 found |
| Punctuation mixing | 0 found |

**Source**: `nowhere/data/scene_walk_discovery.txt` line 115:
```
你走到一个十字路口，车很多，喇叭响。
```

**Verdict**: FAIL — 1 forbidden word "很" in walk discovery scene template

**Fix**: Change "车很多" to "车不少" or "车一辆接一辆" in `scene_walk_discovery.txt` line 115 and `scenes_src/discovery.json` line 915.

---

## Task 3: Card 37 — 长江5步

**Test**: open_door("长江") then walk 5 steps North

**Expected**: Each step has river/water presence
**Actual**: All 5 steps contain water keywords

| Step | Water Keywords Found | Has Water? |
|------|---------------------|-----------|
| 1 | 水, 江, 河, 海 | YES |
| 2 | 水, 江, 河, 海, 岸 | YES |
| 3 | 水, 江, 湖 | YES |
| 4 | 水, 江, 河, 海, 岸 | YES |
| 5 | 水, 江, 河, 岸 | YES |

**Step texts (first 120 chars)**:
1. "人行道的路沿石被磨得发亮。...你沿着河堤走。石阶往下延伸到水边..."
2. "太阳快贴着地平线了...你在河口。河水和海水在这里交汇..."
3. "气候估算。22度...你在湖边坐着。水面在你面前一动不动..."
4. "此刻多云...你站在河边。水面在你脚边流，黄的，慢的..."
5. "收音机里有声音。CRI Easy FM...你站在河边。水面在你脚边流..."

**Verdict**: PASS — all 5 steps have river/water content

---

## Task 4: Card 39 — 长江5步复读检查

**Test**: Same run as Task 3, check for repetition patterns

**Expected**: Radio text <=2 times, no repeated touch sentences, "同时," <30%
**Actual**: Radio <=2 PASS, repeated sentences found, 同时, =5.3% PASS

| Metric | Value | Threshold | Result |
|--------|-------|-----------|--------|
| Radio texts | 2 | <=2 | PASS |
| Total sentences | 94 | — | — |
| "同时," count | 5 (5.3%) | <30% | PASS |
| Repeated sentences | 9 types | 0 | FAIL |

**Repeated sentences** (count: sentence):
- 3x: "你横着江的走向走"
- 3x: "水声从侧面流过"
- 2x: "人行道的路沿石被磨得发亮"
- 2x: "还没开，但空气里已经有了一丝甜"
- 2x: "每走一步，水声换个方位"
- 2x: "水面在你脚边流，黄的，慢的"
- 2x: "岸边的泥是软的，你踩下去，鞋陷了半寸"
- 2x: "水里有泡沫，转着圈往下游走"
- 2x: "你蹲下来，把手伸进去，凉的，指尖碰到滑溜溜的石头"

**Root cause**: The river alignment text (`_river_alignment_text` in server.py) generates from small variant pools (3-4 options each for along/cross river). With 5 steps near the same river, the pool is exhausted quickly and repeats. The "横着江的走向走" and "水声从侧面流过" are from the "walking across river" variant pool (only 3 options).

**Verdict**: FAIL — repeated sentences (especially river narrative variants)

**Fix**: Add more variants to `_river_alignment_text` pools in `server.py` lines 1282-1304, or add dedup logic using `recent_scenes`.

---

## Task 5: Card 40 — 15步密度衰减

**Test**: open_door(random) then walk 15 steps North. Landed at: 安第斯 (-33.48, -70.65), 4231m altitude

**Expected**: Density decay visible, no "回到原来的地方", wilderness depth increases
**Actual**: All checks pass

| Metric | Value | Result |
|--------|-------|--------|
| "回到原来的地方" | 0 occurrences | PASS |
| Wilderness depth step 1 | 2.03 km | — |
| Wilderness depth step 15 | 26.84 km | PASS (increased) |
| Encounters steps 1-7 | 0 | — |
| Encounters steps 8-15 | 1 | — |

**Key step snapshots**:
- **Step 1** (wd=2.03km): "此刻大部晴，15度。...岩石，平的。可4231米的海拔压着胸口..."
- **Step 5** (wd=6.99km): "Radio Nacional de Chile在播新闻、culture...地势平坦，但海拔4231米..."
- **Step 10** (wd=16.87km): "Radio Nacional de Chile在播新闻...地是岩石，没有坡。但4231米的空气稀薄..."
- **Step 15** (wd=26.84km): "附近有电台在播...地势平坦，但海拔4292米...脚下是硬化路面..."

**Observation**: Wilderness depth increases monotonically (2.03 -> 26.84 km). The deep wilderness narrative ("海拔压着胸口", "空气稀薄") correctly activates. At this altitude encounters are naturally sparse (0-1 total).

**Verdict**: PASS

---

## Task 6: Probe clamp期望值更新

**Test**: Check `_DIST_MIN` in walk.py vs expected values in qa_probe.py

**Finding**: `_DIST_MIN` was changed from 0.2 to 0.05 (Card 7: short-distance probing), but qa_probe.py was not updated.

| Item | Old (qa_probe) | Actual (walk.py) |
|------|---------------|-------------------|
| `_DIST_MIN` | 0.2 | **0.05** |
| `_DIST_MAX` | 5.0 | 5.0 |
| step(0.01) result | expects >= 0.2 | actually 0.05 |

**Verification**:
```
step(0.01) -> dist=0.05, clamped=True
Passes dist_min >= 0.05: True
Passes dist_min >= 0.2: False  ← qa_probe would FAIL with old expectation
```

**Fix applied**: Updated `qa_probe.py` lines 364, 386, 389, 393:
- Docstring: `[0.2, 5.0]` → `[0.05, 5.0]`
- Assertion: `dist_min >= 0.2` → `dist_min >= 0.05`
- Expected text: `dist_min>=0.2` → `dist_min>=0.05`
- Evidence: `_DIST_MIN=0.2` → `_DIST_MIN=0.05`

**Old expected**: dist_min >= 0.2
**New expected**: dist_min >= 0.05

**Verdict**: PASS (fix applied)

---

## Task 7: 幽灵索引清理

**Test**: Check 5 phantom entries against explorable_index.json, localcolor.json, humanities.json

**All 5 entries are PHANTOM** — exist in index but have no backing data:

| Entry | In Index | In localcolor | In humanities | Lat/Lon | Status |
|-------|----------|--------------|---------------|---------|--------|
| 南极磷虾 | YES | NO | NO | N/A | PHANTOM |
| 墨西哥湾流 | YES | NO | NO | N/A | PHANTOM |
| 深海热泉 | YES | NO | NO | N/A | PHANTOM |
| 珊瑚礁 | YES | NO | NO | N/A | PHANTOM |
| 黑潮 | YES | NO | NO | N/A | PHANTOM |

**Index entries**: All have `layers: {localcolor: true}`, 黑潮 also has `knowledge: true`. None have lat/lon coordinates.

**Recommendation**: Remove all 5 entries from `explorable_index.json`:
- `nowhere/data/explorable_index.json` — remove keys: 南极磷虾, 墨西哥湾流, 深海热泉, 珊瑚礁, 黑潮

**Verdict**: PASS (identification complete, removal recommended)

---

## Summary

| Task | Card | Description | Result |
|------|------|-------------|--------|
| 1 | 32 | 拉普兰12连抽 | CONDITIONAL PASS (8 hw cards, not 4; tier system correct) |
| 2 | 35 | 渲染链探针 | **FAIL** (1 forbidden word "很" in scene template) |
| 3 | 37 | 长江5步 | PASS (all steps have water content) |
| 4 | 39 | 长江5步复读 | **FAIL** (9 repeated sentence types) |
| 5 | 40 | 15步密度衰减 | PASS (depth 2→27km, no loop-back) |
| 6 | — | Probe clamp更新 | PASS (fixed 0.2→0.05 in qa_probe.py) |
| 7 | — | 幽灵索引清理 | PASS (5 phantoms identified) |

**Passed**: 4/7 (Tasks 3, 5, 6, 7)
**Conditional**: 1/7 (Task 1)
**Failed**: 2/7 (Tasks 2, 4)

### Action Items

1. **[Task 2]** Fix "车很多" in `nowhere/data/scene_walk_discovery.txt:115` and `nowhere/data/scenes_src/discovery.json:915` — change to "车不少" or "车一辆接一辆"
2. **[Task 4]** Add more variants to `_river_alignment_text()` pools in `server.py` lines 1282-1304 (currently only 3-4 options per category)
3. **[Task 7]** Remove 5 phantom entries from `nowhere/data/explorable_index.json`
4. **[Task 6]** qa_probe.py already updated (0.2 → 0.05)
