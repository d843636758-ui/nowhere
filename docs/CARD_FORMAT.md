# 给谁用

给加卡的执行 AI。配合卡30 的 `--check` 质检。本文档描述乌有乡所有卡的数据格式，全部从 `localcolor.py` / `humanities.py` 的解析代码反推，和代码对不上算错。

---

## 一、方志卡 (localcolor)

数据文件：`nowhere/data/localcolor.json`（主文件）+ 三个区域文件：
- `localcolor_china.json`
- `localcolor_japan_korea_sea.json`
- `localcolor_americas_africa_oceania.json`

合并规则（见 `localcolor.py:_load`）：主文件 + 区域文件合并，冲突键以主文件为准。

### 1.1 五大类目

代码只处理这五类（`localcolor.py:89`）：

| 类目 | 语义 | 权重 |
|------|------|------|
| 物产 | 当地能摸到、看到、吃到的实物 | 1.0 |
| 声音 | 当地特有的声音 | 1.0 |
| 痕迹 | 时间留下的印记——旧的、坏的、被改过的 | 1.0 |
| 植被 | 当地植物（烘焙层有 iNat 自动收割） | 1.0 |
| 美食 | 当地食物 | 3.0（饭点翻倍） |

每类的值是字符串数组，每条卡 = 1-3 句散文。

### 1.2 节律 (节律)

节律是地志卡的时间触发层。值可以是：

**格式 A — 纯字符串**（全年、全时段有效）：
```json
"节律": ["早上六点，弄堂里有人在生炉子，烟顺着墙往上爬。"]
```

**格式 B — 对象数组**（带时段和季节过滤）：
```json
"节律": [
  {
    "hours": [6, 8],
    "text": "天没亮,沙漠是冷的..."
  },
  {
    "hours": [22, 1],
    "months": [6, 7, 8],
    "text": "夏天的夜里..."
  }
]
```

#### hours 字段

- 类型：`[int, int]`，两个整数
- 语义：**左闭右开** `[start, end)`。`[6, 8]` = 6:00-7:59 有效
- 跨午夜：`[22, 1]` = 22:00-0:59 有效（代码用 `r["hours"][0] <= local_hour < r["hours"][1]` 判定，跨午夜时 `22 <= hour < 1` 在 Python 中恒 False——**这是已知限制，跨午夜的 hours 目前不会命中**。写卡时避免 `[22, 1]` 这种，改用 `[22, 24]`）
- 范围：0-24（小时制）

#### months 字段

- 类型：`int 数组`，可选
- 语义：月份列表（1-12）。`[6, 7, 8]` = 只在 6/7/8 月出现
- 缺省：**不写 = 全年有效**（代码 `months = r.get("months")`，None 时跳过月份过滤）
- 用途：季节限定——极昼（6-7月）、极光（9-3月）、三文鱼季（7-9月）等

### 1.3 卡 key 规则

```
{地名}/{类目}/{索引}
```

- 地名：JSON 的顶层 key，如 `"敦煌"`、`"K2大本营"`
- 类目：`"物产"` / `"声音"` / `"痕迹"` / `"植被"` / `"美食"`
- 索引：从 0 开始的整数，对应数组下标

示例：`"敦煌/物产/0"`、`"东京/声音/2"`

代码（`localcolor.py:91`）：`key = f"{place_name}/{cat}/{i}"`

### 1.4 美食卡权重

- 基础权重 3.0（`localcolor.py:93`：`w = 3.0 if cat == "美食" else 1.0`）
- 饭点（6-9 / 11-13 / 17-21）再翻倍（`localcolor.py:113-116`）
- 非饭点美食权重降回 1.0（`localcolor.py:116`）

---

## 二、人文卡 (humanities)

数据文件：`nowhere/data/humanities.json`（主文件）+ 区域文件：
- `humanities_films.json`
- `humanities_historical.json`

顶层结构：
```json
{
  "_说明": { ... },
  "aliases": { "Skjolden": "肖尔登", ... },
  "places": {
    "京都": {
      "事件": [...],
      "人物": [...],
      "作品": [...]
    }
  }
}
```

### 2.1 三类目

代码按 `"事件" → "人物" → "作品"` 优先级抽取（`humanities.py:119`）。

**事件**：
```json
{
  "name": "应仁之乱",
  "year": "1467-1477",
  "text": "1467到1477,京都烧了十一年..."
}
```

**人物**：
```json
{
  "name": "紫式部",
  "text": "紫式部一千年前在京都写《源氏物语》..."
}
```

**作品**：
```json
{
  "title": "金阁寺",
  "creator": "三岛由纪夫",
  "kind": "文学",
  "here": "故事在这",
  "text": "三岛由纪夫《金阁寺》,故事在这..."
}
```

### 2.2 卡 key 规则

同方志：`{地名}/{类目}/{索引}`

代码（`humanities.py:128`）：`f"{name}/{cat}/{i}"`

### 2.3 ref 字段

抽卡时返回 `ref`：除 `text` 外的所有字段（`humanities.py:127`）。用于追问（ask ZIM）。

### 2.4 别名系统

`aliases` 字典把英文/变体地名映射到中文标准名（`humanities.py:77-82`）。

---

## 三、纪念品 (souvenirs)

数据文件：`nowhere/data/souvenirs_by_place.json`

格式：
```json
{
  "敦煌": [
    {
      "name": "一粒沙",
      "desc": "鸣沙山上吹来的，你从袖口里抖出来的。手指捻开，颗粒比别处的沙粗。"
    },
    {
      "name": "一片壁画碎屑",
      "desc": "莫高窟外的地上捡的。土红色，带着一点石青。"
    }
  ]
}
```

- 每地 2-3 个纪念品
- `name`：物件名（短，名词性）
- `desc`：诗意描述，2-3 句，第一/二人称

---

## 四、节日 (festivals)

数据文件：`nowhere/data/festivals.json`（卡11 规划，尚未创建）

规划格式（三种窗口）：
```json
[
  {"name": "泼水节", "place": "清迈", "window": {"start": [4, 13], "end": [4, 15]}, "cards": [...]},
  {"name": "亡灵节", "country": "MX", "window": {"start": [11, 1], "end": [11, 2]}, "cards": [...]},
  {"name": "樱花", "place": "京都", "lat_rule": {"base_lat": 31.0, "base_date": [3, 24], "days_per_deg": 2.6, "span_days": 10}, "cards": [...]}
]
```

---

## 五、痕迹链 (traces)

数据文件：`nowhere/data/traces.json`（卡10 规划，尚未创建）

规划格式：
```json
{
  "喀什": {
    "stages": [
      "艾提尕尔广场边的老茶馆在翻新,脚手架刚搭起来。",
      "茶馆的门脸露出来了,比记忆中亮。",
      "翻新完了,老茶客照旧坐在门口,像什么都没发生过。"
    ]
  }
}
```

- 每地 3 阶段，有"时间过去了"的物理逻辑（新→旧→变）
- 跨旅程共享，stage 递增封顶

---

## 六、常见坑清单

### 坑1：键名漂移

地名必须精确匹配。不同数据文件的键必须一致：
- `"突尼斯市"` ≠ `"突尼斯"`
- `"喀什"` ≠ `"喀什地区"` ≠ `"Kashgar"`
- 写卡前先查 `localcolor.json` / `humanities.json` 的已有键

### 坑2：months 缺失

季节限定卡**必须写 months**：
- 冰岛极光：`"months": [9, 10, 11, 12, 1, 2, 3]`
- 北极白夜：`"months": [6, 7]`
- 不写 = 全年有效，极光卡在 7 月出现 = 穿帮

### 坑3：hours 跨午夜

`[22, 1]` 在 Python 中 `22 <= hour < 1` 恒 False，永远不命中。改用 `[22, 24]`。

### 坑4：hours 越界

hours 值必须在 0-24 范围内。`[0, 24]` = 全天。

### 坑5：zh 空串

烘焙层（baked.py）食物条目 `zh` 为空串时，英文菜名会直接进中文散文（"点一份 paprikash"）。写卡时确保有中文名。

### 坑6：地名不属于此地

卡里提到的标志物必须属于该地。"巴黎的埃菲尔铁塔"写进"伦敦"卡 = S1 事实错。

### 坑7：节律可以是纯字符串

节律值不一定是数组对象，可以是纯字符串（如上海、三亚的卡）。纯字符串 = 全年全时段有效。

### 坑8：人文卡优先级

事件 → 人物 → 作品。同类内随机，不同类按优先级。写卡时注意：事件层不幽默，玩笑必须冷（一句封顶）。

---

## 七、数据文件路径速查

| 文件 | 说明 |
|------|------|
| `nowhere/data/localcolor.json` | 方志主文件 |
| `nowhere/data/localcolor_china.json` | 中国区域方志 |
| `nowhere/data/localcolor_japan_korea_sea.json` | 日韩海域方志 |
| `nowhere/data/localcolor_americas_africa_oceania.json` | 美洲非洲大洋洲方志 |
| `nowhere/data/humanities.json` | 人文主文件 |
| `nowhere/data/humanities_films.json` | 电影人文 |
| `nowhere/data/humanities_historical.json` | 历史人文 |
| `nowhere/data/souvenirs_by_place.json` | 纪念品 |
| `nowhere/data/festivals.json` | 节日（待建） |
| `nowhere/data/traces.json` | 痕迹链（待建） |
