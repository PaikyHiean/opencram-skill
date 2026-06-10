"""
merge_l2.py — 把子 agent 的逐章关键词抽取结果合并为 work/distilled/l2.json。

职责分离：
  - 子 agent（out_<k>.json）只负责**内容**：识别关键词、分级、摘录定义。
  - 本脚本（确定性）负责：源指针生成、章内排序（高>中>低，同级按术语字符顺序）。

out_<k>.json 约定 schema（子 agent 写）：
{
  "chapter_title": "...",
  "terms": [
    { "term": "近因原则",
      "freq": "高",         // 高 | 中 | 低
      "definition": "...", // PPT 原文摘录；无则空字符串
      "anchors": ["文件名#s5"] }
  ]
}

用法：
    python scripts/prep_l2.py            # 1. 切输入包
    # 2. 子 agent 逐章产出 out_<k>.json
    python scripts/merge_l2.py           # 3. 合并
    python scripts/render.py l2          # 4. 渲染
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402
from distill_l1 import _pointer  # noqa: E402

L2_DIR = C.WORK_DIR / "distilled" / "l2"
L2_JSON = C.WORK_DIR / "distilled" / "l2.json"

FREQ_ORDER = {"高": 0, "中": 1, "低": 2}


def build_chapter(out: dict, reference_base: str, l0map: dict) -> dict:
    raw_terms = out.get("terms", [])
    # 章内排序：高 > 中 > 低，同频级按术语字符顺序（Unicode 近似排序）
    raw_terms.sort(key=lambda t: (FREQ_ORDER.get(t.get("freq", "低"), 2), t.get("term", "")))

    terms = []
    for item in raw_terms:
        anchors = item.get("anchors") or []
        ptr = _pointer(anchors, reference_base, l0map) if anchors else "源：—"
        terms.append({
            "term": item.get("term", ""),
            "freq": item.get("freq", "低"),
            "definition": item.get("definition", ""),
            "pointer": ptr,
        })
    return {"title": out.get("chapter_title", ""), "terms": terms}


def main() -> int:
    index = C.read_json(L2_DIR / "index.json")
    if not index:
        raise SystemExit(f"未找到 {L2_DIR / 'index.json'}，请先运行 prep_l2.py。")

    cfg = C.load_config()
    reference_base = cfg.get("reference_base", "source")
    l0map = C.read_json(C.L0_PAGEMAP_PATH, {}) or {}
    chapters_doc = C.read_json(C.CHAPTERS_PATH, {}) or {}

    chapters = []
    total_terms = 0
    freq_counts: dict[str, int] = {"高": 0, "中": 0, "低": 0}

    for it in index["chapters"]:
        k = it["k"]
        out_path = L2_DIR / f"out_{k}.json"
        out = C.read_json(out_path)
        if not out:
            continue
        ch = build_chapter(out, reference_base, l0map)
        if ch["terms"]:
            chapters.append(ch)
            total_terms += len(ch["terms"])
            for t in ch["terms"]:
                freq_counts[t.get("freq", "低")] = freq_counts.get(t.get("freq", "低"), 0) + 1

    l2 = {
        "meta": {
            "product": "L2",
            "title": "关键词索引",
            "layout": "portrait-two-column",
            "reference_base": reference_base,
            "cjk_font": cfg.get("cjk_font", "Microsoft YaHei"),
            "cjk_serif": cfg.get("cjk_font_serif", "SimSun"),
            "source_folder": chapters_doc.get("source_folder", ""),
            "total_terms": total_terms,
        },
        "chapters": chapters,
    }
    C.write_json(L2_JSON, l2)

    print("=== L2 合并完成 ===")
    print(f"  章数：{len(chapters)}  词条总数：{total_terms}")
    print(f"  频率分布：高 {freq_counts.get('高', 0)} / 中 {freq_counts.get('中', 0)} / 低 {freq_counts.get('低', 0)}")
    print(f"  → {L2_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
