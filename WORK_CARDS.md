# 乌有乡优化 · 工作卡(发给执行 AI 用)

用法:一张卡 = 一次任务。把卡全文 + 本说明贴给执行 AI。
通用规矩(每张卡都适用):
- 仓库:C:\Users\84989\Desktop\nowhere_repo,Python 3.12,pytest
- 只许改卡里点名的文件,其他文件一行都不许动
- 改完必须跑卡里写的验收命令,全绿才算完
- Windows 控制台 GBK:print 中文前先 `sys.stdout.reconfigure(encoding="utf-8")`
- 代码风格照周边文件:中文注释、禁"很/非常/十分"这类空泛程度词进渲染文案
- 做完报告:每处改动 3 行内说清"改了什么/为什么",附测试结果

执行顺序:卡1→卡2 先行;卡3 依赖卡2 的错配清单;卡4/5 随时;卡6→7→8 必须按序(都动 state/server)。

---

## 卡1:三个运行时 bug(已定位,照着修)

只许改:nowhere/knowledge.py、nowhere/server.py

**bug 1 — knowledge.py 的 NameError**
about() 函数里(约 185-237 行):`place_name = await _resolve_place_name(...)` 只在 `if not title:` 分支里赋值,但后面 Strategy 6(约 237 行)`place = place_name` 在分支外。带话题提问、且 ZIM 策略 1-5 全落空时直接 NameError 炸穿。
修:在分支前(函数靠前处)初始化 `place_name = None`。确认约 192 行 `if not place_name: return None` 逻辑不变。

**bug 2 — walk_to 时间双计**
server.py walk_to_impl:循环里每个 `walk_mod.step()`(约 1910 行)内部已按距离/速度累加 `state.elapsed_hours`(见 walk.py:192),但约 1977 行又 `_state.elapsed_hours += total_km / 5.0` 加第二遍——走 walk_to 时间流两倍快。
修:删掉约 1977 行那行累加(保留下一行 `now = _state.now()`)。参照 walk_impl 约 1097 行的注释模式,补一句同样意思的注释。

**bug 3 — salience 的 prev_env 被覆盖**
walk_impl 约 1143 行调 `_gather_env_cached`,该函数缓存未命中时(约 629 行)直接 `_state.last_env = env`(新值);约 1204 行又拿 `_state.last_env` 当 prev_env 传给 `_build_salience_candidates`——prev 就是 current,天气/天空的"变化量"恒 0, salience 排序退化。
修:walk_impl 开头(调 step 之前)快照 `prev_env = _state.last_env`,1204 行改用快照。
附带:`_build_salience_candidates`(约 692 行)用 `prev_env.get("terrain")` 算地形变化,但 last_env 的四个写入点(约 970、1345、1770、1981 行)都没有 "terrain" 键,地形变化恒 1.0。
修:四个写入点各加一个键 `"terrain": {"elevation": ..., "surface": ...}`(值照上下文里 env 的键取;现有扁平键一个都不许删)。

验收:
```
cd C:\Users\84989\Desktop\nowhere_repo
python -m pytest nowhere/tests/test_server_integration.py nowhere/tests/test_knowledge.py -q
python -c "import asyncio,sys;sys.stdout.reconfigure(encoding='utf-8');from nowhere import server;asyncio.run(server.open_door('北京'));r=asyncio.run(server.walk('N',2));print(r['text'][:100])"
```

---

## 卡2:定位 QA 脚本(量出错配清单,先别修)

只许新建:nowhere/tests/qa_geocode.py、qa_geocode_report.md(仓库根)

背景:geocode 链在 nowhere/geocode.py `lookup(place)`:special_places → places.py 的 find → cities15000.txt 离线包(按"匹配分*1e12+人口"排序,无国家消歧)→ Nominatim 在线。已知症状:查"福州"落到浙江。nowhere/country.py 有坐标→国家码反查函数(先读它拿到确切函数名)。

做:
1. 断言表(a)(b)带期望国家码,每条查离线链(places.find + geocode._offline_lookup;Nominatim 在线部分跳过或加超时保护),再反查国家码比对:
   a. 中国 34 个省级首府 + 20 名城:福州→福建、厦门→福建、苏州→江苏、杭州→浙江、喀什→新疆、敦煌→甘肃、丽江→云南、桂林→广西、洛阳→河南、敦煌……(自己补全)
   b. 30 世界首都/名城:巴黎→FR、伦敦→GB、开罗→EG、廷巴克图→ML、雷克雅未克→IS、威尼斯→IT、京都→JP……
2. 从 nowhere/data/localcolor.json、humanities.json 的键抽 30 个地名,只记录"地名→坐标→反查国家"进报告(这些没标准答案,给人看)。
3. 每条记录命中来源(places.db / cities15000 / Nominatim),报告里写清。
4. 福州案必须复现并写根因:哪条链、哪行数据、为什么赢过了正确的福州。
5. 输出 qa_geocode_report.md:错配总数、错配全表(地名/期望/实际坐标/实际国家/命中链)、福州根因、修复建议(排序规则和消歧怎么改,只建议不许改代码)。

验收:`python nowhere/tests/qa_geocode.py` 跑完不炸,报告生成,福州案根因明确到数据行。

---

## 卡3:修定位消歧(等卡2报告出来再做,把报告贴给 AI)

只许改:nowhere/geocode.py、nowhere/places.py;qa_geocode.py 可加断言不许删

照 qa_geocode_report.md 的错配清单修:
- cities15000 匹配(geocode.py `_offline_lookup`):中文查询命中中文别名撞车时,用 country 反查 + admin1 信息消歧,错配降权;同分时优先"查询语言与条目本地语言一致"的候选。
- places.py:105 附近 nearby() 的经度框:`deg = radius_km / 111.0` 经纬混用,高纬度漏近处地点;经度方向改 `radius_km / (111.0 * cos(radians(lat)))`,注意 cos→0 的极地兜底。
- Nominatim 结果过一遍 country 反查校验,与离线结果冲突时信离线。
- 不许动 special_places 和缓存结构(但注意:瞬时失败现在会永久缓存 None,顺手给 None 结果不缓存)。

验收:qa_geocode 错配清零;`python -m pytest nowhere/tests/test_places.py nowhere/tests/test_latest_regressions.py -q` 绿。

---

## 卡4:数据接线(索引说谎清零 + 双真相源合并)

只许改:nowhere/localcolor.py、nowhere/humanities.py、nowhere/tests/test_localcolor.py、nowhere/tests/test_humanities.py

背景:explorable_index.json 标了"可探索"的地,运行时却抽不出卡,因为:
- localcolor.py `_load()` 只读 data/localcolor.json;但 data/ 下还有 localcolor_china.json、localcolor_japan_korea_sea.json、localcolor_americas_africa_oceania.json 三个区域文件(约 115 地只存在于区域文件:南京/万隆/三亚/丽江……)。
- humanities.py 只读 humanities.json;humanities_films.json(74 地)、humanities_historical.json(60 地)只在建索引时用,运行时是死数据。

做:
1. localcolor._load():主文件 + 三个区域文件合并。冲突键(约 130 个重复,内容已漂移):**主文件为准**;区域文件里主文件没有的类目(如喀什区域文件多"美食")并入。打印合并统计(各地几卡)。
2. humanities.py:同样把 films/historical 合并进加载,冲突键主文件为准。注意先读 humanities.py 搞清楚卡的数据结构再合。
3. 加载失败(文件不存在)静默跳过,不许炸。
4. 测试:test_localcolor.py 加"南京 has_place() 为 True 且能抽出卡";test_humanities.py 加"卡萨布兰卡有卡"。

验收:新增测试绿 + 原测试全绿 `python -m pytest nowhere/tests/test_localcolor.py nowhere/tests/test_humanities.py -q`。

---

## 卡5:encounters 非洲矩形 + baked 空中文名菜

只许改:nowhere/encounters.py、nowhere/baked.py

1. encounters.py 约 84-85 行:africa 矩形 `-35..37N, -20..55E` 排在 europe 前判定,把安达卢西亚(36.7N)、葡萄牙法鲁、西西里、克里特、塞浦路斯、安塔利亚(明明是亚洲)全吞进非洲池。修:北界收紧到 32N,且 lon>10 且 lat>30 的地中海岸排除(或直接读代码用更准的划法,目标是上面六个城市落到正确池)。encounters.py 约 96-97 行第二个 oceania 分支是第一个的严格子集,死代码,删。
2. baked.py 约 137 行:食物条目 zh 为空串时兜底用英文名,直接嵌进中文模板("点一份paprikash")。修:zh 为空的条目不渲染、跳过(从候选池滤掉),不许让英文菜名进中文散文。

验收:`python -m pytest nowhere/tests/test_encounters.py nowhere/tests/test_baked.py -q` 绿;加两个测试:安塔利亚抽到 asia 池、zh 空串条目不出现在渲染结果。

---

## 卡6:多旅程(暂停/切回)— 先动 state,后面的卡都依赖它

只许改:nowhere/state.py、新建 nowhere/journeys.py、nowhere/server.py、新建 nowhere/tests/test_journeys.py

现状:WorldState 单档,存 ~/.nowhere/journey.json(state.py 里 _SAVE_FILE),save/load 只此一份。

1. state.py:把 save() 里的 dict 组装抽成 `to_dict()`,load() 里的还原抽成 `from_dict(d)`;save/load 变薄壳(老 journey.json 照样能读,向后兼容)。
2. 新建 journeys.py:目录 ~/.nowhere/journeys/(尊重 NOWHERE_HOME 环境变量,跟 state.py 一样),一档一文件 <slug>.json + index.json {"active": slug, "journeys": [{slug, place_name, landed_at, last_active}]}。函数:save_current(state)、list()、switch(slug_or_place)→WorldState、delete(slug)。slug = 归一化地名(小写去空格);同地名不重复建档,switch 按 slug 或地名模糊命中。
3. server.py 接语义:
   - open_door(to=新地):当前有未走完的旅程 → 先 save_current 挂起,再开新档;to 命中的旧档已存在 → 直接 switch 回去(文本提示"回到上次的旅程"),不重建。
   - continue_journey 语义不变(回 active 档)。
   - 新 MCP 工具 `journeys()`:列旧旅程,每条一句(地名、落地时间、走了几步、上次离开时在干嘛[last_text 截 50 字])。
   - 新 MCP 工具 `switch_journey(name)`:切回,恢复位置/已见卡/叙事全状态。
   - 工具的注册方式照 server.py 里现有 @mcp.tool() 模式;web.py 不用动。
4. test_journeys.py 验收场景:开门"纽约"→walk 3 步→开门"布拉格"→walk 2 步→journeys() 两条都在→switch_journey("纽约")→位置/步数/已见卡与离开时一致。测试用 tmp_path + monkeypatch NOWHERE_HOME 隔离。

验收:新测试绿 + `python -m pytest nowhere/tests/test_server_integration.py nowhere/tests/test_narrative.py -q` 绿。

---

## 卡7:视角转动 + 短距试探(依赖卡6的 to_dict)

只许改:nowhere/state.py、nowhere/walk.py、nowhere/describe.py、nowhere/server.py、新建 nowhere/tests/test_look.py

乌有乡是文本世界,"视角" = 方向性场景渲染。

1. state.py:`self.heading: float = 0.0`(度数,朝北),进 to_dict/from_dict(缺省 0)。
2. walk.py step():成功迈步后 `state.heading = bearing`。
3. server.py 新工具 `look(direction: str)`:direction ∈ {左,右,后,前} 或绝对方位(N/NE/E/SE/S/SW/W/NW/北/东/南/西)。相对向按 heading 换算(左=heading-90)。渲染:沿该方位 0.5/2/10km 三点采样(terrain.surface/elevation,复用 walk.py 的 water_ahead_km 探水),组成 1-2 句方向性描述("左边是坡,一路上去;两公里外有水。")。**不动位置、不计时、不进 path**。变体池放 describe.py,守禁词规矩(很/非常/十分禁止,数字不裸奔)。
4. 短距试探:walk.py _DIST_MIN 从 0.2 放宽到 0.05;server.py walk_impl 里 dist<0.5km 时走"近景档":不调 _gather_env_cached(天气电台不变),渲染换近景变体池(脚下/十步内的细节,放 describe.py),计时照 walk.py 现有逻辑不动。clamp 提示文案分方向:往下 clamp 说"至少走 50 米,按 50 米算了",往上 clamp 才说"一步最多 5 公里"。
5. test_look.py:落地后 heading=0;look("左") 返回西向描述且 pos 不变;walk("N",0.2) 后 heading 仍 0;look("后") 是南向;walk("N",0.1) 走近景档(文本不重复拉天气)。

验收:新测试绿 + walk/narrative 相关测试绿。

---

## 卡8:保存原话 + 旅程日志(依赖卡6)

只许改:nowhere/state.py、nowhere/journeys.py、nowhere/server.py、新建 nowhere/tests/test_quotes.py

1. state.py:`self.quotes: list[dict]`(每条 {text, place, pos, sim_time}),进 to_dict/from_dict,上限 50 条 FIFO。
2. server.py 新工具 `say(text: str)`:存一条 quote(带当前地名/坐标/模拟时刻),返回一句轻回应(变体池 3-5 条:"记下了。""这句话留在这了。"——不许复读原文)。新工具 `quotes()`:按时间序列出本旅程的全部原话,每条带"在哪说的"。
3. journeys.py:每档配一个 append-only 日志 <slug>.log.jsonl,事件:land/walk/look/listen/say/mark,每条 {t(真实时间), kind, pos, summary(一行)}。在 server.py 各 impl 里埋点(照现有 _record_footprint 的模式,先看它怎么写的再决定是复用还是并进日志)。
4. 新工具 `journal()`:回看本次旅程时间线(读 log.jsonl,每条一行,模拟时刻在前)。
5. test_quotes.py:say("这句话留下")→quotes() 有这条且带地名;journal() 能看到 land→walk→say 完整链;quotes 超过 50 条丢最旧。

验收:新测试绿 + 相关旧测试绿。

---

## 卡9:测试套件本机跑绿(独立,随时可做)

只许改:nowhere/tests/ 下的文件

1. test_terrain.py 3 挂:test_everest_high/test_no_network 断言珠峰 elevation>7000,但 grid_tiny.npz 是 1° 粗网格,珠峰格读出 5364;test_slope_uphill 两点落同一格 slope=0。修:断言改成符合粗网格现实(elevation>5000),或读测试合成地形(synthetic_terrain.py)怎么用,用合成数据测。
2. test_regression.py:129 test_water_ahead_logic 挂:patch 的是 terrain.is_water,但 walk.py:91 的 water_ahead_km 早已改用 terrain.surface(...)=="water_ocean"。修:patch surface。同文件 :121 test_water_ahead_finds_sea 是永久 xfail,修好后把 xfail 摘掉。:114 有 `or True` 恒真断言,顺手改成真断言。
3. win32 挂死:test_observer_feeds.py、test_knowledge.py、test_encounters.py 的 asyncio 测试在 Windows 拆除时 IOCP 挂死(test_server_integration.py:32 已有 skipif win32 的先例,照那个模式推广)。修:同样的 skipif 或 fixture 处理,让 `python -m pytest nowhere/tests -q` 在本机(Windows)能跑完。
4. 删占位空文件 test_humanities_await.py(零断言,docstring 自承是占位)。

验收:`python -m pytest nowhere/tests -q` 在 Windows 本机跑完且全绿(允许保留 1 个非 strict xfail)。

---

# 灵感组(旋复 2026-08-20 拍板"可以")

排序即优先级:卡10 > 卡11 > 卡12 > 卡13 > 卡14 > 卡15。
总原则(每张卡都必须守):**证据,不是陈述**——世界不解释自己,意义让玩家自己拼。文案禁"很/非常/十分",禁攻略腔,禁替玩家下情绪结论。

---

## 卡10:痕迹链(世界在你离开后继续过日子)— 依赖卡6

只许改:nowhere/placememory.py、nowhere/server.py、新建 nowhere/data/traces.json、nowhere/tests/test_traces.py

背景:localcolor 的"痕迹"卡是孤立的,每次去都一样。改成会演化的链:第 1 次到访看到"墙上有新刷的标语",第 2 次"标语被雨水泡花了",第 3 次"重新刷过,字变了"。

1. traces.json 数据格式:
```json
{"喀什": {"stages": ["艾提尕尔广场边的老茶馆在翻新,脚手架刚搭起来。",
                     "茶馆的门脸露出来了,比记忆中亮。",
                     "翻新完了,老茶客照旧坐在门口,像什么都没发生过。"]},
 "拉普兰": {"stages": [...]}}
```
先手写 10 个地方(挑 localcolor.json 里已有"痕迹"卡的地),每地 3 阶段。文案规矩同上,阶段之间要有"时间过去了"的物理逻辑(新→旧→变),不许只是换个说法。
2. placememory.py:每地记录 `trace_stage`(int,默认 0)。server 落地或 walk 抽痕迹卡时:该地有 traces 链 → 按当前 stage 渲染对应阶段,渲染后 stage+1(封顶最后一阶,之后永远停在最末阶段——世界演化完就稳定了)。该地没链 → 照旧抽 localcolor 痕迹卡。
3. 跨旅程共享:trace_stage 存 placememory(全局层,跟 seen_cards 一样),不是单旅程 state——世界是公共的,任何旅程再来都接着上次的阶段。
4. test_traces.py:同地三次落地(模拟三次 open_door),三段文本按序出现且不同;第四段=第三段(封顶);无链地回退正常。

验收:新测试绿 + `python -m pytest nowhere/tests/test_placememory.py -q` 绿。

---

## 卡11:节日历(在对的时间到对的地方)

只许改:nowhere/server.py、nowhere/localcolor.py、新建 nowhere/data/festivals.json、nowhere/tests/test_festivals.py

1. festivals.json,30-50 个起步,格式:
```json
[{"name": "泼水节", "place": "清迈", "window": {"start": [4, 13], "end": [4, 15]},
  "cards": ["满城都是水。..." ]},
 {"name": "亡灵节", "country": "MX", "window": {"start": [11, 1], "end": [11, 2]}, "cards": [...]},
 {"name": "樱花", "place": "京都", "lat_rule": {"base_lat": 31.0, "base_date": [3, 24], "days_per_deg": 2.6, "span_days": 10}, "cards": [...]}]
```
三种窗口:(a) 固定日期 + place(精确地);(b) 固定日期 + country 国家码(全国);(c) 纬度推移(樱花前线/红叶前线:日期 = 基准日期 + (该地纬度-基准纬度)*days_per_deg,南半球红叶用 -days_per_deg)。每种至少 3 个实例。
2. server.py open_door 落地流程:用落地时刻(state.now())检查节日命中——place 精确 > country > lat_rule。命中 → 落地段最前插一张节日卡(rng 选),并在 data 里带 {"festival": name}。节日卡不走 seen_cards(节日每年都来,不是抽完就没)。
3. localcolor.py 不动数据结构,只加一句:命中节日时 rhythm_event 让位(server 层控制,localcolor 无需改——如果发现必须改,改最小)。
4. 卡文案照风格铁律:体感优先("水从头顶浇下来,你眨掉眼睛里的水,满街的人都在笑"),禁百科("泼水节是傣族的新年"这种直接枪毙)。
5. test_festivals.py:mock 模拟时间到 4/14 → 开门清迈命中泼水节;4/20 → 不命中;3/30 京都命中樱花、同天稚内(45°N)不命中;节日卡重复落地不消失。

验收:新测试绿 + 旧测试绿。

---

## 卡12:意图门(open_door 带 intent,priming 做进渲染)

只许改:nowhere/server.py、nowhere/salience.py、nowhere/localcolor.py、nowhere/state.py、nowhere/tests/test_intent.py

设计(不许偏离):意图只偏置"看到什么",世界本身不变;落地文本**绝口不提意图**(不说"你想看孤独"——证据不陈述)。

1. open_door(to=None, intent: str | None = None):intent 存 `state.intent`(序列化进 to_dict,卡6 之后;if 卡6 未合,先加字段+save/load 两行)。无 intent = 现状。
2. salience.py:加 `_INTENT_MAP`,意图关键词→kind/tag 权重表,例:
   - 孤独/安静 → life/radio 权重×0.5,sky/terrain/weather ×1.5
   - 热闹/人 → life/radio/localcolor ×1.5,sky ×0.7
   - 水/海 → water/water_features ×1.5
   - 古老/历史 → humanities/art ×1.5
   - 吃 → localcolor 美食 ×2
   意图不在表里 → 不生效(静默,不报错)。`_build_salience_candidates` 加 intent 参数,delta 算完乘权重再 rank。
3. localcolor.draw():加可选 intent 参数,命中类目权重乘对应系数(美食意图→美食卡权重翻倍,与饭点逻辑叠乘)。
4. state.intent 整个旅程有效;walk 阶段的 salience 同样吃权重(不是只落地那一下)。
5. test_intent.py:同 seed 同落点,intent="吃" 比无 intent 命中美食卡的频率显著高(跑 50 次统计);intent="不存在词" 行为与无 intent 一致;落地文本不含"意图"二字及 intent 原文。

验收:新测试绿 + test_describe/test_server_integration 绿。

---

## 卡13:埋(bury,和 souvenir 闭环)

只许改:nowhere/server.py、nowhere/placememory.py、nowhere/tests/test_bury.py

1. 新工具 `bury()`:把身上带着的 souvenir(state.souvenir)埋在当前坐标。空手 → "你没东西可埋。"埋掉后 souvenir=None。返回一句(变体池 3 条:"你把{name}埋进了土里。这里记得。")。
2. 存储:placememory 层加 buried.json(全局跨旅程,尊重 NOWHERE_HOME):[{name, desc, from, pos, buried_at}]。上限 100 条 FIFO。
3. 发现:walk 时每步检查 3km 内有无埋藏,有 → 8% 概率"脚碰到一个铁盒"(变体池 3 条):空手则捡为 souvenir,有主则只看见不拿("你把它又放了回去")。发现后条目保留(下一个人还能踢到)。
4. 自己埋的自己也能再挖到——世界不偏心。
5. test_bury.py:埋→souvenir 清空→buried.json 有;走到 3km 内反复 walk 能触发发现(mock rng 强制命中);空手埋报错。

验收:新测试绿 + test_placememory 绿。

---

## 卡14:星夜导航(夜里,天给方向)

只许改:nowhere/describe.py、nowhere/server.py、nowhere/tests/test_nightwalk.py

1. walk 渲染时若 sky.phase=="night"(读 env 现有键,sky.py 全算好了):
   - 北半球(lat>10):北极星方向≈真北,30% 概率插一句"北极星在北边挂着,低低的。"之类(变体池 4 条,按纬度变:低纬"贴着地平线",高纬"头顶偏北")。
   - 南半球(lat<-10):南十字变体池。
   - 满月(moon_phase>0.8)走路变体:影子清楚、不用看脚下;无月(moon_phase<0.2):黑、慢、听声走路。各 3 条。
   - 极夜(|lat|>66 且当地冬季月份):专用池 3 条("太阳不上来,但雪把光存住了。")。
2. 全部走 describe 变体池+禁词规矩;句子里有方向词必须和实际方位一致(北就是北,不许文学化乱指)。
3. test_nightwalk.py:mock env 为夜+北半球 → 多次 walk 统计出北极星句且含"北";满月 vs 无月文案池不同;极夜池只在高纬触发。

验收:新测试绿 + test_sky 绿。

---

## 卡15:世界迷雾(journeys 点名清单)— 依赖卡6

只许改:nowhere/journeys.py、nowhere/server.py、nowhere/tests/test_atlas.py

1. journeys.py 加 `atlas()`:聚合全部旅程档(每档的 place_name + pos),统计:去过的地方数、踩过的大洲数(用 describe.py 的 _REGION_MAP 或 country.py,读代码选顺手的)、最北/最南/最东/最西各是哪里。
2. server.py 新工具 `atlas()`:输出一段点名文(变体池 3 条),例:"你去过 14 个地方,踩过 4 个洲。最北到拉普兰,最南到乌斯怀亚。"数据少就说少("才 3 个地方,世界还大。")。零旅程 → "还没出门过。"
3. 不做地图、不做百分比、不做成就徽章——就一段话。
4. test_atlas.py:造 3 个旅程档(纽约/布拉格/拉普兰)→ atlas 输出含"3"、含"拉普兰";零档 → 输出"还没出门"。

验收:新测试绿 + test_journeys 绿。
