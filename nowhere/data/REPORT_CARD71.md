# REPORT_CARD71 — 水系段按坐标就近 + Situation 覆盖补全

## 改动清单

| 文件 | 改动 |
|---|---|
| `nowhere/server.py` | `_find_river_segment` 签名加 lat/lon + haversine 距离计分;调用处 2628 传 lat/lon;B1 water biome 过滤;B2 radio cc 拒绝 |
| `nowhere/radio.py` | `_pick_nearest_from_fallback` culture circle + global nearest 加 cc 不匹配拒绝(Budapest ≠ CZ) |
| `nowhere/describe.py` | B4 sanity_check 加 time_of_day 门:dawn/night 过滤夕阳/日落/晚霞;day 过滤月亮/星辰 |
| `nowhere/tests/test_situation_full.py` | 新建,8 个测试 |

## A. 水系段按坐标就近

- `_find_river_segment(name, segment_hint="", lat=None, lon=None)` — 签名扩展
- lat/lon 提供时用 haversine 距离计分(越近分越高)
- lat/lon 为 None 时保留原 scenic 回退(三峡/宜昌)
- 调用处 server.py:2628 传当前 lat/lon

验证:
```
太仓(31.45, 121.1) → 长江 上海段 ✅
宜昌(30.7, 111.3)  → 长江 宜昌段 ✅
无坐标              → 长江 宜昌段(scenic 回退) ✅
```

`grep -n "scenic = any" nowhere/server.py` → 0(已删)

## B. Situation 覆盖补全

### B1. water biome 过滤
city biome 无 coastal 水系时,过滤 ocean 类型。内陆城市不出海洋段。

### B2. radio cc 拒绝
server.py `_get_radio`:station.cc ≠ listener.cc → reject(None)
radio.py `_pick_nearest_from_fallback`:culture circle 和 global nearest 都加 cc 匹配门。
Budapest(47.5, 19.0) → 无 HU fallback 站 → 静默(None)。✅

### B3. phenology 已接
`_get_climate_zone(lat, elev)` 已有 elev≥3000→寒带 override。
`_check_phenology` 已按 climate_zone 过滤。✅ 无需改动。

### B4. seasonal time_of_day 门
describe.py `sanity_check` 新增:
- dawn/night:过滤夕阳/日落/晚霞/残阳/落日
- day:过滤月亮/月光/星辰/夜幕/星空

验证:Budapest 凌晨 05:30 不出"夕阳"。✅

### B5. 台风海腥 — 数据缺位
seasonal_natural.txt/seasonal_forests.txt 里的台风句 biome 标签有误(标了 mountain/natural 而非 coastal)。归卡33 扩编,本卡不改数据。

## 测试

```
8 passed in 2.07s
  test_taicang_no_three_gorges      PASSED
  test_yichang_has_three_gorges     PASSED
  test_budapest_no_czech_radio      PASSED
  test_oslo_no_grapes               PASSED
  test_budapest_dawn_no_sunset      PASSED
  test_night_no_sunset              PASSED
  test_day_no_moon                  PASSED
  test_river_segment_no_coords_scenic_fallback  PASSED
```

回归:64/65 pass,唯一失败 test_biome_intersection(N1 老账,与本卡无关)。

## 验收清单

- [x] `grep -n "scenic = any" nowhere/server.py` → 0
- [x] `grep -n "_find_river_segment" nowhere/server.py` → 2628 传了 lat/lon
- [x] test_situation_full.py 全绿(8/8)
- [x] 太仓无三峡
- [x] 布达佩斯无 CZ 台
- [x] 奥斯陆无葡萄
- [x] 布达佩斯凌晨无夕阳
- [x] 张家界无台风(数据缺位标 B5,归卡33)
