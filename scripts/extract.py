"""
extract.py — Phase 4 抽取（确定性，按文件处理）。

对每个源文件：
  1. LibreOffice 转 PDF（建 L0 页空间；1 幻灯片 ≈ 1 PDF 页）。
  2. 旧版 .ppt 先转 .pptx 供 python-pptx 读取；.pptx 直接读原件；.pdf 走 pypdf。
  3. 抽取逐页：标题 / 正文（含表格、备注）/ 内嵌图片（原样抠出 blob）。
  4. 建立锚点映射 (源文件名, 源内页序号 1-based) → PDF 页号，落 work/maps/。
  5. 写归一化 markdown 到 work/extracted/<stem>/slides.md，图片存 images/。
  6. 文字层确认：抽取后总字符近零 → 标记疑似扫描件（本期不 OCR），warning。

铁律：只抽取、不臆造。图原样抠取，绝不重绘。

用法：
    python scripts/extract.py                 # 处理 manifest 中全部源
    python scripts/extract.py --only 第六章   # 只处理名字含该子串的源（调试用）
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402

TEXT_LAYER_MIN_CHARS = 30

# 废页判定（保守：宁可少删，删了也全部列入清单供复核）。
_DECOR_KEYWORDS = ["谢谢", "感谢", "致谢", "thank you", "thanks",
                   "参考文献", "references", "本章结束", "本章小结结束",
                   "the end", "课程结束", "敬请批评指正"]


def _decorative_hint(slide: dict) -> tuple[bool, str]:
    """返回 (是否疑似废页, 原因)。仅判定高置信的纯装饰页，纯案例不自动删。"""
    chars = slide["text_chars"]
    n_img = len(slide["images"])
    if chars == 0 and n_img == 0:
        return True, "空白页"
    blob = (slide["title"] + slide["body"]).lower()
    if chars < 60:
        for kw in _DECOR_KEYWORDS:
            if kw.lower() in blob:
                return True, f"含'{kw}'且文本极少"
    return False, ""


# ---------------------------------------------------------------------------
# LibreOffice 转换
# ---------------------------------------------------------------------------

def _lo_profile_arg() -> str:
    """独立 user profile，避免与已开的 LibreOffice 实例抢锁，并允许并行。"""
    prof = (C.WORK_DIR / ".lo_profile").resolve()
    uri = prof.as_uri()  # file:///F:/.../work/.lo_profile
    return f"-env:UserInstallation={uri}"


def convert(soffice: str, src: Path, fmt: str, outdir: Path,
            timeout: int = 180) -> Path | None:
    """用 LibreOffice 把 src 转成 fmt（'pdf'/'pptx'），输出到 outdir。
    返回输出文件路径；失败返回 None。已存在且比源新则复用（缓存，避免重跑慢转换）。"""
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / (src.stem + "." + fmt)
    if out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
        return out
    cmd = [soffice, _lo_profile_arg(), "--headless", "--norestore",
           "--convert-to", fmt, "--outdir", str(outdir), str(src)]
    try:
        # LibreOffice 在 Windows 的 stdout/stderr 是 GBK，errors=replace 防解码崩溃
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        C.eprint(f"  ! 转换超时（{timeout}s）：{src.name} -> {fmt}")
        return None
    if out.exists():
        return out
    C.eprint(f"  ! 转换失败：{src.name} -> {fmt}\n    stdout={r.stdout.strip()}\n    stderr={r.stderr.strip()}")
    return None


# ---------------------------------------------------------------------------
# python-pptx 抽取（递归处理组合形状）
# ---------------------------------------------------------------------------

def _iter_shapes(shapes):
    """深度遍历，展开 group。"""
    for shape in shapes:
        if shape.shape_type == 6:  # MSO_SHAPE_TYPE.GROUP
            yield from _iter_shapes(shape.shapes)
        else:
            yield shape


def _extract_pptx_slide(slide, img_dir: Path, idx: int) -> dict:
    from pptx.util import Emu  # noqa: F401  (确保 pptx 可用)

    title = ""
    title_shape = None
    title_extra: list[dict] = []   # 标题占位符里第一段之外的段落，降为正文
    # 标题占位符：只取第一段作小节标题，其余段落当正文（避免多行标题变大块）
    try:
        title_shape = slide.shapes.title
        if title_shape:
            tparas = [p.text.strip() for p in title_shape.text_frame.paragraphs
                      if p.text.strip()]
            if tparas:
                title = tparas[0]
                title_extra = [{"text": t, "level": 0} for t in tparas[1:]]
    except Exception:  # noqa: BLE001
        title_shape = None

    paragraphs: list[dict] = list(title_extra)  # [{text, level}]，保留缩进层级
    table_parts: list[str] = []
    images: list[str] = []

    img_n = 0
    for shape in _iter_shapes(slide.shapes):
        if title_shape is not None and shape is title_shape:
            continue  # 标题单独处理，正文不重复
        # 文本：逐段保留缩进层级（para.level 0~8）
        if getattr(shape, "has_text_frame", False):
            for para in shape.text_frame.paragraphs:
                t = para.text.strip()
                if not t:
                    continue
                lvl = int(getattr(para, "level", 0) or 0)
                paragraphs.append({"text": t, "level": lvl})
        # 表格（重要内容，逐格抽出）
        if getattr(shape, "has_table", False):
            tbl = shape.table
            rows = []
            for row in tbl.rows:
                cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                rows.append(" | ".join(cells))
            if rows:
                table_parts.append("\n".join(rows))
        # 图片（原样抠出）
        if shape.shape_type == 13:  # PICTURE
            try:
                image = shape.image
                img_n += 1
                fname = f"slide{idx:03d}_img{img_n}.{image.ext}"
                (img_dir / fname).write_bytes(image.blob)
                images.append(fname)
            except Exception:  # noqa: BLE001
                continue

    # 备注
    notes = ""
    try:
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()
    except Exception:  # noqa: BLE001
        pass

    body = "\n".join(p["text"] for p in paragraphs)
    text_chars = len("".join((title + body + " ".join(table_parts)).split()))
    return {"index": idx, "title": title, "body": body, "paragraphs": paragraphs,
            "tables": table_parts, "notes": notes, "images": images,
            "text_chars": text_chars}


def _extract_pdf_pages(pdf_path: Path) -> list[dict]:
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    slides = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            txt = (page.extract_text() or "").strip()
        except Exception:  # noqa: BLE001
            txt = ""
        # PDF 源无缩进层级，每行作 level-0 段落
        paras = [{"text": ln.strip(), "level": 0}
                 for ln in txt.splitlines() if ln.strip()]
        slides.append({"index": i, "title": "", "body": txt, "paragraphs": paras,
                       "tables": [], "notes": "", "images": [],
                       "text_chars": len("".join(txt.split()))})
    return slides


# ---------------------------------------------------------------------------
# 归一化 markdown
# ---------------------------------------------------------------------------

def _write_markdown(stem: str, source_name: str, slides: list[dict],
                    md_path: Path) -> None:
    lines = [f"# 来源：{source_name}", ""]
    for s in slides:
        anchor = C.make_anchor(source_name, s["index"])
        lines.append(f"## s.{s['index']}  «{anchor}»")
        if s["title"]:
            lines.append(f"**标题**：{s['title']}")
        if s["body"]:
            lines.append(s["body"])
        for t in s["tables"]:
            lines.append("\n[表格]")
            lines.append(t)
        if s["images"]:
            lines.append(f"\n[内嵌图 {len(s['images'])}]：{', '.join(s['images'])}")
        if s["notes"]:
            lines.append(f"\n[备注] {s['notes']}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# 单源处理
# ---------------------------------------------------------------------------

def process_source(soffice: str, src_entry: dict) -> dict:
    src = Path(src_entry["abs_path"])
    ext = src_entry["ext"]
    stem = src.stem
    source_name = src_entry["name"]
    C.eprint(f"[extract] {source_name}")

    out_dir = C.WORK_EXTRACTED / stem
    if out_dir.exists():
        raise SystemExit(
            f"stem 冲突：{out_dir} 已存在。请确保所有源文件的文件名唯一后重新运行。"
        )
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    # 1) 转 PDF（L0 页空间）
    pdf = convert(soffice, src, "pdf", C.WORK_PDF) if ext != ".pdf" else _copy_into(src, C.WORK_PDF)
    pdf_pages = None
    if pdf:
        from pypdf import PdfReader
        try:
            pdf_pages = len(PdfReader(str(pdf)).pages)
        except Exception:  # noqa: BLE001
            pdf_pages = None

    # 2) 抽取逐页
    if ext == ".pdf":
        slides = _extract_pdf_pages(pdf) if pdf else []
    else:
        # .ppt 需先转 pptx；.pptx 直接用原件
        if ext == ".ppt":
            pptx_path = convert(soffice, src, "pptx", C.WORK_PPTX)
        else:
            pptx_path = src
        slides = []
        if pptx_path:
            from pptx import Presentation
            prs = Presentation(str(pptx_path))
            for i, slide in enumerate(prs.slides, start=1):
                slides.append(_extract_pptx_slide(slide, img_dir, i))

    # 3) markdown（人读）+ content.json（结构化，供蒸馏/索引读取）
    _write_markdown(stem, source_name, slides, out_dir / "slides.md")
    content = {
        "source_name": source_name,
        "ext": ext,
        "slides": [
            {
                "index": s["index"],
                "anchor": C.make_anchor(source_name, s["index"]),
                "title": s["title"],
                "body": s["body"],
                "paragraphs": s["paragraphs"],
                "tables": s["tables"],
                "notes": s["notes"],
                "images": s["images"],
                "text_chars": s["text_chars"],
                "decorative": (_dec := _decorative_hint(s))[0],
                "decorative_reason": _dec[1],
            }
            for s in slides
        ],
    }
    C.write_json(out_dir / "content.json", content)

    # 4) 锚点映射（1 幻灯片 ≈ 1 PDF 页）
    slide_count = len(slides)
    aligned = (pdf_pages is not None and pdf_pages == slide_count)
    mapping = {
        "source_name": source_name,
        "ext": ext,
        "slide_count": slide_count,
        "pdf_page_count": pdf_pages,
        "aligned": aligned,
        "pdf_path": str(pdf) if pdf else None,
        "slides": [
            {
                "index": s["index"],
                "anchor": C.make_anchor(source_name, s["index"]),
                # 1:1 对齐时 pdf 页=幻灯片序；不齐则置 None 待复核
                "pdf_page": s["index"] if aligned else None,
                "title": s["title"],
                "text_chars": s["text_chars"],
                "n_images": len(s["images"]),
                "has_notes": bool(s["notes"]),
                "decorative": (_dec := _decorative_hint(s))[0],
                "decorative_reason": _dec[1],
            }
            for s in slides
        ],
    }
    C.write_json(C.WORK_MAPS / f"{stem}.json", mapping)

    # 5) 文字层确认
    total_chars = sum(s["text_chars"] for s in slides)
    warning = None
    if slide_count and total_chars < TEXT_LAYER_MIN_CHARS:
        warning = (f"{source_name} 抽取文本近零（{total_chars} 字），疑似扫描件/纯图片，"
                   f"本期不做 OCR，请确认是否纳入。")
        C.eprint("  ⚠ " + warning)
    if not aligned and pdf_pages is not None:
        C.eprint(f"  ⚠ 页数不齐：{slide_count} 张 vs PDF {pdf_pages} 页，pdf_page 已置空待复核。")

    return {
        "source_name": source_name, "stem": stem, "ext": ext,
        "slide_count": slide_count, "pdf_pages": pdf_pages,
        "aligned": aligned, "total_text_chars": total_chars,
        "n_images": sum(len(s["images"]) for s in slides),
        "warning": warning,
    }


def _copy_into(src: Path, outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    dst = outdir / src.name
    shutil.copy2(src, dst)
    return dst


def main() -> int:
    ap = argparse.ArgumentParser(description="开卷考 skill Phase 3 抽取")
    ap.add_argument("--only", help="只处理名字含该子串的源（调试）")
    args = ap.parse_args()

    C.ensure_dirs()
    soffice = C.find_soffice()
    if not soffice:
        raise SystemExit("未找到 LibreOffice（soffice）。请先运行 doctor.py --install。")

    manifest = C.read_json(C.MANIFEST_PATH)
    if not manifest:
        raise SystemExit(f"未找到 {C.MANIFEST_PATH}，请先运行 inventory.py")

    sources = manifest["sources"]
    if args.only:
        sources = [s for s in sources if args.only in s["name"]]

    reports = []
    for s in sources:
        reports.append(process_source(soffice, s))

    # 简报（主控只看这个）
    print("=== 抽取简报 ===")
    for r in reports:
        flag = "⚠" if r["warning"] or not r["aligned"] else "✓"
        print(f"  {flag} {r['source_name']}: {r['slide_count']} 张 / "
              f"PDF {r['pdf_pages']} 页 / 文本 {r['total_text_chars']} 字 / "
              f"图 {r['n_images']} 张" + (" / 页数不齐" if not r["aligned"] else ""))
    warns = [r["warning"] for r in reports if r["warning"]]
    if warns:
        print("\n⚠ 警告：")
        for w in warns:
            print(f"  - {w}")
    print(f"\n→ 抽取产物在 {C.WORK_EXTRACTED}，映射在 {C.WORK_MAPS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
