# QA LQA Report — Card 24: 语义文本审计

**生成时间**: 2026-08-20 02:54
**耗时**: 295.4 秒
**样本数**: 648 (land + walk)
**总 bug 数**: 78

## 按严重度汇总

| 严重度 | 数量 | 说明 |
|--------|------|------|
| S1 | 0 | 严重 (幻觉/数字矛盾/自称矛盾) |
| S2 | 6 | 重大 (场景错配/地名漂移) |
| S3 | 1 | 轻微 (禁词/格式/断气) |
| S4 | 71 | 打磨 (多样性/长度) |

## S2: 重大问题

| ID | 现象 | 复现输入 | 根因初判 |
|----|------|----------|----------|
| R0002 | 内陆 biome (city) 出现海港词「码头」 | place=马普托, action=land, time=dawn, temp=19.8, biome=city, lat=-25.97 | 场景过滤未覆盖内陆情况 |
| R0003 | 内陆 biome (city) 出现海港词「码头」 | place=旧金山, action=land, time=night, temp=17.9, biome=city, lat=37.77 | 场景过滤未覆盖内陆情况 |
| R0004 | 内陆 biome (city) 出现海港词「码头」 | place=卑尔根, action=land, time=dusk, temp=15.0, biome=city, lat=60.39 | 场景过滤未覆盖内陆情况 |
| R0005 | 地名漂移: 同段出现 {'旧楼的楼', '的烤肉摊在市'} | place=温得和克, action=land, time=night, temp=2.0, biome=city, lat=-22.56 | 多张卡拼接时地名未统一 |
| R0006 | 地名漂移: 同段出现 {'的四合院门楼', '党家村'} | place=韩城, action=land, time=dusk, temp=16.1, biome=city, lat=35.48 | 多张卡拼接时地名未统一 |
| R0007 | 地名漂移: 同段出现 {'帕特农神庙', '的比雷埃夫斯港'} | place=雅典, action=land, time=night, temp=12.4, biome=city, lat=37.98 | 多张卡拼接时地名未统一 |

## S3: 轻微问题

| ID | 现象 | 复现输入 | 根因初判 |
|----|------|----------|----------|
| R0001 | 禁词「很」出现在渲染文本中 | place=波士顿, action=land, time=dusk, temp=31.1, biome=city, lat=42.36 | 模板或卡片中残留禁词,describe.py 规则要求禁止 |

## S4: 多样性不足 (ERA 量化)

| ID | 现象 | 复现输入 | 根因初判 |
|----|------|----------|----------|
| D0001 | 多样性不足: 卢森堡市@dawn 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=卢森堡市, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0002 | 多样性不足: 卢森堡市@dusk 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=卢森堡市, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0003 | 多样性不足: 卢森堡市@night 去重率 63.3% (仅 11 个唯一变体 / 30 次) | place=卢森堡市, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0004 | 多样性不足: 河内@dawn 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=河内, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0005 | 多样性不足: 河内@dusk 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=河内, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0006 | 多样性不足: 河内@night 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=河内, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0007 | 多样性不足: 波士顿@dawn 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=波士顿, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0008 | 多样性不足: 波士顿@dusk 去重率 46.7% (仅 16 个唯一变体 / 30 次) | place=波士顿, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0009 | 多样性不足: 波士顿@night 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=波士顿, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0010 | 多样性不足: 马普托@dawn 去重率 43.3% (仅 17 个唯一变体 / 30 次) | place=马普托, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0011 | 多样性不足: 马普托@dusk 去重率 43.3% (仅 17 个唯一变体 / 30 次) | place=马普托, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0012 | 多样性不足: 马普托@night 去重率 60.0% (仅 12 个唯一变体 / 30 次) | place=马普托, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0013 | 多样性不足: 萨尔茨堡@dawn 去重率 56.7% (仅 13 个唯一变体 / 30 次) | place=萨尔茨堡, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0014 | 多样性不足: 萨尔茨堡@dusk 去重率 46.7% (仅 16 个唯一变体 / 30 次) | place=萨尔茨堡, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0015 | 多样性不足: 萨尔茨堡@night 去重率 43.3% (仅 17 个唯一变体 / 30 次) | place=萨尔茨堡, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0016 | 多样性不足: 井冈山@dawn 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=井冈山, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0017 | 多样性不足: 井冈山@dusk 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=井冈山, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0018 | 多样性不足: 井冈山@night 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=井冈山, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0019 | 多样性不足: 的的喀喀湖@dawn 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=的的喀喀湖, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0020 | 多样性不足: 的的喀喀湖@dusk 去重率 46.7% (仅 16 个唯一变体 / 30 次) | place=的的喀喀湖, time=dusk, layer=terrain | 渲染分支变体池太浅 |

## 多样性量化表 (最差 10 个地/层)

| 地点 | 层 | 时段 | 运行次数 | 唯一变体 | 去重率 | 判定 |
|------|------|------|----------|----------|--------|------|
| 卢森堡市 | terrain | night | 30 | 11 | 63.3% | S4 (池浅) |
| 俄亥俄 | terrain | dawn | 30 | 11 | 63.3% | S4 (池浅) |
| 马普托 | terrain | night | 30 | 12 | 60.0% | S4 (池浅) |
| 特立尼达 | terrain | dawn | 30 | 12 | 60.0% | S4 (池浅) |
| 成都 | terrain | night | 30 | 12 | 60.0% | S4 (池浅) |
| 萨尔茨堡 | terrain | dawn | 30 | 13 | 56.7% | S4 (池浅) |
| 呼兰 | terrain | dawn | 30 | 13 | 56.7% | S4 (池浅) |
| 卢森堡市 | terrain | dawn | 30 | 14 | 53.3% | S4 (池浅) |
| 河内 | terrain | night | 30 | 14 | 53.3% | S4 (池浅) |
| 波士顿 | terrain | dawn | 30 | 14 | 53.3% | S4 (池浅) |

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
| Layer 2 规则层 | 78 | 全量,免费,确定性 |
| Layer 3 LLM 裁判 | 0 | 抽样 0 条 (不可用) |
| 合计 | 78 | |

## 已知 bug 复现

- 「像刚下过雪风声大」缺句号拼接: 未复现 (可能需要拉普兰种子)

## 备注

- 本次运行覆盖 45 个地点
- 采样使用离线渲染(气候估算+模板),未联网获取实时天气/电台
- 多样性测试使用 describe.render() 的 terrain 分支
- LLM 裁判使用硅基流动 DeepSeek-V3 (需设置 SILICONFLOW_API_KEY 环境变量)