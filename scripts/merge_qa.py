"""
merge_qa.py — 把子 agent 的逐章 QA 抽取结果合并为 work/distilled/qa.json。

职责分离：
  - 子 agent（out_<k>.json）只负责**内容**：识别题目/答案、判断是否 AI 补答。
  - 本脚本（确定性）负责：题目编号、源指针生成、meta 字段填充。

out_<k>.json 约定 schema（子 agent 写）：
{
  "chapter_title": "...",
  "items": [
    { "type": "简答题",          // 简答题 | 论述题 | 案例题 | 其他
      "question": "题目文本（逐字）",
      "answer":   "答案文本（逐字来自 PPT，或 AI 补充）",
      "anchors":  ["文件名#s5"],  // 题目所在幻灯片，至少一个
      "ai_answer": false }        // true = 答案 AI 补充
  ]
}

用法：
    python scripts/prep_qa.py            # 1. 切输入包
    # 2. 子 agent 逐章产出 out_<k>.json
    python scripts/merge_qa.py           # 3. 合并
    python scripts/render.py qa          # 4. 渲染
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402
from distill_l1 import _pointer  # noqa: E402

QA_DIR = C.WORK_DIR / "distilled" / "qa"
QA_JSON = C.WORK_DIR / "distilled" / "qa.json"


def build_chapter(out: dict, reference_base: str, l0map: dict) -> dict:
    items = []
    for i, item in enumerate(out.get("items", []), start=1):
        anchors = item.get("anchors") or []
        if anchors:
            ptr = _pointer(anchors, reference_base, l0map)
        else:
            ptr = "源：—"
        items.append({
            "type": item.get("type", "简答题"),
            "num": f"Q{i}.",
            "question": item.get("question", ""),
            "answer": item.get("answer", ""),
            "pointer": ptr,
            "ai_answer": bool(item.get("ai_answer", False)),
        })
    return {"title": out.get("chapter_title", ""), "items": items}


def main() -> int:
    index = C.read_json(QA_DIR / "index.json")
    if not index:
        raise SystemExit(f"未找到 {QA_DIR/'index.json'}，请先运行 prep_qa.py。")

    cfg = C.load_config()
    reference_base = cfg.get("reference_base", "source")
    l0map = C.read_json(C.L0_PAGEMAP_PATH, {}) or {}
    chapters_doc = C.read_json(C.CHAPTERS_PATH, {}) or {}

    chapters = []
    ai_chapters: list[str] = []
    total_items = 0

    for it in index["chapters"]:
        k = it["k"]
        out_path = QA_DIR / f"out_{k}.json"
        out = C.read_json(out_path)
        if not out:
            continue
        ch = build_chapter(out, reference_base, l0map)
        if ch["items"]:
            chapters.append(ch)
            total_items += len(ch["items"])
            if any(i["ai_answer"] for i in ch["items"]):
                ai_chapters.append(ch["title"])

    qa = {
        "meta": {
            "product": "QA",
            "title": "简答/论述 QA 记录",
            "layout": "portrait-single",
            "reference_base": reference_base,
            "cjk_font": cfg.get("cjk_font", "Microsoft YaHei"),
            "cjk_serif": cfg.get("cjk_font_serif", "SimSun"),
            "source_folder": chapters_doc.get("source_folder", ""),
            "total_items": total_items,
            "ai_answer_chapters": ai_chapters,
        },
        "chapters": chapters,
    }
    C.write_json(QA_JSON, qa)

    print("=== QA 合并完成 ===")
    print(f"  章数：{len(chapters)}  题目总数：{total_items}")
    if ai_chapters:
        print(f"  含 AI 补答章节：{', '.join(ai_chapters)}")
    print(f"  → {QA_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
