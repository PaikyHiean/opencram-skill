"""
prep_ai_distill.py — 为 L1 的 AI 语义蒸馏切出"每章输入包"。

把每一章涉及的源文件 content.json 汇成一个精简包 work/distilled/ai/in_<k>.json，
供一个子 agent 只读这一章、产出 out_<k>.json。这样主控不必加载全文，子任务可并行。

输入包只含蒸馏所需字段（锚点/标题/段落/表格/图片名），去掉备注与图片二进制。
跳过废页。另写 ai/index.json 记录 k → 章标题、输入/输出文件名、规模。

用法：
    python scripts/prep_ai_distill.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402

AI_DIR = C.WORK_DIR / "distilled" / "ai"


def chapter_blocks(chapters_doc: dict):
    for ch in chapters_doc.get("chapters", []):
        yield (f"第{ch['chapter']}章 {ch['title']}", ch["files"])
    if chapters_doc.get("unfiled"):
        yield ("未归类 / 附录", chapters_doc["unfiled"])


def main() -> int:
    chapters_doc = C.read_json(C.CHAPTERS_PATH)
    if not chapters_doc:
        raise SystemExit(f"未找到 {C.CHAPTERS_PATH}，请先 detect_chapters。")
    AI_DIR.mkdir(parents=True, exist_ok=True)

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
                    "images": s.get("images", []),
                })
        bundle = {"chapter_index": k, "chapter_title": ch_title,
                  "slide_count": len(slides), "slides": slides}
        in_path = AI_DIR / f"in_{k}.json"
        C.write_json(in_path, bundle)
        index.append({"k": k, "chapter_title": ch_title,
                      "slides": len(slides),
                      "in": str(in_path), "out": str(AI_DIR / f"out_{k}.json")})

    C.write_json(AI_DIR / "index.json", {"chapters": index})
    print("=== AI 蒸馏输入包已切好 ===")
    for it in index:
        print(f"  k={it['k']:>2}  {it['chapter_title']}  ({it['slides']} 张)  -> {Path(it['in']).name}")
    print(f"\n→ {AI_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
