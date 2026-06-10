"""
merge_ai_l1.py — 把子 agent 的逐章 AI 蒸馏结果拼回 work/distilled/l1.json。

职责分离：
  - 子 agent（out_<k>.json）只负责**内容**：挑核心、去重、凝练、写小节标题，正文逐字。
  - 本脚本（确定性）负责**机械正确**：一、二编号、节级源指针、1./2. 编号、
    内嵌图按锚点回查原图、参考基准换算。AI 不碰这些，避免指错页/编错号。

流程：先跑 distill_l1.py 得到确定性基线 l1.json 作兜底；本脚本按章覆盖：
某章有 out_<k>.json 就用 AI 版，没有就保留基线版。

out_<k>.json 约定 schema（子 agent 写）：
{
  "chapter_title": "...",
  "sections": [
    { "heading": "概念",
      "anchors": ["<文件名>#s2", "<文件名>#s3"],   // 该节用到的源幻灯片锚点（必须来自输入）
      "points": [ {"text": "逐字定义/论断...", "details": ["逐字子项...", ...]}, ... ],
      "tables": ["可选，逐字表格"],
      "ai_generated": true }    // 选取/归并/改写均算 AI 判断，置 true
  ]
}

用法：
    python scripts/prep_ai_distill.py        # 1. 切输入包
    python scripts/distill_l1.py             # 2. 基线兜底
    # 3. 子 agent 逐章产出 out_<k>.json
    python scripts/merge_ai_l1.py            # 4. 拼回 l1.json
    python scripts/render.py l1
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402
from distill_l1 import int_to_cn, _pointer, _rel_images, L1_JSON  # noqa: E402

# AI 有时照搬 PPT 原有序号（"8、…" "9. …"），strip 掉避免与 merge 追加的 "j." 重复。
# 匹配：纯数字 + 顿号/句号（句号后不跟数字，避免误删小数点）
_RE_PT_PREFIX = re.compile(r'^\d+(?:[、。]|\.(?!\d))\s*')

AI_DIR = C.WORK_DIR / "distilled" / "ai"


class _ContentCache:
    """按源 stem 缓存 content.json，供按锚点回查原图。"""

    def __init__(self) -> None:
        self._cache: dict[str, dict] = {}

    def slide_images(self, anchor: str) -> tuple[str, list[str]]:
        name, idx = C.parse_anchor(anchor)
        stem = Path(name).stem
        if stem not in self._cache:
            self._cache[stem] = C.read_json(
                C.WORK_EXTRACTED / stem / "content.json", {}) or {}
        content = self._cache[stem]
        for s in content.get("slides", []):
            if s["index"] == idx:
                return stem, s.get("images", [])
        return stem, []


def _section_images(anchors: list[str], cache: _ContentCache, cap: int) -> list[str]:
    """按该节锚点回查原图，过滤 Typst 支持格式并限量。"""
    rels: list[str] = []
    for a in anchors:
        stem, imgs = cache.slide_images(a)
        rels.extend(_rel_images(stem, imgs, cap))
        if len(rels) >= cap:
            break
    return rels[:cap]


def build_ai_chapter(out: dict, reference_base: str, l0map: dict,
                     cache: _ContentCache, img_cap: int) -> dict:
    sections = []
    for i, sec in enumerate(out.get("sections", []), start=1):
        anchors = sec.get("anchors") or []
        points = []
        for j, pt in enumerate(sec.get("points", []), start=1):
            details = [{"text": d, "level": 1} for d in pt.get("details", [])]
            clean_text = _RE_PT_PREFIX.sub("", pt.get("text", "")).strip()
            points.append({"num": f"{j}.", "text": clean_text,
                           "details": details})
        sections.append({
            "label": f"{int_to_cn(i)}、",
            "heading": sec.get("heading", "（无标题）"),
            "pointer": _pointer(anchors, reference_base, l0map) if anchors else "源：—",
            "points": points,
            "tables": sec.get("tables", []),
            "images": _section_images(anchors, cache, img_cap) if anchors else [],
            "ai_generated": bool(sec.get("ai_generated", True)),
        })
    return {"title": out.get("chapter_title", ""), "sections": sections}


def main() -> int:
    baseline = C.read_json(L1_JSON)
    if not baseline:
        raise SystemExit(f"未找到基线 {L1_JSON}，请先运行 distill_l1.py。")
    index = C.read_json(AI_DIR / "index.json")
    if not index:
        raise SystemExit(f"未找到 {AI_DIR/'index.json'}，请先运行 prep_ai_distill.py。")

    meta = baseline["meta"]
    reference_base = meta.get("reference_base", "source")
    l0map = C.read_json(C.L0_PAGEMAP_PATH, {}) or {}
    cache = _ContentCache()

    chapters = list(baseline["chapters"])  # 兜底基线，逐章可被 AI 覆盖
    ai_done = []
    for it in index["chapters"]:
        k = it["k"]
        out_path = AI_DIR / f"out_{k}.json"
        out = C.read_json(out_path)
        if not out:
            continue  # 该章未蒸馏，保留基线
        chapters[k - 1] = build_ai_chapter(out, reference_base, l0map, cache, img_cap=3)
        ai_done.append(it["chapter_title"])

    n_sections = sum(len(c["sections"]) for c in chapters)
    meta = dict(meta)
    meta["distiller"] = "ai-semantic + deterministic-fallback"
    meta["ai_chapters"] = ai_done
    meta["total_sections"] = n_sections
    C.write_json(L1_JSON, {"meta": meta, "chapters": chapters})

    print("=== AI 蒸馏合并完成 ===")
    print(f"  AI 蒸馏章节（{len(ai_done)}）：{', '.join(ai_done) or '无'}")
    print(f"  其余保留确定性基线。总小节：{n_sections}")
    print(f"  → {L1_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
