"""
merge_m.py — 把子 agent 的逐章思维导图抽取结果与全局总览合并为 work/distilled/m.json。

职责分离：
  - 子 agent（out_<k>.json）：按主题归纳分支，产出 branches + nodes
  - 全局 agent（out_global.json）：汇总所有章节的分支标题，产出 course_title + 章节摘要
  - 本脚本（确定性）：合并，验证完整性，写 m.json

用法：
    python scripts/prep_m.py              # 1. 切输入包
    # 2. 子 agent 逐章产出 out_<k>.json + 全局 agent 产出 out_global.json
    python scripts/merge_m.py             # 3. 合并
    python scripts/render.py m            # 4. 渲染
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402

M_DIR = C.WORK_DIR / "distilled" / "m"
M_JSON = C.WORK_DIR / "distilled" / "m.json"


def main() -> int:
    index = C.read_json(M_DIR / "index.json")
    if not index:
        raise SystemExit(f"未找到 {M_DIR / 'index.json'}，请先运行 prep_m.py。")

    global_data = C.read_json(M_DIR / "out_global.json")
    if not global_data:
        raise SystemExit(f"未找到 {M_DIR / 'out_global.json'}，请先运行全局总览 agent。")

    cfg = C.load_config()
    chapters_doc = C.read_json(C.CHAPTERS_PATH, {}) or {}

    chapters = []
    total_branches = 0
    total_nodes = 0
    missing = []

    for it in index["chapters"]:
        k = it["k"]
        out_path = M_DIR / f"out_{k}.json"
        out = C.read_json(out_path)
        if not out:
            missing.append(k)
            continue

        branches = out.get("branches", [])
        ch = {
            "chapter_index": out.get("chapter_index", k),
            "chapter_title": out.get("chapter_title", it["chapter_title"]),
            "branches": branches,
        }
        chapters.append(ch)
        total_branches += len(branches)
        total_nodes += sum(len(b.get("nodes", [])) for b in branches)

    if missing:
        print(f"⚠ 以下章节 agent 输出缺失，已跳过：k = {missing}")

    m_data = {
        "meta": {
            "product": "M",
            "title": "思维导图",
            "course_title": global_data.get("course_title", "课程总览"),
            "layout": "portrait-mindmap",
            "cjk_font": cfg.get("cjk_font", "Microsoft YaHei"),
            "cjk_serif": cfg.get("cjk_font_serif", "SimSun"),
            "source_folder": chapters_doc.get("source_folder", ""),
            "total_chapters": len(chapters),
            "total_branches": total_branches,
            "total_nodes": total_nodes,
        },
        "global": global_data,
        "chapters": chapters,
    }
    C.write_json(M_JSON, m_data)

    print("=== M 思维导图合并完成 ===")
    print(f"  章数：{len(chapters)}  分支总数：{total_branches}  节点总数：{total_nodes}")
    print(f"  课程：{global_data.get('course_title', '?')}")
    print(f"  → {M_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
