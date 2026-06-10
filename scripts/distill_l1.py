"""
distill_l1.py — 产物 L1 的蒸馏（确定性·结构保留）。

读 work/extracted/<stem>/content.json + chapters.json + l0_pagemap.json，
按 PPT 自身的「幻灯片标题 + 项目符号缩进层级」机械重建大纲，产出
work/distilled/l1.json 供 render.py 渲染。

层级映射（零臆造，只重排不新增）：
    章          ← chapters.json
    一、二、…   ← 幻灯片标题（无标题则取首个 level-0 段落）；连续同标题幻灯片自动合并
    1. 2. …     ← level-0 项目符号
    明细（缩进）← level≥1 项目符号，挂在所属 1./2. 之下
源指针只标在**节级**（一、二…），节内小知识点不再逐条标注。

精简档（--level，仅做"裁深度"，不改写文本）：
    conservative（默认）：全保留。
    standard            ：保留 1./2. + level-1 明细，丢更深层。
    aggressive          ：只保留 1./2. 标题行，去明细。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402

DISTILLED_DIR = C.WORK_DIR / "distilled"
L1_JSON = DISTILLED_DIR / "l1.json"

_TYPST_IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
_UNITS = "零一二三四五六七八九"


def int_to_cn(n: int) -> str:
    """1..99 → 中文数字；100+ 退回阿拉伯数字。"""
    if n <= 0:
        return str(n)
    if n < 10:
        return _UNITS[n]
    if n < 20:
        return "十" + (_UNITS[n - 10] if n > 10 else "")
    if n < 100:
        t, o = divmod(n, 10)
        return _UNITS[t] + "十" + (_UNITS[o] if o else "")
    return str(n)


def _rel_images(stem: str, images: list[str], cap: int) -> list[str]:
    out = []
    for fn in images:
        if Path(fn).suffix.lower() in _TYPST_IMG_EXTS:
            out.append(f"/work/extracted/{stem}/images/{fn}")
        if len(out) >= cap:
            break
    return out


def _build_points(paragraphs: list[dict], level: str) -> list[dict]:
    """把 [{text,level}] 重建成 [{text, details:[{text,level}]}]。"""
    points: list[dict] = []
    cur: dict | None = None
    for p in paragraphs:
        if p["level"] == 0:
            cur = {"text": p["text"], "details": []}
            points.append(cur)
        else:
            if cur is None:  # 开头就缩进 → 提升为一个点
                cur = {"text": p["text"], "details": []}
                points.append(cur)
            else:
                cur["details"].append({"text": p["text"], "level": p["level"]})
    # 按精简档裁深度
    if level == "aggressive":
        for pt in points:
            pt["details"] = []
    elif level == "standard":
        for pt in points:
            pt["details"] = [d for d in pt["details"] if d["level"] <= 1]
    return points


def _pointer(anchors: list[str], reference_base: str, l0map: dict) -> str:
    name, i0 = C.parse_anchor(anchors[0])
    _, i1 = C.parse_anchor(anchors[-1])
    if reference_base == "l0":
        a2p = (l0map or {}).get("anchor_to_l0_page", {})
        p0, p1 = a2p.get(anchors[0]), a2p.get(anchors[-1])
        if p0:
            return f"L0 p.{p0}" + (f"–{p1}" if p1 and p1 != p0 else "")
    rng = f"s.{i0}" + (f"–{i1}" if i1 != i0 else "")
    return f"源：{name} {rng}"


def distill(level: str, with_images: bool, img_cap: int) -> dict:
    cfg = C.load_config()
    reference_base = cfg.get("reference_base", "source")
    l0map = C.read_json(C.L0_PAGEMAP_PATH, {}) or {}
    chapters_doc = C.read_json(C.CHAPTERS_PATH)
    if not chapters_doc:
        raise SystemExit(f"未找到 {C.CHAPTERS_PATH}，请先 detect_chapters 并确认。")

    def chapter_blocks():
        for ch in chapters_doc.get("chapters", []):
            yield (f"第{ch['chapter']}章 {ch['title']}", ch["files"])
        if chapters_doc.get("unfiled"):
            yield ("未归类 / 附录", chapters_doc["unfiled"])

    out_chapters = []
    n_sections = 0
    for ch_title, files in chapter_blocks():
        sections: list[dict] = []
        roman = 0
        for f in files:
            stem = Path(f["name"]).stem
            content = C.read_json(C.WORK_EXTRACTED / stem / "content.json")
            if not content:
                continue
            last: dict | None = None  # 仅在同一文件内合并连续同标题
            for s in content["slides"]:
                if s.get("decorative"):
                    continue
                heading = s["title"].strip()
                paras = list(s.get("paragraphs", []))
                if not heading:  # 无标题：首个 level-0 段落充当小节标题
                    if paras and paras[0]["level"] == 0:
                        heading = paras[0]["text"]
                        paras = paras[1:]
                    else:
                        heading = "（无标题）"
                points = _build_points(paras, level)
                imgs = _rel_images(stem, s["images"], img_cap) if with_images else []
                if not (points or imgs or s.get("tables")):
                    continue
                # 合并：与上一节同标题（同文件）则并入
                if last is not None and heading and heading == last["heading"]:
                    last["points"].extend(points)
                    last["anchors"].append(s["anchor"])
                    last["tables"].extend(s.get("tables", []))
                    last["images"].extend(imgs)
                else:
                    roman += 1
                    n_sections += 1
                    last = {
                        "label": f"{int_to_cn(roman)}、",
                        "heading": heading,
                        "anchors": [s["anchor"]],
                        "points": points,
                        "tables": list(s.get("tables", [])),
                        "images": imgs,
                        "ai_generated": False,  # 基线纯抽取；AI 增强改写时置 True
                    }
                    sections.append(last)
        # 收尾：编号 + 指针 + 清理内部字段
        for sec in sections:
            for i, pt in enumerate(sec["points"], 1):
                pt["num"] = f"{i}."
            sec["pointer"] = _pointer(sec["anchors"], reference_base, l0map)
            del sec["anchors"]
        out_chapters.append({"title": ch_title, "sections": sections})

    return {
        "meta": {
            "product": "L1",
            "title": "核心知识手册",
            "layout": "portrait-single",
            "compression": level,
            "reference_base": reference_base,
            "cjk_font": cfg.get("cjk_font", "Microsoft YaHei"),
            "cjk_serif": cfg.get("cjk_font_serif", "SimSun"),
            "source_folder": chapters_doc.get("source_folder", ""),
            "total_sections": n_sections,
            "distiller": "deterministic-structure-preserving (纯抽取)",
        },
        "chapters": out_chapters,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="开卷考 skill L1 蒸馏（确定性·结构保留）")
    ap.add_argument("--level", choices=["conservative", "standard", "aggressive"],
                    default=None, help="精简力度，默认取 config 或 conservative")
    ap.add_argument("--no-images", dest="with_images", action="store_false",
                    help="不内嵌图片（先验证文本链路）")
    ap.add_argument("--img-cap", type=int, default=2, help="每节最多内嵌图片数")
    ap.set_defaults(with_images=True)
    args = ap.parse_args()

    level = args.level or C.load_config().get("compression", "conservative")
    data = distill(level, args.with_images, args.img_cap)
    C.write_json(L1_JSON, data)
    print(f"=== L1 蒸馏完成（{level}，结构保留·纯抽取）===")
    print(f"  章数：{len(data['chapters'])}  小节：{data['meta']['total_sections']}")
    print(f"  参考基准：{data['meta']['reference_base']}")
    print(f"  → {L1_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
