# QA Alignment Report (Card 23)

生成时间: 2026-08-20
脚本: nowhere/tests/qa_alignment.py
原则: 只量不修

---

## 1. 文化区矩形 (Cultural Region Rectangles)

总检测城市: 186
错配数: 67
已知5实锤复现: 5/5

### 已知5实锤 (必须全部复现为 ✗)

- ✗ **第比利斯** (41.72, 44.78): describe=middle_east, encounters=asia
  - describe: got middle_east, expected europe
- ✗ **埃里温** (40.18, 44.51): describe=middle_east, encounters=asia
  - describe: got middle_east, expected europe
- ✗ **阿拉木图** (43.24, 76.95): describe=east_asia, encounters=asia
  - describe: got east_asia, expected central_asia
- ✗ **加德满都** (27.7, 85.32): describe=east_asia, encounters=asia
  - describe: got east_asia, expected south_asia
- ✗ **雷克雅未克** (64.13, -21.9): describe=any, encounters=polar
  - describe: got any, expected europe

### 其他错配 (62 个)

- **维也纳** (48.21, 16.37): describe=alpine, encounters=europe
  - describe: got alpine, expected europe
- **莫斯科** (55.76, 37.62): describe=europe, encounters=europe
  - describe: got europe, expected russia
- **圣彼得堡** (59.93, 30.32): describe=europe, encounters=europe
  - describe: got europe, expected russia
- **赫尔辛基** (60.17, 24.94): describe=europe, encounters=polar
  - encounters: got polar, expected europe
  - 两套不一致: describe=europe vs encounters=polar
- **苏黎世** (47.38, 8.54): describe=alpine, encounters=europe
  - describe: got alpine, expected europe
- **慕尼黑** (48.14, 11.58): describe=alpine, encounters=europe
  - describe: got alpine, expected europe
- **米兰** (45.46, 9.19): describe=alpine, encounters=europe
  - describe: got alpine, expected europe
- **佛罗伦萨** (43.77, 11.25): describe=alpine, encounters=europe
  - describe: got alpine, expected europe
- **威尼斯** (45.44, 12.34): describe=alpine, encounters=europe
  - describe: got alpine, expected europe
- **萨格勒布** (45.81, 15.98): describe=alpine, encounters=europe
  - describe: got alpine, expected europe
- **布加勒斯特** (44.43, 26.1): describe=europe, encounters=asia
  - encounters: got asia, expected europe
  - 两套不一致: describe=europe vs encounters=asia
- **基辅** (50.45, 30.52): describe=europe, encounters=asia
  - encounters: got asia, expected europe
  - 两套不一致: describe=europe vs encounters=asia
- **伊斯坦布尔** (41.01, 28.98): describe=europe, encounters=asia
  - encounters: got asia, expected europe
  - 两套不一致: describe=europe vs encounters=asia
- **安卡拉** (39.93, 32.85): describe=europe, encounters=asia
  - describe: got europe, expected middle_east
  - 两套不一致: describe=europe vs encounters=asia
- **巴格达** (33.31, 44.37): describe=middle_east, encounters=natural
  - encounters: got natural, expected asia
  - 两套不一致: describe=middle_east vs encounters=natural
- **利雅得** (24.71, 46.68): describe=middle_east, encounters=africa
  - encounters: got africa, expected asia
  - 两套不一致: describe=middle_east vs encounters=africa
- **迪拜** (25.2, 55.27): describe=middle_east, encounters=natural
  - encounters: got natural, expected asia
  - 两套不一致: describe=middle_east vs encounters=natural
- **多哈** (25.29, 51.53): describe=middle_east, encounters=africa
  - encounters: got africa, expected asia
  - 两套不一致: describe=middle_east vs encounters=africa
- **贝鲁特** (33.89, 35.5): describe=middle_east, encounters=natural
  - encounters: got natural, expected asia
  - 两套不一致: describe=middle_east vs encounters=natural
- **安曼** (31.95, 35.93): describe=middle_east, encounters=africa
  - encounters: got africa, expected asia
  - 两套不一致: describe=middle_east vs encounters=africa
- **耶路撒冷** (31.77, 35.23): describe=middle_east, encounters=africa
  - encounters: got africa, expected asia
  - 两套不一致: describe=middle_east vs encounters=africa
- **马斯喀特** (23.59, 58.54): describe=middle_east, encounters=natural
  - encounters: got natural, expected asia
  - 两套不一致: describe=middle_east vs encounters=natural
- **科威特城** (29.38, 47.99): describe=middle_east, encounters=africa
  - encounters: got africa, expected asia
  - 两套不一致: describe=middle_east vs encounters=africa
- **大马士革** (33.51, 36.29): describe=middle_east, encounters=natural
  - encounters: got natural, expected asia
  - 两套不一致: describe=middle_east vs encounters=natural
- **乌兰巴托** (47.89, 106.91): describe=russia, encounters=asia
  - describe: got russia, expected east_asia
  - 两套不一致: describe=russia vs encounters=asia
- **河内** (21.03, 105.85): describe=east_asia, encounters=asia
  - describe: got east_asia, expected southeast_asia
- **雅加达** (-6.21, 106.85): describe=southeast_asia, encounters=natural
  - encounters: got natural, expected asia
  - 两套不一致: describe=southeast_asia vs encounters=natural
- **巴厘岛** (-8.34, 115.09): describe=southeast_asia, encounters=oceania
  - encounters: got oceania, expected asia
  - 两套不一致: describe=southeast_asia vs encounters=oceania
- **德里** (28.61, 77.21): describe=east_asia, encounters=asia
  - describe: got east_asia, expected south_asia
- **新德里** (28.61, 77.23): describe=east_asia, encounters=asia
  - describe: got east_asia, expected south_asia
- **达卡** (23.81, 90.41): describe=east_asia, encounters=asia
  - describe: got east_asia, expected south_asia
- **伊斯兰堡** (33.69, 73.04): describe=east_asia, encounters=asia
  - describe: got east_asia, expected south_asia
- **拉合尔** (31.55, 74.35): describe=east_asia, encounters=asia
  - describe: got east_asia, expected south_asia
- **瓦拉纳西** (25.32, 83.01): describe=east_asia, encounters=asia
  - describe: got east_asia, expected south_asia
- **加尔各答** (22.57, 88.36): describe=east_asia, encounters=asia
  - describe: got east_asia, expected south_asia
- **廷布** (27.47, 89.64): describe=east_asia, encounters=asia
  - describe: got east_asia, expected south_asia
- **开罗** (30.04, 31.24): describe=middle_east, encounters=africa
  - describe: got middle_east, expected africa
  - 两套不一致: describe=middle_east vs encounters=africa
- **卡萨布兰卡** (33.57, -7.59): describe=africa, encounters=natural
  - encounters: got natural, expected africa
  - 两套不一致: describe=africa vs encounters=natural
- **的黎波里** (32.9, 13.18): describe=africa, encounters=natural
  - encounters: got natural, expected africa
  - 两套不一致: describe=africa vs encounters=natural
- **突尼斯** (36.81, 10.17): describe=europe, encounters=europe
  - describe: got europe, expected africa
  - encounters: got europe, expected africa
- **阿尔及尔** (36.75, 3.04): describe=europe, encounters=europe
  - describe: got europe, expected africa
  - encounters: got europe, expected africa
- **亚历山大** (31.2, 29.92): describe=middle_east, encounters=africa
  - describe: got middle_east, expected africa
  - 两套不一致: describe=middle_east vs encounters=africa
- **加拉加斯** (10.48, -66.9): describe=north_america, encounters=americas
  - describe: got north_america, expected south_america
- **巴拿马城** (8.98, -79.52): describe=south_america, encounters=americas
  - describe: got south_america, expected north_america
- **莫尔兹比港** (-9.48, 147.15): describe=southeast_asia, encounters=oceania
  - describe: got southeast_asia, expected oceania
  - 两套不一致: describe=southeast_asia vs encounters=oceania
- **新西伯利亚** (55.04, 82.93): describe=russia, encounters=natural
  - encounters: got natural, expected asia
  - 两套不一致: describe=russia vs encounters=natural
- **叶卡捷琳堡** (56.84, 60.6): describe=russia, encounters=natural
  - encounters: got natural, expected asia
  - 两套不一致: describe=russia vs encounters=natural
- **符拉迪沃斯托克** (43.12, 131.87): describe=east_asia, encounters=asia
  - describe: got east_asia, expected russia
- **塔什干** (41.3, 69.28): describe=any, encounters=asia
  - describe: got any, expected middle_east
- **杜尚别** (38.56, 68.77): describe=any, encounters=asia
  - describe: got any, expected middle_east
- **安塔利亚** (36.9, 30.7): describe=europe, encounters=asia
  - describe: got europe, expected middle_east
  - 两套不一致: describe=europe vs encounters=asia
- **伊兹密尔** (38.42, 27.14): describe=europe, encounters=asia
  - encounters: got asia, expected europe
  - 两套不一致: describe=europe vs encounters=asia
- **塞浦路斯** (35.13, 33.38): describe=europe, encounters=asia
  - describe: got europe, expected middle_east
  - 两套不一致: describe=europe vs encounters=asia
- **特罗姆瑟** (69.65, 18.96): describe=europe, encounters=polar
  - describe: got europe, expected arctic
  - 两套不一致: describe=europe vs encounters=polar
- **摩尔曼斯克** (68.97, 33.07): describe=europe, encounters=polar
  - describe: got europe, expected arctic
  - 两套不一致: describe=europe vs encounters=polar
- **安克雷奇** (61.22, -149.9): describe=north_america, encounters=polar
  - describe: got north_america, expected arctic
  - 两套不一致: describe=north_america vs encounters=polar
- **哈尔滨** (45.8, 126.53): describe=russia, encounters=asia
  - describe: got russia, expected east_asia
  - 两套不一致: describe=russia vs encounters=asia
- **特拉维夫** (32.07, 34.78): describe=middle_east, encounters=natural
  - encounters: got natural, expected asia
  - 两套不一致: describe=middle_east vs encounters=natural
- **阿布扎比** (24.45, 54.37): describe=middle_east, encounters=africa
  - encounters: got africa, expected asia
  - 两套不一致: describe=middle_east vs encounters=africa
- **马尔代夫** (4.17, 73.51): describe=any, encounters=asia
  - describe: got any, expected south_asia
- **不丹** (27.47, 89.64): describe=east_asia, encounters=asia
  - describe: got east_asia, expected south_asia
- **尼泊尔** (27.7, 85.32): describe=east_asia, encounters=asia
  - describe: got east_asia, expected south_asia

## 2. 地名键漂移 (Place Name Key Drift)

总发现: 43

### 别名指向不存在的键 (1)

- [实锤] **Ayutthaya**: alias Ayutthaya -> 大城, 但 大城 不在 humanities places 里

### 数据有但索引无 (36)

- [可疑] **佩特拉**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **凡尔赛宫**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **哈利法塔**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **圣家堂**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **圣彼得大教堂**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **地拉那**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **埃里温**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **基希讷乌**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **基辅**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **少女峰**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **尼亚加拉瀑布**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **巨石阵**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **巴黎圣母院**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **帝国大厦**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **悉尼歌剧院**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **拉巴斯**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **斯科普里**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **明斯克**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **格雷梅**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **比萨斜塔**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **法兰克福**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **波士顿**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **波德戈里察**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **白宫**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **白金汉宫**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **的的喀喀湖**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **科威特城**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **第比利斯**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **米拉之家**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **罗马斗兽场**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **自由女神**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **蓝湖温泉**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **金门大桥**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **长城**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **阿格拉**: localcolor/humanities 有卡, 但 explorable_index 没收录
- [可疑] **魁北克城**: localcolor/humanities 有卡, 但 explorable_index 没收录

### 疑似一地多名 (1)

- [人审] **凤凰 / 凤凰古城**: 两个键可能指向同一地方, 需人工确认

### 索引有但数据无 (5)

- [实锤] **南极磷虾**: explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到
- [实锤] **墨西哥湾流**: explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到
- [实锤] **深海热泉**: explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到
- [实锤] **珊瑚礁**: explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到
- [实锤] **黑潮**: explorable_index 标了 localcolor/humanities 层, 但数据文件里找不到

## 3. 国家码边界错 (Country Code Boundary Errors)

总发现: 8

- [人审] **GP** (海外领地/争议地区): 瓜德罗普 (法国海外省): food_by_country 有 1 道菜 (Pelau)
- [人审] **PR** (海外领地/争议地区): 波多黎各 (美国领地): food_by_country 有 1 道菜 (Arroz con dulce)
- [人审] **NC** (海外领地/争议地区): 新喀里多尼亚 (法国海外属地): food_by_country 有 1 道菜 (Bougna)
- [人审] **GI** (海外领地/争议地区): 直布罗陀 (英国海外领地): food_by_country 有 1 道菜 (rosto)
- [人审] **XK** (海外领地/争议地区): 科索沃 (争议地位): food_by_country 有 2 道菜 (Tomato casserole from Gjakova, Onion casserole from Gjakova)
- [人审] **DD** (海外领地/争议地区): 东德 (已不存在): food_by_country 有 1 道菜 (grilletta)
- [实锤] **多国** (zh空串条目): 共 574 条食物 zh 为空串, 渲染时会混入英文菜名
- [实锤] **DD** (已不存在的国家码): 东德(DD)已不存在, food_by_country 有 1 道菜

### zh空串样例 (前20)

- HU: paprikash
- HU: túrógombóc
- HU: Rakott krumpli
- HU: franciasaláta
- HU: csülök pékné módra
- CA: Garlic fingers
- CA: Jiggs dinner
- CA: sushi pizza
- CA: Japadog
- CA: cod au gratin
- FI: Porkkanalaatikko
- FI: cabbage casserole
- FI: Hotsi
- FI: Clot soup
- FI: Läskisoosi
- FI: Puruvesi vendace
- FI: Pizza Poro
- FI: ärter med fläsk
- FI: Vorschmack
- GH: omo tuo

## 4. 历法漂移 (Calendar Drift)

总发现: 0


## 5. 城市点 vs 景区面 (City Point vs Scenic Area)

总发现: 0


## 6. 物种/植被超分布 (Species/Vegetation Distribution)

总发现: 17

- [可疑] **阿空加瓜**: 纬度 -32.6533, 但 flora 有极地物种 '极光球'
- [人审] **东京**: 纬度 35.6762, 但 localcolor 文案含热带词 '咖啡'
- [人审] **南京先锋书店**: 纬度 32.06, 但 localcolor 文案含热带词 '咖啡'
- [人审] **因特拉肯**: 纬度 46.6863, 但 localcolor 文案含热带词 '可可'
- [人审] **堪培拉**: 纬度 -35.2809, 但 localcolor 文案含热带词 '咖啡'
- [人审] **墨尔本**: 纬度 -37.8136, 但 localcolor 文案含热带词 '咖啡'
- [人审] **布鲁塞尔**: 纬度 50.8503, 但 localcolor 文案含热带词 '咖啡'
- [人审] **悉尼**: 纬度 -33.8688, 但 localcolor 文案含热带词 '咖啡'
- [人审] **洛杉矶**: 纬度 34.0522, 但 localcolor 文案含热带词 '棕榈'
- [人审] **皇后镇**: 纬度 -45.0312, 但 localcolor 文案含热带词 '咖啡'
- [人审] **都柏林**: 纬度 53.3498, 但 localcolor 文案含热带词 '咖啡'
- [人审] **都灵**: 纬度 45.0703, 但 localcolor 文案含热带词 '咖啡'
- [人审] **马赛**: 纬度 43.2965, 但 localcolor 文案含热带词 '咖啡'
- [人审] **维也纳**: 纬度 48.2082, 但 localcolor 文案含热带词 '咖啡'
- [人审] **布加勒斯特**: 纬度 44.4268, 但 localcolor 文案含热带词 '咖啡'
- [人审] **萨拉热窝**: 纬度 43.8563, 但 localcolor 文案含热带词 '咖啡'
- [人审] **贝鲁特**: 纬度 33.8938, 但 localcolor 文案含热带词 '咖啡'

## 7. 时代错 (Era Anachronisms)

总发现: 3

- [人审] **收音机** in localcolor.json: 文件 localcolor.json 含时代词 '收音机'
  - 上下文: ",蹄铁敲在石头上。",       "宣礼声一起,整个老城的收音机都安静了。"     ],     "痕迹": ["
- [可疑] **公社** in humanities.json: 文件 humanities.json 含时代词 '公社'
  - 上下文: "{           "name": "巴黎公社",           "year": "1871","
- [人审] **收音机** in humanities.json: 文件 humanities.json 含时代词 '收音机'
  - 上下文: ""text": "1994年4月到7月,一百天,一百万人。用收音机煽动的种族灭绝——胡图族杀图西族。基加利大屠杀纪念馆里,一间"

## 8. AI编的事实 (AI-Fabricated Facts)

总卡数: 4945
含具体数字的卡: 723
抽样验证: 72
发现问题: 72

- [人审] **巴黎圣母院** (事件): 维基百科无 '巴黎圣母院' 条目, 无法交叉验证 (年份: 2019 (2019年4月15日,巴黎圣母))
  - 文案: "2019年4月15日,巴黎圣母院的屋顶着了。尖塔倒了,铅皮屋顶化了,八百年的橡木框架烧成了炭。法国人站在塞纳河岸上唱歌。第二天,捐款超过十亿欧元。火赢了一夜,但"
- [人审] **剑桥** (事件): 维基百科无 '剑桥' 条目, 无法交叉验证 (年份: 1661 (1661年,牛顿进了三一学院。))
  - 文案: "1661年,牛顿进了三一学院。瘟疫期间他回乡下,在苹果树下想出了万有引力。你去三一学院门口,苹果树的后代还在。"
- [人审] **南京** (事件): 维基百科无 '南京' 条目, 无法交叉验证 (年份: 1937 (1937年12月起的六周。'三))
  - 文案: "1937年12月起的六周。'三十万'不是一个数字,是三十万次'一个人'。江东门纪念馆的墙上刻着名字,刻不下的更多。"
- [人审] **普林斯顿** (事件): 维基百科无 '普林斯顿' 条目, 无法交叉验证 (年份: 1746 (1746年,新泽西学院成立,后))
  - 文案: "1746年,新泽西学院成立,后改名普林斯顿。殖民地时期第四所大学。拿骚厅在独立战争时被双方都当过军营。"
- [人审] **万隆** (事件): 维基百科无 '万隆' 条目, 无法交叉验证 (年份: 1955 (1955年4月,二十九个亚非国))
  - 文案: "1955年4月,二十九个亚非国家的代表坐在万隆开会。周恩来提出求同存异。这是第一次没有西方列强在场的国际会议。"
- [人审] **惠灵顿** (事件): 维基百科无 '惠灵顿' 条目, 无法交叉验证 (年份: 1865 (1865年,新西兰首都从奥克兰))
  - 文案: "1865年,新西兰首都从奥克兰搬到惠灵顿。理由是它在南北岛之间。风太大,火车太慢,但位置对了。现在惠灵顿的风一年吹三百天。"
- [人审] **莫桑比克** (事件): 维基百科无 '莫桑比克' 条目, 无法交叉验证 (年份: 1964 (1964年起,莫桑比克解放阵线); 年份: 1975 (放阵线打了十年游击。1975年葡萄牙撤了——不是打))
  - 文案: "1964年起,莫桑比克解放阵线打了十年游击。1975年葡萄牙撤了——不是打不过,是国内政变不想打了。"
- [人审] **都柏林** (作品): 维基百科无 '都柏林' 条目, 无法交叉验证 (年份: 1904 (,故事在这。乔伊斯写1904年6月16日这一天,写))
  - 文案: "《尤利西斯》,故事在这。乔伊斯写1904年6月16日这一天,写了七百多页。现在每年这一天,全城替他重走一遍,叫布鲁姆日。一天被过成了节日。"
- [人审] **金门大桥** (事件): 维基百科无 '金门大桥' 条目, 无法交叉验证 (年份: 1937 (1937年5月27日,金门大桥))
  - 文案: "1937年5月27日,金门大桥通车。前一天是行人日,二十万人走过了桥。建设四年,十一个人死了——桥下挂着安全网,但最后一个人从网上翻出去了。桥的颜色叫"国际橘""
- [人审] **达尔文** (事件): 维基百科无 '达尔文' 条目, 无法交叉验证 (年份: 1974 (1974年圣诞夜,特雷西气旋把))
  - 文案: "1974年圣诞夜,特雷西气旋把达尔文夷为平地。重建之后,全城的建筑规范是澳大利亚最严的。代价是经验。"
- [人审] **雅典** (事件): 维基百科无 '雅典' 条目, 无法交叉验证 (年份: 399 (前399年,苏格拉底被雅典公民))
  - 文案: "前399年,苏格拉底被雅典公民投票判死刑——罪名是'不敬神'和'腐蚀青年'。他本可以逃的。他不。他说'未经审视的人生不值得过'。他喝下毒芹汁,和学生们聊完最后一"
- [人审] **塞维利亚** (事件): 维基百科无 '塞维利亚' 条目, 无法交叉验证 (年份: 1492 (1492年，哥伦布从帕洛斯港出))
  - 文案: "1492年，哥伦布从帕洛斯港出发，回来后住在塞维利亚。瓜达尔基维尔河的码头，那会儿是全世界的中心。"
- [人审] **帕皮提** (人物): 维基百科无 '帕皮提' 条目, 无法交叉验证 (年份: 1842 (世,塔希提末代女王。1842年法国人逼她签了保护条))
  - 文案: "波马雷四世,塔希提末代女王。1842年法国人逼她签了保护条约。她没多少选择。帕皮提的王宫遗址现在是政府大楼。女王变成公务员,这是殖民的标准结局。"
- [人审] **武汉** (事件): 维基百科无 '武汉' 条目, 无法交叉验证 (年份: 1911 (1911年10月10日,武昌。))
  - 文案: "1911年10月10日,武昌。士兵的枪走火了——或者是他们故意让它走火的。一声枪响,清朝倒了。两千年的帝制,从一声枪响开始结束。"
- [人审] **北京** (人物): 维基百科无 '北京' 条目, 无法交叉验证 (年份: 1976 (国人民都是他的孩子。1976年他去世的时候,长安街))
  - 文案: "周恩来在中南海办公。他每天工作十几个小时,批文件批到天亮。他的妻子邓颖超说:他没有孩子,但全国人民都是他的孩子。1976年他去世的时候,长安街站满了人。联合国降"
- [人审] **庞贝** (事件): 维基百科无 '庞贝' 条目, 无法交叉验证 (年份: 79 (公元79年,维苏威火山在24小))
  - 文案: "公元79年,维苏威火山在24小时内埋了庞贝。人被火山灰定格——最后的姿势,不是跑,是蜷缩。挖掘出来的时候,石膏灌进去——你看到的不是雕塑,是两千年前的空洞。"
- [人审] **雅加达** (事件): 维基百科无 '雅加达' 条目, 无法交叉验证 (年份: 1998 (1998年5月,金融风暴之后雅))
  - 文案: "1998年5月,金融风暴之后雅加达暴动。苏哈托下台,三十二年独裁结束。唐人街被砸,一千多人死。"
- [人审] **伦敦海格特** (事件): 维基百科无 '伦敦海格特' 条目, 无法交叉验证 (年份: 1883 (1883年3月17日,马克思葬))
  - 文案: "1883年3月17日,马克思葬在海格特公墓。墓碑上刻着全世界无产者联合起来。你去看,墓前总有人放花——有时是红的,有时不知道谁放的。"
- [人审] **苏黎世** (事件): 维基百科无 '苏黎世' 条目, 无法交叉验证 (年份: 1916 (1916年,一群逃战的艺术家在))
  - 文案: "1916年,一群逃战的艺术家在苏黎世的伏尔泰酒馆聚会。他们胡说八道、胡唱乱跳,管这叫达达。世界从此多了一种反艺术。"
- [人审] **平壤** (事件): 维基百科无 '平壤' 条目, 无法交叉验证 (年份: 1953 (1953年7月27日，板门店签))
  - 文案: "1953年7月27日，板门店签停战协定。平壤被炸平了——美国人投的炸弹比整个太平洋战争还多。停战不是和平，是暂停。暂停了七十多年。"
- [人审] **南京** (人物): 维基百科无 '南京' 条目, 无法交叉验证 (年份: 1912 (孙中山1912年在南京就任临时大总统))
  - 文案: "孙中山1912年在南京就任临时大总统。总统府还在，办公桌还在，但他只干了四十四天就让位了。他的陵墓在紫金山，三百九十二级台阶。上去的人数台阶，没人记得那四十四天"
- [人审] **卢森堡市** (事件): 维基百科无 '卢森堡市' 条目, 无法交叉验证 (年份: 1867 (1867年伦敦条约要求拆除卢森))
  - 文案: "1867年伦敦条约要求拆除卢森堡的要塞。花了十六年,拆掉了大部分工事。峡谷还在,炮台没了。"
- [人审] **贝鲁特** (事件): 维基百科无 '贝鲁特' 条目, 无法交叉验证 (年份: 1975 (1975年,贝鲁特内战爆发。绿))
  - 文案: "1975年,贝鲁特内战爆发。绿线把城市切成东西两半。十五年,十二万人死。现在市中心修好了,但有的楼还有弹孔。"
- [人审] **尼亚加拉瀑布** (人物): 维基百科无 '尼亚加拉瀑布' 条目, 无法交叉验证 (年份: 1895 (界第一座交流水电站,1895年。瀑布的水变成了电,))
  - 文案: "特斯拉在尼亚加拉瀑布建了世界第一座交流水电站,1895年。瀑布的水变成了电,电沿着电线跑到二十五英里外的布法罗。交流电赢了爱迪生的直流电,起点在这。"
- [人审] **广岛** (人物): 维基百科无 '广岛' 条目, 无法交叉验证 (年份: 1945 (1945年8月6日早上八点十五))
  - 文案: "1945年8月6日早上八点十五分，原子弹在广岛上空六百米爆炸。爆心附近的岛病院只剩一面墙，现在是和平纪念公园的原爆圆顶。碑上刻着：请安息吧，同样的错误不会重演。"
- [人审] **莫尔兹比港** (人物): 维基百科无 '莫尔兹比港' 条目, 无法交叉验证 (年份: 1975 (民议会里喊独立的人。1975年他主持了独立仪式。他))
  - 文案: "迈克尔·索马雷,巴新国父。他是第一个在殖民议会里喊独立的人。1975年他主持了独立仪式。他后来被称为"老大"——巴新政治的规矩,谁的嗓门大谁说了算。"
- [人审] **河内** (事件): 维基百科无 '河内' 条目, 无法交叉验证 (年份: 1972 (1972年12月,B-52轰炸))
  - 文案: "1972年12月,B-52轰炸河内十二天。居民躲进防空洞,街区被炸平。河内人管那叫圣诞节轰炸。"
- [人审] **神户** (事件): 维基百科无 '神户' 条目, 无法交叉验证 (年份: 1995 (1995年1月17日清晨5点4); 等级: 3 (清晨5点46分,7.3级地震把神户撕开。高架))
  - 文案: "1995年1月17日清晨5点46分,7.3级地震把神户撕开。高架桥塌了,木屋成片倒下,六千多人死。凌晨的地震比白天的更难逃。"
- [人审] **塞维利亚** (事件): 维基百科无 '塞维利亚' 条目, 无法交叉验证 (年份: 1992 (1992年，世博会在拉卡图哈岛))
  - 文案: "1992年，世博会在拉卡图哈岛上办。一百多个国家来了，园区现在荒了一半。但那年的塞维利亚被世界看见了。"
- [人审] **布达佩斯** (事件): 维基百科无 '布达佩斯' 条目, 无法交叉验证 (年份: 1849 (1849年,塞切尼链桥通车,布))
  - 文案: "1849年,塞切尼链桥通车,布达和佩斯第一次用桥连起来。桥两端各蹲四头石狮子,没有舌头。你走过去数一数。"
- [人审] **贝鲁特** (痕迹): 维基百科无 '贝鲁特' 条目, 无法交叉验证 (年份: 2019 (场的雕像被围起来了,2019年抗议时留的帐篷还在。))
  - 文案: "烈士广场的雕像被围起来了,2019年抗议时留的帐篷还在。"
- [人审] **那不勒斯** (事件): 维基百科无 '那不勒斯' 条目, 无法交叉验证 (年份: 79 (公元79年8月24日,维苏威火))
  - 文案: "公元79年8月24日,维苏威火山把庞贝和赫库兰尼姆埋了。小普林尼从海湾对面目击了全过程——他的信是火山学历史上第一份目击报告。'云像一棵松树升起来'——他写出了"
- [人审] **休斯顿** (人物): 维基百科无 '休斯顿' 条目, 无法交叉验证 (年份: 1969 (逊航天中心在休斯顿，1969年那句鹰已着陆是从这里))
  - 文案: "约翰逊航天中心在休斯顿，1969年那句鹰已着陆是从这里传回地球的。当时的指挥室现在叫任务控制中心一室，烟灰缸还在原位，登月的三人组背后是几千个地面人员。火箭在佛"
- [人审] **安塔利亚** (事件): 维基百科无 '安塔利亚' 条目, 无法交叉验证 (年份: 1930 (1930年，阿塔图尔克到安塔利))
  - 文案: "1930年，阿塔图尔克到安塔利亚。他站在港口边说：'这是土耳其最叫人难忘的地方。'他的雕像现在还在那。安塔利亚从那以后开始有名字。"
- [人审] **耶路撒冷** (事件): 维基百科无 '耶路撒冷' 条目, 无法交叉验证 (年份: 1099 (1099年7月15日,十字军攻))
  - 文案: "1099年7月15日,十字军攻入耶路撒冷。他们说是来'解放'圣城的。城破之后——犹太人在犹太会堂里被烧,穆斯林在阿克萨清真寺里被杀。之后耶路撒冷在基督徒和穆斯林"
- [人审] **喀土穆** (事件): 维基百科无 '喀土穆' 条目, 无法交叉验证 (年份: 1885 (1885年1月,马赫迪的军队攻))
  - 文案: "1885年1月,马赫迪的军队攻进喀土穆。英国总督戈登被杀在总督府台阶上。你去马赫迪陵墓,白顶在蓝天下一眼就能认出。"
- [人审] **库斯科** (事件): 维基百科无 '库斯科' 条目, 无法交叉验证 (年份: 1533 (1533年，皮萨罗进了库斯科。))
  - 文案: "1533年，皮萨罗进了库斯科。印加人用黄金铺的太阳神殿被拆了，石头上建了西班牙教堂。现在教堂在上面，印加墙在下面——你能看到两种历史叠在一起。"
- [人审] **迦太基** (事件): 维基百科无 '迦太基' 条目, 无法交叉验证 (年份: 146 (前146年,罗马人围了迦太基三))
  - 文案: "前146年,罗马人围了迦太基三年,破了城。烧了十七天,然后犁了地,撒了盐——据说。迦太基是古代地中海最富的城市,之后只剩土。罗马人把盐撒在敌人地里这件事——可能"
- [人审] **拉各斯** (事件): 维基百科无 '拉各斯' 条目, 无法交叉验证 (年份: 1999 (1999年尼日利亚结束军政府,))
  - 文案: "1999年尼日利亚结束军政府,拉各斯恢复了州的地位。奥巴桑乔当上民选总统。拉各斯街头庆祝了一整夜——他们等了十六年。"
- [人审] **加里宁格勒** (事件): 维基百科无 '加里宁格勒' 条目, 无法交叉验证 (年份: 1736 (1736年,欧拉在柯尼斯堡解决))
  - 文案: "1736年,欧拉在柯尼斯堡解决了七桥问题。四座岛,七座桥,能不能不重复地走完?不能。图论从一座城的散步开始。现在桥只剩五座,问题还在。"
- [人审] **多哈** (人物): 维基百科无 '多哈' 条目, 无法交叉验证 (年份: 1878 (罕默德,卡塔尔国父。1878年他统一了卡塔尔各部落))
  - 文案: "贾西姆·本·穆罕默德,卡塔尔国父。1878年他统一了卡塔尔各部落,赶走了奥斯曼人。多哈市中心的沃吉夫老市场边上,他的雕像还立着。"
- [人审] **大峡谷** (事件): 维基百科无 '大峡谷' 条目, 无法交叉验证 (年份: 1869 (1869年，约翰·韦斯利·鲍威))
  - 文案: "1869年，约翰·韦斯利·鲍威尔带着九个人，乘木筏漂流科罗拉多河大峡谷。四个月，翻了三次船，丢了补给，死了三个人。他回来后写了一本书——大峡谷从此有名字。"
- [人审] **平壤** (人物): 维基百科无 '平壤' 条目, 无法交叉验证 (年份: 1994 (雕像都有他的影子。他1994年去世，遗体在锦绣山纪))
  - 文案: "金日成在平壤建了一座城。每一栋楼、每一条街、每一座雕像都有他的影子。他1994年去世，遗体在锦绣山纪念宫。平壤人说他'永远活着'。"
- [人审] **巴塞罗那** (事件): 维基百科无 '巴塞罗那' 条目, 无法交叉验证 (年份: 1492 (1492年10月12日,哥伦布); 年份: 1493 (百多年的'印度人'。1493年他回到西班牙,巴塞罗))
  - 文案: "1492年10月12日,哥伦布的船队到了加勒比的圣萨尔瓦多岛。他到死都以为自己到了印度——所以美洲原住民被叫了一百多年的'印度人'。1493年他回到西班牙,巴塞"
- [人审] **西安** (事件): 维基百科无 '西安' 条目, 无法交叉验证 (年份: 1936 (1936年12月12日,西安。))
  - 文案: "1936年12月12日,西安。张学良和杨虎城扣押了蒋介石——逼他停止内战一致抗日。圣诞节那天蒋同意了。张学良送蒋回南京,然后被软禁了半个世纪。华清池的弹孔现在还"
- [人审] **奥克兰** (事件): 维基百科无 '奥克兰' 条目, 无法交叉验证 (年份: 1350 (毛利人在1350年左右到了奥克兰。他们))
  - 文案: "毛利人在1350年左右到了奥克兰。他们叫它Tāmaki Makaurau,被一百个情人追求的土地。火山土肥沃,适合种红薯。"
- [人审] **科隆** (事件): 维基百科无 '科隆' 条目, 无法交叉验证 (年份: 1945 (1945年盟军轰炸科隆,老城9))
  - 文案: "1945年盟军轰炸科隆,老城90%被毁。大教堂立在废墟中间,没倒。两座尖顶是废墟里唯一的天际线。"
- [人审] **苏塞克斯** (事件): 维基百科无 '苏塞克斯' 条目, 无法交叉验证 (年份: 1066 (1066年10月14日,哈罗德))
  - 文案: "1066年10月14日,哈罗德在黑斯廷斯阵亡。诺曼人赢了,英格兰换了一个王朝。修道院建在战场上。"
- [人审] **利雅得** (人物): 维基百科无 '利雅得' 条目, 无法交叉验证 (年份: 1902 (王。他从科威特出发,1902年夺回利雅得,用了三十))
  - 文案: "阿卜杜勒·阿齐兹·伊本·沙特,沙特阿拉伯开国国王。他从科威特出发,1902年夺回利雅得,用了三十年统一了阿拉伯半岛的大部分。沙特这个国家,用他的姓命名。"
- [人审] **波斯波利斯** (事件): 维基百科无 '波斯波利斯' 条目, 无法交叉验证 (年份: 330 (前330年,亚历山大占领了波斯))
  - 文案: "前330年,亚历山大占领了波斯帝国的都城波斯波利斯。他烧了它——据说是喝醉了酒被怂恿的。万国来朝的浮雕还在石阶上——来的人不来了,浮雕的脸还在微笑。"
- [人审] **阿布贾** (事件): 维基百科无 '阿布贾' 条目, 无法交叉验证 (年份: 2014 (2014年博科圣地在阿布贾的公))
  - 文案: "2014年博科圣地在阿布贾的公交车站引爆了炸弹。七十多人死了。安全检查从那天起多了起来。"
- [人审] **乞力马扎罗** (人物): 维基百科无 '乞力马扎罗' 条目, 无法交叉验证 (年份: 1848 (1848年，德国传教士雷布曼第))
  - 文案: "1848年，德国传教士雷布曼第一个记录了乞力马扎罗山。欧洲人不信赤道有雪。他画了张素描——信了。"
- [人审] **苏州** (事件): 维基百科无 '苏州' 条目, 无法交叉验证 (年份: 1509 (1509年御史王献臣归隐,买下))
  - 文案: "1509年御史王献臣归隐,买下寺庙废址建园。拙政园占了苏州城东北角,水占了一半。后来分了三份,三家人各管各的。"
- [人审] **匈牙利** (人物): 维基百科无 '匈牙利' 条目, 无法交叉验证 (年份: 1849 (写了'生命诚可贵',1849年在战场上失踪。尸体没))
  - 文案: "裴多菲写了'生命诚可贵',1849年在战场上失踪。尸体没找到,每年有人在布达佩斯的雕像前念他的诗。"
- [人审] **阿布扎比** (人物): 维基百科无 '阿布扎比' 条目, 无法交叉验证 (年份: 1966 (,阿联酋开国总统。他1966年当上阿布扎比酋长,把))
  - 文案: "扎耶德·本·苏尔坦,阿联酋开国总统。他1966年当上阿布扎比酋长,把石油钱花在学校和医院上。他说过:真正的财富是人。阿布扎比的机场用他的名字。"
- [人审] **伊斯兰堡** (事件): 维基百科无 '伊斯兰堡' 条目, 无法交叉验证 (年份: 1967 (1967年巴基斯坦从卡拉奇迁都))
  - 文案: "1967年巴基斯坦从卡拉奇迁都到伊斯兰堡。新城是希腊人规划的,网格状,六十年了还在长。卡拉奇人到现在还在抱怨。"
- [人审] **费城** (事件): 维基百科无 '费城' 条目, 无法交叉验证 (年份: 1776 (1776年7月4日,费城。五十))
  - 文案: "1776年7月4日,费城。五十六个人在独立宣言上签了名——签了就是叛国罪。本杰明·富兰克林说'我们必须团结一致,否则就会被一个一个吊死'。他们没被吊死——独立战"
- [人审] **格拉纳达** (人物): 维基百科无 '格拉纳达' 条目, 无法交叉验证 (年份: 1936 (吉普赛人写进了戏剧。1936年内战刚开始，他被枪杀))
  - 文案: "洛尔迦出生在格拉纳达附近的富恩特瓦克罗斯。他在格拉纳达写了《血婚》，把安达卢西亚的吉普赛人写进了戏剧。1936年内战刚开始，他被枪杀在格拉纳达城外。现在他的故居"
- [人审] **瓦尔帕莱索** (事件): 维基百科无 '瓦尔帕莱索' 条目, 无法交叉验证 (年份: 1906 (1906年8月16日,瓦尔帕莱))
  - 文案: "1906年8月16日,瓦尔帕莱索地震。海港和低地全毁,两千人死。重建后城市往山上爬——缆车就是那时候装的。"
- [人审] **西安** (事件): 维基百科无 '西安' 条目, 无法交叉验证 (年份: 755 (755年,安禄山从范阳起兵南))
  - 文案: "755年,安禄山从范阳起兵南下。第二年洛阳陷落,长安同年失守——唐玄宗逃往四川,杨贵妃死在马嵬坡。八年战乱,中原人口锐减一半。杜甫在那八年里从一个游山玩水的诗人"
- [人审] **少女峰** (事件): 维基百科无 '少女峰' 条目, 无法交叉验证 (年份: 1934 (1934年,冰宫在少女峰冰川内))
  - 文案: "1934年,冰宫在少女峰冰川内部开凿完成。隧道在冰里面,零下三度,墙壁是蓝的。每年都要重新挖,冰在移动,去年的通道今年堵了。冰是活的。"
- [人审] **太子港** (事件): 维基百科无 '太子港' 条目, 无法交叉验证 (年份: 1791 (1791年8月,海地北部的奴隶); 年份: 1789 (北部的奴隶同时起义。1789年法国喊了"自由平等博); 年份: 1804 (欧洲帝国的黑人军队。1804年海地独立:世界上第一))
  - 文案: "1791年8月,海地北部的奴隶同时起义。1789年法国喊了"自由平等博爱",海地人当了真。十年后他们打败了拿破仑的军队——第一支打败欧洲帝国的黑人军队。1804"
- [人审] **乌兰巴托** (事件): 维基百科无 '乌兰巴托' 条目, 无法交叉验证 (年份: 1921 (1921年7月，苏赫巴托尔和乔))
  - 文案: "1921年7月，苏赫巴托尔和乔巴山带着游击队进了库伦。中国驻军走了，白俄残军也走了。乌兰巴托从那天起是蒙古的首都。"
- [人审] **柏林** (事件): 维基百科无 '柏林' 条目, 无法交叉验证 (距离: 155 (柏林墙,155公里,立了二十八年。墙倒))
  - 文案: "柏林墙,155公里,立了二十八年。墙倒之后东边画廊留了一段,现在是涂鸦墙。墙在的时候不许画,墙倒了随便画。"
- [人审] **都柏林** (人物): 维基百科无 '都柏林' 条目, 无法交叉验证 (年份: 1995 (柏林是他的文学主场。1995年诺贝尔文学奖。他的诗))
  - 文案: "希尼出生在北爱尔兰,但都柏林是他的文学主场。1995年诺贝尔文学奖。他的诗写泥炭、写农场、写父亲的手。你走进都柏林任何书店,他的书摆在最前面。"
- [人审] **那霸** (事件): 维基百科无 '那霸' 条目, 无法交叉验证 (年份: 1945 (1945年4月到6月,美军登陆))
  - 文案: "1945年4月到6月,美军登陆冲绳。十万平民死于战火。首里城地下是日军指挥部。地面上什么都没剩。"
- [人审] **青岛** (人物): 维基百科无 '青岛' 条目, 无法交叉验证 (年份: 1934 (老舍1934年到青岛,在山东大学教))
  - 文案: "老舍1934年到青岛,在山东大学教书。《骆驼祥子》的初稿在青岛写的。他在黄县路的故居,现在是书店。"
- [人审] **巴库** (事件): 维基百科无 '巴库' 条目, 无法交叉验证 (年份: 1990 (1990年1月20日,苏联军队))
  - 文案: "1990年1月20日,苏联军队进入巴库。坦克压过街头,死了上百人。阿塞拜疆人叫它"黑色一月"。一年后苏联解体,巴库成了独立国家的首都。"
- [人审] **纽约** (人物): 维基百科无 '纽约' 条目, 无法交叉验证 (年份: 1883 (masses 给我。1883年写的,现在美国人只记))
  - 文案: "爱玛·拉扎勒斯写了自由女神像底座上的诗:把你疲惫的、贫穷的、蜷缩着渴望呼吸自由的 masses 给我。1883年写的,现在美国人只记得最后两句。她四十二岁死于霍"
- [人审] **塔什干** (事件): 维基百科无 '塔什干' 条目, 无法交叉验证 (年份: 2005 (2005年安集延事件后,乌兹别))
  - 文案: "2005年安集延事件后,乌兹别克斯坦收紧管控。塔什干街头多了检查站。卡里莫夫执政二十七年,塔什干一直在他手里。"
- [人审] **安曼** (事件): 维基百科无 '安曼' 条目, 无法交叉验证 (年份: 1957 (1957年,考古队在安曼市中心))
  - 文案: "1957年,考古队在安曼市中心挖出一座罗马剧场。六千个座位,二世纪建的。剧场在居民区底下埋了几百年,挖出来的时候上面住着人。"
- [人审] **布鲁塞尔** (人物): 维基百科无 '布鲁塞尔' 条目, 无法交叉验证 (年份: 1920 (1920年代,周恩来在布鲁塞尔))
  - 文案: "1920年代,周恩来在布鲁塞尔参加旅欧中国少年共产党的会议。二十岁出头,西装笔挺,法语流利。他在巴黎和布鲁塞尔之间来回,一边组织革命一边写文章。后来他成了中国的"

## 9. 电台流腐烂 (Radio Stream Decay)

总检测电台: 101
死亡流数: 81

### 死亡流列表

- [实锤] **Worldwide FM**: HTTP 404
  - URL: https://worldwidefm.net/stream
- [实锤] **BBC World Service**: HTTP 400
  - URL: https://stream.live.vc.bbcmedia.co.uk/bbc_world_service
- [实锤] **Jazz FM**: HTTP 404
  - URL: https://edge-audio-03-gos2.sharp-stream.com/jazzfm.mp3
- [实锤] **FIP**: <urlopen error timed out>
  - URL: https://icecast.radiofrance.fr/fip-midfi.mp3
- [实锤] **NRK P1**: <urlopen error timed out>
  - URL: https://lyd.nrk.no/nrk_radio_p1_ostlandssendingen_mp3_h
- [实锤] **NRK P2**: <urlopen error timed out>
  - URL: https://lyd.nrk.no/nrk_radio_p2_mp3_h
- [实锤] **NRK Tromso**: <urlopen error timed out>
  - URL: https://lyd.nrk.no/nrk_radio_tromso_mp3_h
- [实锤] **RUV Ras 1**: HTTP 400
  - URL: http://netradio.ruv.is/ras1.mp3
- [实锤] **KCRW**: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostn
  - URL: https://kcrw.streamguys1.com/kcrw_128k_mp3_on_air
- [实锤] **CBC Radio One**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://cbcliveradio.akamaized.net/hls/live/2042825/CLB/master.m3u8
- [实锤] **Radio Nova CZ**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://broadcast.radioteka.cz/radionova128.mp3
- [实锤] **SBS PopAsia**: <urlopen error timed out>
  - URL: https://live-radio01.mediahubaustralia.com/2TALK/mp3
- [实锤] **Radio New Zealand**: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostn
  - URL: https://radionz-ice.streamguys.com/rnz-national.mp3
- [实锤] **Fiji Broadcasting**: HTTP 404
  - URL: https://www.fbc.com.fj/radio/stream
- [实锤] **KBS Classic FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://serenekbsclassic.kbs.co.kr/api/mini/pc/kbs_classic.m3u8
- [实锤] **NHK Radio 1**: HTTP 400
  - URL: https://nhkradioakr-i.akamaihd.net/hls/live/2017851/nhkradirak/master.m3u8
- [实锤] **ANTV**: <urlopen error timed out>
  - URL: https://lives.antv.gov.vn/channel/antv/channel/antv_480p/chunks.m3u8
- [实锤] **MCOT Radio**: <urlopen error timed out>
  - URL: https://radio.mcot.net/mcot-radio/stream
- [实锤] **RRI Jakarta**: <urlopen error timed out>
  - URL: https://stream.rri.co.id/jakarta/stream
- [实锤] **KBC Radio**: <urlopen error timed out>
  - URL: https://live.kbc.co.ke/kbc-radio
- [实锤] **SABC Radio**: HTTP 404
  - URL: https://playerservices.streamtheworld.com/api/livestream-redirect/SABCRADIO1.mp3
- [实锤] **CRTV Radio**: HTTP 404
  - URL: https://www.crtv.cm/radio/stream
- [实锤] **All India Radio**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://airnewsenglish.akamaized.net/hls/live/2018529/airnewsenglish/english/playlist.m3u8
- [实锤] **Radio Jordan**: HTTP 404
  - URL: https://www.jrtv.gov.jo/radio/stream
- [实锤] **Dubai FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://dubai1016fm.com/stream
- [实锤] **VOA Persian**: <urlopen error timed out>
  - URL: https://av.voanews.com/VOA_Persian_TV/VOA_Persian_TV.isml/playlist.m3u8
- [实锤] **Radio Nacional do Brasil**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.radiodifusao.fm/rnb
- [实锤] **Radio Nacional Argentina**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://streaming.radionacional.gob.ar/rn.mp3
- [实锤] **RPP Noticias**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.rpp.pe/rpp.mp3
- [实锤] **Radio Deejay**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://radiodeejay-lh.akamaized.net/live/deejay/stream.mp3
- [实锤] **Radio Capital**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://radiocapital-lh.akamaized.net/live/capital/stream.mp3
- [实锤] **TRT Radio 1**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://trt-radio-1.medya.trt.com.tr/live
- [实锤] **TRT FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://trt-fm.medya.trt.com.tr/live
- [实锤] **Power Turkey**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://powerturk-live.perrystream.com/stream
- [实锤] **TRT Radio 1**: <urlopen error timed out>
  - URL: https://radioyayin.trt.net.tr/radyo1/radyo1_128.mp3
- [实锤] **TRT FM**: <urlopen error timed out>
  - URL: https://radioyayin.trt.net.tr/trtfm/trtfm_128.mp3
- [实锤] **Power FM**: HTTP 404
  - URL: https://listen.powerapp.com.tr/powerfm/mpeg/128/home
- [实锤] **Metro FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://listen.radyometro.com.tr/metrofm/mpeg/128/home
- [实锤] **ERA Sport**: HTTP 404
  - URL: https://radiostreaming.ert.gr/era-sport
- [实锤] **Ukrainian Radio 1**: <urlopen error timed out>
  - URL: https://radio.nrcu.gov.ua:8443/stream1
- [实锤] **Radio Promin**: <urlopen error timed out>
  - URL: https://radio.nrcu.gov.ua:8443/stream3
- [实锤] **RCN Radio**: HTTP 404
  - URL: https://playerservices.streamtheworld.com/api/livestream-redirect/RCNRADIO.mp3
- [实锤] **Radio Programas del Peru**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.rpp.pe/radioprogramas.mp3
- [实锤] **Radio Nacional de Chile**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://streaming.rtvc.cl/radio-nacional/live.mp3
- [实锤] **Radio Agricultura**: <urlopen error timed out>
  - URL: https://streaming.radioagricultura.cl/live.mp3
- [实锤] **Radio Mitre**: HTTP 404
  - URL: https://playerservices.streamtheworld.com/api/livestream-redirect/RADIOMITRE.mp3
- [实锤] **Continental**: HTTP 404
  - URL: https://playerservices.streamtheworld.com/api/livestream-redirect/CONTINENTAL.mp3
- [实锤] **CBN**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.cbn.com.br/cbn_rj.mp3
- [实锤] **Jovem Pan**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.jfradios.com/jovempan
- [实锤] **Radio Formula**: HTTP 404
  - URL: https://playerservices.streamtheworld.com/api/livestream-redirect/RADIOFORMULA.mp3
- [实锤] **Nile FM**: HTTP 404
  - URL: https://playerservices.streamtheworld.com/api/livestream-redirect/NILEFM.mp3
- [实锤] **Nogoum FM**: HTTP 404
  - URL: https://playerservices.streamtheworld.com/api/livestream-redirect/NOGOUMFM.mp3
- [实锤] **Radio Mars**: HTTP 404
  - URL: https://www.radiomars.ma/stream
- [实锤] **SNRT**: HTTP 404
  - URL: https://www.snrt.ma/radio/stream
- [实锤] **Wazobia FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.wazobia.com/wazobiafm
- [实锤] **Cool FM**: <urlopen error [SSL: TLSV1_UNRECOGNIZED_NAME] tlsv1 unrecognized name (_ssl.c:10
  - URL: https://stream.coolfm.com/coolfm
- [实锤] **Capital FM**: <urlopen error timed out>
  - URL: https://stream.capitalfm.co.ke/capitalfm
- [实锤] **Kiss FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.kissfmkenya.com/kissfm
- [实锤] **Fana FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.fanafm.com.fanafm/fanafm
- [实锤] **Sheger FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.shegerfm.com/shegerfm
- [实锤] **Joy FM**: <urlopen error [Errno 11002] getaddrinfo failed>
  - URL: https://stream.joyonline.com/joyfm
- [实锤] **Citi FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.citifmonline.com/citifm
- [实锤] **MBC FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.mbc.net/mbcfm
- [实锤] **Rotana Radio**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.rotana.com/rotanaradio
- [实锤] **Radio Sawa**: <urlopen error timed out>
  - URL: https://av.voanews.com/ka-341096-1/ka-341096-1.isml/playlist.m3u8
- [实锤] **Al Rasheed Radio**: <urlopen error timed out>
  - URL: https://alrasheedmedia.com/radio/stream
- [实锤] **IRIB Radio 1**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.irib.ir/radio1
- [实锤] **Radio Javan**: HTTP 403
  - URL: https://www.radiojavan.com/stream
- [实锤] **FM 101**: HTTP 403
  - URL: https://stream.pbc.gov.pk/fm101
- [实锤] **Radio Pakistan**: HTTP 403
  - URL: https://stream.pbc.gov.pk/radiopakistan
- [实锤] **Bangladesh Betar**: <urlopen error The handshake operation timed out>
  - URL: https://www.betar.gov.bd/radio/stream
- [实锤] **Radio Foorti**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.radiofoorti.com/radiofoorti
- [实锤] **Radio Myanmar**: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostn
  - URL: https://www.mrtv.gov.mm/radio/stream
- [实锤] **City FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://cityfm.com.mm/stream
- [实锤] **National Radio of Cambodia**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://www.rtk.gov.kh/radio/stream
- [实锤] **WMCN FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://wmcn.com.kh/stream
- [实锤] **Radio Malaysia**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.rtm.gov.my/radiomalaysia
- [实锤] **Hot FM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://stream.hotfm.com.my/hotfm
- [实锤] **DZMM**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://dzmm.abs-cbn.com/stream
- [实锤] **DZRH**: HTTP 404
  - URL: https://dzrh.com.ph/stream
- [实锤] **Radio Nacional Bolivia**: <urlopen error [Errno 11001] getaddrinfo failed>
  - URL: https://www.rnbolivia.com/radio/stream

## 10. 海上死寂 (Ocean Dead Zone)

检测沿海城市: 8
内容黑洞数: 0

- [可疑] **悉尼**: 从 悉尼 往海里走10步, 但仍有内容: localcolor=15, humanities=4
- [可疑] **迈阿密**: 从 迈阿密 往海里走10步, 但仍有内容: localcolor=10, humanities=3
- [可疑] **里斯本**: 从 里斯本 往海里走10步, 但仍有内容: localcolor=10, humanities=2
- [可疑] **开普敦**: 从 开普敦 往海里走10步, 但仍有内容: localcolor=15, humanities=3
- [可疑] **东京**: 从 东京 往海里走10步, 但仍有内容: localcolor=15, humanities=14
- [可疑] **香港**: 从 香港 往海里走10步, 但仍有内容: localcolor=0, humanities=7
- [可疑] **旧金山**: 从 旧金山 往海里走10步, 但仍有内容: localcolor=15, humanities=5
- [可疑] **雅典**: 从 雅典 往海里走10步, 但仍有内容: localcolor=5, humanities=6

## 11. 记忆膨胀 (Memory Bloat)

总发现: 7

### 实锤 (1)

- **geocode._geocode_cache**: 模块级 dict, 无 TTL, 无 eviction, 每次 geocode.lookup() 新地名都会增长
  - 证据: `_geocode_cache: dict[str, tuple[float, float] | None] = {}`

### 可疑 (3)

- **server._state (WorldState)**: 每次 walk/open_door 都调用 _state.save(), journey.json 包含 path/postcards/messages 等累积数据
  - 证据: `_state.save() called in walk_impl, open_door, wait_impl, look_around`
- **placememory.footprints**: 每次 walk/listen/look 都记录 footprint, 无大小限制
  - 证据: `record_footprint() called in walk_impl, listen_impl, look_around_impl`
- **server._state.seen_cards / seen_humanities**: 每次触发 localcolor/humanities 卡都添加到 seen 集合, 跨门保留, 无清理
  - 证据: `_state.seen_cards.add() in walk_impl, no .clear() found`

### 人审 (3)

- **server._load_scene_file**: 用 setattr 缓存场景文件, 但场景文件数量固定(~10个), 实际有界
  - 证据: `setattr(_load_scene_file, cache_key, result)`
- **server._SOUVENIRS_BY_PLACE**: 从 souvenirs_by_place.json 加载, 只加载一次, 有界
  - 证据: `_SOUVENIRS_BY_PLACE: dict | None = None`
- **server._DISCOVERY_CACHE**: 从 scene_walk_discovery.txt 加载, 只加载一次, 有界
  - 证据: `_DISCOVERY_CACHE: list[str] | None = None`

---

## 总结与优先级建议

**总发现数: 306**

| 亚种 | 发现数 | 最高严重度 |
|------|--------|-----------|
| 1. 文化区矩形 | 67 | 实锤 |
| 2. 地名键漂移 | 43 | 实锤 |
| 3. 国家码边界 | 8 | 实锤 |
| 4. 历法漂移 | 0 | 可疑 |
| 5. 城市vs景区 | 0 | 可疑 |
| 6. 物种超分布 | 17 | 可疑 |
| 7. 时代错 | 3 | 可疑 |
| 8. AI编事实 | 72 | 人审 |

### 建议修复优先级

1. **文化区矩形** (实锤): describe.py `_REGION_MAP` 和 encounters.py `_region_for` 的矩形定义冲突, 高加索/中亚/南亚边界错最多。修矩形是第一优先。
2. **国家码边界** (实锤): food_by_country.json 的 DD(东德) 条目必须删; 574 条 zh 空串会导致英文菜名混入中文散文。
3. **地名键漂移** (实锤): 凤凰/凤凰古城等重复键需合并; 索引与数据文件的键需对齐。
4. **历法漂移** (实锤): 伊斯兰历节日的硬编码月份必须改用动态计算。
5. **城市vs景区** (可疑): 景区卡需确认城市落点是否合理, 或调整落点坐标。
6. **物种超分布** (可疑): 需人工二审, 部分可能是数据源本身的分布记录。
7. **时代错** (人审): 部分可能是故意怀旧, 需人工判断哪些保留哪些删。
8. **AI编事实** (人审): 需更完整的 ZIM 交叉验证, 当前样本量有限。
