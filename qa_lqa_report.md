# QA LQA Report — Card 24: 语义文本审计

**生成时间**: 2026-08-20 02:39
**耗时**: 272.7 秒
**样本数**: 594 (land + walk)
**总 bug 数**: 83

## 按严重度汇总

| 严重度 | 数量 | 说明 |
|--------|------|------|
| S1 | 0 | 严重 (幻觉/数字矛盾/自称矛盾) |
| S2 | 9 | 重大 (场景错配/地名漂移) |
| S3 | 3 | 轻微 (禁词/格式/断气) |
| S4 | 71 | 打磨 (多样性/长度) |

## S2: 重大问题

| ID | 现象 | 复现输入 | 根因初判 |
|----|------|----------|----------|
| R0002 | 地名漂移: 同段出现 {'罗马剧场在城市', '清真寺'} | place=安曼, action=land, time=dawn, temp=25.4, biome=coast, lat=31.95 | 多张卡拼接时地名未统一 |
| R0004 | 地名漂移: 同段出现 {'太空针塔', '笛在普吉特海湾', '传向班布里奇岛'} | place=西雅图, action=land, time=dawn, temp=18.3, biome=city, lat=47.61 | 多张卡拼接时地名未统一 |
| R0005 | 内陆 biome (city) 出现海港词「码头」 | place=西雅图, action=land, time=dawn, temp=18.3, biome=city, lat=47.61 | 场景过滤未覆盖内陆情况 |
| R0006 | 地名漂移: 同段出现 {'太空针塔', '的风从艾略特湾'} | place=西雅图, action=land, time=dusk, temp=18.3, biome=city, lat=47.61 | 多张卡拼接时地名未统一 |
| R0007 | 地名漂移: 同段出现 {'太空针塔', '笛在普吉特海湾', '传向班布里奇岛'} | place=西雅图, action=land, time=night, temp=18.3, biome=city, lat=47.61 | 多张卡拼接时地名未统一 |
| R0008 | 内陆 biome (city) 出现海港词「码头」 | place=西雅图, action=land, time=night, temp=18.3, biome=city, lat=47.61 | 场景过滤未覆盖内陆情况 |
| R0009 | 内陆 biome (city) 出现海港词「灯塔」 | place=波士顿, action=land, time=night, temp=30.9, biome=city, lat=42.36 | 场景过滤未覆盖内陆情况 |
| R0010 | 地名漂移: 同段出现 {'帕特农神庙', '斯提拉基跳蚤市'} | place=雅典, action=land, time=dawn, temp=27.1, biome=city, lat=37.98 | 多张卡拼接时地名未统一 |
| R0011 | 地名漂移: 同段出现 {'帕特农神庙', '普拉卡区'} | place=雅典, action=land, time=night, temp=27.1, biome=city, lat=37.98 | 多张卡拼接时地名未统一 |

## S3: 轻微问题

| ID | 现象 | 复现输入 | 根因初判 |
|----|------|----------|----------|
| R0001 | 禁词「很」出现在渲染文本中 | place=新潟, action=land, time=dusk, temp=25.1, biome=city, lat=37.90 | 模板或卡片中残留禁词,describe.py 规则要求禁止 |
| R0003 | 禁词「很」出现在渲染文本中 | place=台北, action=land, time=night, temp=25.9, biome=city, lat=25.03 | 模板或卡片中残留禁词,describe.py 规则要求禁止 |
| R0012 | 缺句号拼接断气: 「雪」与「风声」之间缺少句号 (已知 bug 复现) | place=皇后镇, action=land, time=dawn | describe.compose() 中 smell 描述末尾无标点,与 soundscape 拼接 |

## S4: 多样性不足 (ERA 量化)

| ID | 现象 | 复现输入 | 根因初判 |
|----|------|----------|----------|
| D0001 | 多样性不足: 阿姆斯特丹@dawn 去重率 56.7% (仅 13 个唯一变体 / 30 次) | place=阿姆斯特丹, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0002 | 多样性不足: 阿姆斯特丹@dusk 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=阿姆斯特丹, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0003 | 多样性不足: 阿姆斯特丹@night 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=阿姆斯特丹, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0004 | 多样性不足: 皇后镇@dawn 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=皇后镇, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0005 | 多样性不足: 皇后镇@dusk 去重率 46.7% (仅 16 个唯一变体 / 30 次) | place=皇后镇, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0006 | 多样性不足: 皇后镇@night 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=皇后镇, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0007 | 多样性不足: 新潟@dawn 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=新潟, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0008 | 多样性不足: 新潟@dusk 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=新潟, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0009 | 多样性不足: 新潟@night 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=新潟, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0010 | 多样性不足: 太仓@dawn 去重率 60.0% (仅 12 个唯一变体 / 30 次) | place=太仓, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0011 | 多样性不足: 太仓@dusk 去重率 50.0% (仅 15 个唯一变体 / 30 次) | place=太仓, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0012 | 多样性不足: 太仓@night 去重率 46.7% (仅 16 个唯一变体 / 30 次) | place=太仓, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0013 | 多样性不足: 斐济@dawn 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=斐济, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0014 | 多样性不足: 斐济@dusk 去重率 46.7% (仅 16 个唯一变体 / 30 次) | place=斐济, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0015 | 多样性不足: 斐济@night 去重率 56.7% (仅 13 个唯一变体 / 30 次) | place=斐济, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0016 | 多样性不足: 安曼@dawn 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=安曼, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0017 | 多样性不足: 安曼@dusk 去重率 46.7% (仅 16 个唯一变体 / 30 次) | place=安曼, time=dusk, layer=terrain | 渲染分支变体池太浅 |
| D0018 | 多样性不足: 安曼@night 去重率 56.7% (仅 13 个唯一变体 / 30 次) | place=安曼, time=night, layer=terrain | 渲染分支变体池太浅 |
| D0019 | 多样性不足: 米兰@dawn 去重率 53.3% (仅 14 个唯一变体 / 30 次) | place=米兰, time=dawn, layer=terrain | 渲染分支变体池太浅 |
| D0020 | 多样性不足: 米兰@dusk 去重率 56.7% (仅 13 个唯一变体 / 30 次) | place=米兰, time=dusk, layer=terrain | 渲染分支变体池太浅 |

## 多样性量化表 (最差 10 个地/层)

| 地点 | 层 | 时段 | 运行次数 | 唯一变体 | 去重率 | 判定 |
|------|------|------|----------|----------|--------|------|
| 太仓 | terrain | dawn | 30 | 12 | 60.0% | S4 (池浅) |
| 基韦斯特 | terrain | dawn | 30 | 12 | 60.0% | S4 (池浅) |
| 科隆 | terrain | night | 30 | 12 | 60.0% | S4 (池浅) |
| 阿姆斯特丹 | terrain | dawn | 30 | 13 | 56.7% | S4 (池浅) |
| 斐济 | terrain | night | 30 | 13 | 56.7% | S4 (池浅) |
| 安曼 | terrain | night | 30 | 13 | 56.7% | S4 (池浅) |
| 米兰 | terrain | dusk | 30 | 13 | 56.7% | S4 (池浅) |
| 波士顿 | terrain | dusk | 30 | 13 | 56.7% | S4 (池浅) |
| 波士顿 | terrain | night | 30 | 13 | 56.7% | S4 (池浅) |
| 新潟 | terrain | dawn | 30 | 14 | 53.3% | S4 (池浅) |

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
| Layer 2 规则层 | 83 | 全量,免费,确定性 |
| Layer 3 LLM 裁判 | 0 | 抽样 0 条 (不可用) |
| 合计 | 83 | |

## 已知 bug 复现

- 「像刚下过雪风声大」缺句号拼接: 已复现

## 备注

- 本次运行覆盖 46 个地点
- 采样使用离线渲染(气候估算+模板),未联网获取实时天气/电台
- 多样性测试使用 describe.render() 的 terrain 分支
- LLM 裁判使用硅基流动 DeepSeek-V3 (需设置 SILICONFLOW_API_KEY 环境变量)