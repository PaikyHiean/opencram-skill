"""
merge_c.py — 把子 agent 的逐章速查卡抽取结果合并为 work/distilled/c.json。

职责分离：
  - 子 agent（out_<k>.json）只负责**内容**：识别卡片类型、抽取规则/流程/表格/公式。
  - 本脚本（确定性）负责：源指针生成、章内排序（公式>规则>对比>流程）。

out_<k>.json 约定 schema（子 agent 写）：
{
  "chapter_title": "...",
  "cards": [
    { "type": "formula",
      "label": "保费计算公式",
      "body": "应缴保费 = 保险金额 × 保险费率",
      "anchors": ["文件名#s12"] }
  ]
}

用法：
    python scripts/prep_c.py            # 1. 切输入包
    # 2. 子 agent 逐章产出 out_<k>.json
    python scripts/merge_c.py           # 3. 合并
    python scripts/render.py c          # 4. 渲染
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402
from distill_l1 import _pointer  # noqa: E402

C_DIR = C.WORK_DIR / "distilled" / "c"
C_JSON = C.WORK_DIR / "distilled" / "c.json"

# 章内排序：公式最精确（优先查）→ 规则 → 对比表 → 流程
TYPE_ORDER = {"formula": 0, "rule": 1, "table": 2, "flow": 3}


def build_chapter(out: dict, reference_base: str, l0map: dict) -> dict:
    raw_cards = out.get("cards", [])
    raw_cards.sort(key=lambda c: (
        TYPE_ORDER.get(c.get("type", "rule"), 1),
        c.get("label", ""),
    ))

    cards = []
    for item in raw_cards:
        anchors = item.get("anchors") or []
        ptr = _pointer(anchors, reference_base, l0map) if anchors else "源：—"
        cards.append({
            "type": item.get("type", "rule"),
            "label": item.get("label", ""),
            "body": item.get("body", ""),
            "pointer": ptr,
        })
    return {"title": out.get("chapter_title", ""), "cards": cards}


def main() -> int:
    index = C.read_json(C_DIR / "index.json")
    if not index:
        raise SystemExit(f"未找到 {C_DIR / 'index.json'}，请先运行 prep_c.py。")

    cfg = C.load_config()
    reference_base = cfg.get("reference_base", "source")
    l0map = C.read_json(C.L0_PAGEMAP_PATH, {}) or {}
    chapters_doc = C.read_json(C.CHAPTERS_PATH, {}) or {}

    chapters = []
    total_cards = 0
    type_counts: dict[str, int] = {"formula": 0, "rule": 0, "table": 0, "flow": 0}

    for it in index["chapters"]:
        k = it["k"]
        out_path = C_DIR / f"out_{k}.json"
        out = C.read_json(out_path)
        if not out:
            continue
        ch = build_chapter(out, reference_base, l0map)
        if ch["cards"]:
            chapters.append(ch)
            total_cards += len(ch["cards"])
            for card in ch["cards"]:
                t = card.get("type", "rule")
                type_counts[t] = type_counts.get(t, 0) + 1

    c_data = {
        "meta": {
            "product": "C",
            "title": "速查卡",
            "layout": "portrait-single-column",
            "reference_base": reference_base,
            "cjk_font": cfg.get("cjk_font", "Microsoft YaHei"),
            "cjk_serif": cfg.get("cjk_font_serif", "SimSun"),
            "source_folder": chapters_doc.get("source_folder", ""),
            "total_cards": total_cards,
            "total_chapters": len(chapters),
        },
        "chapters": chapters,
    }
    C.write_json(C_JSON, c_data)

    print("=== C 速查卡合并完成 ===")
    print(f"  章数：{len(chapters)}  卡片总数：{total_cards}")
    print(f"  类型分布：公式 {type_counts.get('formula', 0)} / 规则 {type_counts.get('rule', 0)} "
          f"/ 对比 {type_counts.get('table', 0)} / 流程 {type_counts.get('flow', 0)}")
    print(f"  → {C_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
