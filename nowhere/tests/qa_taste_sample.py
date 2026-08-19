"""盲评抽样脚本 (Card 36: 品味回路)

从乌有乡的真实渲染管线里随机抽取 10 段文本,去掉地名标签,打乱顺序,
保存为 docs/taste_samples/YYYY-MM-DD.md 供旋复盲评。

用法:
    python nowhere/tests/qa_taste_sample.py              # 随机种子
    python nowhere/tests/qa_taste_sample.py --seed 42    # 固定种子(可复现)
    python nowhere/tests/qa_taste_sample.py --count 20   # 抽 20 段

铁律: 产物只进 golden set,不直接改卡。
"""

from __future__ import annotations

import asyncio
import os
import random
import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Windows GBK console fix
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# 项目根目录
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))

from nowhere.server import open_door_impl, walk_impl, _state, _rng  # noqa: E402
from nowhere import state as state_mod  # noqa: E402


# ── 地名脱敏 ────────────────────────────────────────────────────────────

# 从落地文本里去掉地名标注行: 【国家, 地名, 时段, 季节。】
_RE_LOCATION_TAG = re.compile(r"【[^】]*?[,，][^】]*?[,，][^】]*?[,，][^】]*?。】")
# 去掉 "你落在了XXX附近" 中的 XXX
_RE_NEAR_PLACE = re.compile(r"你落在了.{1,20}?附近")
# 去掉 "到了。XXX。" 中的 XXX
_RE_ARRIVED = re.compile(r"到了。.{1,20}?。")
# 去掉 "XXX在Y边" 中的 XXX
_RE_PLACE_DIR = re.compile(r"[一-鿿A-Za-z]{1,15}在[东西南北]边")
# 去掉 "又来了——第 N 次来XXX"
_RE_REVISIT = re.compile(r"又来了——第 \d+ 次来.{1,20}?。")


def _strip_place_names(text: str) -> str:
    """尽可能去掉文本中的地名,让评审者无法猜出地点。"""
    text = _RE_LOCATION_TAG.sub("[地点已隐藏]", text)
    text = _RE_NEAR_PLACE.sub("你落在了一个地方附近", text)
    text = _RE_ARRIVED.sub("到了。", text)
    text = _RE_REVISIT.sub("又来了。", text)
    return text


# ── 分段 ────────────────────────────────────────────────────────────────

def _segment_text(text: str) -> list[str]:
    """把一段渲染文本按句子边界拆成独立段落。

    策略: 按句号/问号/感叹号断句,每 2-3 句合并为一个评阅段。
    """
    # 按中文句号、问号、感叹号断句(保留标点)
    sentences = re.split(r"(?<=[。？！])", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    segments: list[str] = []
    chunk: list[str] = []
    for s in sentences:
        chunk.append(s)
        # 每 2-3 句一段
        if len(chunk) >= 3 or (len(chunk) >= 2 and random.random() < 0.4):
            segments.append("".join(chunk))
            chunk = []
    if chunk:
        segments.append("".join(chunk))
    return segments


# ── 采集 ────────────────────────────────────────────────────────────────

async def _collect_segments(seed: int, count: int) -> list[dict]:
    """运行真实渲染管线,收集文本段落。

    流程: 随机开门 → 走 3-5 步 → 收集每步的文本 → 拆段。
    重复直到收集够 count 段。
    """
    # 设置种子,保证可复现
    os.environ["NOWHERE_SEED"] = str(seed)
    rng = random.Random(seed)

    all_segments: list[dict] = []
    max_attempts = count * 3  # 防止无限循环
    attempt = 0

    while len(all_segments) < count and attempt < max_attempts:
        attempt += 1
        try:
            # 随机开门
            result = await open_door_impl()
            if "error" in result.get("data", {}):
                continue

            # 走 3-5 步
            n_steps = rng.randint(3, 5)
            for _ in range(n_steps):
                direction = rng.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
                dist = rng.uniform(0.5, 3.0)
                try:
                    step_result = await walk_impl(direction, dist)
                    raw_text = step_result.get("text", "")
                    if not raw_text or len(raw_text) < 15:
                        continue

                    # 脱敏
                    blinded = _strip_place_names(raw_text)
                    # 拆段
                    segments = _segment_text(blinded)
                    for seg in segments:
                        if len(seg) >= 15:  # 太短的不要
                            all_segments.append({
                                "text": seg,
                                "seed": seed,
                                "attempt": attempt,
                            })
                except Exception:
                    continue
        except Exception:
            continue

    # 按 count 取前段
    return all_segments[:count]


# ── 输出 ────────────────────────────────────────────────────────────────

def _save_review_file(segments: list[dict], seed: int, out_dir: Path) -> Path:
    """保存盲评文件。"""
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}.md"

    lines: list[str] = [
        f"# 品味盲评 — {today}",
        "",
        f"种子: `{seed}` (用 `--seed {seed}` 可复现)",
        f"段落数: {len(segments)}",
        "",
        "---",
        "",
        "每段评一个字: **好** / **平** / **差** (愿意多写更好)",
        "",
        "---",
        "",
    ]

    for i, seg in enumerate(segments, 1):
        lines.append(f"## 段 {i}")
        lines.append("")
        lines.append(seg["text"])
        lines.append("")
        lines.append(f"> 评: ___")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.extend([
        "## 回填指引",
        "",
        "评完后:",
        "- **好** → 加入 `qa_lqa_golden.json` 作为 PASS 好样例",
        "- **平** / **差** → 加入 `qa_lqa_golden.json` 作为对应 S 级坏样例",
        "- 格式照现有条目: `{id, label, env, text, note}`",
        "- 产物只进 golden set,不直接改卡",
    ])

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ── 主函数 ──────────────────────────────────────────────────────────────

async def main_async(seed: int, count: int, out_dir: Path) -> None:
    print(f"开始采集 {count} 段盲评文本 (种子={seed}) ...")

    segments = await _collect_segments(seed, count)
    print(f"采集到 {len(segments)} 段")

    out_path = _save_review_file(segments, seed, out_dir)
    print(f"已保存: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="品味回路盲评抽样")
    parser.add_argument("--seed", type=int, default=None, help="随机种子(不给=真随机)")
    parser.add_argument("--count", type=int, default=10, help="抽样段数(默认 10)")
    parser.add_argument("--out", type=str, default=None, help="输出目录(默认 docs/taste_samples)")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    out_dir = Path(args.out) if args.out else _REPO / "docs" / "taste_samples"

    asyncio.run(main_async(seed, args.count, out_dir))


if __name__ == "__main__":
    main()
