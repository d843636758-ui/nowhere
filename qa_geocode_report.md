# QA Geocode Report

Generated: 2026-08-20 02:02

## Summary

- Total tested: 84
- Mismatches: **7**

## Mismatch Table

| Place | Expected CC | Actual CC | Coords | Hit Chain |
|-------|-------------|-----------|--------|-----------|
| 台北 | CN | TW | (25.0531, 121.5264) | cities15000(Taipei,cc=TW,pop=7871900,score=3.0,exact_alt:台北) |
| 香港 | CN | HK | (22.2783, 114.1747) | cities15000(Hong Kong,cc=HK,pop=7396076,score=3.0,exact_alt:香港) |
| 澳门 | CN | MO | (22.2006, 113.5461) | cities15000(Macau,cc=MO,pop=649335,score=3.0,exact_alt:澳门) |
| 维也纳 | AT | None | N/A | no_match(skipped_nominatim) |
| 河内 | VN | JP | (34.4411, 135.5828) | cities15000(Kawachi-Nagano,cc=JP,pop=101692,score=1.0,partial_alt:河内長野) |
| 利马 | PE | CY | (34.6841, 33.0379) | cities15000(Limassol,cc=CY,pop=154000,score=1.0,partial_alt:利马索尔) |
| 温哥华 | CA | None | N/A | no_match(skipped_nominatim) |

## 福州 Root Cause Analysis

### All matching entries for '福州' in cities15000.txt

| Name | ASCII | Lat | Lon | CC | Pop | Score | Rank | Match Paths | Has 福州 in alts |
|------|-------|-----|-----|----|-----|-------|------|-------------|-----------------|
| Fuzhou | Fuzhou | 26.06139 | 119.30611 | CN | 3740000 | 3.0 | 3000003740000 | exact_alt:[福州] | True |

### Winner: Fuzhou at (26.06139, 119.30611)

- Match paths: exact_alt:[福州]
- Population: 3740000
- Score: 3.0, Rank: 3000003740000

### Correct entry: Fuzhou at (26.06139, 119.30611)

- Population: 3740000
- Has 福州 in alternatenames: True

### Root Cause

The geocode chain is: special_places -> places.find -> cities15000 -> Nominatim.

For '福州': special_places has no entry; places.db is empty (no tables), so places.find returns None.

In cities15000.txt there are two entries with ASCII name 'Fuzhou':

1. **Jiangxi (抚州)**: lat=27.95999, lon=116.33333, pop=1,089,888. Alternatenames do NOT contain '福州'. Scores via partial_name match (score=2.0) since '福州' is not a substring of 'Fuzhou' — this entry should NOT match.

2. **Fujian (福州)**: lat=26.06139, lon=119.30611, pop=3,740,000. Alternatenames contain '福州' (exact alt, score=3.0). This is the correct match.

The current code correctly returns the Fujian entry (score=3.0 beats no match). If the historical bug was that 福州 resolved to Jiangxi/Zhejiang, it was likely due to:

- **Scenario A**: The Jiangxi entry's alternatenames previously contained '福州' as a variant, giving it score=3.0 with higher rank (score*1e12 is equal, but population tiebreak: Jiangxi pop < Fujian pop, so Fujian should still win).
- **Scenario B**: places.db was not empty and had a wrong entry for 福州 with Jiangxi/Zhejiang coordinates, which is checked before cities15000.
- **Scenario C**: The bug was in places_patch.json having a wrong entry.

Recommendation: Ensure places_patch.json and places.db never contain conflicting entries for well-known cities. Add a disambiguation step: when multiple cities share the same ASCII name, prefer the one whose Chinese name matches the query exactly in alternatenames.

## Dataset Samples (localcolor / humanities)

No expected country code — for human review.

| Place | Coords | Country Code | Hit Chain |
|-------|--------|-------------|-----------|
| K2大本营 | N/A | None | no_match(skipped_nominatim) |
| 乌斯怀亚 | (-54.8108, -68.3159) | AR | cities15000(Ushuaia,cc=AR,pop=56825,score=3.0,exact_alt:乌斯怀亚) |
| 亚速尔群岛 | N/A | None | no_match(skipped_nominatim) |
| 加拉帕戈斯 | N/A | None | no_match(skipped_nominatim) |
| 北海道 | N/A | None | no_match(skipped_nominatim) |
| 卑尔根 | N/A | None | no_match(skipped_nominatim) |
| 卡帕多西亚 | N/A | None | no_match(skipped_nominatim) |
| 卢克索 | N/A | None | no_match(skipped_nominatim) |
| 卢布尔雅那 | (46.0511, 14.5051) | SI | cities15000(Ljubljana,cc=SI,pop=272220,score=3.0,exact_alt:卢布尔雅那) |
| 塞维利亚 | (37.3828, -5.9732) | ES | cities15000(Sevilla,cc=ES,pop=686741,score=3.0,exact_alt:塞维利亚) |
| 圣彼得堡 | (59.9386, 30.3141) | RU | cities15000(Saint Petersburg,cc=RU,pop=5351935,score=3.0,exact_alt:圣彼得堡) |
| 塔林 | (59.4370, 24.7535) | EE | cities15000(Tallinn,cc=EE,pop=394024,score=3.0,exact_alt:塔林) |
| 大马士革 | (33.5102, 36.2913) | SY | cities15000(Damascus,cc=SY,pop=1569394,score=3.0,exact_alt:大马士革) |
| 马拉喀什 | (31.6342, -7.9999) | MA | cities15000(Marrakesh,cc=MA,pop=995871,score=3.0,exact_alt:马拉喀什) |
| 撒马尔罕 | (39.6546, 66.9644) | UZ | cities15000(Samarkand,cc=UZ,pop=595200,score=3.0,exact_alt:撒马尔罕) |
| 尾道 | (34.4167, 133.2000) | JP | cities15000(Onomichi,cc=JP,pop=131170,score=3.0,exact_alt:尾道) |
| 新潟 | (37.9226, 139.0412) | JP | cities15000(Niigata,cc=JP,pop=797591,score=3.0,exact_alt:新潟) |
| 长崎 | (32.7500, 129.8833) | JP | cities15000(Nagasaki,cc=JP,pop=409118,score=1.0,partial_alt:长崎市) |
| 广岛 | N/A | None | no_match(skipped_nominatim) |
| 敦刻尔克 | (51.0344, 2.3768) | FR | cities15000(Dunkirk,cc=FR,pop=86263,score=3.0,exact_alt:敦刻尔克) |
| 锡拉库萨 | N/A | None | no_match(skipped_nominatim) |
| 赤壁 | N/A | None | no_match(skipped_nominatim) |
| 荆州 | (30.3503, 112.1903) | CN | cities15000(Jingzhou,cc=CN,pop=1052282,score=1.0,partial_alt:荆州市) |
| 白帝城 | N/A | None | no_match(skipped_nominatim) |
| 曲阜 | (35.5967, 116.9911) | CN | cities15000(Qufu,cc=CN,pop=85144,score=1.0,partial_alt:曲阜市) |
| 布拉格 | (50.0880, 14.4208) | CZ | cities15000(Prague,cc=CZ,pop=1165581,score=3.0,exact_alt:布拉格) |
| 瓦尔帕莱索 | (-33.0360, -71.6296) | CL | cities15000(Valparaíso,cc=CL,pop=282448,score=3.0,exact_alt:瓦尔帕莱索) |
| 特奥蒂瓦坎 | N/A | None | no_match(skipped_nominatim) |
| 阿拉卡塔卡 | (10.5918, -74.1898) | CO | cities15000(Aracataca,cc=CO,pop=41872,score=3.0,exact_alt:阿拉卡塔卡) |
| 阿尤恩 | (27.1418, -13.1880) | EH | cities15000(Laayoune,cc=EH,pop=196331,score=3.0,exact_alt:阿尤恩) |

## Fix Suggestions

1. **cities15000 disambiguation**: When multiple entries match with the same score, prefer the one whose Chinese alternatenames contain the query. Currently the tiebreak is population only — add a 'query_lang_match' bonus.

2. **Country-aware filtering**: If the query is a Chinese city name, prefer entries with cc=CN. Use country.py's country_code_of to validate the result post-match.

3. **places_patch.json audit**: Ensure all patch entries have correct coordinates. No conflicting entries for cities already in cities15000.

4. **None result caching**: Currently geocode.py caches None results permanently. Failed lookups should not be cached (or cached with a short TTL) to allow retries after data fixes.
