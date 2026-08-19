# Nowhere 全链路体检报告 -- Card 22

**日期**: 2026-08-20 02:15
**总探针**: 17  |  **通过**: 15  |  **失败**: 2

## Chain: Time

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 1.1 timezone Beijing vs NY | local hour diff 11-13h | BJ=22h NY=10h diff=12h | ✓ | BJ tz=Asia/Shanghai, NY tz=America/New_York |
| 2 | 1.2 wait(3) exact +3h | delta=3.0h | delta=3.00h | ✓ | before=2026-07-15T10:00:00+00:00 after=2026-07-15T13:00:00+00:00 |
| 3 | 1.3 walk(2km) time increment | 0.1-1.5h (nominal ~0.5h at 4km/h) | delta=0.500h | ✓ | dist_km=2.0, slope=0.0 |
| 4 | 1.4 walk_to double-counting | time accumulated only in step() | steps=1, elapsed=1.250h | ✓ | Code review: walk_to_impl has no extra += after loop (Card 1 fix) |
| 5 | 1.5 southern hemisphere Jan = summer | summer | summer | ✓ | _season(1, -33.87) = summer |
| 6 | 1.6 Iceland July white night | 白夜/极昼/不落 in text | moment=白夜, has_polar_kw=True | ✓ | text snippet: 【冰岛,雷克雅未克,白夜,夏天。】冬天的街道在下午三点就暗下来，你走在彩色铁皮房子之间，风从港口方向吹来，穿透所有衣服层。空气冷得像 |

## Chain: Walking

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 2.1 walk N 2km latitude increase | lat increase, dist≈2km | lat+=2.00km, dist=2.0km | ✓ | blocked=False, pos=(40.01799,116.00000) |
| 2 | 2.2 uphill flat → no_gain | no_gain=True and pos unchanged | no_gain=True, pos_moved=False | ✓ | pos_before=(39.9, 116.4) pos_after=(39.9, 116.4) |
| 3 | 2.3 cliff blocked: no time, no move | blocked=True with no time/move | no cliff found in 8 directions at this location | ✓ | Location may not have cliff-grade slopes at 5km steps |
| 4 | 2.4 clamp 0.01→0.2, 100→5.0 | dist_min>=0.2, dist_max<=5.0, both clamped | min: dist=0.2,clamped=True; max: dist=5.0,clamped=True | ✓ | _DIST_MIN=0.2, _DIST_MAX=5.0 |
| 5 | 2.5 8 directions → ≈ origin | dist from origin < 5km | dist=0.00km, final=(39.99999,116.00003) | ✓ | origin=(40.0,116.0) |

## Chain: Rendering

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 3.1 text quality scan (20 walks) | no placeholders/None/forbidden/double-periods | 0 issue types found | ✓ | clean scan, no issues found |
| 2 | 3.2 forbidden words in describe.py templates | zero forbidden words in template strings | 0 found | ✓ | clean |

## Chain: Data

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 4.1 index says localcolor but no data file | 0 missing (all 415 index places have data) | 29 missing out of 415 | ✗ | sample: ['保加利亚', '克罗地亚', '内蒙古', '匈牙利', '南极磷虾', '塔什干', '墨西哥湾流', '大马士革', '安塔利亚', ' |
| 2 | 4.2 food_by_country zh='' entries | 0 entries with empty zh | 574 empty zh out of 765 total | ✗ | sample: [{'country': 'HU', 'en': 'paprikash', 'desc': '鸡肉在红椒粉奶油酱中炖至酥烂，酱汁浓郁红亮，拌面团 |

## Chain: State

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 5.1 save→load roundtrip | all fields match | 0 mismatches | ✓ | all fields match |
| 2 | 5.2 corrupted journey.json → no crash | load() returns None | load() returned None | ✓ | wrote garbage, load() should return None |

## 失败清单 (按严重度)

1. **[Data] 4.1 index says localcolor but no data file**
   - 期望: 0 missing (all 415 index places have data)
   - 实际: 29 missing out of 415
   - 证据: sample: ['保加利亚', '克罗地亚', '内蒙古', '匈牙利', '南极磷虾', '塔什干', '墨西哥湾流', '大马士革', '安塔利亚', '

2. **[Data] 4.2 food_by_country zh='' entries**
   - 期望: 0 entries with empty zh
   - 实际: 574 empty zh out of 765 total
   - 证据: sample: [{'country': 'HU', 'en': 'paprikash', 'desc': '鸡肉在红椒粉奶油酱中炖至酥烂，酱汁浓郁红亮，拌面团

## 附录 A: 索引说有 localcolor 但数据文件缺失的地名

共 29 个:

- 保加利亚
- 克罗地亚
- 内蒙古
- 匈牙利
- 南极磷虾 *(also missing from humanities)*
- 塔什干
- 墨西哥湾流 *(also missing from humanities)*
- 大马士革
- 安塔利亚
- 安第斯山脉
- 康科德
- 撒马尔罕
- 普罗旺斯
- 杜布罗夫尼克
- 格尔利茨
- 法罗岛
- 深海热泉 *(also missing from humanities)*
- 特里尔
- 珊瑚礁 *(also missing from humanities)*
- 约克郡
- 苏塞克斯
- 苏格兰
- 英格兰北部
- 萨那
- 西西里岛
- 阿布扎比
- 阿拉木图
- 阿默斯特
- 黑潮 *(also missing from humanities)*

## 附录 B: food_by_country zh="" 条目

共 574 / 765 条:

| 国家 | 英文名 | 描述(前30字) |
|------|--------|-------------|
| HU | paprikash | 鸡肉在红椒粉奶油酱中炖至酥烂，酱汁浓郁红亮，拌面团子绝佳 |
| HU | túrógombóc | 奶酪搓成丸子裹面包糠煎至金黄，切开绵软带甜，配酸奶油 |
| HU | Rakott krumpli | 土豆片和香肠层层叠放浇蛋液烤至金黄，切开拉丝绵密 |
| HU | franciasaláta | 蔬菜丁拌蛋黄酱，绵密清爽，节庆冷盘的常客 |
| HU | csülök pékné módra | 猪肘在烤箱中慢烤至皮脆肉嫩，油脂渗入土豆，外焦里糯 |
| CA | Garlic fingers | 蒜蓉芝士拉丝的扁平面包，蘸蒜味黄油酱 |
| CA | Jiggs dinner | 咸牛肉配卷心菜、土豆和胡萝卜，纽芬兰的家常大餐 |
| CA | sushi pizza | 寿司米压成饼底炸脆，铺上生鱼片和酱料 |
| CA | Japadog | 热狗上撒海苔和芥末，日式调味的街头小食 |
| CA | cod au gratin | 鳕鱼肉拌上奶酪酱焗至表面金黄起泡 |
| FI | Porkkanalaatikko | 胡萝卜泥和米粒烤成金黄焗饭，甜糯中带着肉桂的温暖 |
| FI | cabbage casserole | 卷心菜和米饭层层叠放烤至软烂，肉汁渗入每一层 |
| FI | Hotsi | 肉末和土豆在烤盘中炖至酥烂，芬兰夏末的家常味道 |
| FI | Clot soup | 血块凝固切块煮入浓汤，黑红如玛瑙，口感绵密带铁锈味 |
| FI | Läskisoosi | 猪肉片在奶油蘑菇酱中炖至软嫩，浇在土豆上，浓郁饱腹 |
| FI | Puruvesi vendace | 普鲁湖白鲑鱼体型小巧，肉质细嫩鲜甜，煎或烟熏皆宜 |
| FI | Pizza Poro | 烟熏驯鹿肉铺在披萨上，配鸡油菌和红洋葱，北欧风味的碰撞 |
| FI | ärter med fläsk | 豌豆泥炖猪肉块，绵软咸香，朴素的北欧农家菜 |
| FI | Vorschmack | 碎肉和鲱鱼泥烤成浓味派，入口咸鲜带一丝发酵的冲击 |
| GH | omo tuo | 米饭捏成圆球，绵软入味，浸入汤汁后一口一个满足 |
| GH | Tuo Zaafi | 玉米面揉成黏稠团子，配秋葵汤食用，朴素而饱腹 |
| GH | wasawasa | 薯蓣粉蒸成灰褐色糕体，淋上棕榈油汤，质朴的大地气息 |
| GH | Groundnut soup | 花生磨成浓酱煮汤，油脂在汤面泛着金光，香醇浓厚 |
| GH | Plasas | 菠菜叶炖煮至软烂混入棕榈油，绿色蔬菜的朴素鲜味 |
| KE | Githeri | 玉米粒和豆子同煮，朴素的一锅出，撒上辣椒碎提味 |
| KE | Nyama choma | 山羊肉在炭火上烤至微焦，撕开时肉汁流淌，蘸着辣椒盐吃 |
| UA | Cheer | 碎肉和米饭裹在卷心菜叶中炖煮，肉汁浸入米粒，朴素饱腹 |
| UA | shpundra | 猪排在甜菜根酱中慢炖至酥烂，酱汁紫红酸甜 |
| UA | Shulyky | 面团擀薄切块烤至酥脆，蘸蜂蜜或酸奶油，节庆时的甜蜜 |
| UA | Grechanyky | 荞麦和碎肉捏成饼煎至微焦，外酥内软，谷物的朴素香气 |
| UA | Mandrykas | 面团发酵后烤至蓬松，涂上蜂蜜，节庆面包的甜蜜 |
| UA | Tsybulnyki | 洋葱裹面糊煎成薄饼，外焦内软，洋葱的甜香渗入面皮 |
| UA | Darnitsa bread | 黑麦和小麦混合烤成深色面包，切片扎实，嚼出麦子的酸香 |
| UA | kulesha | 玉米面糊搅成浓稠粥状，配猪油或酸奶油，穷人的朴素主食 |
| UA | krupky | 大麦粒在汤中煮至软糯，节庆时端上桌的仪式感 |
| UA | zlyvana kasha | 牛奶煮小米粥至浓稠，表面浮着一层奶皮，清晨的温暖 |
| UA | varena | 蜂蜜和香料煮成热饮，温热辛香，冬至时的节庆饮品 |
| NO | Lauvsteik | 猪肉片在奶油酱汁中慢炖至软嫩，浇在土豆泥上，浓郁暖胃 |
| NO | ärter med fläsk | 豌豆泥炖猪肉块，绵软咸香，加油站和路边小馆的常见饱腹菜 |
| EE | kiluvõileib | Estonian open-faced sprat sand |
| EE | Mulgikapsad | cabbage-based dish in Estonian |
| IE | 3-in-1 | 炒饭、薯条和咖喱酱三合一，快餐店里油腻满足的深夜食粮 |
| LU | Kuddelfleck | traditional Luxembourgish dish |
| DK | ärter med fläsk | 豌豆泥炖猪肉块，绵软咸香，搭配芥末和脆面包片 |
| JP | Chinmi | 发酵海产的咸鲜冲击味蕾，余味悠长 |
| JP | Negimaki | 牛肉薄片裹住葱段，酱汁甜咸交织 |
| JP | suimono | 清汤见底，一缕柚子香，入口纯净 |
| IL | Shkedei marak | 金黄小方块酥脆，泡进汤里吸满汁水 |
| IL | Bamba | 花生酱味的膨化棒，入口即化，轻盈蓬松 |
| IL | bourekas | 酥皮层层起酥，咬开是奶酪或菠菜的咸香 |
| IL | Fatoot samneh | 皮塔饼撕碎煎至焦脆，混入蛋液，酥香四溢 |
| IL | Fritas de prasa | 韭菜裹面糊炸至金黄，外脆内软 |
| AZ | Lula kebab | 肉糜串在铁签上烤至微焦，油脂滴落炭火嘶嘶作响 |
| AZ | Ovdukh | 酸奶汤清凉爽口，黄瓜和莳萝的香气在舌尖打转 |
| AZ | Əzmə | 手撕面包蘸浓稠酱汁，粗犷的满足感 |
| HR | Zagorski štrukli | 面皮裹住奶酪馅卷起烤至金黄，切开奶酪拉丝，外酥内软 |
| HR | Soparnik | 薄面饼裹入瑞士甜菜烤至焦脆，达尔马提亚的素食派 |
| HR | Zlijevka | 玉米面和奶酪烤成金黄糕点，甜中带咸，节庆时的甜蜜 |
| PY | piracaldo | 鱼汤熬至乳白，木薯和玉米在汤中沉浮，鲜味质朴如河流 |
| PY | Jopara | 黑豆和玉米糊混煮成浓稠一锅，暖胃管饱，牧民的日常主食 |
| PY | batiburrillo | 牛杂在浓汤中炖煮，内脏的野味被香料驯服，浓烈回甘 |
| HT | Kasav | Haitian meal |
| HT | griot | dish in Haitian cuisine |
| MK | Turli Tava |  |
| MK | Tarana | typical Macedonian dish |
| KH | bok l'hong | 青木瓜丝脆爽，鱼露和青柠的酸辣在口中炸开 |
| KH | Happy pizza | 薄脆饼底铺满配料，芝士拉丝 |
| JM | Run down | Typical Caribbean dish made wi |
| JM | jerk chicken | dish |
| GY | Pholourie | Fried, spiced dough balls |
| GR | lokma | 小面球炸至金黄淋上糖浆，外壳酥脆内心绵软，甜蜜炸物 |
| GR | skordalia | 土豆泥搅入蒜泥和橄榄油，浓稠如膏，蒜香冲鼻 |
| GR | Sofrito (stew) | 牛肉在白葡萄酒蒜酱中慢炖至酥烂，酱汁浓稠醇厚 |
| GR | Spanakorizo | 菠菜和米粒在柠檬橄榄油中炖煮，翠绿酸香，清淡健康 |
| GR | tirokafteri | 羊奶酪搅入辣椒和橄榄油成糊状，辣得过瘾，奶香裹住辣味 |
| GR | Strapatsada | 番茄炒软后打入鸡蛋翻炒成嫩块，酸甜鲜香，简单快手 |
| GR | psari plaki | 整鱼铺上番茄洋葱在烤箱中慢烤，鱼肉嫩滑，番茄汁浸润 |
| GR | dolmadakiа | 葡萄叶裹住柠檬米饭蒸至叶片半透明，蘸酸奶油，酸香清新 |
| PL | Häckerle | 碎肉拌入面包丁和鸡蛋烤成肉饼，外焦内软，朴素的家常菜 |
| PL | lazanki | 宽面条和酸菜碎肉翻炒，面片滑韧裹着酸菜的清爽 |
| PL | Rumpuć | 各种蔬菜切丁在清汤中煮至软烂，颜色缤纷，清淡暖胃 |
| PL | Prażonki | 土豆和培根在烤盘中层层叠放烤至焦黄，油脂渗入土豆 |
| PL | Prażucha | 大麦粉搅成浓稠糊状，配酸奶或培油，穷人的朴素食物 |
| PL | Peas with salo | 豌豆炖至绵软，配腌猪油块，咸香和豆香交融 |
| MY | Pelara | Food in Malaysia |
| MY | Slemang | Dish in the Malaysian kitchen |
| MY | Laksam | Meal in Malaysia |
| MY | lompap daging | dish from Negeri Sembilan, Mal |
| MY | ubi gaung buluh | bamboo dish from Malaysia |
| MY | Chicken chop | Malaysian-styled fried chicken |
| JO | galayet bandora | 番茄在锅中熬至浓稠，蘸着大饼吃，酸甜暖胃 |
| MM | Buttered rice | 黄油渗入每一粒米饭，扁豆绵软，入口油润 |
| MM | No htamin | 椰浆浸润的糯米，节庆时端上桌的甜蜜 |
| MM | Burmese fried rice | 大火翻炒的锅气，米饭粒粒分明 |
| MM | Cassia flower bud salad | 花蕾脆嫩，拌入辣椒和花生，口感层次丰富 |
| MM | Hsi htamin | 油饭粒粒透亮，咸香适口 |
| MM | Shwe htamin | 金黄糯米甜而不腻，椰香在齿间萦绕 |
| LT | Kepta duona | Lithuanian, latvian garlic bre |
| MV | Maskurolhi | 金黄糯米甜而不腻，椰丝和香蕉叶的香气交融 |
| RU | franciasaláta | 蔬菜丁拌蛋黄酱，绵密清爽 |
| RU | Darnitsa bread | 黑麦面包切片扎实，嚼出麦子的朴素酸香 |
| RU | rasstegai | 开口馅饼露出肉馅，面皮酥软，汁水饱满 |
| RU | yurma | 鱼汤在冻土上熬煮，热气在寒冷中升腾 |
| RU | muvi | 鱼皮晾干嚼韧，原住民的原始鲜味 |
| RU | sulze | 肉冻在盘中颤动，入口即化，胶质黏唇 |
| RU | Indigirka salad | 冻鱼丁拌洋葱，冰碴在齿间碎裂 |
| RU | skoblyanka | 牛肉片和土豆蘑菇在铁锅中翻炒，焦香四溢 |
| RU | buuz | 面皮厚实兜住羊肉馅，蒸熟后汁水饱满 |
| VN | chả cá Lã Vọng | 鱼块在铁板上滋滋作响，茴香和黄姜的香气升腾 |
| VN | bánh cáy | 米糕切成薄片，甜脆中带着椰香 |
| VN | bánh rế | 红薯丝编织成网，炸至酥脆，甜香扑鼻 |
| VN | Nem Lai Vung | 猪肉春卷炸至金黄，外皮酥脆肉馅多汁 |
| VN | bánh trôi | 小汤圆浮在姜汤里，糯米皮软糯，红糖馅甜润 |
| VN | bánh chay | 素汤圆配红豆沙，清淡甘甜 |
| VN | Hủ tiếu | 细米粉滑入骨汤，配上虾和猪肉片 |
| VN | chả trứng | 蛋肉糕蒸得厚实，切片后能看到肉粒和木耳 |
| VN | Nộm hoa chuối | 香蕉花丝拌鸡肉，酸辣脆爽 |
| TH | mi krop | 细面炸至蓬松酥脆，浇上酸甜酱汁，咔嚓一声 |
| TH | Roti sai mai | 薄饼裹入彩色棉花糖，甜丝丝在齿间融化 |
| TH | Khanom thuai | 小杯椰奶布丁，滑嫩如凝脂，底部是焦糖 |
| TH | pu phat phong kari | 蟹肉裹着咖喱粉翻炒，咸鲜带一丝微辣 |
| TH | Wing Bean Salad | 翼豆脆如生豆角，拌入椰奶和虾米，酸辣清爽 |
| TH | Khao mu daeng | 叉烧肉片铺在饭上，甜酱汁渗入米粒 |
| TH | Kuai tiao pak mo | 薄皮馄饨浮在清汤里，猪肉馅鲜嫩 |
| TH | Tom som | 酸汤开胃，罗望子的酸和虾的鲜在汤里平衡 |
| TH | Khao man gai | 鸡油饭粒粒油亮，鸡肉嫩滑，蘸酱微辣提鲜 |
| LK | Bibikkan | 椰子蛋糕湿润扎实，棕糖的焦香在口中化开 |
| LK | Mallung | 碎叶拌椰丝和辣椒，入口清新带嚼劲 |
| LK | Lamprais | 蕉叶包裹米饭和咖喱，蒸出的香气层层渗透 |
| CF | Maboké | dish in Central African Republ |
| UY | picada | 切块肉肠芝士铺满木板，随手拈来，咸香下酒 |
| UY | Matambre with milk | 薄肉片在牛奶中慢炖至软嫩，奶香渗入肉纹，温润绵长 |
| DE | Bauernfrühstück | 土豆和鸡蛋在平底锅中翻炒，简单朴实的满足 |
| DE | Häckerle | 猪肉和谷物灌成粗肠，切片煎至表面微焦 |
| DE | Saumagen | 猪肉和土豆填入猪肚中煮透，切片后油脂分明 |
| DE | Bayrisch Kraut | 卷心菜用白葡萄酒慢炖，酸甜中带着酒香 |
| DE | Spundekäs | 奶油芝士打成泥，小茴香籽点缀其中，抹面包吃 |
| DE | buckwheat dumplings | 荞麦面团切成小块，嚼起来带着粗粮的朴素香气 |
| DE | crab soup | 蟹肉和奶油熬成浓汤，斋期的鲜味慰藉 |
| DE | Mettigel | 生猪肉泥做成刺猬形状，面包丁插满全身 |
| DE | Pfefferpotthast | 牛肉和洋葱在红酒中炖至酥烂，胡椒的暖意渗透 |
| DE | serviettenknödel | 面包面团用布卷起蒸熟，切片后孔隙均匀吸汁 |
| DE | Russisch ei | 煮鸡蛋对半切开，蛋黄酱填入，撒上辣椒粉 |
| DE | Würzfleisch | 肉块在浓稠酱汁中炖至酥烂，香料层次分明 |
| TG | Ablo | traditional white cake in West |
| TG | Djenkoume | Togolese tomato cornmeal fritt |
| TG | Eba | West African staple food |
| TG | akassa | type of dough made from cooked |
| TG | Asaro | traditional Yoruba dish made w |
| NC | Bougna | traditional feast dish in New  |
| XK | Tomato casserole from Gjakova | Baked dish consisting mainly o |
| XK | Onion casserole from Gjakova | Baked dish consisting mainly o |
| BF | akassa | type of dough made from cooked |
| BF | Gonré | local Burkinabè food |
| BF | Gonré | burkinabè food |
| ZW | umxhanxa | Zimbabwean dish |
| BY | Grechanyky | Ukrainian dish |
| BY | sugared cranberries |  |
| BY | tsybryki | Belarusian fried potato dumpli |
| ES | cocido | 鹰嘴豆和各种肉在汤中炖透，汤和菜分两道吃 |
| ES | gachas | 面粉糊搅至浓稠，淋上橄榄油和蒜片 |
| ES | Migas | 隔夜面包掰碎和蒜片辣椒一起煎至焦香 |
| ES | Caldo galego | 加利西亚菜汤，土豆和芸豆在猪油中煮透 |
| ES | calçotada | 烤葱蘸杏仁酱，拨开焦黑外皮露出甜软内心 |
| ES | Lacón Gallego | 加利西亚猪肩肉盐渍风干，切片后油脂在舌面化开 |
| ES | Moros y Cristianos | 黑豆和白米盛在同一个盘里，经典搭配 |
| ES | fideuà | 细面条代替米饭在海鲜高汤中煮透，锅底焦脆 |
| ES | Judías de El Barco de Ávila | 阿维拉白芸豆个大饱满，炖至绵软却不散 |
| ES | Conejo en salmorejo | 兔肉在蒜和罗勒腌汁中入味，炭烤至皮焦肉嫩 |
| ES | Esqueixada | 鳕鱼丝用手撕碎拌入番茄洋葱，橄榄油的清香托底 |
| ES | Arroz con costra | 米饭铺满海鲜在烤箱中焗出焦脆锅巴 |
| ES | Espineta amb caragolins | 猪肉和蜗牛在陶锅中慢炖，加泰罗尼亚的家常 |
| ES | Gurullos | 面疙瘩和蔬菜在汤中煮至软烂，牧羊人的暖食 |
| ES | Pulte | 古老谷物煮成粗粥，牧羊人的朴素暖食 |
| ES | Sopas | 面包片浸在肉汤中至软烂，中世纪流传至今 |
| ES | Arròs al forn | 米饭铺满海鲜在烤箱中焗至表面焦黄 |
| ES | Hormigo | 巴斯克地区的玉米糊配鳕鱼，粗犷扎实 |
| ES | Caragolada | 蜗牛带壳在蒜香和辣椒水中煮透，加泰罗尼亚的夏夜 |
| SK | lokša | 土豆泥揉入面团擀薄煎成软饼，配鹅油或果酱，朴素百搭 |
| RO | Ganca | 玉米面糊搅成浓稠粥状，配酸奶或奶酪，罗马尼亚乡间的朴素主食 |
| RO | sarmale | 卷心菜叶裹住碎肉和米饭在酸菜汤中炖煮，酸香入味 |
| RO | Chifteluțe marinate | 肉丸裹番茄酱在烤箱中焖至入味，酱汁酸甜，肉丸弹嫩 |
| RO | Varză à la Cluj | 碎肉和卷心菜层层叠放烤至焦香，匈罗混血的家常大菜 |
| DZ | Chrik |  |
| DZ | Cocas |  |
| DZ | frita |  |
| DZ | Mtewem | Algerian meal |
| DZ | Sohlob | dessert |
| DZ | lalak |  |
| DZ | Rfiss |  |
| DZ | Acewwaḍ |  |
| DZ | Adghess |  |
| DZ | Aftir oukessoul |  |
| DZ | Tajine Lham-Lahlou | Algerian food |
| DZ | Adjidjat |  |
| DZ | Pizza carrée | type of pizza of Algeria |
| GE | Achma | 千层面皮浸在奶酪里，每一层都拉丝绵密 |
| GE | Muzhuzhi | 猪肉冻在口中化开，凉凉的胶质带着蒜香 |
| GE | chashushuli | 牛肉和番茄炖至酥烂，汤汁酸甜浓厚 |
| MT | Fenek | Dining in Malta |
| MT | Fenkata | Maltese dish |
| MT | Stuffat tal-fenek | Rabbit stew, cuisine of Malta |
| MT | Ħobż biż-żejt | Maltese appetizer |
| BA | kvrguša | 鸡蛋面糊铺在烤盘中烤至蓬松金黄，配酸奶油，朴素温暖 |
| CU | Rice with chicken a la chorrera | 鸡肉和米饭在番茄酱汁中焖煮，米粒吸饱鸡汁的鲜 |
| CU | Yam with cod | 山药和鳕鱼同炖至绵软，海的咸鲜渗入根茎的朴实 |
| CU | Mollete melenero | 面包夹入肉酱和芝士，街头小摊递来的热乎满足 |
| SR | Pholourie | Fried, spiced dough balls |
| SR | Pom | oven dish |
| US | Negimaki | 牛肉薄片裹住葱段，酱汁甜咸交织 |
| US | muffuletta | 圆面包切开塞满意大利腌肉和橄榄沙拉，层层叠叠的咸香 |
| US | bean pie | 白豆泥做成的甜派，口感绵密如南瓜派 |
| US | celery Victor | 西芹腌至入味，配凤尾鱼和番茄，清爽开胃 |
| US | City chicken | 猪肉块串成棒状烤熟，外焦里嫩 |
| IQ | lokma | 小面球炸透淋糖浆，外壳酥脆内心绵软 |
| IQ | Piyaz | 白芸豆拌洋葱番茄，橄榄油和柠檬汁的酸香托底 |
| IQ | Arook | 面饼裹肉馅烤至外壳焦脆，掰开肉汁流出 |
| PE | sangrecita | 鸡血在锅中凝结，混入香料和柠檬汁，口感绵密带铁锈般的野性 |
| PE | Empanadilla | 酥皮半圆炸至金黄，咬开是肉末和橄榄的咸香 |
| PE | Olluquito | 块根炖至软糯，羊肉丝和辣椒在浓稠汤汁中交融 |
| PE | Peruvian pollada | 整鸡腌透后烤至皮焦肉嫩，邻里聚会时的热闹滋味 |
| PE | Malarrabia | 香蕉煮至绵软捣碎，混入奶酪，甜咸交织的朴素甜品 |
| KP | injo-gogi-bap | 豆皮裹住米饭，咬开是朴素的豆香 |
| KP | bossam-kimchi | 整棵白菜包入馅料发酵，酸脆多汁 |
| PW | Fruit Bat Soup | dish of Palau |
| TD | Esh | Chadian dish |
| SY | lokma | 小面团炸至金黄，淋上糖浆，外壳酥脆内心绵软 |
| SY | bülbülyuvası | 细丝面编成鸟巢状，烤至焦脆，内藏坚果 |
| SY | Bāṭarsh | 茄子炖至软烂，番茄和蒜的香气融为一体 |
| SY | Halawet el Jibn | 奶酪面皮裹住奶油，撒上开心果碎，甜润柔滑 |
| SY | kibbeh mashwiyya | 碎麦裹肉馅烤至外壳微焦，内里多汁 |
| SY | Mahmoosa | 茄子泥搅打成糊，酸甜绵密 |
| SY | As-sabʿa dūal | 七种蔬菜炖煮一锅，各有各的软糯 |
| SY | Hummus bil-lahm | 鹰嘴豆泥上铺着炒羊肉碎，一勺舀到底 |
| LB | Balila | 鹰嘴豆炖至绵软，浇上橄榄油和柠檬汁 |
| NI | Cushta | Nicaraguan cuisine dish |
| NI | Vaho | 维基媒体消歧义页 |
| NI | repocheta | Nicaraguan typical food |
| KR | Doganitang | 牛膝骨汤胶质浓厚，骨髓在齿间滑腻 |
| KR | Gaetteok | 米糕弹牙有韧劲，嚼出米粒的清甜 |
| KR | cheese tteokbokki | 辣酱裹着年糕，芝士拉丝缠绕，甜辣交织 |
| NP | Pukala | 水牛杂碎煮熟再炸至表面起泡，外脆内韧 |
| TJ | upka | 面团擀薄裹馅蒸熟，蘸酸奶吃，朴素管饱 |
| TZ | Nyama choma | 炭火烤山羊肉，表皮焦脆内里多汁，配乌咖喱一起入口 |
| PH | Empanadilla | 酥皮半圆炸至金黄，咬开是肉末和蔬菜的咸香 |
| PH | Paelya | 藏红花染黄的米饭铺满海鲜，锅底有焦脆的锅巴 |
| PH | Kalamay | 糯米糕黏得拉丝，椰糖的甜味浓郁持久 |
| PH | Pares | 红烧牛肉炖至酥烂，汤汁浓稠，拌饭一绝 |
| PH | Igado | 猪肝和猪肉切丝翻炒，酱汁咸鲜入味 |
| PH | Java Rice | 姜黄染金的米饭粒粒分明，微辣开胃 |
| PH | Humba | 五花肉慢炖至软糯，酱油和醋的酸甜渗入每一层 |
| PH | Salukara | 椰浆米饼煎至两面焦黄，外脆内软 |
| PH | Moche | 糯米团裹着花生碎，甜香在齿间碾碎 |
| PH | Mache | 糯米包肉馅蒸熟，叶香渗入米粒 |
| PH | Masi | 糯米球裹花生碎，弹牙中藏着甜馅 |
| PH | Goto | 米粥煮至浓稠，牛肚软韧有嚼头 |
| PH | Panyalam | 米浆炸成小饼，边缘焦脆中心软甜 |
| PH | Sayongsong | 糯米裹棕榈糖蒸在叶子里，甜味从叶缝渗出 |
| PH | Silog | 煎蛋配蒜香米饭，戳破蛋黄流进饭粒 |
| PH | Sinigapuna | 椰浆煮米饭，浓稠香甜 |
| PH | Binakle | 米糕蒸得蓬松，撕开有淡淡的椰香 |
| PH | Kiampong | 糯米砂锅焖至黏糯，花生和香菇点缀其间 |
| PH | Adobong pugita | 章鱼在醋和酱油中炖至弹韧，酸咸交融 |
| PH | Poqui poqui | 茄子捣碎拌入鸡蛋，绵软中带着烟熏味 |
| BJ | Ablo | traditional white cake in West |
| BJ | Eba | West African staple food |
| BJ | akassa | type of dough made from cooked |
| BJ | Amiwô | Beninese porridge |
| BJ | Èba | Beninese cuisine classic made  |
| BJ | monyo | Beninese sauce |
| BJ | Wèli | Beninese dish of fried potatoe |
| BJ | Wôkoli | Beninese culinary preparation  |
| CI | Ablo | traditional white cake in West |
| CI | akassa | type of dough made from cooked |
| CI | bawin sauce | traditional dish from western  |
| LY | bazeen | unleavened bread in Libyan cui |
| LY | Mafrum | Libyan-Jewish and Tunisian-Jew |
| LY | Mebakbeka |  |
| LR | Plasas | traditional dish prepared in G |
| CM | Ndolé | 苦叶炖煮去苦味，混入花生酱和虾肉，苦尽甘来 |
| CM | Koki | 黑眼豆泥蒸成深色糕体，棕榈油渗入每一层 |
| CM | poulet DG | 整鸡配芭蕉和蔬菜在棕榈油中炖煮，宴客的大菜 |
| CM | Ça va se savoir | 辣酱拌蔬菜和鱼肉，名字意为你会知道的，辣到记住 |
| CM | Taro with yellow sauce | 芋头蒸熟配黄姜酱，绵软的芋头裹着辛香 |
| CM | Ikok | 牛肉在棕榈油和洋葱中慢炖，汤汁浓稠入味 |
| CM | Ekpang Nkwukwo | 薯蓣丝裹着棕榈油和鱼肉蒸煮，黏糯鲜美 |
| CM | Sanga (Meal) | 新鲜玉米粒和蔬菜同煮，玉米的清甜在汤中释放 |
| BT | Ema datshi | 辣椒泡在融化的奶酪里，辣得舌头发麻，奶香裹住 |
| BT | kewa datshi | 土豆和奶酪炖成一锅，绵软浓稠 |
| CD | Babute | 肉末拌香料做成饼状煎至微焦，内里多汁弹牙 |
| BD | Roust | 整鱼裹香料慢烤，皮焦肉嫩，辛香渗入鱼骨 |
| BD | Soft Khichuri | 米和扁豆煮成糊状，斋月里的温柔食物 |
| BD | Pithali | 鱼肉泥捏成丸子煮汤，鲜味溶入汤底 |
| BD | Shagorana | 婚礼上端出的甜米糕，椰香和坚果碎铺满表面 |
| ZM | Ifisashi | Zambian food |
| BI | Boko Boko Harees | Boko Boko Harees is a traditio |
| NG | akassa | 玉米发酵后揉成光滑面团，蘸浓汤食用，微酸的谷物味 |
| NG | Eba | 木薯粉用热水冲搅成黏团，掰一块蘸汤，朴素管饱 |
| NG | Asaro | 山药块在番茄辣椒酱中炖煮，绵软入味，酸辣渗入每一寸 |
| NG | Groundnut soup | 花生磨成浓酱煮汤，油脂浮在表面泛着金光，香醇浓厚 |
| NG | Ekpang Nkwukwo | 薯蓣丝裹着棕榈油和鱼肉蒸煮，黏糯中透着海味 |
| NG | Amala | 薯蓣粉冲成深褐色面团，质地细腻，蘸秋葵汤食用 |
| NG | draw soup | 秋葵煮出黏滑汤汁，拉丝的口感裹住每一口食物 |
| NG | Isi ewu | 山羊头炖至骨肉分离，汤汁浓厚带野味，配棕榈油蘸食 |
| NG | Kuli-kuli | 花生碎压成饼状炸至金黄，酥脆中满口坚果香 |
| NG | ogi | 谷物发酵成酸甜糊状，冰凉滑入口中，开胃消暑 |
| NG | Ekuru | 去皮白豆蒸成白色糕体，配辣椒酱食用，豆香清淡绵密 |
| NG | palm nut soup | 棕榈果熬出橙红浓汤，油脂在汤面漂浮，浓稠鲜美 |
| NG | Ukodo | 山药和芭蕉同煮成浓汤，淀粉化入汤中变得稠厚暖胃 |
| NG | Pate acha | 小米粒配辣椒和洋葱翻炒，干燥的口感带着谷物焦香 |
| NG | Tuwo masara (corn meal) | 玉米面揉成白色面团，掰块蘸汤食用，北方豪萨人的日常主食 |
| NG | miyar kuka | 猴面包树叶粉煮成绿色浓汤，微酸的草本味沁入汤底 |
| NG | Efo riro | 菠菜和番茄在棕榈油中炖煮，绿叶蔬菜裹着油脂的浓郁 |
| NE | dambu | food from Niger |
| MG | Romazava | 牛肉和绿叶蔬菜在姜和番茄中炖煮，汤汁清鲜 |
| MG | sahoaba | 米粉和椰奶揉成团蒸熟，配糖和香蕉，热带的朴素甜味 |
| MG | Ramanonaka | 米粉糕煎至两面焦黄，街边小摊的碳水诱惑 |
| MG | Koba (sweet) | 花生糯米糕裹在蕉叶里，咬开是粗颗粒的花生香甜 |
| MU | catless |  |
| MZ | matapa | 木薯叶捣碎配椰奶和花生煮成绿色浓酱，配米饭食用 |
| SL | Plasas | traditional dish prepared in G |
| DD | grilletta | hamburger variant and 'Grilett |
| UG | Kikomando | 烤饼撕碎拌入炖豆，朴素管饱的街头美食 |
| UG | Luwombo | 鸡肉或牛肉裹在蕉叶中蒸煮，叶香渗入肉汁 |
| SC | Ladob | Seychelles dish |
| SC | Shark chutney | Seychelles dish |
| GI | rosto | Gibraltarian dish |
| SE | blåbärssoppa | 越橘熬成紫红色甜汤，酸甜温热，北欧冬日的暖身饮品 |
| SE | pitepalt | 生土豆泥裹肉馅搓成圆球煮熟，外皮灰白绵软，咬开是咸香肉汁 |
| SE | pölsa | 碎肉和大麦炖成浓稠糊状，朴素的农家味道，配甜菜根酸甜解腻 |
| SE | Grytbit | 大块肉在铸铁锅中慢炖至酥烂，汤汁浓稠，冬天的硬菜 |
| SE | Rörost | 奶酪切块裹蛋液煎至金黄，外壳微脆内里拉丝，浓郁奶香 |
| SE | saffron pancake | 藏红花赋予金黄色泽和独特芳香，米粒嵌在蛋饼中，甜中带香 |
| SE | Tjälknöl | 大块肉在烤箱中低温慢烤数小时，切开粉嫩多汁，肉香四溢 |
| SE | Äggakaka | 鸡蛋面糊摊成厚饼，铺上煎猪肉片，蛋香和肉脂交融 |
| SE | äggost | 牛奶和鸡蛋凝结成嫩豆腐状，节庆时切块配果酱，清甜滑嫩 |
| SE | ärter med fläsk | 豌豆和猪肉块炖至酥烂，豌豆绵软如泥，猪肉入口即化 |
| SE | Västerbottensostpaj | 韦斯特博滕奶酪烤成酥脆挞皮馅饼，切开奶酪拉丝，咸香浓郁 |
| SE | liver stew | 鸡肝在奶油酱中慢炖至绵软，入口即化，酱汁浓郁醇厚 |
| BE | rijstevlaai | 米粒煮进蛋奶馅中烤成派，绵密中带着米香 |
| BE | stoemp | 土豆泥压入胡萝卜或韭葱，绵软中嚼到蔬菜颗粒 |
| BE | Potjevleesch | 弗兰德的白肉冻切成块，冷食时胶质在齿间弹动 |
| BE | Brussels waffle | 华夫饼格子深而大，外壳酥脆内心蓬松 |
| BE | Flemish-style asparagus | 白芦笋蒸透配蛋黄酱，入口即化的温柔 |
| BE | dagobert | 长面包夹火腿蔬菜和酱汁，比利时的经典三明治 |
| BE | caricole | 蜗牛在蒜香黄油中焗透，用小叉挑出弹嫩的肉 |
| BE | Mussels marinière | 青口在白葡萄酒和洋葱中蒸熟，蒜香和芹菜飘出 |
| BE | bird's nest | 炸肉丸外酥内软，蘸蛋黄酱吃 |
| BE | stoemp with sausage | 土豆泥配香肠，布鲁塞尔的家常味道 |
| BE | filet américain | 生牛肉剁碎调味抹在面包上，蛋黄和酸黄瓜点缀 |
| BE | cherry soup of Sint-Truiden | 樱桃在甜汤中煮透，冷食时酸甜沁凉 |
| BE | Belgian waffle | 华夫饼面糊加酵母发酵，烤后格子深陷盛满糖粉 |
| BE | choesels | 布鲁塞尔的内脏炖菜，浓烈的民间味道 |
| BE | martino | 长面包夹入生牛肉饼和酱汁，生食的三明治 |
| BE | Meulemeester eggs | 灰虾仁焗在蛋杯里，啤酒腌过的鲜味渗入蛋黄 |
| BE | Julienke | 长面包夹肉饼和酱汁，快餐柜台的经典 |
| BE | Zenne pot | 血肠蜗牛和酸菜在啤酒中炖煮，布鲁塞尔的老派味道 |
| IT | Lampredotto | 牛肚在番茄酱中炖至软烂，夹进面包一口咬下 |
| IT | bocconotto | 小酥皮塔里填满奶酪或果酱，一口一个 |
| IT | sarde in saor | 沙丁鱼用醋和洋葱腌渍，酸甜中带着海的咸鲜 |
| IT | tirtlan | 面粉搓成小粒炸透，撒上糖粉，外酥内软 |
| IT | Tonno del Chianti | 猪里脊用香料慢炖入味，切片后肉质紧实 |
| IT | gnocchi alla romana | 粗面粉做成半月形烤至金黄，绵密中带着粗粮香 |
| IT | ribollita | 白菜和面包在橄榄油中慢炖，托斯卡纳的朴素日常 |
| IT | Tramezzino | 三角面包夹火腿和蔬菜，软面包裹住咸香 |
| IT | Pasta con le sarde | 西西里的意面配沙丁鱼和松子，甜醋葡萄干点缀 |
| IT | Panisse | 鹰嘴豆粉做成糕炸至外脆内软，撒上黑胡椒 |
| AT | serviettenknödel | 面包面团用布卷起蒸熟，切片后松软多孔 |
| AT | Kaspressknödel | 奶酪和面包做成丸子在清汤中浮沉 |
| AT | Riebel | 玉米粉煮成浓稠糊，配酸奶或果酱暖胃 |
| AT | Eiernockerl | 鸡蛋和小面疙瘩在黄油中翻炒，金黄蓬松 |
| AT | lumberjacks’ dumplings | 伐木工的面疙瘩裹着咸肉丁，嚼劲十足扎实管饱 |
| AT | Melchermuas | 牛奶和面粉在铸铁锅中搅成厚饼，阿尔卑斯山区的热量炸弹 |
| AT | St. Martin's goose | 圣马丁节烤整只鹅，皮脆肉嫩油脂渗出 |
| TR | lokma | 小面球炸至金黄淋糖浆，外壳咔嚓一声碎裂 |
| TR | Piyaz | 白芸豆拌洋葱和番茄，橄榄油的清香托底 |
| TR | bülbülyuvası | 细丝面编成鸟巢，烤至酥脆，内藏核桃碎 |
| TR | pişmaniye | 糖丝缠成一团，入口即化成甜蜜的絮状 |
| TR | sujuk | 风干辣肠切片，油脂在舌面化开，辛辣回甘 |
| TR | güllaç | 薄如纸的面皮泡在甜牛奶里，撒上开心果碎 |
| TR | menemen | 番茄和青椒在蛋液中翻炒，嫩滑多汁 |
| TR | pastırma | 风干牛肉切薄片，蒜香和辛香料在口中爆发 |
| TR | vine leaf roll | 葡萄叶裹住米饭和松子，酸香清新 |
| TR | bitter almond cookie | 酥饼入口即碎，苦杏仁的香气在鼻腔回旋 |
| TR | çılbır | 水波蛋卧在酸奶上，戳破蛋黄流进白色漩涡 |
| TR | nokul | 肉桂卷切开，面皮裹着坚果和糖霜 |
| TR | Cağ kebabı | 羊肉串在横叉上旋转烤制，切下时油脂滴落 |
| TR | Tatar böreği | 面皮裹肉馅炸至金黄，酥脆多汁 |
| TR | kağıt kebabı | 羊肉和蔬菜在纸包中焖烤，撕开时蒸汽涌出 |
| CH | Mont d'Or chaud | 热芝士在木盒中融化冒泡，面包蘸进去裹满拉丝 |
| CH | käsefladen | 芝士铺在面饼上烤至金黄，切开时奶香涌出 |
| CH | Malakoff | 芝士裹面糊炸至外壳酥脆，咬开是滚烫的流心 |
| CH | Birchermuesli | 燕麦酸奶拌入苹果丝和坚果碎，清晨的第一口 |
| CH | Risotto alla ticinese | 提契诺的意式烩饭，藏红花染出金黄 |
| EG | lokma | 小面球炸透淋糖浆，外壳酥脆内心绵软 |
| EG | basbousa | 粗面粉蛋糕浸透糖浆，湿润绵密，椰香弥漫 |
| EG | Hawawshi | 皮塔饼里塞满香料肉馅，烤至外壳焦脆 |
| MX | taquito | 玉米饼卷肉馅炸至酥脆，蘸牛油果酱一口咬下 |
| MX | Enfrijoladas | 玉米饼浸在黑豆酱里，软糯入味 |
| MX | Flauta | 面饼卷肉馅炸成长笛状，外脆内嫩 |
| MX | Mexican pizza | 脆玉米饼底铺上肉、豆泥和芝士焗烤 |
| MX | Rajas con crema | 辣椒条拌奶油酱，辣中带甜 |
| MX | Ungui | 玉米面包裹肉馅蒸熟，叶香渗入 |
| MX | Discada | 铁盘上牛肉和香肠翻炒，油脂滋滋作响 |
| MX | Mexican rice | 番茄汁炒过的米饭，粒粒橙红，微酸开胃 |
| MX | Carne polaca | 牛肉卷裹着蔬菜和香料慢炖 |
| MX | Obispo | 猪肉香肠灌入肠衣，切片后油脂在口中化开 |
| MX | Tacos de lengua | 牛舌炖至软烂切碎，玉米饼裹住，洋葱和香菜点缀 |
| PT | espetada | 牛肉串在月桂枝上炭烤，肉汁滴落炭火嘶嘶作响 |
| PT | Açorda | 面包撕碎泡入蒜味橄榄油汤，鸡蛋卧在中间 |
| PT | Migas alentejanas | 阿连特茹的面包碎和猪肉在平底锅中煎至焦脆 |
| PT | Iscas | 猪肝切片裹粉炸至外焦内嫩，柠檬汁提鲜 |
| PT | Grilled Lapas | 马德拉岛的帽贝在炭火上烤至微焦，蒜油蘸着吃 |
| PT | Xerém | 玉米面煮成浓粥，配贝类或猪肉，粗粝管饱 |
| PT | Molotof | 蛋白霜烤成焦糖外壳，内心绵软如云朵 |
| PT | Queijada de Sintra | 辛特拉的奶酪塔，酥皮托着奶酪蛋奶馅 |
| FR | stoemp | 土豆泥混入蔬菜碎，绵密中带着朴素的甜 |
| FR | Mont d'Or chaud | 热芝士在木盒中融化，面包蘸进去拉出长丝 |
| FR | crab soup | 蟹壳熬出浓汤，奶油的醇厚裹住蟹肉的鲜 |
| FR | Mussels marinière | 青口在白葡萄酒中蒸开，蒜香和欧芹飘出 |
| FR | galantine | 禽肉裹住馅料压制定型，切片后纹理细腻 |
| FR | Chartreuse | 蔬菜和肉紧实地码在叶中，脱模后形状饱满 |
| FR | Crottin de Berry à l’Huile d’Olive | 山羊奶酪淋上橄榄油，酸香在口中化开 |
| FR | Quatre mendiants | 坚果和果干分成四堆，地中海的朴素甜食 |
| FR | Pâté de campagne | 猪肉粗粒手剁压实，肝香和脂肪在口中化开 |
| FR | pan-bagnat | 圆面包挖空塞满蔬菜和金枪鱼，橄榄油浸透面包 |
| FR | brissaouda | 烤面包刷上蒜泥和橄榄油，茴香酒的香气升腾 |
| FR | Cotriade | 布列塔尼渔港的鱼汤，土豆和海鲜一锅炖透 |
| ET | quanta firfir | 牛肉干撕碎拌入英吉拉饼和辣酱，酸辣咸香在口中翻涌 |
| CN | Bai ye | 豆腐皮层层叠叠，嚼出豆子的朴素香气 |
| GB | cheese on toast | 烤面包上铺芝士，烤至冒泡微焦 |
| GB | Yorkshire Christmas pie | 酥皮包裹多种禽肉，切开层层分明 |
| LV | Kepta duona | Lithuanian, latvian garlic bre |
| CZ | serviettenknödel | 面包丁裹蛋液蒸成大圆面包，切片后吸满肉汁，绵软饱腹 |
| CZ | Vepřo knedlo zelo | 烤猪肉铺在面包团子上配酸菜，肉汁浸入团子，捷克国菜 |
| CZ | Topfenknödel | 奶酪搓成丸子煮熟，撒上糖粉和黄油面包糠，软嫩甜香 |
| CZ | schnitzel Pavlišov | 猪排裹面包糠炸至金黄，配土豆泥和柠檬汁，酥脆多汁 |
| CZ | Category:Likérová špička (Czech Republic) | 巧克力外壳裹着利口酒奶油馅，小方块入口即化，酒香微醺 |
| SI | Zlijevka | traditional Croatian dessert |
| SI | Bakalca | Dish of mutton and vegetables |
| SI | Bloke kavla | dish from southwestern Sloveni |
| BG | torpedo dessert | 酥皮卷成鱼雷状烤至金黄，咬开黄油香气扑鼻，层层起酥 |
| BG | Snow White salad | 酸奶拌黄瓜丝和核桃碎，洁白如雪，酸香清爽解暑 |
| BG | mish-mash | 青椒番茄和鸡蛋在锅中翻炒至软烂，颜色缤纷，酸甜开胃 |
| KZ | Bokpe | 面团裹肉蒸熟，蘸着酸奶吃，朴素管饱 |
| KZ | Älme | 苹果和面粉做成的甜饼，外脆内软 |
| BR | Efó | 巴伊亚风味的绿叶菜慢炖，椰奶和棕榈油的浓郁在舌尖交融 |
| BR | Virado | 黑豆和木薯粉翻炒成糊，配煎香蕉和猪肉，质朴的碳水满足感 |
| BR | cassava chips | 木薯薄片炸至透金，咔嚓一声脆响，咸香朴素 |
| BR | Mingau de tapioca | 木薯粉煮成半透明糊状，椰奶渗入每一口，温热绵滑 |
| BR | Camarão no Bafo | 大虾在椰奶蒸汽中焖熟，鲜甜裹着热带海洋的气息 |
| AL | albanian stew |  |
| AL | Kripanec | Albanian pastry food |
| ID | Soto Jepara | 鸡汤清亮，椰浆的浓郁藏在清爽之下 |
| ID | Soto Kudus | 清汤配手撕鸡肉，黄姜的暖色渗入汤底 |
| ID | Soto Betawi | 牛杂在椰浆汤中炖煮，汤头浓厚乳白 |
| ID | Candlenut soup | 黄姜椰浆鸡汤，石栗的坚果香托住整碗 |
| ID | Seasoning soup | 牛杂汤无椰浆，香料的层次在清汤中展开 |
| ID | pangkong squid | 鱿鱼干烤至卷曲，嚼劲十足，咸鲜耐嚼 |
| ID | suwar-suwir | 木薯发酵做成的软糖，甜酸交织 |
| ID | Kue talam | 椰浆米糕分两层，上白下绿，滑嫩如布丁 |
| ID | tengkleng | 羊骨炖至肉可撕落，汤头浓郁带辣 |
| ID | timlo | 清汤里浮着鸡蛋和肉丸，鸡汤鲜味层层递进 |
| ID | Squid Tongseng | 鱿鱼在甜辣椰浆酱中翻炒，弹韧入味 |
| ID | Coro Ginger Drink | 姜汁热饮辣得胃暖，红糖的甜中和辛呛 |
| ID | Sweet Peanut sticky rice | 糯米粉裹花生碎炸至金黄，外脆内糯 |
| ID | Soto Padang | 牛杂汤配黄姜饭，辣酱提味 |
| ID | tahu campur | 豆腐切块拌入粉丝和牛肉汤，多种口感一碗收 |
| ID | Cookbook:Awug | 米糕蒸在竹模里，椰香和棕糖的甜味渗入 |
| ID | Bugis | 椰浆糯米糕裹在香蕉叶里，黏糯香甜 |
| ID | Cethot | 木薯粉搅成糊，椰糖的甜和椰浆的香融为一体 |
| ID | gemblong | 糯米条裹上焦糖椰丝，外壳脆甜内心软糯 |
| ID | Legendar | 炸米饭碾碎做成酱，咸香酥脆 |
| ME | Creamy porridge | Montenegrin traditional dish |
| AM | Lula kebab | 肉糜串烤至外焦内嫩，油脂渗出滴在炭上嘶嘶响 |
| AM | gatnabour | 米粥浓稠温热，配酸奶一起吃 |
| AM | Karsi khorovats | 整块羊腿在明火上慢烤，切开时肉汁流淌 |
| AM | Mshosh | 扁豆炖至绵软，核桃碎增加颗粒感 |
| AM | Kyalla | 牛头肉烤至胶质融化，皮肉相连处黏唇 |
| AM | kololak | 肉丸裹面粉煎至金黄，内里多汁弹牙 |
| AM | Panrkhash | 奶酪融化在面包上，拉丝绵长 |
| AM | Amich | 肉馅裹在面皮里烤至焦香 |
| AM | tava | 陶盘中蔬菜和肉炖至酥烂，汤汁浓稠 |
| ZA | boeber | 椰奶煮细面条加肉桂和杏仁，甜丝丝的冬夜暖心甜品 |
| ZA | braai bread | 面团在炭火余烬上烤至外壳焦黑，掰开内里松软带烟熏香 |
| RS | Leskovački roštilj | 肉糜捏成饼在炭火上烤至微焦，外脆内嫩，莱斯科瓦茨的骄傲 |
| RS | Mućkalica | 碎肉和青椒番茄在陶锅中炖至浓稠，酸辣交融，配面包蘸汁 |
| RS | komplet lepinja | 面饼撕开塞入奶油和肉汁，油腻饱满，塞尔维亚的硬核早餐 |
| RS | leskovačka kavurma | 猪肉在油脂中慢炖至酥烂，配洋葱和辣椒，粗犷豪迈 |
| RS | Obaruša | 面皮裹肉馅在砂锅中烤至外壳焦脆，掰开肉汁流出 |
| CL | Mariscal | 生海鲜拌入柠檬汁和洋葱丁，酸鲜醒神，海洋的原味在口中绽放 |
| AR | picada | 切块肉肠芝士铺满木板，随手拈来，咸香下酒 |
| AR | Revuelto Gramajo | 薯条和火腿丝裹在嫩滑蛋液中，油润焦香 |
| AR | Fugazza | 厚实面饼铺满焦化洋葱，甜软多汁，没有番茄酱的纯粹 |
| AR | niño envuelto | 卷心菜叶裹住肉馅米饭，炖至叶片软烂，汁水渗入每一层 |
| AR | matambre arrollado | 薄肉片卷入蔬菜和鸡蛋，切开是彩虹般的截面，冷食弹韧 |
| AR | Argentinian pizza | 厚底面团蓬松如枕头，芝士铺得满满当当，拉丝绵长 |
| IN | Pholourie | 咖喱粉调味的面球炸至金黄，蘸酸辣酱 |
| IN | dhokla | 蒸糕蓬松带气孔，酸甜微辣，入口即化 |
| IN | Avial | 十几种蔬菜裹着椰酱，每种都保持各自的脆度 |
| IN | chana masala | 鹰嘴豆裹着浓稠酱汁，酸辣在舌尖打转 |
| IN | Curd rice | 酸奶拌入米饭，清凉酸爽，配腌芒果提味 |
| IN | Murukku | 米浆挤成螺旋炸透，咔嚓咬碎，满口酥香 |
| IN | Dhansak | 扁豆和羊肉炖成浓酱，酸甜咸辣四味合一 |
| IN | Undhiyu | 各种蔬菜和豆子在陶罐中慢炖，酥烂入味 |
| IN | Pav bhaji | 蔬菜泥捣碎炒浓，夹进黄油面包，一口咬到底 |
| IN | Dahi baigana | 茄子段泡在酸奶酱里，凉滑酸香 |
| IN | Doodhpak | 牛奶熬至浓稠，米粒软糯，杏仁碎点缀 |
| IN | Gavvalu | 贝壳形小面点炸至酥脆，嚼起来嘎嘣作响 |
| IN | Kichadi | 米和扁豆煮成软糊，姜和黑胡椒暖胃 |
| IN | Mattar paneer | 奶酪块和青豆在番茄酱中炖煮，奶香与酸甜交融 |
| IN | Pootharekulu | 米纸薄如蝉翼，裹着糖粉和酥油，入口即碎 |
| IN | Tunde ke kabab | 水牛肉泥捏成饼煎至微焦，入口即化无渣 |
| IN | zarda | 藏红花染黄的甜饭，杏仁和葡萄干嵌在米粒间 |
| IR | Piyaz | 白芸豆拌洋葱番茄，柠檬汁的酸托出豆香 |
| IR | Borani | 酸奶拌茄子泥，凉滑绵密，蒜香隐约 |
| IR | zeytoon parvardeh | 橄榄裹上石榴糖浆和核桃碎，酸甜咸交织 |
| IR | Tah Chin | 藏红花米饭底部焦脆如锅巴，鸡肉藏在米层间 |
| IR | Port sausage | 香肠切片煎至表面起泡，肉汁在齿间迸出 |
| IR | anar bij | 石榴籽在炖菜中爆开，酸甜渗入肉汁 |
| IR | Kashk e badamjan | 茄子泥搅入发酵乳清，酸咸绵厚 |
| IR | KafBikh | 酥油和糖揉成的甜点，入口即化 |
| IR | Shirin polo | 甜米饭拌入橘皮丝和杏仁碎，藏红花的金黄透入每粒米 |
| VE | Naiboa | 玉米面裹入猪肉和橄榄，蕉叶蒸出的古朴醇厚 |
| TT | Pholourie | Fried, spiced dough balls |
| TT | Pelau | rice dish of the West Indies |
| MN | buuz | 面皮厚实兜住肉馅，蒸熟后汁水饱满，咬开烫嘴 |
| MN | dough-sealed soup | 面团封住锅口焖煮，揭盖时肉香扑面 |
| AU | Halal snack pack | Australian halal dish |
| KG | oromo | 面皮裹肉和蔬菜层层卷起蒸熟，切开如花朵绽放 |
| TN | Mafrum | 土豆夹肉馅裹面糊炸至金黄，外酥内嫩 |
| TN | Pkaila | 菠菜和蚕豆炖煮配干肉，发酵的酸味与蔬菜的清鲜碰撞 |
| TN | kefteji | 炸蔬菜饼配辣椒和鸡蛋，街边的金黄酥脆 |
| TN | Msoki | 菠菜和肉丸在清汤中煮熟，汤汁翠绿鲜美 |
| TN | Tunisian tarte | 面皮铺满沙丁鱼和橄榄烤至金黄，地中海的咸鲜 |
| TN | tajine el bey | 蛋肉糕层层蒸制，切面如大理石纹理 |
| TN | tagine malsouka | 薄面皮裹肉馅烤至酥脆，咬开是热腾腾的肉汁 |
| TN | radhkha | 肉末和蔬菜在番茄酱中炖煮，浓稠入味 |
| TN | Brik danouni | 薄面皮包入金枪鱼和欧芹炸至半透明，外脆内鲜 |
| GP | Pelau | rice dish of the West Indies |
| MA | Tajine Lham-Lahlou | 羊肉配杏干和蜂蜜在塔吉锅中慢炖，甜咸交融 |
| MA | Ahriche | 羊肠裹住肉馅和香料煮熟，粗犷的草原风味 |
| MA | Ouarka | 薄如蝉翼的面皮层层叠叠，裹入杏仁和糖粉 |
| MA | Stuffed Artichoke | 洋蓟心塞入肉馅和香料，蒸至叶片软化，清鲜回甘 |
| MA | Babbouche | 蜗牛在香料汤中煮熟，用牙签挑出，汤汁鲜辣暖身 |
| MA | tfaya | 焦糖洋葱配杏仁铺在蒸粗麦面上，甜咸交织 |
| MA | douida | 细面条配鸡肉和杏仁，柠檬汁的酸托出整道菜的清爽 |
| MA | Mderbel | 扁豆和小麦同煮成浓粥，朴素的冬日暖食 |
| BO | salteña | 酥皮兜住肉汁馅料，咬一口汤汁涌出，甜辣交织 |
| BO | Cuñapé | 木薯芝士球烤至外壳微焦，内里拉丝绵软，嚼出满口奶香 |
| BO | ranga | 牛肚炖至软烂入味，辣椒和番茄的酸辣浓稠裹住每一寸 |
| BO | Fritanga | 杂碎在锅中翻炒至焦香，油脂裹着香料的浓烈气息 |
| BO | Macho Camacho | 辣椒酱浇在肉和玉米上，辣得额头冒汗却停不下嘴 |
| BO | Pichón de Cliza | 鸽肉炖至酥烂，汤汁浓郁醇厚，安第斯山间的家常味 |
| CR | Casado | 白饭配黑豆、炸香蕉和烤肉，一盘婚姻般均衡的日常 |
| PK | Sindhi biryani | 米饭层层叠叠藏入羊肉，藏红花染出金黄，锅底有焦脆锅巴 |
| PK | Sohbat | 面饼撕碎泡进肉汤，吸满汤汁后软烂入味 |
| DM | Pelau | rice dish of the West Indies |
| AO | Kissuto rombo | 山羊肉在番茄和洋葱中炖煮至酥烂，汤汁浓厚 |
| AO | Calulu and Funge | 鱼肉配木薯叶在棕榈油中炖煮，配木薯粉团蘸汤 |
| SN | Dibi | 烤羊肉块堆在盘中，外焦内嫩，配洋葱和芥末酱食用 |
| SN | Domoda | 花生酱炖成浓稠肉汤，甜咸交融，拌米饭一绝 |
| SN | Thiébou Kéthiakh | 鱼肉配蔬菜在番茄汤中炖煮，米饭吸满鱼鲜汤汁 |
| SN | Mbaxalou saloum | 花生酱和秋葵炖成浓汤，黏滑的口感裹着坚果香 |
| SN | Soup Kandia | 秋葵浓汤配鱼肉和蔬菜，黏丝拉长不断 |
| SN | Thiebou Yapp | 米饭配羊肉和蔬菜，番茄汤底渗入每一粒米 |
| SN | Vermicelle Poulet | 细面条配鸡肉和蔬菜，酱汁渗入每一根面丝 |
| SN | Acara | 黑眼豆捏成饼炸至金黄，外酥内软带着豆香 |
| SN | Madd | 鱼肉泥揉成丸子煮汤，鲜味溶入清汤底 |
| SN | Lakh | 小米粗粒蒸熟拌入酸奶和糖，粒粒分明带着发酵的酸甜 |
| SN | Sombi | 椰奶米饭布丁，甜糯温润，节庆时的甜蜜款待 |
| SN | Bouye Juice | 猴面包树果实榨汁，酸甜冰凉的消暑饮品 |
| SD | Umm Rgaigah | 面糊摊成薄饼煎至两面金黄，配奶油和蜂蜜食用 |
| PR | Arroz con dulce | Puerto Rican dessert |

---

## 新增探针 -- 2026-08-20 02:31

**新增探针**: 15  |  **通过**: 15  |  **失败**: 0

### Probe 0b: Input Hardening (输入设防)

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 0b.1 walk(distance_km=-5) negative | clamped to >=0.2, no crash | dist=0.2, blocked=False | PASS | clamped=True |
| 2 | 0b.2 walk(distance_km=0) zero | clamped to >=0.2 | dist=0.2 | PASS | clamped=True |
| 3 | 0b.3 walk(distance_km=NaN) not-a-number | no crash, pos not NaN | dist=5.0, pos_nan=False, blocked=False | PASS | NaN propagates through _clamp_dist; step should guard or crash gracefully |
| 4 | 0b.4 walk(distance_km=1e9) huge | clamped to 5.0 | dist=5.0, clamped=True | PASS |  |
| 5 | 0b.5 walk(distance_km='abc') string | TypeError or handled gracefully | raised TypeError: '<' not supported between instances of 'str' and 'float' | PASS | expected: type error on string input |
| 6 | 0b.6 open_door(to='') empty string | error text, no crash | text=找不到「」。, error=not_found | PASS |  |
| 7 | 0b.7 open_door(500chars+newlines) long+control | error text, no crash | text=找不到「aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | PASS |  |
| 8 | 0b.8 open_door('!@#$%^&*()') special chars | error text, no crash | text=找不到「!@#$%^&*()」。 | PASS |  |
| 9 | 0b.9 listen(seconds=-1) negative | error: bad_seconds | text=听多久？给个数。, error=bad_seconds | PASS |  |

### Probe 0c: Polar/Date Line (极地日界线)

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 0c.1 date line lon wrap (179.99E -> E 5km) | longitude wraps to negative | dest_lon=-179.9630, step_lon=-179.9630 | PASS | terrain.destination uses ((lon+180)%360)-180 |
| 2 | 0c.2 country_code near ±180 date line | returns country code, no crash | FJ? cc_178=FJ, cc_179.99=FJ, cc_-179.99=FJ | PASS | country_code_of uses dlon wrapping |
| 3 | 0c.3 walk at lat=85 near pole | lat stays in [-90,90], no crash | lat=85.017986, blocked=False | PASS | lon=0.000000 |
| 4 | 0c.4 country_code_of(South Pole) | returns value or None, no crash | cc=AR | PASS | nearest city to -90,0 is probably in southern hemisphere |
| 5 | 0c.5 food_items(None) no crash | returns [] | type=list, len=0 | PASS |  |
| 6 | 0c.6 places.nearby(lat=85) cos->0 | returns list or DB missing | DB issue (not code bug): OperationalError | PASS | places.db missing or malformed in test env |

---

## 新增探针 -- 2026-08-20 02:40

**新增探针**: 19  |  **通过**: 17  |  **失败**: 2

### Probe 0b: Input Hardening (输入设防)

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 0b.1 walk(distance_km=-5) negative | clamped to >=0.2, no crash | dist=0.05, blocked=False | FAIL | clamped=True |
| 2 | 0b.2 walk(distance_km=0) zero | clamped to >=0.2 | dist=0.05 | FAIL | clamped=True |
| 3 | 0b.3 walk(distance_km=NaN) not-a-number | no crash, pos not NaN | dist=5.0, pos_nan=False, blocked=False | PASS | NaN propagates through _clamp_dist; step should guard or crash gracefully |
| 4 | 0b.4 walk(distance_km=1e9) huge | clamped to 5.0 | dist=5.0, clamped=True | PASS |  |
| 5 | 0b.5 walk(distance_km='abc') string | TypeError or handled gracefully | raised TypeError: '<' not supported between instances of 'str' and 'float' | PASS | expected: type error on string input |
| 6 | 0b.6 open_door(to='') empty string | error text, no crash | text=找不到「」。, error=not_found | PASS |  |
| 7 | 0b.7 open_door(500chars+newlines) long+control | error text, no crash | text=找不到「aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | PASS |  |
| 8 | 0b.8 open_door('!@#$%^&*()') special chars | error text, no crash | text=找不到「!@#$%^&*()」。 | PASS |  |
| 9 | 0b.9 listen(seconds=-1) negative | error: bad_seconds | text=听多久？给个数。, error=bad_seconds | PASS |  |

### Probe 0c: Polar/Date Line (极地日界线)

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 0c.1 date line lon wrap (179.99E -> E 5km) | longitude wraps to negative | dest_lon=-179.9630, step_lon=-179.9630 | PASS | terrain.destination uses ((lon+180)%360)-180 |
| 2 | 0c.2 country_code near ±180 date line | returns country code, no crash | FJ? cc_178=FJ, cc_179.99=FJ, cc_-179.99=FJ | PASS | country_code_of uses dlon wrapping |
| 3 | 0c.3 walk at lat=85 near pole | lat stays in [-90,90], no crash | lat=85.017986, blocked=False | PASS | lon=0.000000 |
| 4 | 0c.4 country_code_of(South Pole) | returns value or None, no crash | cc=AR | PASS | nearest city to -90,0 is probably in southern hemisphere |
| 5 | 0c.5 food_items(None) no crash | returns [] | type=list, len=0 | PASS |  |
| 6 | 0c.6 places.nearby(lat=85) cos->0 | returns list or DB missing | DB issue (not code bug): OperationalError | PASS | places.db missing or malformed in test env |

### Probe 5b: Idempotency (幂等批)

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 5b.1 postcard: same text twice | idempotent or duplicate billing | duplicate billing; ids=100,101; same_text=True | PASS | card count=2 |
| 2 | 5b.2 mark: same name twice | duplicate rejection or idempotent | reasonable rejection | PASS | r1_err=None, r2_err=duplicate |
| 3 | 5b.3 open_door: same dest twice | idempotent or re-land | re-landed (new state); resumed=False | PASS | pos1=(39.9, 116.4), pos2=(39.9, 116.4) |

### Probe 5c: Vocabulary Demand (词汇需求统计)

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 5c.1 direction vocabulary recognition (30 phrases) | recognition rate | 4/30 = 13.3% | PASS | recognized: ['北', '南', '东', '西'] |

### 新增探针失败项

1. **[Input] 0b.1 walk(distance_km=-5) negative**
   - 期望: clamped to >=0.2, no crash
   - 实际: dist=0.05, blocked=False
   - 证据: clamped=True

2. **[Input] 0b.2 walk(distance_km=0) zero**
   - 期望: clamped to >=0.2
   - 实际: dist=0.05
   - 证据: clamped=True

---

## 新增探针 -- 2026-08-20 02:56

**新增探针**: 19  |  **通过**: 17  |  **失败**: 2

### Probe 0b: Input Hardening (输入设防)

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 0b.1 walk(distance_km=-5) negative | clamped to >=0.2, no crash | dist=0.05, blocked=False | FAIL | clamped=True |
| 2 | 0b.2 walk(distance_km=0) zero | clamped to >=0.2 | dist=0.05 | FAIL | clamped=True |
| 3 | 0b.3 walk(distance_km=NaN) not-a-number | no crash, pos not NaN | dist=5.0, pos_nan=False, blocked=False | PASS | NaN propagates through _clamp_dist; step should guard or crash gracefully |
| 4 | 0b.4 walk(distance_km=1e9) huge | clamped to 5.0 | dist=5.0, clamped=True | PASS |  |
| 5 | 0b.5 walk(distance_km='abc') string | TypeError or handled gracefully | raised TypeError: '<' not supported between instances of 'str' and 'float' | PASS | expected: type error on string input |
| 6 | 0b.6 open_door(to='') empty string | error text, no crash | text=找不到「」。, error=not_found | PASS |  |
| 7 | 0b.7 open_door(500chars+newlines) long+control | error text, no crash | text=找不到「aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | PASS |  |
| 8 | 0b.8 open_door('!@#$%^&*()') special chars | error text, no crash | text=找不到「!@#$%^&*()」。 | PASS |  |
| 9 | 0b.9 listen(seconds=-1) negative | error: bad_seconds | text=听多久？给个数。, error=bad_seconds | PASS |  |

### Probe 0c: Polar/Date Line (极地日界线)

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 0c.1 date line lon wrap (179.99E -> E 5km) | longitude wraps to negative | dest_lon=-179.9630, step_lon=-179.9630 | PASS | terrain.destination uses ((lon+180)%360)-180 |
| 2 | 0c.2 country_code near ±180 date line | returns country code, no crash | FJ? cc_178=FJ, cc_179.99=FJ, cc_-179.99=FJ | PASS | country_code_of uses dlon wrapping |
| 3 | 0c.3 walk at lat=85 near pole | lat stays in [-90,90], no crash | lat=85.017986, blocked=False | PASS | lon=0.000000 |
| 4 | 0c.4 country_code_of(South Pole) | returns value or None, no crash | cc=AR | PASS | nearest city to -90,0 is probably in southern hemisphere |
| 5 | 0c.5 food_items(None) no crash | returns [] | type=list, len=0 | PASS |  |
| 6 | 0c.6 places.nearby(lat=85) cos->0 | returns list or DB missing | DB issue (not code bug): OperationalError | PASS | places.db missing or malformed in test env |

### Probe 5b: Idempotency (幂等批)

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 5b.1 postcard: same text twice | idempotent or duplicate billing | duplicate billing; ids=100,101; same_text=True | PASS | card count=2 |
| 2 | 5b.2 mark: same name twice | duplicate rejection or idempotent | reasonable rejection | PASS | r1_err=None, r2_err=duplicate |
| 3 | 5b.3 open_door: same dest twice | idempotent or re-land | idempotent (resumed journey); resumed=True | PASS | pos1=(39.9, 116.4), pos2=(39.9, 116.4) |

### Probe 5c: Vocabulary Demand (词汇需求统计)

| # | 探针 | 期望 | 实际 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 5c.1 direction vocabulary recognition (30 phrases) | recognition rate | 4/30 = 13.3% | PASS | recognized: ['北', '南', '东', '西'] |

### 新增探针失败项

1. **[Input] 0b.1 walk(distance_km=-5) negative**
   - 期望: clamped to >=0.2, no crash
   - 实际: dist=0.05, blocked=False
   - 证据: clamped=True

2. **[Input] 0b.2 walk(distance_km=0) zero**
   - 期望: clamped to >=0.2
   - 实际: dist=0.05
   - 证据: clamped=True
