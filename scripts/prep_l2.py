"""
prep_l2.py — 为 L2 关键词索引切出"每章输入包"。

把每一章涉及的源文件 content.json 汇成精简包 work/distilled/l2/in_<k>.json，
供子 agent 只读这一章、抽取高/中/低频关键词/术语、产出 out_<k>.json。

与 QA 包相比，L2 包不含备注（关键词判断不依赖备注），但保留表格（定义常藏表中）。

用法：
    python scripts/prep_l2.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402

L2_DIR = C.WORK_DIR / "distilled" / "l2"


def chapter_blocks(chapters_doc: dict):
    for ch in chapters_doc.get("chapters", []):
        yield (f"第{ch['chapter']}章 {ch['title']}", ch["files"])
    if chapters_doc.get("unfiled"):
        yield ("未归类 / 附录", chapters_doc["unfiled"])


def main() -> int:
    chapters_doc = C.read_json(C.CHAPTERS_PATH)
    if not chapters_doc:
        raise SystemExit(f"未找到 {C.CHAPTERS_PATH}，请先运行 detect_chapters。")
    L2_DIR.mkdir(parents=True, exist_ok=True)

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
                    # 不含 notes —— 关键词提取不依赖备注
                })
        bundle = {
            "chapter_index": k,
            "chapter_title": ch_title,
            "slide_count": len(slides),
            "slides": slides,
        }
        in_path = L2_DIR / f"in_{k}.json"
        C.write_json(in_path, bundle)
        index.append({
            "k": k,
            "chapter_title": ch_title,
            "slides": len(slides),
            "in": str(in_path),
            "out": str(L2_DIR / f"out_{k}.json"),
        })

    C.write_json(L2_DIR / "index.json", {"chapters": index})
    print("=== L2 输入包已切好 ===")
    for it in index:
        print(f"  k={it['k']:>2}  {it['chapter_title']}  ({it['slides']} 张)  -> {Path(it['in']).name}")
    print(f"\n→ {L2_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
