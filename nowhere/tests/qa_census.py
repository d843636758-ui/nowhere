# -*- coding: utf-8 -*-
"""Card 34: Full Card Census — LLM judge scores all cards (localcolor + humanities).

Scores 1-5:
  5 = 杆上 (旧北京/敦煌级, 可当新样例)
  4 = 好 (有地方血肉, 声口对)
  3 = 能用 (信息对但平, 像资料卡)
  2 = 差 (模板壳/空泛/断气)
  1 = 有害 (错配/编造/英文裸进)

Steps:
  1. Judge calibration on golden set (qa_lqa_golden.json), must >= 80% agreement
  2. Full scoring of every card
  3. Output qa_census_report.md

Usage:
    cd C:\\Users\\84989\\Desktop\\nowhere_repo
    python nowhere/tests/qa_census.py
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# GBK console fix
sys.stdout.reconfigure(encoding="utf-8")

_REPO = pathlib.Path(__file__).resolve().parent.parent.parent
_REPORT = _REPO / "qa_census_report.md"
_GOLDEN = _REPO / "nowhere" / "tests" / "qa_lqa_golden.json"
_DATA = _REPO / "nowhere" / "data"


# ═══════════════════════════════════════════════════════════════════════
# Data Loading
# ═══════════════════════════════════════════════════════════════════════

def _load_all_cards() -> list[dict]:
    """Load every individual text card from all data files.

    Returns list of {place, source, category, text, card_type} dicts.
    card_type: 'localcolor' or 'humanities'
    """
    cards: list[dict] = []

    # ── Localcolor files ──
    lc_files = [
        "localcolor.json",
        "localcolor_china.json",
        "localcolor_japan_korea_sea.json",
        "localcolor_americas_africa_oceania.json",
    ]
    for fname in lc_files:
        fp = _DATA / fname
        if not fp.exists():
            continue
        d = json.loads(fp.read_text(encoding="utf-8"))
        for place, place_data in d.items():
            if not isinstance(place_data, dict):
                continue
            for cat, items in place_data.items():
                if not isinstance(items, list):
                    # string 节律
                    if isinstance(items, str):
                        cards.append({
                            "place": place, "source": fname,
                            "category": cat, "text": items,
                            "card_type": "localcolor",
                        })
                    continue
                for item in items:
                    if isinstance(item, str):
                        cards.append({
                            "place": place, "source": fname,
                            "category": cat, "text": item,
                            "card_type": "localcolor",
                        })
                    elif isinstance(item, dict):
                        # 节律 with hours
                        text = item.get("text", "")
                        if text:
                            cards.append({
                                "place": place, "source": fname,
                                "category": cat, "text": text,
                                "card_type": "localcolor",
                            })

    # ── Humanities files ──
    hu_files = [
        "humanities.json",
        "humanities_films.json",
        "humanities_historical.json",
    ]
    for fname in hu_files:
        fp = _DATA / fname
        if not fp.exists():
            continue
        d = json.loads(fp.read_text(encoding="utf-8"))
        places = d.get("places", d)
        for place, place_data in places.items():
            if not isinstance(place_data, dict):
                continue
            for cat, items in place_data.items():
                if cat in ("lat", "lon", "_说明", "aliases"):
                    continue
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    text = item.get("text", "")
                    if text:
                        cards.append({
                            "place": place, "source": fname,
                            "category": cat, "text": text,
                            "card_type": "humanities",
                        })

    return cards


# ═══════════════════════════════════════════════════════════════════════
# LLM Caller
# ═══════════════════════════════════════════════════════════════════════

def _get_api_key() -> str:
    """Get API key from env vars. Returns empty string if not found."""
    for var in ("SILICONFLOW_API_KEY", "SF_API_KEY"):
        key = os.environ.get(var, "").strip()
        if key:
            return key
    return ""


def _call_llm(prompt: str, max_tokens: int = 300) -> str | None:
    """Call LLM via SiliconFlow DeepSeek. Returns response text or None."""
    api_key = _get_api_key()
    if not api_key:
        return None

    import urllib.request
    payload = json.dumps({
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.1,
    }).encode()

    req = urllib.request.Request(
        "https://api.siliconflow.cn/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def _parse_score_response(resp: str | None) -> tuple[int, str]:
    """Parse LLM response to extract score (1-5) and reason.
    Returns (score, reason). score=0 if unparseable.
    """
    if resp is None:
        return 0, "LLM call failed"

    # Try JSON extraction
    try:
        json_match = re.search(r'\{[^{}]+\}', resp)
        if json_match:
            parsed = json.loads(json_match.group())
            score = int(parsed.get("score", 0))
            reason = parsed.get("reason", "")
            if 1 <= score <= 5:
                return score, reason
    except Exception:
        pass

    # Try to find score in text
    for s in range(5, 0, -1):
        if f'"score": {s}' in resp or f'"score":{s}' in resp:
            return s, resp[:100]
        if f'评分: {s}' in resp or f'评分:{s}' in resp:
            return s, resp[:100]

    return 0, f"Parse failed: {resp[:150]}"


# ═══════════════════════════════════════════════════════════════════════
# Judge Calibration
# ═══════════════════════════════════════════════════════════════════════

_JUDGE_CALIBRATION_PROMPT = """你是卡片质量审核员。给这张地方卡片打分(1-5):

评分标准:
- 5=杆上: 细节精准、声口对、有血肉、可当新样例(如旧北京/敦煌级)
- 4=好: 有地方特色、五感到位、声口对
- 3=能用: 信息正确但平,像资料卡,缺乏体感
- 2=差: 模板壳/空泛/断气/泛泛而谈
- 1=有害: 事实错配/编造/英文裸进/严重bug

地点: {place}
分类: {category}
文本: {text}

只输出JSON: {{"score": 1-5, "reason": "一句话理由"}}"""


def _calibrate_judge(golden: list[dict]) -> tuple[float, list[dict]]:
    """Run judge on golden set, compute agreement rate.

    The golden set has labels PASS/S1-S4. We map them to scores:
      PASS -> 4 (good), S4 -> 3 (acceptable), S3 -> 2 (poor), S2 -> 1 (bad), S1 -> 1 (bad)
    Then compare with our 1-5 score.

    Returns (agreement_rate, details).
    """
    # Map golden labels to expected score ranges
    label_to_score = {
        "PASS": (4, 5),   # PASS = good or excellent
        "S4": (3, 4),     # S4 = acceptable, needs polish
        "S3": (2, 3),     # S3 = poor, minor issues
        "S2": (1, 2),     # S2 = bad, major issues
        "S1": (1, 2),     # S1 = harmful, critical issues
    }

    details = []
    correct = 0

    for g in golden:
        label = g.get("label", "")
        text = g.get("text", "")
        env = g.get("env", {})
        expected_range = label_to_score.get(label, (3, 3))

        prompt = _JUDGE_CALIBRATION_PROMPT.format(
            place=f"golden_{g.get('id', '')}",
            category=f"env={env}",
            text=text,
        )
        resp = _call_llm(prompt)
        score, reason = _parse_score_response(resp)

        # Check if score falls in expected range
        match = expected_range[0] <= score <= expected_range[1] if score > 0 else False
        if match:
            correct += 1

        details.append({
            "id": g.get("id", ""),
            "golden_label": label,
            "expected_range": expected_range,
            "judge_score": score,
            "match": match,
            "reason": reason,
        })

    agreement = correct / len(golden) if golden else 0
    return agreement, details


# ═══════════════════════════════════════════════════════════════════════
# Full Scoring
# ═══════════════════════════════════════════════════════════════════════

_SCORE_PROMPT = """你是卡片质量审核员。给这张地方卡片打分(1-5):

评分标准:
- 5=杆上: 细节精准、声口对、有血肉、可当新样例(如旧北京/敦煌级)
- 4=好: 有地方特色、五感到位、声口对
- 3=能用: 信息正确但平,像资料卡,缺乏体感
- 2=差: 模板壳/空泛/断气/泛泛而谈
- 1=有害: 事实错配/编造/英文裸进/严重bug

地点: {place}
分类: {category}
文本: {text}

只输出JSON: {{"score": 1-5, "reason": "一句话理由"}}"""


def _score_single_card(card: dict) -> dict:
    """Score a single card. Returns card with score and reason added."""
    prompt = _SCORE_PROMPT.format(
        place=card["place"],
        category=card["category"],
        text=card["text"][:500],  # truncate long texts
    )
    resp = _call_llm(prompt)
    score, reason = _parse_score_response(resp)
    return {**card, "score": score, "reason": reason}


def _score_all_cards(cards: list[dict], max_workers: int = 8) -> list[dict]:
    """Score all cards using concurrent LLM calls."""
    scored: list[dict] = []
    total = len(cards)
    done = 0
    errors = 0

    print(f"  Scoring {total} cards with {max_workers} workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_score_single_card, c): i for i, c in enumerate(cards)}
        for future in as_completed(futures):
            done += 1
            try:
                result = future.result()
                scored.append(result)
                if result["score"] == 0:
                    errors += 1
            except Exception as e:
                idx = futures[future]
                scored.append({**cards[idx], "score": 0, "reason": str(e)[:100]})
                errors += 1

            if done % 100 == 0 or done == total:
                avg_so_far = sum(c["score"] for c in scored if c["score"] > 0) / max(1, len(scored) - errors)
                print(f"    {done}/{total} scored (avg={avg_so_far:.2f}, errors={errors})",
                      flush=True)

    return scored


# ═══════════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════════

def _generate_report(
    all_cards: list[dict],
    calibration_agreement: float,
    calibration_details: list[dict],
    elapsed: float,
) -> None:
    """Generate qa_census_report.md."""
    scored = [c for c in all_cards if c.get("score", 0) > 0]
    if not scored:
        _REPORT.write_text(
            "# QA Census Report\n\nLLM not available, manual review needed.\n",
            encoding="utf-8",
        )
        print(f"  Report written: {_REPORT}")
        return

    lines: list[str] = []
    lines.append("# QA Census Report -- Card 34: 全量卡片普查")
    lines.append("")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**耗时**: {elapsed:.0f} 秒 ({elapsed/60:.1f} 分钟)")
    lines.append(f"**总卡片数**: {len(all_cards)}")
    lines.append(f"**已评分**: {len(scored)} (有效)")
    lines.append(f"**评分失败**: {len(all_cards) - len(scored)}")
    lines.append("")

    # ── Score Distribution ──
    lines.append("## 分数分布")
    lines.append("")
    score_counts = Counter(c["score"] for c in scored)
    total_scored = len(scored)
    labels = {5: "杆上", 4: "好", 3: "能用", 2: "差", 1: "有害"}
    lines.append("| 分数 | 含义 | 数量 | 占比 | 柱状图 |")
    lines.append("|------|------|------|------|--------|")
    for s in range(5, 0, -1):
        cnt = score_counts.get(s, 0)
        pct = cnt / total_scored * 100 if total_scored else 0
        bar = "█" * int(pct / 2)
        lines.append(f"| {s} | {labels[s]} | {cnt} | {pct:.1f}% | {bar} |")
    avg_score = sum(c["score"] for c in scored) / total_scored
    lines.append("")
    lines.append(f"**平均分**: {avg_score:.2f}")
    lines.append("")

    # ── Score by card_type ──
    lines.append("## 按类型分布")
    lines.append("")
    for ctype in ("localcolor", "humanities"):
        subset = [c for c in scored if c["card_type"] == ctype]
        if not subset:
            continue
        sub_avg = sum(c["score"] for c in subset) / len(subset)
        sub_counts = Counter(c["score"] for c in subset)
        lines.append(f"### {ctype} ({len(subset)} cards, avg={sub_avg:.2f})")
        lines.append("")
        lines.append("| 分数 | 数量 | 占比 |")
        lines.append("|------|------|------|")
        for s in range(5, 0, -1):
            cnt = sub_counts.get(s, 0)
            pct = cnt / len(subset) * 100
            lines.append(f"| {s} | {cnt} | {pct:.1f}% |")
        lines.append("")

    # ── Score by source file ──
    lines.append("## 按来源文件分布")
    lines.append("")
    source_groups: dict[str, list] = defaultdict(list)
    for c in scored:
        source_groups[c["source"]].append(c)
    lines.append("| 来源 | 卡片数 | 平均分 | 5分占比 | 1-2分占比 |")
    lines.append("|------|--------|--------|---------|-----------|")
    for src in sorted(source_groups.keys()):
        subset = source_groups[src]
        sub_avg = sum(c["score"] for c in subset) / len(subset)
        pct5 = sum(1 for c in subset if c["score"] == 5) / len(subset) * 100
        pct12 = sum(1 for c in subset if c["score"] <= 2) / len(subset) * 100
        lines.append(f"| {src} | {len(subset)} | {sub_avg:.2f} | {pct5:.1f}% | {pct12:.1f}% |")
    lines.append("")

    # ── Top 20 Best Places ──
    lines.append("## Top 20 最佳地点 (按平均分)")
    lines.append("")
    place_groups: dict[str, list] = defaultdict(list)
    for c in scored:
        place_groups[c["place"]].append(c)
    place_stats = []
    for place, cards in place_groups.items():
        avg = sum(c["score"] for c in cards) / len(cards)
        place_stats.append((place, avg, len(cards), cards))
    place_stats.sort(key=lambda x: x[1], reverse=True)

    lines.append("| 排名 | 地点 | 平均分 | 卡片数 | 最高 | 最低 |")
    lines.append("|------|------|--------|--------|------|------|")
    for i, (place, avg, cnt, cards) in enumerate(place_stats[:20], 1):
        scores = [c["score"] for c in cards]
        lines.append(f"| {i} | {place} | {avg:.2f} | {cnt} | {max(scores)} | {min(scores)} |")
    lines.append("")

    # ── Bottom 40 Worst Places ──
    lines.append("## Bottom 40 最差地点 (按平均分)")
    lines.append("")
    place_stats.sort(key=lambda x: x[1])
    lines.append("| 排名 | 地点 | 平均分 | 卡片数 | 最高 | 最低 |")
    lines.append("|------|------|--------|--------|------|------|")
    for i, (place, avg, cnt, cards) in enumerate(place_stats[:40], 1):
        scores = [c["score"] for c in cards]
        lines.append(f"| {i} | {place} | {avg:.2f} | {cnt} | {max(scores)} | {min(scores)} |")
    lines.append("")

    # ── Every card scoring <3 ──
    lines.append("## 低分卡片清单 (score < 3)")
    lines.append("")
    low_cards = sorted(
        [c for c in scored if c["score"] < 3],
        key=lambda x: (x["score"], x["place"]),
    )
    lines.append(f"共 {len(low_cards)} 张卡片评分 < 3:")
    lines.append("")
    lines.append("| 分数 | 地点 | 类型 | 来源 | 卡片文本(截断) | 理由 |")
    lines.append("|------|------|------|------|----------------|------|")
    for c in low_cards:
        text_short = c["text"][:80].replace("\n", " ").replace("|", "\\|")
        reason_short = c.get("reason", "")[:60].replace("|", "\\|")
        lines.append(
            f"| {c['score']} | {c['place']} | {c['category']} | {c['source']} "
            f"| {text_short} | {reason_short} |"
        )
    lines.append("")

    # ── Rewrite Priority List ──
    lines.append("## 重写优先级清单")
    lines.append("")
    lines.append("排序公式: `place_avg_score x card_count` — 平均分低且卡片多的地方优先重写")
    lines.append("")
    # Only places with avg < 4 (need rewrite)
    rewrite_candidates = [(p, a, n, cs) for p, a, n, cs in place_stats if a < 4.0]
    rewrite_candidates.sort(key=lambda x: x[1] * x[2])  # score * count, lower = higher priority

    lines.append("| 优先级 | 地点 | 平均分 | 卡片数 | score*count | 建议 |")
    lines.append("|--------|------|--------|--------|-------------|------|")
    for i, (place, avg, cnt, cards) in enumerate(rewrite_candidates[:50], 1):
        priority_score = avg * cnt
        if avg < 2:
            suggestion = "紧急重写"
        elif avg < 3:
            suggestion = "需要重写"
        else:
            suggestion = "可优化"
        lines.append(
            f"| {i} | {place} | {avg:.2f} | {cnt} | {priority_score:.0f} | {suggestion} |"
        )
    lines.append("")

    # ── Calibration ──
    lines.append("## 裁判校准")
    lines.append("")
    lines.append(f"**Golden set 一致率**: {calibration_agreement:.1%} "
                 f"({'达标' if calibration_agreement >= 0.80 else '未达标,结果仅供参考'})")
    lines.append("")
    if calibration_details:
        lines.append("| Golden ID | 标注 | 预期范围 | 裁判分 | 匹配 | 理由 |")
        lines.append("|-----------|------|----------|--------|------|------|")
        for d in calibration_details:
            r = d["expected_range"]
            lines.append(
                f"| {d['id']} | {d['golden_label']} | {r[0]}-{r[1]} "
                f"| {d['judge_score']} | {'Y' if d['match'] else 'N'} "
                f"| {d['reason'][:50]} |"
            )
        lines.append("")

    # ── Notes ──
    lines.append("## 备注")
    lines.append("")
    lines.append("- LLM 裁判使用硅基流动 DeepSeek-V3 (SILICONFLOW_API_KEY)")
    lines.append("- 评分温度 0.1, 保证一致性")
    lines.append("- 并发 8 线程, 每请求超时 45 秒")
    lines.append(f"- 有效评分 {len(scored)}/{len(all_cards)} ({len(scored)/len(all_cards)*100:.1f}%)")

    _REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Report written: {_REPORT}")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    start = time.time()

    print("=" * 60)
    print("QA Census -- Card 34: 全量卡片普查")
    print("=" * 60)

    # ── Check API key ──
    api_key = _get_api_key()
    if not api_key:
        print("\n  LLM not available: SILICONFLOW_API_KEY / SF_API_KEY not set")
        print("  Skipping scoring, report will note manual review needed.")
        _REPORT.write_text(
            "# QA Census Report\n\n"
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            "## 状态\n\n"
            "LLM not available, manual review needed.\n\n"
            "未设置 SILICONFLOW_API_KEY / SF_API_KEY 环境变量，无法调用 LLM 裁判。\n",
            encoding="utf-8",
        )
        print(f"  Report: {_REPORT}")
        return

    # ── Load all cards ──
    print("\nStep 1: Loading all cards...")
    all_cards = _load_all_cards()
    print(f"  Total cards loaded: {len(all_cards)}")

    lc_count = sum(1 for c in all_cards if c["card_type"] == "localcolor")
    hu_count = sum(1 for c in all_cards if c["card_type"] == "humanities")
    print(f"    localcolor: {lc_count}")
    print(f"    humanities: {hu_count}")

    sources = Counter(c["source"] for c in all_cards)
    for src, cnt in sorted(sources.items()):
        print(f"    {src}: {cnt}")

    # ── Step 2: Judge calibration ──
    print("\nStep 2: Judge calibration on golden set...")
    if not _GOLDEN.exists():
        print("  Golden set not found, skipping calibration")
        calibration_agreement = 0
        calibration_details = []
    else:
        golden = json.loads(_GOLDEN.read_text(encoding="utf-8"))
        print(f"  Golden set: {len(golden)} examples")

        calibration_agreement, calibration_details = _calibrate_judge(golden)
        print(f"  Calibration agreement: {calibration_agreement:.1%}")

        if calibration_agreement < 0.80:
            print(f"  WARNING: Agreement {calibration_agreement:.1%} < 80%")
            print("  Proceeding anyway, but results may be unreliable")
        else:
            print("  Calibration passed (>= 80%)")

    # ── Step 3: Full scoring ──
    print("\nStep 3: Full scoring...")
    all_cards = _score_all_cards(all_cards, max_workers=8)

    elapsed = time.time() - start

    # ── Step 4: Generate report ──
    print("\nStep 4: Generating report...")
    _generate_report(all_cards, calibration_agreement, calibration_details, elapsed)

    # ── Summary ──
    scored = [c for c in all_cards if c.get("score", 0) > 0]
    score_counts = Counter(c["score"] for c in scored)
    avg = sum(c["score"] for c in scored) / len(scored) if scored else 0

    print(f"\n{'='*60}")
    print(f"COMPLETE in {elapsed:.0f}s ({elapsed/60:.1f}min)")
    print(f"  Total cards: {len(all_cards)}")
    print(f"  Scored: {len(scored)}")
    print(f"  Average: {avg:.2f}")
    for s in range(5, 0, -1):
        print(f"    {s}={labels.get(s, '?')}: {score_counts.get(s, 0)}")
    print(f"  Report: {_REPORT}")
    print(f"{'='*60}")


labels = {5: "杆上", 4: "好", 3: "能用", 2: "差", 1: "有害"}

if __name__ == "__main__":
    main()
