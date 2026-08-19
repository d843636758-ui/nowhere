# -*- coding: utf-8 -*-
"""V3 生成器 v2(事实严格版)"""
import json, sys, time, urllib.request

SF_KEY = "sk-uijgdvpjfrbgzwuepbglmbrztcmaqckitwynaftxnrxbxeis"
TV_KEY = "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"

def post(url, headers, payload, timeout=200, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if i == retries-1: raise
            time.sleep(3*(i+1))

def tavily(place, q=None, retries=2):
    q = q or f"{place} 当地 特色 历史 物产 美食"
    for i in range(retries):
        try:
            r = post("https://api.tavily.com/search",
                     {"Content-Type":"application/json"},
                     {"api_key":TV_KEY,"query":q,"max_results":5,"search_depth":"basic"}, timeout=40)
            return [x["content"][:300] for x in r.get("results",[])][:5]
        except Exception:
            if i==retries-1: return []
            time.sleep(3)

STYLE = """目标:给一个旅行/传送门游戏写"地方志卡"。参照风格:第一人称行纪、具体体感、当地实据、每处不同切入。
【铁律·事实】只许写"当地实据"里出现的事实。实据里没有的数字/年代/专名/人名一律不写。专名必须真实且属于该地——不属于该地的标志物(别的城市的塔/庙/建筑)绝不许写。宁可写体感、写场景，不编数字。
【铁律·用词】不许用:很/非常/十分/巨大/美丽。不许用空泛词:一些/很多/感觉/仿佛/好像/似乎/有点。
【铁律·结构】必须输出 JSON,不能多字。格式:
{"place":"地名","entry":{"物产":[2-3条],"声音":[2-3条],"痕迹":[2-3条],"美食":[2-3条],"节律":[{"hours":[起,止],"text":"..."}]},"souvenir":{"name":"本地物件名","desc":"诗意2-3句"}}
每条卡:2-3句,有具体可感细节,第二人称或第一人称都可。souvenir 必须是这个地点当地能捡到/买到的物件。"""

def gen(place):
    facts = tavily(place)
    facts_txt = "\n".join(f"- {f}" for f in facts) if facts else "(无实据,凭常识写体感,不编具体数字专名)"
    prompt = f"写《{place}》的地方志卡。\n\n当地实据(搜索来的,只准用这里面的,用不上就忽略,别加别的):\n{facts_txt}\n\n{STYLE}"
    try:
        r = post("https://api.siliconflow.cn/v1/chat/completions",
                 {"Content-Type":"application/json","Authorization":f"Bearer {SF_KEY}"},
                 {"model":"deepseek-ai/DeepSeek-V3",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":1600, "temperature":0.85})
        txt = r["choices"][0]["message"]["content"].strip()
        if txt.startswith("```"):
            txt = txt.split("\n",1)[1].rsplit("```",1)[0].strip()
        return json.loads(txt)
    except Exception as e:
        return {"place":place,"error":str(e),"raw":txt if 'txt' in locals() else ""}

if __name__ == "__main__":
    places = sys.argv[1:]
    out = {}
    for p in places:
        print(f"== {p} ==", flush=True)
        out[p] = gen(p)
        time.sleep(2)
    with open("task_text_quality/rewrite/v3_out.json","w",encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    for p in places:
        g = out[p]
        if "error" in g: print(f"  {p}: ERROR {g['error']}")
        else: print(f"  {p}: OK 物产{len(g['entry']['物产'])} 声音{len(g['entry']['声音'])} 痕迹{len(g['entry']['痕迹'])} 美食{len(g['entry']['美食'])} 节律{len(g['entry']['节律'])} souvenir={g['souvenir']['name']}")
