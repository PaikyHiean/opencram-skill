"""
detect_chapters.py — Phase 1 章节识别。

读 work/manifest.json，按以下优先级推断每个源文件归属的"章"，产出草稿章节图
work/drafts/chapters.json 供用户复核（合并/拆分/重命名/标记附录或习题）。

推断优先级（见 TODO.md §7）：
    1. 文件名模式：第N章 / 第〔中文数字〕章 / chN / chapterN / 0N_ / N. 等
    2. （此处仅文件名层；幻灯片内节标题需 extract 后才有，留待复核环节补充）
    3. 兜底：1 文件 = 1 章

特别处理本数据集出现的真实"脏"情况：
    - 中文数字章号（第十四章）
    - 同一章号多个文件（第六章 ×2 + 无号"企业财产保险"）→ 同章多文件
    - 无章号文件 → 先归入 "未归类"，待用户指派

注意：本脚本只产出**草稿**。最终章节图必须经用户在 Phase 1 确认后锁定。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402

# ---------------------------------------------------------------------------
# 中文数字 → int
# ---------------------------------------------------------------------------
_CN_DIGIT = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
             "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def cn_to_int(s: str) -> int | None:
    """解析中文数字（支持到 999，覆盖常见章号如 十四 / 二十一 / 一百零五）。"""
    s = s.strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    total, section, num = 0, 0, 0
    for ch in s:
        if ch in _CN_DIGIT:
            num = _CN_DIGIT[ch]
        elif ch == "十":
            section += (num or 1) * 10
            num = 0
        elif ch == "百":
            section += (num or 1) * 100
            num = 0
        else:
            return None
    return total + section + num


# ---------------------------------------------------------------------------
# 从文件名提取章号
# ---------------------------------------------------------------------------
# 第N章 / 第〔中文数字〕章
_RE_CN_CHAP = re.compile(r"第\s*([0-9零〇一二两三四五六七八九十百]+)\s*章")
# chN / chapterN / chap N
_RE_EN_CHAP = re.compile(r"(?:chapter|chap|ch)\s*[._-]?\s*(\d+)", re.IGNORECASE)
# 前缀编号：01_ / 1. / 1、 / 1 -（避免误吞年份等，仅取 1~2 位且在串首）
_RE_PREFIX_NUM = re.compile(r"^\s*(\d{1,2})\s*[._、,\-]")


def chapter_of(filename: str) -> tuple[int | None, str]:
    """返回 (章号或None, 命中方式说明)。"""
    stem = Path(filename).stem
    m = _RE_CN_CHAP.search(stem)
    if m:
        n = cn_to_int(m.group(1))
        if n is not None:
            return n, f"文件名'第{m.group(1)}章'"
    m = _RE_EN_CHAP.search(stem)
    if m:
        return int(m.group(1)), f"文件名'{m.group(0)}'"
    m = _RE_PREFIX_NUM.match(stem)
    if m:
        return int(m.group(1)), f"文件名前缀编号'{m.group(1)}'"
    return None, "无章号"


def _clean_title(filename: str, chap: int | None) -> str:
    """从文件名推一个可读章名（去掉章号前缀、扩展名、'上传/最终'等噪声）。"""
    stem = Path(filename).stem
    stem = _RE_CN_CHAP.sub("", stem)
    stem = _RE_EN_CHAP.sub("", stem)
    stem = _RE_PREFIX_NUM.sub("", stem)
    stem = re.sub(r"[—\-–\s]+", " ", stem).strip()
    stem = re.sub(r"(上传|最终|定稿|完整版|\d+)$", "", stem).strip()
    return stem or (f"第{chap}章" if chap else "未命名")


def detect(manifest: dict) -> dict:
    # 按章号聚合
    by_chap: dict[int, list[dict]] = {}
    unfiled: list[dict] = []
    for s in manifest["sources"]:
        chap, how = chapter_of(s["name"])
        rec = {"name": s["name"], "abs_path": s["abs_path"],
               "ext": s["ext"], "match": how,
               "guess_title": _clean_title(s["name"], chap)}
        if chap is None:
            unfiled.append(rec)
        else:
            by_chap.setdefault(chap, []).append(rec)

    chapters = []
    for chap in sorted(by_chap):
        files = by_chap[chap]
        # 章名：取该章内最像"完整标题"的（最长 guess_title）
        title = max((f["guess_title"] for f in files), key=len)
        chapters.append({
            "chapter": chap,
            "title": title,
            "files": files,
            "multi_file": len(files) > 1,
            "confidence": "high" if len(files) == 1 else "review",
        })

    draft = {
        "source_folder": manifest["folder"],
        "method": "filename-heuristic (草稿，待用户确认)",
        "chapters": chapters,
        "unfiled": unfiled,
        "notes": [],
    }
    # 生成需用户关注的提示
    for c in chapters:
        if c["multi_file"]:
            names = "、".join(f["name"] for f in c["files"])
            draft["notes"].append(
                f"第{c['chapter']}章 命中多个文件，请确认是否同章合并：{names}")
    if unfiled:
        names = "、".join(f["name"] for f in unfiled)
        draft["notes"].append(
            f"以下文件无章号，请指派归属/标记为附录或习题：{names}")
    return draft


def _human(d: dict) -> str:
    lines = ["=== 草稿章节图（待你确认，可合并/拆分/重命名/标记附录习题）==="]
    for c in d["chapters"]:
        tag = "  ⚠多文件" if c["multi_file"] else ""
        lines.append(f"  第{c['chapter']}章  {c['title']}{tag}")
        for f in c["files"]:
            lines.append(f"      ├─ {f['name']}  ({f['match']})")
    if d["unfiled"]:
        lines.append("  〔未归类〕")
        for f in d["unfiled"]:
            lines.append(f"      ├─ {f['name']}")
    if d["notes"]:
        lines.append("")
        lines.append("需你确认：")
        for n in d["notes"]:
            lines.append(f"  - {n}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="开卷考 skill Phase 1 章节推断")
    ap.add_argument("--json", action="store_true", help="仅输出 JSON")
    args = ap.parse_args()

    manifest = C.read_json(C.MANIFEST_PATH)
    if not manifest:
        raise SystemExit(f"未找到 {C.MANIFEST_PATH}，请先运行 inventory.py")

    draft = detect(manifest)
    C.write_json(C.CHAPTERS_PATH, draft)

    if args.json:
        print(json.dumps(draft, ensure_ascii=False, indent=2))
    else:
        print(_human(draft))
        print(f"\n→ 已写入 {C.CHAPTERS_PATH}（草稿，确认后锁定）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
