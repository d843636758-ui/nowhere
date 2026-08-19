# 乌有乡优化 · 工作卡(发给执行 AI 用)

用法:一张卡 = 一次任务。把卡全文 + 本说明贴给执行 AI。
通用规矩(每张卡都适用):
- 仓库:C:\Users\84989\Desktop\nowhere_repo,Python 3.12,pytest
- 只许改卡里点名的文件,其他文件一行都不许动
- 改完必须跑卡里写的验收命令,全绿才算完
- Windows 控制台 GBK:print 中文前先 `sys.stdout.reconfigure(encoding="utf-8")`
- 代码风格照周边文件:中文注释、禁"很/非常/十分"这类空泛程度词进渲染文案

## ★根因铁律(每张修 bug 的卡都必须守,游戏公司 QA 的行规)
1. **先复现,再定位,最后才改**。报告里必须写复现步骤(输入→错误输出)。
2. **根因链三段**:现象 → 出错的数据行/代码行 → **为什么它会错/为什么之前没被抓到**(缺测试?断言太松?数据没校验?)。不写第三段不许交差——只修现象不除根,下次换个地名又犯。
3. **每条发现带 ID 和严重度**(照游戏 LQA 的行规,统一语言):
   - **S1 事实错/破沉浸**:编造的数据、张冠李戴的事实、国家搞错、自称矛盾
   - **S2 错配**:风俗/气候/物种/宗教/语言/矩形归错地方
   - **S3 断气**:拼段断裂、缺标点、风格跳变、人称漂移、攻略腔百科腔
   - **S4 疲劳**:复读、变体池太浅、信息轰炸或死寂
4. **修完必须留抓得住它的测试**(回归用),没测试的修复=没修。
5. **报告格式**:每条 = ID / 严重度 / 现象 / 根因链 / 修法 / 新测试名。

执行顺序:卡2/22/23(量的)先发;卡1/4/5/9 可同发;卡3 依赖卡2 的错配清单;卡6→7→8 必须按序(都动 state/server);卡10-21 灵感组按号序。

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

**脑已预扫(2026-08-20,不必重复,直接在此基础上扩):48 个浙江/海南中小城市,22 错配。三种死法:**
1. **覆盖稀疏**(17 个):象山/嵊州/临海/桐乡/海盐/平湖/兰溪/浦江/武义/常山/龙游/天台/玉环/洞头/苍南/文成/泰顺/乐清 → places.db 和 cities15000 全查不到(NONE),只能掉 Nominatim——在线、limit=1、无校验,"查福州跑到浙江"最可能就是这么来的(网络抖动时 Nominatim 返回什么就用什么)。
2. **跨国撞名**(4 个):海南→日本和歌山(34.15,135.21)、海宁→丹麦(56.13,8.97)、安吉→美国德州(31.46,-100.43)、永康→台湾(23.02,120.25)。cities15000 别名匹配无国家消歧,同分取人口最高者。
3. **福州本体目前是对的**(cities15000 → 26.06,119.30 福建)——所以"福州→浙江"是变体查询或 Nominatim 路径的锅,卡2 要把"福州市""Fuzhou"等变体也扫一遍定位到它。

做:
1. 断言表(a)(b)带期望国家码,每条查离线链(places.find + geocode._offline_lookup;Nominatim 在线部分跳过或加超时保护),再反查国家码比对(country.py 有 country_code_of):
   a. 中国 34 个省级首府 + 上面预扫的 48 城 + 20 名城(福州→福建、厦门→福建、苏州→江苏、杭州→浙江、喀什→新疆、敦煌→甘肃、丽江→云南、桂林→广西、洛阳→河南……)
   b. 30 世界首都/名城:巴黎→FR、伦敦→GB、开罗→EG、廷巴克图→ML、雷克雅未克→IS、威尼斯→IT、京都→JP……
   c. 变体表:福州/福州市/Fuzhou、广州/Canton 之类,每个变体一行。
2. 从 nowhere/data/localcolor.json、humanities.json 的键抽 30 个地名,只记录"地名→坐标→反查国家"进报告(这些没标准答案,给人看)。
3. 每条记录命中来源(places.db / cities15000 / Nominatim / NONE),报告里写清。
4. 输出 qa_geocode_report.md:错配总数、错配全表(地名/期望/实际坐标/实际国家/命中链)、按上面三种死法分类统计、修复建议(只建议不许改代码)。

验收:`python nowhere/tests/qa_geocode.py` 跑完不炸,报告生成,三种死法各给出数据行级证据。

---

## 卡3:修定位消歧(等卡2报告出来再做,把报告贴给 AI)

只许改:nowhere/geocode.py、nowhere/places.py;qa_geocode.py 可加断言不许删

**脑已定的修复方向(照卡2 三种死法对症):**
1. **跨国撞名**(海南→日本/海宁→丹麦/安吉→美国):`_offline_lookup` 加 CJK 偏向——查询串含中文字符时,同分候选里 country code 为 CN/TW/HK/MO 的优先(parts[8] 是国家码,读 cities15000 格式确认列号);中文撞外文别名时,中文名完全等于查询的条目优先于"别名 token 命中"。
2. **覆盖稀疏**(17 城 NONE):两条路,都做——(a) GeoNames 有免费中国数据(CN.zip,含 admin 码和 alternatenames),下载转成 data/packs/cities_cn.txt 补进离线链(格式照 cities15000);(b) Nominatim 结果必须过 country 反查,且把 display_name 一并返回便于核对,错配时弃用并记日志。下载数据用脚本做(build_index.py 那种一次性收割模式),收割产物入库,运行时不联网。
3. places.py:105 附近 nearby() 的经度框:`deg = radius_km / 111.0` 经纬混用,高纬度漏近处地点;经度方向改 `radius_km / (111.0 * cos(radians(lat)))`,极地 cos→0 兜底。
4. 顺手:瞬时失败缓存 None 是永久的——None 结果不进缓存(或加 TTL)。

验收:qa_geocode 错配清零(含 48 城预扫表);`python -m pytest nowhere/tests/test_places.py nowhere/tests/test_latest_regressions.py -q` 绿。

---

## 卡22:全链路体检脚本(时间/走路/渲染,量而不修)— 立刻可发

只许新建:nowhere/tests/qa_probe.py、qa_probe_report.md(仓库根)

旋复原话:"不仅地点,可能还有别的问题,时间啦,走路啦什么的。"照卡2 的模式,把体检面铺到全链路。**只量不修**,每条探针输出"期望 vs 实际"。

探针清单(每条一个函数,独立可跑,结果全进报告):
0. **探活链(最优先,脑新增)**:真实网络下逐个探外部源——Nominatim、Overpass(已知中国被墙)、iNaturalist、Met Museum API、Radio-Browser mirror、radio_fallback 里抽 10 个台的流 URL(HEAD 请求)。每个:通/不通/延迟。**感知静默全灭是绝症早期:except→None 的安静降级让感官慢慢死光且测试全绿,这张表就是体检单。**
0b. **输入设防**:walk(distance_km=-5 / 0 / NaN / 1e9 / "abc")、open_door(to=""/500字带换行/特殊字符)、listen(seconds=-1)。每个记录:报错文本合理还是炸栈/诡异行为。
0c. **极地日界线**:walk 跨过 ±180° 经线(斐济 179.9→-179.9)坐标 wrap 对不对、region 判定跳不跳变;lat=±85 极地 walk/落地;country_code_of(南极点)返回什么,food_items(None) 炸不炸;cos(lat)→0 附近 places.nearby。
1. **时间链**:落地北京 vs 落地纽约,同一真实时刻,两地模拟时刻的当地小时是否合理(时区);**新疆特案:喀什按 UTC+8 官方时区 vs 太阳时 UTC+6,节律卡"9 点开城"时天亮了没有(时区政治 vs 太阳物理)**;wait(3)后模拟时刻是否+3h(不多不少);walk(2km)后时间增量是否在 0.3-0.7h(合理步行配速),walk_to 是否双计(已知 bug,确认还在不在);南半球(悉尼/布宜诺斯艾利斯)1 月落地,季节文案是不是夏天;北半球 7 月落地冰岛,有没有白夜/极昼相关输出。
2. **走路链**:walk("N",2) 后纬度确实增加且增量≈2km(±10%);walk("uphill") 在平地返回 no_gain 且**位置不动**(核实审计误报);walk 被悬崖挡住时不计时不移位;walk(0.01)/walk(100) 的 clamp 行为与文案一致(文案说不说谎);连续 8 步朝 8 个方向,最终位置≈回到原点(物理自洽)。
3. **渲染链**:落地+walk 20 次,全文扫描——占位符残留({xxx})、双句号、None 泄漏、全半角标点混用、禁词(很/非常/十分)、同一段内地名前后不一致。
4. **数据链**:localcolor/humanities/explorable_index 三地键集合交叉,列出"索引说有、运行时抽不出"的地名全集(卡4 的范围确认);food_by_country 里 zh 空串条目逐条列出。
5. **状态链**:save→load 后 pos/已见卡/narrative/明信片逐项比对;损坏的 journey.json(乱写)加载不炸。**幂等批(IF"伞-戒指"类):同一操作连发两次的行为清单**——postcard 连寄两张一样的/say 同一句话两遍/mark 同名两次/bury 空手再 bury/open_door 同一目的地连开两次,每个记录:合理拒绝/幂等/重复记账。**词汇需求统计**:walk 方向喂 30 个自然说法("往前/继续/回头/朝亮处/往里走/左拐/后退"……),统计识别率(IF 行规:被拒的输入是金矿,照需求量词表)。

输出 qa_probe_report.md:按五链分组,每条探针 期望/实际/判定(✓/✗)/证据(关键输出截 80 字)。✗ 的就是新 bug 清单,按严重度排序收尾。

验收:`python nowhere/tests/qa_probe.py` 不炸,报告生成,时间链第 2 条(walk_to 双计)必须复现。

---

## 卡23:风俗/内容错配体检(脑 2026-08-20 预判的最大错配家族)— 立刻可发

只许新建:nowhere/tests/qa_alignment.py、qa_alignment_report.md(仓库根)

背景:脑已实锤——describe.py `_get_region` 文化区矩形把第比利斯/埃里温判成 middle_east、阿拉木图判成 east_asia、加德满都判成 east_asia、雷克雅未克判成 any;且 encounters.py 的大洲矩形是另一套(安塔利亚在 encounters=非洲、describe=europe),两套矩形互相矛盾。这只是八亚种之一。

**体检覆盖八亚种(只量不修):**
1. **文化区矩形**:取 200 个世界名城坐标过 _get_region + encounters 的归属函数,人审名单对照,输出"矩形判错/两套矩形互判不一致"清单。
2. **地名键漂移**:localcolor/humanities/traces(如有)/festivals(如有)的键,与 geocode 链、explorable_index 的键两两比对——"喀什"vs"喀什地区"vs"Kashgar"式的一地多名、同键不同地,全列。
3. **国家码边界错**:food_by_country 的国家码 vs 主要城市 country_code_of 反查,边境城/海外领地(留尼汪/法属波利尼西亚/香港/澳门)单列人工审。
4. **历法漂移**:节律/节日卡里写死月份的宗教节日(斋月、开斋节、春节、藏历新年、泼水节没问题)对照 2026-2030 实际日期表,伊斯兰历类全部标 ✗(每年提前 ~11 天,写死必错);南半球的冬季节日文案(圣诞=雪)出现在悉尼/开普敦 12 月,标 ✗。
5. **城市点 vs 景区面**:localcolor 卡里提到具体景点(漓江/黄山/天池)的,核对景点坐标与地名落点距离,>50km 的列出来("桂林"落市区却给你漓江卡)。
6. **物种/植被超分布**:flora/encounters 卡里的动植物名,对照常识分布带(椰子/棕榈→热带,雪松→山地……),规则粗筛出可疑,人工二审。
7. **时代错**:全文扫"绿皮火车/供销社/公社/粮票/BP机"等时代词,逐条列出人工判(有些是故意的怀旧,标出来人看)。
8. **AI 编的事实**:localcolor/humanities 卡里含具体数字(距离/价格/年代/人数)的,抽 10% 与离线维基(zim)对答案,列"对不上"清单。

方法:1-4 规则脚本;5-8 规则粗筛+报告分级(实锤/可疑/人审)。**不许用在线 API**,维基对答案用 data/packs/wikipedia_zh_mini.zim(facts_zim.py 有现成读法)。

输出 qa_alignment_report.md:八亚种分组,每条=卡/地点/为什么可疑/严重度。收尾给"建议修哪几个矩形、哪批卡"的优先级。

验收:`python nowhere/tests/qa_alignment.py` 不炸;亚种 1 必须复现已知的 5 个实锤(第比利斯/埃里温/阿拉木图/加德满都/雷克雅未克)。

**亚种扩编(脑 2026-08-20 加三个,同报告输出):**
9. **电台流腐烂**:radio_fallback.json 101 个台的流 URL 逐个 HEAD 探活,死流列清单(收割日期未知,流媒体 URL 半年死一批)。
10. **海上死寂**:模拟 walk 进海后连走 10 步,统计文本里 localcolor/人文/遭遇的命中数——全空就是内容黑洞,列出来。
11. **记忆膨胀**:_geocode_cache/scene 缓存/journey.json 在长会话(模拟 500 次调用)后的体积曲线,无界增长的列出来。

---

## 卡24:语义文本审计(in-context LQA,游戏公司行规+学术界方法)— 立刻可发

只许新建:nowhere/tests/qa_lqa.py、nowhere/tests/qa_lqa_golden.json、qa_lqa_report.md(仓库根)

**方法来源(照做,不许发明新轮子):**
- 游戏 LQA 行规:**玩出来的,不是看出来的**——审"渲染出来的整段文本",不是审数据文件;每条 bug 带 ID/严重度(S1-S4,见通用规矩)/复现输入。
- 学术界 PCG 评估(Expressive Range Analysis, Smith & Whitehead 2010;Summerville 2018):生成器的多样性要**量化**——同一输入跑 N 次,看去重率/重复曲线,池子浅不浅拿数字说话。
- LLM-as-judge 2025 行规(FaithJudge/EMNLP 2025 等):**两层制**——规则层全量跑(快/免费),LLM 裁判只抽 5-10%(慢/花钱);裁判模型≠生成模型;裁判先用 golden set 校验,与人类标注一致率 <80% 的裁判结论不采信。

**三层执行:**

1. **批量玩出来(in-context 采样)**:脚本驱动真实渲染链——open_door + walk×5,覆盖 ≥100 个地点(localcolor/humanities 键+随机野地)× ≥3 个模拟时段(晨/昏/夜)× 南北半球。所有输出文本+当时 env(温度/天气/biome/时段)存 jsonl。**不审数据文件,只审这条流水线的最终输出。**

2. **规则层(全量,免费)**,每条命中记 ID+S 级+复现输入:
   - 禁词(很/非常/十分)→ S3;占位符残留/None 泄漏/双句号 → S3
   - 数字矛盾:文本说"冷/寒风"但 env.temp>25;说"汗流浃背"但 temp<0;海拔数字前后不一致 → S1
   - 地名漂移:同一段里出现两个不同地名(排除"从A到B"句式)→ S2
   - 场景错配粗筛:码头/渔船/海港词 出现在内陆 biome(距海>100km);雪/冰川词 出现在热带(|lat|<23.5 且海拔<2000);沙漠词出现在 water biome → S2
   - 自称矛盾:同一段先说"四下无人"再说"人声鼎沸"类反义词对 → S1
   - **多样性量化(ERA 方法)**:同一地点同一时段连跑 30 次 walk,统计文本去重率和变体消耗曲线;去重率 <70% 的地/层标 S4(池太浅);全库变体池 <5 条的渲染分支列清单。
   - 长度分布:落地文本 >600 字(信息轰炸)或 walk 文本 <15 字(死寂)的占比 → S4。

3. **LLM 裁判层(抽样,两层制)**:
   - 先用 qa_lqa_golden.json(脑已标注 20 条:5 条好文本+15 条各 S 级坏文本,executor 不许改)校验裁判:一致率 ≥80% 才进入下一步,达不到就换 prompt/换裁判模型再校,并在报告里写校验结果。
   - 裁判 ≠ 文本生成方(文本是模板+人工卡,裁判可用任何便宜 LLM;调用方式照仓库里已有的 LLM 调用惯例,没有就用硅基流动 DeepSeek,key 从环境变量读,**key 不许写进代码**)。
   - 从规则层全过的文本里抽 10%(按地点分层抽样),裁判按 S1-S4 rubric 判:事实有据吗(对照 env 和地点常识)?错配吗?断气吗(像人话吗,拼段处顺吗)?复读吗?
   - grounding 原则(VLDB 2025):文本说的超出 env 数据+卡片原文的,算 S1 幻觉("文本可以是真话但不是这个世界的事")。

**输出 qa_lqa_report.md**:S1-S4 分组清单(ID/严重度/现象/复现输入/根因初判);多样性量化表(最差 10 个地/层);裁判校验一致率;三层各抓到多少条的对比(证明规则层和裁判层各自的价值)。

验收:脚本不炸;golden set 校验跑出一致率数字;规则层必须复现这条已知断气——"像刚下过雪风声大"(缺句号拼接,落地拉普兰种子可复现);多样性量化必须有具体数字不许只说"够/不够"。

**规则层补三条(脑 2026-08-20,来自 IF 测试文献):**
- **悬空发现(Chekhov's gun)**:文本提到具体地标/实体("远处有座塔""有炊烟"),但对不上任何数据源(humanities 卡/hydrology/feature)——IF 行规:描述里出现的东西,玩家走向它必须有下文。规则粗筛:discovery 句里的实体词与数据层交叉,对不上标 S2。
- **默认回复疲劳**:扫"还没开门呢""找不到「」"等错误/兜底回复,每个意图只有 1 条文案的标 S4(行规:单调默认回复是 IF 第一杀手)。
- **跨步叙事矛盾**:长会话采样里,narrative 说"转身向南"后 3 步内出现方位矛盾句(朝向与太阳方位可对算)标 S1。

**方法论补丁(同行规):冷启动测试抓不到"历史依赖型 bug"(代词绑定/状态漂移),采样必须是长会话——同一旅程连续 100 步随机指令序列,不许每步重置。**

---

## 卡26:落点校验(落水落点+粗网格)— 立刻可发

只许改:nowhere/landing.py、nowhere/server.py(open_door 落地处)、nowhere/tests/test_landing.py(新建)、nowhere/data/pool.json(只许按报告改坐标)

背景:脑实测 pool.json 329 个落点 10 个落水(耶路撒冷 31.8,35.2、贝鲁特、惠灵顿、新西兰、珍珠港、阿皮亚——大堡礁/北大西洋/死海/里海是水域目的地不算)。根因:grid_tiny.npz 1° 粗网格把海岸格标成 ocean + 落点坐标无人校验。落在耶路撒冷却"你在水里",世界观当场碎。

1. **先量**:遍历 pool.json + landing 抖动后的点,surface 为 water_* 但 name_hint 是陆地地的,全列进报告(含建议的最近陆地坐标)。
2. **再修两层**:
   a. landing.py:落点选定后校验 surface,水域且非水域目的地 → 8 方向 0.5° 步进找最近陆地 nudge(找不到才保留原点并在 data 标 "water_landing": true);
   b. server.py open_door:被 nudge 的情况静默不加戏;水域目的地保持现状。
3. pool.json 坐标明显偏离其城市的(耶路撒冷),按报告逐个修到城市中心。
4. test_landing.py:329 点全过校验(陆地地→land surface,水域目的地白名单);耶路撒冷落点不在水里。

验收:新测试绿;`python -m pytest nowhere/tests -q` 不引入新红。

---

## 卡27:旅程收尾(peak-end:记忆=高潮+结尾)— 依赖卡6

只许改:nowhere/server.py、nowhere/journeys.py、nowhere/describe.py、nowhere/tests/test_farewell.py(新建)

依据(不许偏离):Kahneman peak-end rule——人对一段体验的记忆≈高潮+结尾,长度几乎不计(Kemp 2008 度假研究:时长对评价零影响)。乌有乡落地有高潮(establish 段),但**离开一段旅程=直接消失**,没有结尾。切走布拉格去纽约,布拉格就死掉了——按 peak-end,这段旅程在记忆里就是"没结尾",整个 atlas 的回味打折。

1. 离开/切换旅程时(open_door 去新地、switch_journey 触发挂起),给一段**告别时刻**(1-3 句):
   - 用当前 env 收一个"最后一眼":你在这地方的最后一个画面(天气/时段/地标卡,优先没见过的卡);
   - 一句身体告别(变体池 5 条:"你又看了一眼{地标}。然后你转身,门就在那。""鞋底还沾着这里的土。门在身后合上。");
   - 进 journey 档的 log(kind="farewell")。
2. 重游归来(switch 回旧档)给对称的**回来时刻**:距上次离开过了多少模拟时间("你离开时还是{季节},现在{季节}了")+ 痕迹链阶段推进(卡10 的钩子在这)。
3. 文案规矩照旧:不煽情、不总结("这次旅行很有意义"枪毙)、证据不陈述——给画面,不给评价。
4. test_farewell.py:离开触发告别段且进 log;归来文本含时间跨度;文案池无禁词。

验收:新测试绿 + test_journeys 绿。

---

## 卡28:意外层(mishap,旅行的记忆锚)— 不依赖其他卡

只许改:nowhere/server.py、nowhere/state.py、新建 nowhere/data/mishaps.json、nowhere/tests/test_mishap.py(新建)

依据:Camino 论坛的 LIVE 帖里最有血有肉的全是倒霉事(凌晨两点信用卡被盗刷);旅行研究里"意外+克服"是记忆编码最强的锚。乌有乡现在**全是顺的**——没有不顺,就没有故事。意外不是惩罚,是叙事原料。

1. data/mishaps.json,20 条起步,分四级(全是小不顺,不许出大事):
   - 鞋级:"鞋里进了粒沙,你走三步硌一下,停下来倒。"(无任何状态影响)
   - 时级:"突然一阵雨,你在屋檐下站了二十分钟。"(elapsed_hours +0.3,与 weather 数据联动:env 本来就有雨才出)
   - 路级:"走错了,绕回来多花了半小时。"(elapsed_hours +0.5,位置不变)
   - 物级:"水袋漏了,到下一个镇之前得省着喝。"(挂 state.mishap_tag,后续 3 步内文案里口渴权重升)
2. 触发:walk 每步 3% 概率,同一场旅程 10 步冷却,每条卡一旅程只出一次(state.mishap_seen,序列化)。**只在与 env 不矛盾时出**(没雨不出雨级,城里有店不出物级——读 env 判定)。
3. 每条意外**有下文**:下一步 walk 的文本里 50% 概率带一句余韵("鞋里那粒沙好像还在")——意外要有回声,不然就是孤立事件。
4. test_mishap.py:3% 概率可 mock 命中;env 无雨时雨级卡永不出;同一卡一旅程不重复;回声在下步出现。

验收:新测试绿 + walk 相关测试绿。

---

# 效率基建组(2026-08-20,旋复:"怎么让下次找bug更顺利/加城市写卡更有效率")

## 卡29:一条命令全量体检(health)— 立刻可发

只许新建:nowhere/health.py、nowhere/tests/test_health.py;不许改已有 qa 脚本(收编调用,不改逻辑)

1. `python -m nowhere.health`:依次跑 qa_geocode / qa_probe / qa_alignment / qa_lqa 的规则层(四个脚本如果还没建,先把探活+禁词+结构这几个最轻的收进来,其余 stub 留接口),外加 `pytest nowhere/tests -q`。
2. 输出一份分级报告(控制台摘要 + nowhere/health_report.md 全文):每项 ✓/✗/S 级,✗ 的带复现输入。总耗时控制在 3 分钟内(重的探针异步并行)。
3. **复利钩子**:报告尾部自动生成"新确认 bug 类型清单"(与上次报告 diff,首次为空跑)——每种确认的新病,提示该加进哪个 qa 的规则/golden。
4. test_health.py:命令跑通、报告生成、✗ 项确实出现在报告里(mock 一个已知失败)。

验收:`python -m nowhere.health` 三分钟内出报告;故意弄坏一个卡,下次体检抓得到。

---

## 卡30:加城市流水线(add_place)— 立刻可发

只许新建:tools/add_place.py、tools/__init__.py(如需)、nowhere/tests/test_add_place.py;不许改数据文件(merge 只在显式 --merge 时动)

`python tools/add_place.py 南京` 一条龙,**人只写卡,其余管道干**:

1. **坐标关**:geocode 查坐标 + country 反查校验,错配/落水(terrain.surface)当场红字拦下,给建议坐标——错配城市根本进不了门。
2. **实据关**:zim(nowhere/data/packs/wikipedia_zh_mini.zim,facts_zim.py 有读法)拉条目存 drafts/南京_facts.md,供写卡参考。
3. **模板关**:生成 drafts/南京_cards.json 骨架——localcolor 五类(物产/声音/痕迹/植被/美食)+ 节律,每个字段带注释说明(hours 是 [起,止) 左闭右开、months 不写=全年、卡文案规矩一句话),照 docs/CARD_FORMAT.md(卡31)。
4. **质检关**:`--check 南京`:禁词扫描(含时间语境假阳性过滤,merge_qc.py 里有现成正则)/节律 hours 合法/键与文件名一致/坐标仍对——五关全过才许 merge。
5. **合并关**:`--merge 南京`:进 localcolor.json 主文件(键冲突=红字停,不许静默覆盖)/explorable_index 注册/跑 test_localcolor + test_humanities。
6. 幂等:同地重复 add 提示已存在;drafts/ 里有人改过的草稿不许覆盖(先备份)。
7. test_add_place.py:全流程用 tmp 目录 mock 跑一遍;错配城市在第 1 关被拦;质检抓得出禁词卡。

验收:新测试绿;拿一个真城市(南京)全流程走通留档。

---

## 卡31:资产存档(格式文档+写作 prompt)— 立刻可发

只许新建:docs/CARD_FORMAT.md、docs/WRITING_PROMPT.md

1. **CARD_FORMAT.md**:localcolor 五类卡的字段和语义(节律 hours [起,止) / months 缺省全年 / 卡 key 规则 "{地}/{类}/{i}")、humanities 卡结构、souvenirs/festivals(卡11)/traces(卡10)的格式、**常见坑清单**——键名漂移(突尼斯市≠突尼斯)、months 丢失(冰岛极光 9-3 月)、hours 越界、zh 空串。全部从 localcolor.py/humanities.py 的解析代码反推,和代码对不上算错。
2. **WRITING_PROMPT.md**:把 task_text_quality/rewrite/ 里**过了敦煌单测的那版 prompt** 收编正式化——旧北京声口五条(一开场就在现场/你全程在动/声音是惊喜/色香味叠层次/零攻略百科腔)+ 禁词表 + 时间季节双硬要求(hours 整数+months)+ 四维度内容要求(动物/水文/植物/天空)+ 质量地板样例(廷巴克图/阿瑜陀耶/敦煌新卡各一)。**这是验证过的资产,一个字不许改,只许搬运整理。**
3. 两份文档头部分别写"给谁用":CARD_FORMAT 给加卡的执行 AI(配合卡30 的 --check);WRITING_PROMPT 给写卡的 AI(配合实据 draft)。

验收:文档生成;CARD_FORMAT 的字段说明与 localcolor.py 解析代码逐条对得上(抽查 5 处);WRITING_PROMPT 与 task_text_quality 原文 diff 为零(搬运不改写)。

---

## 卡32:卡源级差(手写层优先,烘焙层降级)— 立刻可发

只许改:nowhere/localcolor.py、nowhere/baked.py、nowhere/tests/test_localcolor.py

背景(脑实测,audit_cards_20260820.md):拉普兰连抽 12 张,手写卡 4 张/烘焙模板句 8 张——455 地手写心血和收割模板平权同池。写得好的地方反而烂卡渗漏更多(手写层先抽空,烘焙占比升高)。

1. **级差抽卡**:localcolor.draw() 两档——手写层(该地五类卡)没抽空时,烘焙卡不进池或权重×0.2;手写层空了烘焙才顶上("先吃现房,再吃罐头")。饭点美食加权和级差叠乘。
2. **外文名过滤**:baked.render_food:zh 为空或纯 ASCII 名 → 返回 None,draw() 滤掉不出卡(同卡5 规矩,这里在渲染层再拦一道)。"Grytbit/äggost"这种裸英文进中文散文=断气。
3. **模板壳减肥**:_FOOD_TEMPLATES 的万能尾句("在这里,吃饭不是将就的事"/"名字记不住没关系,味道会替你记住")全删——空话;无 desc 的模板(_FOOD_TEMPLATES_NODESC)整个砍掉,没有 desc 的食物不出卡。壳剩前 3 条,尾部不再补话。
4. test_localcolor.py 加:同地连抽到手写层空,期间烘焙卡占比 <20%;zh 空的美食卡永不出现;渲染结果不含"在这里,吃饭不是将就的事"。

验收:新测试绿;重跑 audit_cards 的拉普兰 12 连抽,手写 4 张全出在前 6 抽内。

---

## 卡33:通用场景池按 biome 门禁 + 深度扩池 — 立刻可发

只许改:nowhere/describe.py、nowhere/hydrology.py、nowhere/data/scene_water_features.txt、nowhere/data/scene_walk_discovery.txt、nowhere/tests/test_describe.py

背景:通用场景文件是"为了方便随便匹配"的重灾区——32 句 water_features 里码头/海运句在内陆苔原渲染出来;walk_discovery 66 句全球共享,重复感的另一半来源(变体池消耗曲线见卡24 量化)。

1. **句级 biome 标注**:scene_water_features.txt 每句行首加 tag(#河 #湖 #码头 #海),渲染层按 feature type + 距海(hydrology 数据有 distance_km;拿不到就用 terrain.surface 探 10km 内有无水_ocean)过滤——内陆永远不进 #码头 #海 句。tag 解析进 _load_scenes(向后兼容:无 tag 句算 #任意)。
2. **hydrology 过滤索引修复**(审计低8):代码注释声称的行号索引与真实文件对不上,_LAKE_IDX={1,6} 删错句——改成按 tag 选句,索引死代码删掉。
3. **发现池扩容**:scene_walk_discovery.txt 66→130 句,新增句按 biome 分组(#城 #林 #漠 #山 #海 #极),_pick_discovery 按 current biome 过滤(拿不到 biome 用 surface 映射)。新句文案照 WRITING_PROMPT(卡31)声口,每句独立成景,禁模板壳。
4. test_describe.py:内陆点渲染 water_features 永不含"码头/卸货/船";tag 过滤后各 biome 池 ≥8 句;Discovery 同 biome 连抽 8 次去重率 ≥6/8。

验收:新测试绿 + test_hydrology/test_regression 绿。

---

# 质量层二期(2026-08-20,旋复:"文本质量如何提升")

理论:文本质量 = 杆 × 卡 × 缝 × 回路。杆已有(卡31),这组补另外三个角。

## 卡34:全卡打分普查(census)— 立刻可发

只许新建:nowhere/tests/qa_census.py、qa_census_report.md(仓库根)

卡24 是巡逻(抽样),这张是普查(全量)。给**每张卡**打分,产出差距地图。

1. 裁判先用 qa_lqa_golden.json 校验(一致率 ≥80% 才上岗,达不到换 prompt 重校;裁判≠生成方,key 环境变量读,不许进代码)。
2. 全量打分对象:localcolor.json + 区域文件 + humanities.json 全部 films/historical 的每张卡,5 分制:
   - 5=杆上(旧北京/敦煌级,可当新样例)
   - 4=好(有地方血肉,声口对)
   - 3=能用(信息对但平,像资料卡)
   - 2=差(模板壳/空泛/断气)
   - 1=有害(错配/编造/英文裸进)
3. 输出 qa_census_report.md:总分分布直方图、**按地平均分排名**(最好 20 / 最差 40)、每张 <3 分的卡列出(卡原文+扣分理由一句话)。
4. **产出是重写优先清单**:按"地平均分×卡数"排出最值得重写的 30 个地——这是下一波重写工程的靶子,不许自己动手改卡。

验收:全量覆盖(卡数对得上文件计数);golden 校验有数字;最差 40 地清单成型。

---

## 卡35:缝合工坊(seam quality)— 立刻可发

只许改:nowhere/describe.py、nowhere/server.py、nowhere/tests/test_seam.py(新建)

背景:卡再好,拼起来也要顺。已实锤的缝病:落地段缺句号("像刚下过雪风声大")、walk 转移句("走着走着,草地,一马平川")混进落地段、全半角标点混用、人称漂移。这些病**重写一万张卡都治不了**,只能在缝上治。

1. **标点规整器**:`_normalize_prose(text)`——拼接处缺句号补句号(前段尾字是中文且后段开头非标点→补"。")、全半角统一(英文句读转中文语境用)、连续句号压成一个、多余空格压掉。进 describe.compose() 和 server 各拼段处(落地/走/wait 一处封装,处处调用)。
2. **段落语义守卫**:compose 前扫 sections——"走着走着"类转移短语只许出现在 walk 文本(落地段出现即剥除);开场段(establish)禁入"你继续/又走了一段"类续行句。规则表形式,可扩展。
3. **人称统一**:段落渲染链出口统一"你"——扫 sections 里孤立的"他/她/它"开头句(卡内部自带的不动,只管拼接产生的)。
4. **缝合烟测**:test_seam.py 固定 seed 跑 8 地×落地+3 walk,断言输出无"雪风声"式无标点拼接(mock 段尾构造)、无转移句进开场、标点归一。
5. 修完把"像刚下过雪"案例跑一遍进测试(回归锚)。

验收:新测试绿;重跑卡22 渲染链探针,占位符/双句号/标点混用清零。

---

## 卡36:品味回路(旋复盲评,轻流程)

只许新建:docs/TASTE_LOOP.md、nowhere/tests/qa_taste_sample.py

杆不是文档写死的,是你读出来的。把"你骂一句我修一批"变成制度:

1. `python nowhere/tests/qa_taste_sample.py`:从渲染输出里随机抽 10 段(盲评:不带地名标注,打乱顺序,存 docs/taste_samples/2026-08-XX.md)。
2. 旋复读,每段一个字评:好/平/差(愿意多写更好)。
3. 评完的段回填:平/差的进 qa_lqa_golden.json 当新坏样例,好的进新好样例——golden 长大,裁判越判越像你。
4. docs/TASTE_LOOP.md 写清这个循环怎么跑、多久一次(建议:每波大改后一次)、回填格式。**不自动执行,旋复手动触发。**
5. 铁律:这个流程的产物只进 golden set,不直接改卡——改卡走卡34 的优先清单。

验收:抽样脚本跑通;TASTE_LOOP.md 成文;首次盲评包生成(10 段,等你读)。

---

# 走路引擎组(2026-08-20,旋复:"走路引擎很无聊,走几步就往回走";脑在长江实测5步实锤四病)

## 卡37:河流意识(196 条离线水系接线,含长江 7 段)— 立刻可发

只许改:nowhere/server.py、nowhere/hydrology.py、nowhere/describe.py、nowhere/tests/test_river.py(新建)

背景:water_features_offline.json 有 196 条水系(长江 7 段:宜宾/重庆/三峡/武汉/九江/南京/入海口;珠江 5 段;漓江 2 段),旋复亲手分的段——但 walk 渲染把水文整个跳过(server.py 约1165 硬编码 water_features=[],注释"Overpass 被墙")。**走在长江上,看不见长江。**

1. **离线水文接线**:walk/落地时用 water_features_offline.json 判"你在不在河边"(距某分段中心 < radius_km,server.py 里已有 _offline_water_nearby 的距离算法可复用);在河边 → 水文描写走离线分段(名称+类型),不再依赖 Overpass。原 Overpass 在线路径保留为增强(能通就细化),不通静默降级到离线——**不许再整段跳过**。
2. **沿河叙事**:在河边且行走方向与河流走向夹角小(用前后两个分段中心算流向)→ 识别"顺流/逆流",walk 文本给一句(变体池 4 条:"江水和你一个方向,它走得比你稳。"/"你逆着水走,水声一直在耳朵边。");跨过流向(夹角大)→ "你横着江的走向走"或渡口意象。只在河流 3km 内生效,离开就淡出。
3. **open_door("长江")分段感知**:special_places 的长江单点(30.7,111.0)扩为按分段就近落——to="长江"默认三峡段(风景段),to="长江 上游/入海口/南京段"可指定(匹配分段名/顺位);落地文本报段名("长江,三峡段")。
4. **河边专属卡池**:scene_water_features.txt 增 8 句 #江 句(江雾/渡船/货轮/江滩卵石/汽笛,声口照 WRITING_PROMPT),只在河边渲染。
5. test_river.py:落地"长江"→水文描写出现且分段正确;沿河走 3 步至少 1 次顺流/逆流句;离开 5km 后江意象消失;"长江 入海口"落到上海段。

验收:新测试绿;长江实测 5 步每步都有江的存在感(卡37 报告贴 5 步原文)。

---

## 卡38:look_around 去"往回走"— 立刻可发,10 分钟的活

只许改:nowhere/server.py、nowhere/tests/test_look_around.py(新建,或就近测试文件加)

背景:server.py 约1502 硬编码"你往回走，回到了原来的地方。"——环视本来不移动位置,这句假装走了一圈又回来,且每次必出。旋复体感"走几步就说往回走了"的直接来源。

1. 删掉该句。环视的收尾改为**不动身位的收束**(变体池 5 条,低频出现,40%概率不收尾直接停):"你看完了,收回目光。"/"风把刚才的声音又送了一遍。"/"你站了一会儿,没动。"
2. look_around 期间不许有任何"移动"语义句(exploration 段固有文案里扫一遍,凡"走/迈/步"动词进 look_around 上下文的,换静态动词)。
3. test:look_around 输出永不含"往回走/回到";两次 look_around 收尾句不同(seed 控制)。

验收:新测试绿;连续 look_around 3 次输出贴报告。

---

## 卡39:walk 节奏去复读— 立刻可发

只许改:nowhere/server.py、nowhere/describe.py、nowhere/tests/test_walk_rhythm.py(新建)

背景(长江 5 步实测):每步都出"附近有电台在播。CRI Easy FM,music/news"(电台 sticky 每步重渲染)+"树根绊了一下,你没倒"(触觉池小)+"同时,"胶水词每段都当开头。

1. **电台冷却**:radio 文案 N 步冷却(默认 5 步)+只在换台/信号变化时再提;同台复读改"电台还在,声音小了"式弱化句(变体 3 条)或干脆沉默。
2. **触觉/嗅觉池扩容+冷却**:_TOUCH_BY_SURFACE 每面从 2-4 句扩到 6 句(新句照声口);同一句 10 步内不重出(recent 池,已有 recent_scenes 机制,接线到 touch/smell)。
3. **"同时,"胶水**:compose 的连接词变体池扩(同时/这会儿/紧接着/没过多会儿/——直接句号另起),按 rng;同一段连接词不重复。
4. **方向句只在变化时说**:narrative 已有 direction 追踪,walk 文本里"你继续往北走"这种每步句删掉,只在转向/第 3 步节奏点出一次。
5. test_rhythm.py:固定 seed 走 10 步,统计:radio 句 ≤2 次、同一 touch 句不重复、"同时,"占比 <30%、方向句 ≤3 次。

验收:新测试绿;长江 5 步重跑,复读感肉眼可见消失(报告贴前后对比)。

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
3b. **方向词汇表扩充(IF 行规"unrecognized commands are gold")**:现在 _BEARING_MAP/_SEMANTIC_MAP(server.py:117-130)只有罗盘词+"上山/向海/向前",旅行者说"往回走/回头/继续/直走/往后退"全不识别,invalid=True 时**按原方向照走**(只加一句提示)。改:(a) 词汇表加:前/往前/直走/继续→forward;后/回/回头/往回/退→heading+180(相对向,用 state.heading);左/右→heading∓90;(b) 仍然不认识的:停下不走,返回"听不懂「X」。可以说:前/后/左/右/八个方位/上山/向海。"——IF 行规:听不懂就该明确失败,猜着执行=对玩家说谎。这是拍板项,executor 照(a)(b)做,有异议在报告里提不许自作主张。
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

## 卡25:提示词注入闸(AI 是玩家的游戏特有的攻击面)— 立刻可发

只许改:nowhere/web.py、nowhere/server.py、nowhere/tests/test_injection.py(新建)

背景:乌有乡的旅行者是 AI,文本=它的眼睛。web.py 的 post_message、reply_postcard 是公开端点,内容**不过滤**就渲染进 walk/postcard 文本——等于任何人都能往 AI 的 context 里写字。人写的话进 AI 的眼睛,中间必须有闸。

1. web.py 两个写入端点加内容闸(进库前):
   - 长度上限:message 200 字、postcard 回复 300 字,超出截断;
   - 剥控制字符(换行保留,其余 \x00-\x1f 删);
   - 拒收清单(命中即 400):典型注入句式("忽略/无视/ignore previous/以上指令/system prompt/你现在是/new instructions"——中英都列,大小写不敏感)。
2. server.py 渲染层兜底(第二道):message/postcard 内容进文本前,统一过 `_sanitize_external(text)`:剥反引号/代码块标记,外加明确包裹(如「」),让 AI 玩家一眼认出这是"别人留的话"不是系统叙事。
3. test_injection.py:post 注入句 → 400;正常留言 → 渲染后带「」包裹且无控制字符;剥掉的句式清单逐条过。

验收:新测试绿 + test_web 绿。

---

## ★卡册依赖注记(新功能继承烂地基,修顺序错了白做)

- 卡15(atlas)依赖 _REGION_MAP 数大洲——**矩形错的 atlas 就错**,卡5 修完矩形之前卡15 只是文字对、数字错,发排时注意。
- 卡16(盲开门)与卡11(节日历)冲突:节日卡会喊"泼水节"=报答案。**卡16 实现时,blind=True 期间节日卡也要禁抽**,卡16 里已写 humanities 禁抽,executor 注意把节日卡一并处理。
- 卡12(意图门)动 salience;卡1-bug3 已改 prev_env——如果卡1 还没合,卡12 要在卡1 之后发。

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

1. 新工具 `bury(note: str | None = None)`:把身上带着的 souvenir(state.souvenir)埋在当前坐标,**可以留一句话**(geocaching 社区共识:最好的 cache 带故事,不只是物件)。空手 → "你没东西可埋。"埋掉后 souvenir=None。返回一句(变体池 3 条:"你把{name}埋进了土里。这里记得。")。note 进注入闸(卡25 的 sanitize)。
2. 存储:placememory 层加 buried.json(全局跨旅程,尊重 NOWHERE_HOME):[{name, desc, from, pos, buried_at}]。上限 100 条 FIFO。
3. 发现:walk 时每步检查 3km 内有无埋藏,有 → 8% 概率"脚碰到一个铁盒"(变体池 3 条):空手则捡为 souvenir,有主则只看见不拿("你把它又放了回去")。**埋时留了 note 的,发现时一起读出来("盒子里还有一行字:{note}")**。发现后条目保留(下一个人还能踢到)。
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

---

# 灵感第二拨(旋复 2026-08-20 拍板"可以";浏览器实探 Slow Roads / earth.fm / Dérive app)

排序即优先级:卡16 > 卡17 > 卡18 > 卡19 > 卡20 > 卡21。

---

## 卡16:盲开门(GeoGuessr 反转,落地不报名字)— 第二拨头号

只许改:nowhere/server.py、nowhere/state.py、nowhere/tests/test_blind.py

设计(不许偏离):落地不告诉地名,旅者靠证据(电台语言/太阳方位/植物/人文卡)自己拼;猜或认输才揭晓。**证据照常给,而且要给足——盲开不是少给信息,是把"名字"这一项扣下。**

1. open_door 加参数 `blind: bool = False`。blind=True:正常随机落点,但 `state.blind = True`(序列化),落地文本**砍掉地名头**(`【瑞典,拉普兰,黄昏,夏天。】`整段不输出地名,保留时段季节),返回文本一句不提地名。
2. 盲开期间(state.blind=True):
   - humanities 卡禁抽(卡文本常含地名,等于直接报答案);
   - localcolor 卡**照抽**("艾提尕尔"这种专名就是线索,允许);
   - 电台/天气/植物/天空照常(全是证据);
   - where_am_i 隐去地名和坐标,只给"你走了 X 公里,出门 Y 小时"。
3. 新工具 `guess(place: str)`:归一化比对地名(命中 place_name 或别名,或命中所在国家且明确说了国家名)→ 猜中:揭晓(地名+国家+一句"对,就是{place}。"),state.blind=False,走人正常流程;猜错:给一条新线索(从粗到细:大洲→气候带→国家),`state.blind_clues += 1`,最多 3 条线索后第 4 次猜错直接揭晓("是{place}。你绕了有点远。")。
4. 新工具 `reveal()`:认输,直接揭晓,state.blind=False。
5. test_blind.py:盲开落地文本不含地名;walk 后文本仍不含;guess 错误→给线索;guess 命中国家/地名→揭晓;reveal→揭晓;blind 状态存得进档读得回来。

验收:新测试绿 + test_server_integration 绿。

---

## 卡17:门牌号(同一个 key 永远开同一扇门)

只许改:nowhere/server.py、nowhere/tests/test_doorkey.py

1. open_door 加参数 `key: str | None`。给了 key:不随机,用 `hashlib.md5(key.encode()).hexdigest()` 前 8 位转 int,对 landing pool(landing.py 的 random_spot 用的池,读代码确认)取模,落固定点。同 key 永远同点。key 与 to(地名)互斥,同时给 → 报错文本("门牌和地名只能给一个。")。
2. key 归一化:strip+lower,空格/全半角不影响("旋复的门"=="旋复的门 ")。
3. 落地文本照常报地名(门牌不是盲开),但在文本尾部加一句(变体池 2 条:"这扇门是{key}开的。别人用同一个门牌,也会落在这里。")——这是机制说明,允许陈述。
4. test_doorkey.py:同 key 两次开门坐标一致;不同 key 大概率不同点;key+to 同传报错;归一化生效。

验收:新测试绿。

---

## 卡18:漂流卡(drift,走到一半抽个方向)

只许改:nowhere/server.py、nowhere/sky.py(如需要)、新建 nowhere/data/drift_cards.json、nowhere/tests/test_drift.py

1. data/drift_cards.json,30 张起步,按 biome 分组(city/forest/desert/mountain/coast/water/any),格式:
```json
{"any": [{"text": "跟着水声走。", "action": "toward_sea"},
          {"text": "朝最亮的地方走。", "action": "toward_light"},
          {"text": "背着风走。", "action": "downwind"}],
 "city": [{"text": "找下一个拐角,拐。", "action": "turn_next"}, ...]}
```
action 映射:toward_sea/uphill 复用 walk.py 现有语义方向;toward_light = 太阳方位角(sky.py 有 sun_alt,读代码找方位角,没有就加一个);downwind = 风向反方向(weather 数据有 wind 方向就用,没有就从卡池剔除这张);turn_next = 纯文案,无机制(旅者自己选个新方向)。action 无数据支撑的卡在该环境自动剔除。
2. 新工具 `drift()`:按当前 biome(落点 biome,没有就 any)抽一张,返回卡面文案 + data 里带 action。不自动走——卡是建议,脚是旅者的。同一趟旅程同一张卡不重复抽(state.drift_seen,序列化)。
3. 卡面文案:祈使句、短、物理("跟着水声走。"不是"建议你前往水域方向")。
4. test_drift.py:任意 biome 抽出的卡 action 都有数据支撑;toward_light 卡给出的方位与 sky 计算一致;重复抽不重复卡。

验收:新测试绿。

---

## 卡19:黎明合唱(日出前一小时,鸟先醒)

只许改:nowhere/server.py、nowhere/soundscape.py、新建 nowhere/data/dawn_chorus.json、nowhere/tests/test_dawn.py

1. 判定:当地太阳高度角在 -6°~0° 之间(民用晨昏蒙影,sky.py 有 sun_alt)且为上升段(用当地小时 3-8 粗判近似,读 sky.py 看有没有现成日出判定,有就用)。
2. data/dawn_chorus.json:12 条起步,按 biome 三组(forest/city/water),文案从"一只"到"满树"的弧线("先是一只,在很远的树上。然后是第二只,近了。""天还没亮,鸟先把天叫亮了。"),禁词规矩同上。
3. 接入:listen 的 soundscape 层——黎明合唱窗口内,鸟叫卡顶替普通 soundscape;walk 时窗口内 30% 概率插一句。窗口外这些卡永远不出。
4. test_dawn.py:mock sun_alt=-3 且晨 → listen/walk 出合唱卡;sun_alt=30 → 不出;午后(sun_alt=-3 但 hour=17)不出(晨昏判别生效)。

验收:新测试绿 + test_soundscape 绿。

---

## 卡20:里程表(跨旅程总公里数)— 依赖卡6更顺,不依赖也能做

只许改:nowhere/placememory.py、nowhere/server.py、nowhere/tests/test_odometer.py

1. placememory 层(全局,跨旅程)加 `total_distance_km`(float,默认 0,持久化在 placememory 的存储文件里,读代码找顺手的存法)。walk 每步把实际走的距离(walk.step 返回的 dist_km)累加进去——只加 walk_impl/walk_to_impl 一处,别在 walk.py 里加(保持 walk.py 纯物理)。
2. where_am_i 输出加一行(变体池 2 条):"这趟出门,你已经走了 {n} 公里。"(n 取整;<1km 说"还没走出一条街")。
3. test_odometer.py:走 3 步(2km each)→ where_am_i 含"6 公里";重开档累计不清零(全局);monkeypatch 隔离存储。

验收:新测试绿。

---

## 卡21:声音出处(listen 的署名层)

只许改:nowhere/server.py、nowhere/soundscape.py、新建 nowhere/data/soundscape_credits.json、nowhere/tests/test_credits.py

1. data/soundscape_credits.json,30 条,按 surface/biome 键:
```json
{"forest": [{"who": "录音师 Jan Brelih", "where": "喜马拉雅山谷", "note": "他守了一个星期,等到一场雨后的清晨。"}],
 "water_ocean": [...]}
```
who/where/note 三件套,人名地名要真实可信(真实录音师+真实地,earth.fm 那种);note 一句,讲"这段声音怎么来的",禁攻略腔。
2. listen 无电台兜底时(soundscape 路径),20% 概率在环境音文案后附一句出处(变体模板:"这段声音,是{who}在{where}录的。{note}")。
3. 出处与环境必须匹配(森林里不给海洋录音师)。
4. test_credits.py:森林环境附的出处 biome 匹配;20% 概率可 mock rng 命中;不匹配环境的出处永不出现。

验收:新测试绿 + test_listen 绿。
