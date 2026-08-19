# -*- coding: utf-8 -*-
"""查实据: python facts.py <地点>  [可加第二参数=查询词]
输出 Tavily 搜索到的当地事实(每条约200-300字),供写卡用。不联网时返回空。"""
import json, sys, urllib.request, time
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
TV_KEY = "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"
def post(url, h, p, t=45, retries=2):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(p).encode(), headers=h, method="POST")
            with urllib.request.urlopen(req, timeout=t) as r: return json.loads(r.read().decode())
        except Exception:
            if i == retries-1: raise
            time.sleep(3)
def zim_fallback(place):
    """Tavily 限流时落离线维基(nowhere/data/packs/wikipedia_zh_mini.zim)。"""
    try:
        import facts_zim
        txt = facts_zim.fetch(place)
        if txt:
            return f"## {place} (离线维基)\n\n{txt}"
    except Exception:
        pass
    return None


if __name__ == "__main__":
    place = sys.argv[1]
    q = sys.argv[2] if len(sys.argv) > 2 else f"{place} 当地 特色 历史 物产 美食 建筑"
    res = None
    try:
        r = post("https://api.tavily.com/search", {"Content-Type":"application/json"},
                 {"api_key":TV_KEY,"query":q,"max_results":5,"search_depth":"advanced"})
        res = r.get("results", [])
        for x in res[:5]:
            print("##", x.get("title","")[:80])
            print(x.get("content","")[:400].replace("\n"," "))
            print()
    except Exception as e:
        print(f"(tavily err: {e}, 落离线维基)")
    if not res:
        fallback = zim_fallback(place)
        if fallback:
            print(fallback)
        else:
            print(f"(无实据: tavily 限流且 zim 无 {place} 条目)")
