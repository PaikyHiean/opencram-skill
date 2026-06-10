"""
build_l0.py — 产物 L0：带书签的清洗版全集。

输入：work/pdf/<stem>.pdf（extract 已转好的逐源 PDF）、work/maps/<stem>.json
（含每页 decorative 提示与锚点）、work/drafts/chapters.json（锁定的章节图）。

动作：
  1. 按章节顺序合并各源 PDF；删除"疑似废页"（保守，--keep-all 可全保留）。
  2. 写章节书签（多文件章再加逐文件子书签）。
  3. 每页角盖中文来源戳（reportlab overlay + pypdf merge）。
  4. 产出 outputs/L0.pdf、work/l0_pagemap.json（锚点→L0页）、
     work/l0_deleted.json（删了哪些页 + 原因，供复核）。

注意：真实使用中章节图须先经用户确认锁定；此处直接读 chapters.json。
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402

L0_OUT = C.OUTPUTS_DIR / "L0.pdf"


# ---------------------------------------------------------------------------
# 来源戳 overlay（reportlab，内置中文 CID 字体 STSong-Light）
# ---------------------------------------------------------------------------

def _make_stamp(width: float, height: float, text: str) -> "PageObject":  # type: ignore[name-defined]
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from pypdf import PdfReader

    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    except Exception:  # noqa: BLE001  已注册则忽略
        pass

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    font_size = 8
    pad = 4
    tw = pdfmetrics.stringWidth(text, "STSong-Light", font_size)
    x, y = pad, pad  # 左下角
    # 半透明白底，避免压住内容看不清
    c.setFillColorRGB(1, 1, 1)
    try:
        c.setFillAlpha(0.6)
    except Exception:  # noqa: BLE001
        pass
    c.rect(x - 1, y - 1, tw + 2, font_size + 2, fill=1, stroke=0)
    try:
        c.setFillAlpha(1)
    except Exception:  # noqa: BLE001
        pass
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.setFont("STSong-Light", font_size)
    c.drawString(x, y + 1, text)
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


# ---------------------------------------------------------------------------
# 章节顺序展开
# ---------------------------------------------------------------------------

def _ordered_sources(chapters_doc: dict) -> list[dict]:
    """展开成 [{chapter_title, source_stem, source_name, is_chapter_head, is_source_head}]。"""
    items = []
    for ch in chapters_doc.get("chapters", []):
        title = f"第{ch['chapter']}章 {ch['title']}"
        for i, f in enumerate(ch["files"]):
            items.append({
                "chapter_title": title,
                "source_name": f["name"],
                "source_stem": Path(f["name"]).stem,
                "is_chapter_head": (i == 0),
                "is_source_head": True,
                "multi": ch["multi_file"],
            })
    # 未归类 → 附录
    unfiled = chapters_doc.get("unfiled", [])
    for i, f in enumerate(unfiled):
        items.append({
            "chapter_title": "未归类 / 附录",
            "source_name": f["name"],
            "source_stem": Path(f["name"]).stem,
            "is_chapter_head": (i == 0),
            "is_source_head": True,
            "multi": len(unfiled) > 1,
        })
    return items


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def build(keep_all: bool, stamp: bool) -> dict:
    from pypdf import PdfReader, PdfWriter

    chapters_doc = C.read_json(C.CHAPTERS_PATH)
    if not chapters_doc:
        raise SystemExit(f"未找到 {C.CHAPTERS_PATH}，请先运行 detect_chapters.py 并确认。")

    writer = PdfWriter()
    pagemap: dict[str, int] = {}       # anchor -> L0 页(1-based)
    deleted: list[dict] = []           # 删除清单
    outline_plan: list[tuple] = []     # (level, title, writer_page_index)
    warnings: list[str] = []
    open_readers = []                  # 保持 reader 存活直到写盘

    last_chapter = None
    final_page = 0  # 已写入 writer 的页数

    for item in _ordered_sources(chapters_doc):
        stem = item["source_stem"]
        mp = C.read_json(C.WORK_MAPS / f"{stem}.json")
        pdf_path = C.WORK_PDF / f"{stem}.pdf"
        if not mp or not pdf_path.exists():
            warnings.append(f"缺少 {stem} 的 PDF 或映射，跳过（请先 extract）。")
            continue

        reader = PdfReader(str(pdf_path))
        open_readers.append(reader)
        n_pages = len(reader.pages)
        aligned = mp.get("aligned")
        slides = mp.get("slides", [])

        # 章/源书签：后置记录，避免全废页源的书签指向上一章末页
        pages_before = final_page
        is_new_chapter = item["is_chapter_head"] and item["chapter_title"] != last_chapter
        if is_new_chapter:
            last_chapter = item["chapter_title"]

        if aligned:
            for s in slides:
                pno = s["pdf_page"]  # 1-based
                if pno is None or pno > n_pages:
                    continue
                if s.get("decorative") and not keep_all:
                    deleted.append({"anchor": s["anchor"], "l0_would_be": None,
                                    "reason": s.get("decorative_reason", "")})
                    continue
                writer.add_page(reader.pages[pno - 1])
                final_page += 1
                pagemap[s["anchor"]] = final_page
                if stamp:
                    _stamp_last(writer, C.stamp_text(item["source_name"], s["index"]))
        else:
            # 页数不齐：保守全保留，按 PDF 页位盖戳，锚点用页位近似
            warnings.append(f"{item['source_name']} 页数不齐，未删页、按 PDF 页位盖戳。")
            for pno in range(1, n_pages + 1):
                writer.add_page(reader.pages[pno - 1])
                final_page += 1
                anchor = C.make_anchor(item["source_name"], pno)
                pagemap[anchor] = final_page
                if stamp:
                    _stamp_last(writer, C.stamp_text(item["source_name"], pno))

        # 书签目标：有新页取第一新页（0-based），全废页回退到最后已有页
        bm_target = pages_before if final_page > pages_before else max(pages_before - 1, 0)
        if is_new_chapter:
            outline_plan.append((0, item["chapter_title"], bm_target))
        if item["multi"]:
            outline_plan.append((1, item["source_name"], bm_target))

    # 写书签
    parents = {}
    for level, title, page_idx in outline_plan:
        if level == 0:
            ref = writer.add_outline_item(title, page_idx)
            parents["_last_chapter"] = ref
        else:
            writer.add_outline_item(title, page_idx,
                                    parent=parents.get("_last_chapter"))

    C.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    with L0_OUT.open("wb") as f:
        writer.write(f)

    C.write_json(C.L0_PAGEMAP_PATH, {
        "output": str(L0_OUT),
        "total_pages": final_page,
        "anchor_to_l0_page": pagemap,
    })
    C.write_json(C.L0_DELETED_PATH, {
        "deleted_count": len(deleted),
        "kept_all": keep_all,
        "deleted": deleted,
    })

    return {"total_pages": final_page, "deleted": len(deleted),
            "warnings": warnings, "out": str(L0_OUT)}


def _stamp_last(writer, text: str) -> None:
    """给 writer 最新追加的那一页盖来源戳。"""
    page = writer.pages[-1]
    w = float(page.mediabox.width)
    h = float(page.mediabox.height)
    overlay = _make_stamp(w, h, text)
    page.merge_page(overlay)


def main() -> int:
    ap = argparse.ArgumentParser(description="开卷考 skill 产物 L0")
    ap.add_argument("--keep-all", action="store_true", help="不删废页，全部保留")
    ap.add_argument("--no-stamp", dest="stamp", action="store_false",
                    help="不盖来源戳（调试快出）")
    ap.set_defaults(stamp=True)
    args = ap.parse_args()

    C.ensure_dirs()
    r = build(args.keep_all, args.stamp)
    print("=== L0 构建完成 ===")
    print(f"  总页数：{r['total_pages']}")
    print(f"  删除废页：{r['deleted']}（清单见 {C.L0_DELETED_PATH}）")
    if r["warnings"]:
        print("  ⚠ 警告：")
        for w in r["warnings"]:
            print(f"    - {w}")
    print(f"  → {r['out']}")
    print(f"  → 锚点映射 {C.L0_PAGEMAP_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
