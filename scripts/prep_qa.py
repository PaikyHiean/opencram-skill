"""
prep_qa.py — 为 QA 简答库切出"每章输入包"。

把每一章涉及的源文件 content.json 汇成精简包 work/distilled/qa/in_<k>.json，
供子 agent 只读这一章、识别题目/答案、产出 out_<k>.json。

与 L1 输入包相比，QA 包额外保留幻灯片备注（notes），因为
简答题/案例题答案常藏在备注栏里。

用法：
    python scripts/prep_qa.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402

QA_DIR = C.WORK_DIR / "distilled" / "qa"


def chapter_blocks(chapters_doc: dict):
    for ch in chapters_doc.get("chapters", []):
        yield (f"第{ch['chapter']}章 {ch['title']}", ch["files"])
    if chapters_doc.get("unfiled"):
        yield ("未归类 / 附录", chapters_doc["unfiled"])


def main() -> int:
    chapters_doc = C.read_json(C.CHAPTERS_PATH)
    if not chapters_doc:
        raise SystemExit(f"未找到 {C.CHAPTERS_PATH}，请先运行 detect_chapters。")
    QA_DIR.mkdir(parents=True, exist_ok=True)

    index = []
    for k, (ch_title, files) in enumerate(chapter_blocks(chapters_doc), start=1):
        slides = []
        for f in files:
            stem = Path(f["name"]).stem
            content = C.read_json(C.WORK_EXTRACTED / stem / "content.json")
            if not content:
                continue
            for s in content["slides"]:
                if s.get("decorative"):
                    continue
                slides.append({
                    "anchor": s["anchor"],
                    "title": s["title"],
                    "paragraphs": s.get("paragraphs", []),
                    "tables": s.get("tables", []),
                    "notes": s.get("notes", ""),  # 备注里常藏答案
                })
        bundle = {
            "chapter_index": k,
            "chapter_title": ch_title,
            "slide_count": len(slides),
            "slides": slides,
        }
        in_path = QA_DIR / f"in_{k}.json"
        C.write_json(in_path, bundle)
        index.append({
            "k": k,
            "chapter_title": ch_title,
            "slides": len(slides),
            "in": str(in_path),
            "out": str(QA_DIR / f"out_{k}.json"),
        })

    C.write_json(QA_DIR / "index.json", {"chapters": index})
    print("=== QA 输入包已切好 ===")
    for it in index:
        print(f"  k={it['k']:>2}  {it['chapter_title']}  ({it['slides']} 张)  -> {Path(it['in']).name}")
    print(f"\n→ {QA_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
