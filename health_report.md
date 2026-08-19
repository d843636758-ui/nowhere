# Nowhere Health Report

**Generated**: 2026-08-20 05:12
**Total items**: 57 | **Pass**: 34 | **Fail**: 22 | **Skip**: 1
**Total time**: 160.1s

## Summary by Source

| Source | Items | Pass | Fail | Skip | Time |
|--------|-------|------|------|------|------|
| geocode | 8 | 1 | 7 | 0 | 38.1s |
| probe | 36 | 31 | 5 | 0 | 61.9s |
| alignment | 11 | 2 | 8 | 1 | 0.7s |
| lqa | 1 | 0 | 1 | 0 | 60.2s |
| tests | 1 | 0 | 1 | 0 | 160.1s |

## GEOCODE

| ID | Level | Phenomenon | Reproduction |
|----|-------|------------|--------------|
| GEO-台北 | ✗ | 台北: 期望 CN, 实际 TW | trace_lookup('台北') -> (25.0531, 121.5264) via cities15000(Taipei,cc=TW,pop=78719 |
| GEO-香港 | ✗ | 香港: 期望 CN, 实际 HK | trace_lookup('香港') -> (22.2783, 114.1747) via cities15000(Hong Kong,cc=HK,pop=73 |
| GEO-澳门 | ✗ | 澳门: 期望 CN, 实际 MO | trace_lookup('澳门') -> (22.2006, 113.5461) via cities15000(Macau,cc=MO,pop=649335 |
| GEO-维也纳 | ✗ | 维也纳: 期望 AT, 实际 None | trace_lookup('维也纳') -> N/A via no_match(skipped_nominatim) |
| GEO-河内 | ✗ | 河内: 期望 VN, 实际 JP | trace_lookup('河内') -> (34.4411, 135.5828) via cities15000(Kawachi-Nagano,cc=JP,p |
| GEO-利马 | ✗ | 利马: 期望 PE, 实际 CY | trace_lookup('利马') -> (34.6841, 33.0379) via cities15000(Limassol,cc=CY,pop=1540 |
| GEO-温哥华 | ✗ | 温哥华: 期望 CA, 实际 None | trace_lookup('温哥华') -> N/A via no_match(skipped_nominatim) |
| GEO-FUZHOU | ✓ | 福州解析正确: Fuzhou (26.06139, 119.30611) | - |

### GEOCODE Failures Detail

- **GEO-台北**: 台北: 期望 CN, 实际 TW
  - Reproduction: `trace_lookup('台北') -> (25.0531, 121.5264) via cities15000(Taipei,cc=TW,pop=7871900,score=3.0,exact_alt:台北)`
- **GEO-香港**: 香港: 期望 CN, 实际 HK
  - Reproduction: `trace_lookup('香港') -> (22.2783, 114.1747) via cities15000(Hong Kong,cc=HK,pop=7396076,score=3.0,exact_alt:香港)`
- **GEO-澳门**: 澳门: 期望 CN, 实际 MO
  - Reproduction: `trace_lookup('澳门') -> (22.2006, 113.5461) via cities15000(Macau,cc=MO,pop=649335,score=3.0,exact_alt:澳门)`
- **GEO-维也纳**: 维也纳: 期望 AT, 实际 None
  - Reproduction: `trace_lookup('维也纳') -> N/A via no_match(skipped_nominatim)`
- **GEO-河内**: 河内: 期望 VN, 实际 JP
  - Reproduction: `trace_lookup('河内') -> (34.4411, 135.5828) via cities15000(Kawachi-Nagano,cc=JP,pop=101692,score=1.0,partial_alt:河内長野)`
- **GEO-利马**: 利马: 期望 PE, 实际 CY
  - Reproduction: `trace_lookup('利马') -> (34.6841, 33.0379) via cities15000(Limassol,cc=CY,pop=154000,score=1.0,partial_alt:利马索尔)`
- **GEO-温哥华**: 温哥华: 期望 CA, 实际 None
  - Reproduction: `trace_lookup('温哥华') -> N/A via no_match(skipped_nominatim)`

## PROBE

| ID | Level | Phenomenon | Reproduction |
|----|-------|------------|--------------|
| PRB-0b.1 walk(distance_k | ✗ | [Input] 0b.1 walk(distance_km=-5) negative: dist=0.05, blocked=False | clamped=True |
| PRB-0b.2 walk(distance_k | ✗ | [Input] 0b.2 walk(distance_km=0) zero: dist=0.05 | clamped=True |
| PRB-0b.3 walk(distance_k | ✓ | [Input] 0b.3 walk(distance_km=NaN) not-a-number: dist=5.0, pos_nan=False, blocke | NaN propagates through _clamp_dist; step should guard or crash gracefully |
| PRB-0b.4 walk(distance_k | ✓ | [Input] 0b.4 walk(distance_km=1e9) huge: dist=5.0, clamped=True | - |
| PRB-0b.5 walk(distance_k | ✓ | [Input] 0b.5 walk(distance_km='abc') string: raised TypeError: '<' not supported | expected: type error on string input |
| PRB-0b.6 open_door(to='' | ✓ | [Input] 0b.6 open_door(to='') empty string: text=找不到「」。, error=not_found | - |
| PRB-0b.7 open_door(500ch | ✓ | [Input] 0b.7 open_door(500chars+newlines) long+control: text=找不到「aaaaaaaaaaaaaaa | - |
| PRB-0b.8 open_door('!@#$ | ✓ | [Input] 0b.8 open_door('!@#$%^&*()') special chars: text=找不到「!@#$%^&*()」。 | - |
| PRB-0b.9 listen(seconds= | ✓ | [Input] 0b.9 listen(seconds=-1) negative: text=听多久？给个数。, error=bad_seconds | - |
| PRB-0c.1 date line lon w | ✓ | [Polar] 0c.1 date line lon wrap (179.99E -> E 5km): dest_lon=-179.9630, step_lon | terrain.destination uses ((lon+180)%360)-180 |
| PRB-0c.2 country_code ne | ✓ | [Polar] 0c.2 country_code near ±180 date line: FJ? cc_178=FJ, cc_179.99=FJ, cc_- | country_code_of uses dlon wrapping |
| PRB-0c.3 walk at lat=85  | ✓ | [Polar] 0c.3 walk at lat=85 near pole: lat=85.000000, blocked=False | lon=0.000000 |
| PRB-0c.4 country_code_of | ✓ | [Polar] 0c.4 country_code_of(South Pole): cc=AR | nearest city to -90,0 is probably in southern hemisphere |
| PRB-0c.5 food_items(None | ✓ | [Polar] 0c.5 food_items(None) no crash: type=list, len=0 | - |
| PRB-0c.6 places.nearby(l | ✓ | [Polar] 0c.6 places.nearby(lat=85) cos->0: DB issue (not code bug): OperationalE | places.db missing or malformed in test env |
| PRB-1.1 timezone Beijing | ✓ | [Time] 1.1 timezone Beijing vs NY: BJ=22h NY=10h diff=12h | BJ tz=Asia/Shanghai, NY tz=America/New_York |
| PRB-1.2 wait(3) exact +3 | ✓ | [Time] 1.2 wait(3) exact +3h: delta=3.00h | before=2026-07-15T10:00:00+00:00 after=2026-07-15T13:00:00+00:00 |
| PRB-1.3 walk(2km) time i | ✓ | [Time] 1.3 walk(2km) time increment: delta=0.500h | dist_km=2.0, slope=0.0 |
| PRB-1.4 walk_to double-c | ✓ | [Time] 1.4 walk_to double-counting: steps=1, elapsed=1.250h | Code review: walk_to_impl has no extra += after loop (Card 1 fix) |
| PRB-1.5 southern hemisph | ✓ | [Time] 1.5 southern hemisphere Jan = summer: summer | _season(1, -33.87) = summer |
| PRB-1.6 Iceland July whi | ✓ | [Time] 1.6 Iceland July white night: moment=白夜, has_polar_kw=True | text snippet: 【冰岛,雷克雅未克,白夜,夏天。】冬天的街道在下午三点就暗下来，你走在彩色铁皮房子之间，风从港口方向吹来，穿透所有衣服层。空气冷得像 |
| PRB-2.1 walk N 2km latit | ✓ | [Walking] 2.1 walk N 2km latitude increase: lat+=2.00km, dist=2.0km | blocked=False, pos=(40.01799,116.00000) |
| PRB-2.2 uphill flat → no | ✓ | [Walking] 2.2 uphill flat → no_gain: no_gain=True, pos_moved=False | pos_before=(39.9, 116.4) pos_after=(39.9, 116.4) |
| PRB-2.3 cliff blocked: n | ✓ | [Walking] 2.3 cliff blocked: no time, no move: no cliff found in 8 directions at | Location may not have cliff-grade slopes at 5km steps |
| PRB-2.4 clamp 0.01→0.2,  | ✗ | [Walking] 2.4 clamp 0.01→0.2, 100→5.0: min: dist=0.05,clamped=True; max: dist=5. | _DIST_MIN=0.2, _DIST_MAX=5.0 |
| PRB-2.5 8 directions → ≈ | ✓ | [Walking] 2.5 8 directions → ≈ origin: dist=0.00km, final=(39.99999,116.00003) | origin=(40.0,116.0) |
| PRB-3.1 text quality sca | ✓ | [Rendering] 3.1 text quality scan (20 walks): 0 issue types found | clean scan, no issues found |
| PRB-3.2 forbidden words  | ✓ | [Rendering] 3.2 forbidden words in describe.py templates: 0 found | clean |
| PRB-4.1 index says local | ✗ | [Data] 4.1 index says localcolor but no data file: 29 missing out of 415 | sample: ['保加利亚', '克罗地亚', '内蒙古', '匈牙利', '南极磷虾', '塔什干', '墨西哥湾流', '大马士革', '安塔利亚', ' |
| PRB-4.2 food_by_country  | ✗ | [Data] 4.2 food_by_country zh='' entries: 574 empty zh out of 765 total | sample: [{'country': 'HU', 'en': 'paprikash', 'desc': '鸡肉在红椒粉奶油酱中炖至酥烂，酱汁浓郁红亮，拌面团 |
| PRB-5.1 save→load roundt | ✓ | [State] 5.1 save→load roundtrip: 0 mismatches | all fields match |
| PRB-5.2 corrupted journe | ✓ | [State] 5.2 corrupted journey.json → no crash: load() returned None | wrote garbage, load() should return None |
| PRB-5b.1 postcard: same  | ✓ | [Idempotency] 5b.1 postcard: same text twice: duplicate billing; ids=101,102; sa | card count=2 |
| PRB-5b.2 mark: same name | ✓ | [Idempotency] 5b.2 mark: same name twice: reasonable rejection | r1_err=None, r2_err=duplicate |
| PRB-5b.3 open_door: same | ✓ | [Idempotency] 5b.3 open_door: same dest twice: idempotent (resumed journey); res | pos1=(39.9, 116.4), pos2=(39.9, 116.4) |
| PRB-5c.1 direction vocab | ✓ | [Vocabulary] 5c.1 direction vocabulary recognition (30 phrases): 4/30 = 13.3% | recognized: ['北', '南', '东', '西'] |

### PROBE Failures Detail

- **PRB-0b.1 walk(distance_k**: [Input] 0b.1 walk(distance_km=-5) negative: dist=0.05, blocked=False
  - Reproduction: `clamped=True`
  - Detail: expected: clamped to >=0.2, no crash
- **PRB-0b.2 walk(distance_k**: [Input] 0b.2 walk(distance_km=0) zero: dist=0.05
  - Reproduction: `clamped=True`
  - Detail: expected: clamped to >=0.2
- **PRB-2.4 clamp 0.01→0.2, **: [Walking] 2.4 clamp 0.01→0.2, 100→5.0: min: dist=0.05,clamped=True; max: dist=5.0,clamped=True
  - Reproduction: `_DIST_MIN=0.2, _DIST_MAX=5.0`
  - Detail: expected: dist_min>=0.2, dist_max<=5.0, both clamped
- **PRB-4.1 index says local**: [Data] 4.1 index says localcolor but no data file: 29 missing out of 415
  - Reproduction: `sample: ['保加利亚', '克罗地亚', '内蒙古', '匈牙利', '南极磷虾', '塔什干', '墨西哥湾流', '大马士革', '安塔利亚', '`
  - Detail: expected: 0 missing (all 415 index places have data)
- **PRB-4.2 food_by_country **: [Data] 4.2 food_by_country zh='' entries: 574 empty zh out of 765 total
  - Reproduction: `sample: [{'country': 'HU', 'en': 'paprikash', 'desc': '鸡肉在红椒粉奶油酱中炖至酥烂，酱汁浓郁红亮，拌面团`
  - Detail: expected: 0 entries with empty zh

## ALIGNMENT

| ID | Level | Phenomenon | Reproduction |
|----|-------|------------|--------------|
| ALN-1-KNOWN5 | ✓ | 文化区矩形: 已知5实锤全部复现 (5/5) | - |
| ALN-1-OTHER | ✗ | 文化区矩形: 额外 62 个城市错配 (总 67) | qa_alignment.audit_1_region_rectangles() |
| ALN-2-南极磷虾 | ✗ | 地名键漂移[索引有但数据无]: 南极磷虾 | explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到 |
| ALN-2-墨西哥湾流 | ✗ | 地名键漂移[索引有但数据无]: 墨西哥湾流 | explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到 |
| ALN-2-深海热泉 | ✗ | 地名键漂移[索引有但数据无]: 深海热泉 | explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到 |
| ALN-2-珊瑚礁 | ✗ | 地名键漂移[索引有但数据无]: 珊瑚礁 | explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到 |
| ALN-2-黑潮 | ✗ | 地名键漂移[索引有但数据无]: 黑潮 | explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到 |
| ALN-2-MORE | S | 还有 1 个实锤键漂移 (见 qa_alignment_report.md) | - |
| ALN-3-多国 | ✗ | 国家码[zh空串条目]: 多国 | 共 574 条食物 zh 为空串, 渲染时会混入英文菜名 |
| ALN-3-DD | ✗ | 国家码[已不存在的国家码]: DD | 东德(DD)已不存在, food_by_country 有 1 道菜 |
| ALN-4 | ✓ | 历法漂移: 0 个发现, 无实锤 | - |

### ALIGNMENT Failures Detail

- **ALN-1-OTHER**: 文化区矩形: 额外 62 个城市错配 (总 67)
  - Reproduction: `qa_alignment.audit_1_region_rectangles()`
- **ALN-2-南极磷虾**: 地名键漂移[索引有但数据无]: 南极磷虾
  - Reproduction: `explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到`
- **ALN-2-墨西哥湾流**: 地名键漂移[索引有但数据无]: 墨西哥湾流
  - Reproduction: `explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到`
- **ALN-2-深海热泉**: 地名键漂移[索引有但数据无]: 深海热泉
  - Reproduction: `explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到`
- **ALN-2-珊瑚礁**: 地名键漂移[索引有但数据无]: 珊瑚礁
  - Reproduction: `explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到`
- **ALN-2-黑潮**: 地名键漂移[索引有但数据无]: 黑潮
  - Reproduction: `explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到`
- **ALN-3-多国**: 国家码[zh空串条目]: 多国
  - Reproduction: `共 574 条食物 zh 为空串, 渲染时会混入英文菜名`
- **ALN-3-DD**: 国家码[已不存在的国家码]: DD
  - Reproduction: `东德(DD)已不存在, food_by_country 有 1 道菜`

## LQA

| ID | Level | Phenomenon | Reproduction |
|----|-------|------------|--------------|
| R0001 | ✗ | [S2] 内陆 biome (city) 出现海港词「码头」 | place=惠灵顿, action=land, time=dusk, temp=10.4, biome=city, lat=-41.29 |

### LQA Failures Detail

- **R0001**: [S2] 内陆 biome (city) 出现海港词「码头」
  - Reproduction: `place=惠灵顿, action=land, time=dusk, temp=10.4, biome=city, lat=-41.29`
  - Detail: 场景过滤未覆盖内陆情况

## TESTS

| ID | Level | Phenomenon | Reproduction |
|----|-------|------------|--------------|
| TEST-TIMEOUT | ✗ | pytest 超时 (>160s) | python -m pytest nowhere/tests -q |

### TESTS Failures Detail

- **TEST-TIMEOUT**: pytest 超时 (>160s)
  - Reproduction: `python -m pytest nowhere/tests -q`

---

## New Confirmed Bug Types

No new bug types since last run.
