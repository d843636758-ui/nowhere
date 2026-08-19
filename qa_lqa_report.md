# QA LQA Report — Card 24: 语义文本审计

**生成时间**: 2026-08-20 02:24
**耗时**: 51.8 秒
**样本数**: 576 (land + walk)
**总 bug 数**: 88

## 按严重度汇总

| 严重度 | 数量 | 说明 |
|--------|------|------|
| S1 | 1 | 严重 (幻觉/数字矛盾/自称矛盾) |
| S2 | 10 | 重大 (场景错配/地名漂移) |
| S3 | 6 | 轻微 (禁词/格式/断气) |
| S4 | 71 | 打磨 (多样性/长度) |

## S1: 严重问题

| ID | 现象 | 复现输入 | 根因初判 |
|----|------|----------|----------|
| R0013 | 温度 -5.0 度但文本说「热」 | place=wild_-38.5_-90.6, action=land, time=night, temp=-5.0, biome=coast, lat=-38 | 温度数据与文本体感矛盾,场景过滤未生效 |

## S2: 重大问题

| ID | 现象 | 复现输入 | 根因初判 |
|----|------|----------|----------|
| R0001 | 地名漂移: 同段出现 {'远处岛', '你站在福浦桥', '松树的香气从瑞岩寺'} | place=仙台, action=land, time=dusk, temp=15, biome=city, lat=38.27 | 多张卡拼接时地名未统一 |
| R0002 | 地名漂移: 同段出现 {'的唤礼声从宣礼塔', '清真寺'} | place=阿比让, action=land, time=dusk, temp=15, biome=city, lat=5.36 | 多张卡拼接时地名未统一 |
| R0003 | 地名漂移: 同段出现 {'冷的火山', '富士山'} | place=富士山, action=land, time=dusk, temp=15, biome=mountain, lat=35.36 | 多张卡拼接时地名未统一 |
| R0004 | 地名漂移: 同段出现 {'乳香在老市', '隔壁香料铺的卡塔'} | place=马斯喀特, action=land, time=night, temp=15, biome=city, lat=23.59 | 多张卡拼接时地名未统一 |
| R0005 | 地名漂移: 同段出现 {'远处的山', '一群浮在牛奶上的岛', '你站在山'} | place=黄山, action=land, time=dawn, temp=15, biome=rainforest, lat=30.13 | 多张卡拼接时地名未统一 |
| R0006 | 地名漂移: 同段出现 {'远处的山', '一群浮在牛奶上的岛', '你站在山'} | place=黄山, action=land, time=dusk, temp=15, biome=rainforest, lat=30.13 | 多张卡拼接时地名未统一 |
| R0007 | 地名漂移: 同段出现 {'飞来石立在山', '风从山'} | place=黄山, action=land, time=night, temp=15, biome=rainforest, lat=30.13 | 多张卡拼接时地名未统一 |
| R0008 | 地名漂移: 同段出现 {'顶上是佛塔', '普西山'} | place=琅勃拉邦, action=land, time=night, temp=15, biome=city, lat=19.89 | 多张卡拼接时地名未统一 |
| R0009 | 地名漂移: 同段出现 {'走过一袋一袋堆成山', '香料市'} | place=马拉喀什, action=land, time=dusk, temp=15, biome=city, lat=31.63 | 多张卡拼接时地名未统一 |
| R0010 | 地名漂移: 同段出现 {'公园的湖', '茂腔的调子从村'} | place=高密, action=land, time=night, temp=15, biome=city, lat=36.38 | 多张卡拼接时地名未统一 |

## S3: 轻微问题

| ID | 现象 | 复现输入 | 根因初判 |
|----|------|----------|----------|
| R0011 | 禁词「很」出现在渲染文本中 | place=岳阳楼, action=land, time=dusk, temp=15, biome=city, lat=29.38 | 模板或卡片中残留禁词,describe.py 规则要求禁止 |
| R0012 | 禁词「很」出现在渲染文本中 | place=岳阳楼, action=land, time=night, temp=15, biome=city, lat=29.38 | 模板或卡片中残留禁词,describe.py 规则要求禁止 |
| R0014 | 缺句号拼接断气: 味觉/触觉描述与声景之间缺少句号 | place=科隆, action=land, time=dusk | describe.compose() 未对缺少标点的段落做补全 |
| R0015 | 缺句号拼接断气: 味觉/触觉描述与声景之间缺少句号 | place=塔林, action=land, time=dusk | describe.compose() 未对缺少标点的段落做补全 |
| R0016 | 缺句号拼接断气: 味觉/触觉描述与声景之间缺少句号 | place=尼斯, action=land, time=dusk | describe.compose() 未对缺少标点的段落做补全 |
| R0017 | 缺句号拼接断气: 味觉/触觉描述与声景之间缺少句号 | place=wild_-14.0_66.4, action=land, time=dawn | describe.compose() 未对缺少标点的段落做补全 |

## S4: 多样性不足 (ERA 量化)

| ID | 现象 | 复现输入 | 根因初判 |
|----|------|----------|----------|
| D0001 | 多样性不足: 悉尼歌剧院@dawn 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=悉尼歌剧院, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0002 | 多样性不足: 悉尼歌剧院@dusk 去重率 60.0% (仅 12 个唯一变体 / 30 次) | place=悉尼歌剧院, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0003 | 多样性不足: 悉尼歌剧院@night 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=悉尼歌剧院, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0004 | 多样性不足: 唐山@dawn 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=唐山, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0005 | 多样性不足: 唐山@dusk 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=唐山, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0006 | 多样性不足: 唐山@night 去重率 46.7% (仅 16 个唯一变体 / 30 次) | place=唐山, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0007 | 多样性不足: 耶路撒冷@dawn 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=耶路撒冷, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0008 | 多样性不足: 耶路撒冷@dusk 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=耶路撒冷, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0009 | 多样性不足: 耶路撒冷@night 去重率 56.7% (仅 13 个唯一变体 / 30 次) | place=耶路撒冷, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0010 | 多样性不足: 科隆@dawn 去重率 63.3% (仅 11 个唯一变体 / 30 次) | place=科隆, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0011 | 多样性不足: 科隆@dusk 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=科隆, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0012 | 多样性不足: 科隆@night 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=科隆, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0013 | 多样性不足: 道后温泉@dawn 去重率 46.7% (仅 16 个唯一变体 / 30 次) | place=道后温泉, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0014 | 多样性不足: 道后温泉@dusk 去重率 56.7% (仅 13 个唯一变体 / 30 次) | place=道后温泉, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0015 | 多样性不足: 道后温泉@night 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=道后温泉, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0016 | 多样性不足: 仙台@dawn 去重率 43.3% (仅 17 个唯一变体 / 30 次) | place=仙台, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0017 | 多样性不足: 仙台@dusk 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=仙台, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0018 | 多样性不足: 仙台@night 去重率 46.7% (仅 16 个唯一变体 / 30 次) | place=仙台, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0019 | 多样性不足: 克拉科夫@dawn 去重率 56.7% (仅 13 个唯一变体 / 30 次) | place=克拉科夫, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0020 | 多样性不足: 克拉科夫@dusk 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=克拉科夫, time=dusk, layer=terrain | 渲染分支变体池太浅 |

## 多样性量化表 (最差 10 个地/层)

| 地点 | 层 | 时段 | 运行次数 | 唯一变体 | 去重率 | 判定 |
|------|------|------|----------|----------|--------|------|
| 科隆 | terrain | dawn | 30 | 11 | 63.3% | S4 (池浅) |
| 富士山 | terrain | dusk | 30 | 11 | 63.3% | S4 (池浅) |
| 悉尼歌剧院 | terrain | dusk | 30 | 12 | 60.0% | S4 (池浅) |
| 耶路撒冷 | terrain | night | 30 | 13 | 56.7% | S4 (池浅) |
| 道后温泉 | terrain | dusk | 30 | 13 | 56.7% | S4 (池浅) |
| 克拉科夫 | terrain | dawn | 30 | 13 | 56.7% | S4 (池浅) |
| 克拉科夫 | terrain | night | 30 | 13 | 56.7% | S4 (池浅) |
| 阿比让 | terrain | dawn | 30 | 13 | 56.7% | S4 (池浅) |
| 塔林 | terrain | night | 30 | 13 | 56.7% | S4 (池浅) |
| 尼斯 | terrain | night | 30 | 13 | 56.7% | S4 (池浅) |

## 变体池大小清单 (<5 条的分支)

| 池名 | 条数 | 判定 |
|------|------|------|
| _ARRIVE_VARIANTS | 4 | S4 |
| _WEATHER_ABS_VARIANTS | 3 | S4 |
| _WEATHER_RAIN_VARIANTS | 3 | S4 |
| _WEATHER_SNOW_VARIANTS | 3 | S4 |
| _WEATHER_STORM_VARIANTS | 3 | S4 |
| _WEATHER_DELTA_VARIANTS | 3 | S4 |
| _TERRAIN_VARIANTS | 3 | S4 |
| _TERRAIN_SCREE_VARIANTS | 3 | S4 |
| _TERRAIN_FLAT_VARIANTS | 3 | S4 |
| _TERRAIN_FLAT_GRASS_VARIANTS | 3 | S4 |
| _TERRAIN_FLAT_BARE_VARIANTS | 3 | S4 |
| _TERRAIN_FLAT_ROCK_VARIANTS | 3 | S4 |
| _TERRAIN_FLAT_URBAN_VARIANTS | 3 | S4 |
| _TERRAIN_FLAT_WATER_VARIANTS | 3 | S4 |
| _TERRAIN_HIGH_FLAT_VARIANTS | 3 | S4 |
| _SKY_NIGHT_VARIANTS | 3 | S4 |
| _SKY_DAY_VARIANTS | 3 | S4 |
| _SKY_DAY_LOW_VARIANTS | 3 | S4 |
| _WATER_COLD_VARIANTS | 3 | S4 |
| _WATER_COOL_VARIANTS | 3 | S4 |
| _WATER_WARM_VARIANTS | 3 | S4 |
| _LIFE_VARIANTS | 3 | S4 |
| _ART_VARIANTS | 3 | S4 |
| _RADIO_VARIANTS | 3 | S4 |
| _BLOCKED_VARIANTS | 3 | S4 |
| _MESSAGE_VARIANTS | 4 | S4 |

## LLM 裁判校验

LLM 裁判不可用 (未设置 SILICONFLOW_API_KEY / SF_API_KEY)。

## 三层对比

| 层 | 捕获 bug 数 | 说明 |
|----|------------|------|
| Layer 2 规则层 | 88 | 全量,免费,确定性 |
| Layer 3 LLM 裁判 | 0 | 抽样 0 条 (不可用) |
| 合计 | 88 | |

## 已知 bug 复现

- 「像刚下过雪风声大」缺句号拼接: 已复现

## 备注

- 本次运行覆盖 41 个地点
- 采样使用离线渲染(气候估算+模板),未联网获取实时天气/电台
- 多样性测试使用 describe.render() 的 terrain 分支
- LLM 裁判使用硅基流动 DeepSeek-V3 (需设置 SILICONFLOW_API_KEY 环境变量)