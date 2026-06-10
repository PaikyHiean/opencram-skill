"""
prep_m.py — 为 M 思维导图切出"每章输入包"。

直接从 work/distilled/l1.json 读取已蒸馏内容，无需回溯原始 PPT。
每章输出 work/distilled/m/in_<k>.json，供子 agent 按主题归纳分支结构。

用法：
    python scripts/prep_m.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402

M_DIR = C.WORK_DIR / "distilled" / "m"
L1_JSON = C.WORK_DIR / "distilled" / "l1.json"


def flatten_points(points: list) -> list[str]:
    """把 point.text + point.details 展开为字符串列表，去空。"""
    out = []
    for pt in points:
        t = (pt.get("text") or "").strip()
        if t:
            out.append(t)
        for d in pt.get("details") or []:
            dt = (d.get("text") or "").strip()
            if dt:
                out.append(dt)
    return out


def main() -> int:
    l1 = C.read_json(L1_JSON)
    if not l1:
        raise SystemExit(f"未找到 {L1_JSON}，请先完成 L1 管线。")

    M_DIR.mkdir(parents=True, exist_ok=True)

    index = []
    for k, ch in enumerate(l1.get("chapters", []), start=1):
        ch_title = ch.get("title", f"第{k}章")
        sections = []
        for sec in ch.get("sections", []):
            label = (sec.get("label") or "").strip()
            heading = (sec.get("heading") or "").strip()
            pointer = (sec.get("pointer") or "").strip()
            pts = flatten_points(sec.get("points") or [])
            # 表格：仅保留第一行（表头）作为提示；tables 是 pipe-delimited 字符串列表
            tables = []
            for tbl in sec.get("tables") or []:
                if isinstance(tbl, str):
                    first_line = tbl.split("\n")[0].strip()
                    if first_line:
                        tables.append(first_line)
                elif isinstance(tbl, dict):
                    rows = tbl.get("rows") or []
                    if rows:
                        tables.append(" | ".join(str(c) for c in rows[0]))
            entry = {
                "label": label,
                "heading": heading,
                "pointer": pointer,
                "points": pts,
            }
            if tables:
                entry["table_hints"] = tables
            sections.append(entry)

        bundle = {
            "chapter_index": k,
            "chapter_title": ch_title,
            "section_count": len(sections),
            "sections": sections,
        }
        in_path = M_DIR / f"in_{k}.json"
        C.write_json(in_path, bundle)
        index.append({
            "k": k,
            "chapter_title": ch_title,
            "section_count": len(sections),
            "in": str(in_path),
            "out": str(M_DIR / f"out_{k}.json"),
        })

    C.write_json(M_DIR / "index.json", {"chapters": index})
    print("=== M 思维导图输入包已切好 ===")
    for it in index:
        print(f"  k={it['k']:>2}  {it['chapter_title']}  ({it['section_count']} 节)  -> {Path(it['in']).name}")
    print(f"\n→ {M_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
