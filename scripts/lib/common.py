"""
开卷考课件整理 skill — 共享工具库。

集中放置：路径解析、工具(LibreOffice/Typst)定位、来源锚点(anchor)读写、
JSON 落盘/读取、中文字体检测、配置默认值。

设计铁律（见 TODO.md / 计划文件）：
- 内部真值锚点 = (源文件名, 源内页序号)，永不漂移。
- 所有产物的页码指针都基于锚点 + 参考基准换算，不硬编码 L0 页码。
- 脚本负责"确定性"工作并落盘；编排/AI 判断由上层 Claude 读盘完成。
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


def _setup_utf8_io() -> None:
    """Windows 控制台默认 GBK，输出中文/符号(•✅→)会 UnicodeEncodeError。
    强制 stdout/stderr 用 UTF-8（errors=replace 永不崩溃）。所有脚本都 import
    本模块，故在此一处修复即全局生效。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


_setup_utf8_io()

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------

# common.py 位于 <skill_root>/scripts/lib/common.py
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
SKILL_ROOT = SCRIPTS_DIR.parent
TEMPLATES_DIR = SKILL_ROOT / "templates"
WORK_DIR = SKILL_ROOT / "work"
OUTPUTS_DIR = SKILL_ROOT / "outputs"

# work/ 子目录
WORK_PDF = WORK_DIR / "pdf"          # LibreOffice 转出的逐源 PDF（L0 页空间）
WORK_PPTX = WORK_DIR / "pptx"        # LibreOffice 转出的逐源 pptx（供 python-pptx）
WORK_EXTRACTED = WORK_DIR / "extracted"   # 归一化 markdown + 抠出的图
WORK_MAPS = WORK_DIR / "maps"        # (源文件名,源内页序号)->页 映射
WORK_DRAFTS = WORK_DIR / "drafts"    # 章节草稿图等待确认产物

MANIFEST_PATH = WORK_DIR / "manifest.json"
CHAPTERS_PATH = WORK_DRAFTS / "chapters.json"
CONFIG_PATH = WORK_DIR / "config.json"
L0_PAGEMAP_PATH = WORK_DIR / "l0_pagemap.json"
L0_DELETED_PATH = WORK_DIR / "l0_deleted.json"


def ensure_dirs() -> None:
    """创建运行时目录（幂等）。"""
    for d in (WORK_DIR, WORK_PDF, WORK_PPTX, WORK_EXTRACTED, WORK_MAPS,
              WORK_DRAFTS, OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# JSON 读写（统一 UTF-8，禁 ASCII 转义，便于人工复核）
# ---------------------------------------------------------------------------

def read_json(path: str | os.PathLike, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | os.PathLike, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# 来源锚点 anchor = (源文件名, 源内页序号)
# 源内页序号统一 1-based（与用户对幻灯片/页的直觉一致）。
# 字符串形式："<filename>#s<index>"，用于 JSON key 与展示。
# ---------------------------------------------------------------------------

def make_anchor(source_name: str, page_index: int) -> str:
    return f"{source_name}#s{page_index}"


def parse_anchor(anchor: str) -> tuple[str, int]:
    name, _, idx = anchor.rpartition("#s")
    return name, int(idx)


def stamp_text(source_name: str, page_index: int) -> str:
    """L0 每页角上盖的来源戳文案，如：源：第六章 企业财产保险.ppt s.12"""
    return f"源：{source_name} s.{page_index}"


# ---------------------------------------------------------------------------
# 工具定位：LibreOffice / Typst
# ---------------------------------------------------------------------------

def find_soffice() -> str | None:
    """返回 soffice 可执行文件路径，找不到返回 None。"""
    # 1) PATH
    for name in ("soffice", "soffice.exe", "soffice.bin"):
        hit = shutil.which(name)
        if hit:
            return hit
    # 2) Windows 常见安装路径
    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    # 3) macOS / Linux 常见路径（保持跨平台）
    candidates += [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def find_typst() -> str | None:
    """返回 typst 可执行文件路径，找不到返回 None。"""
    hit = shutil.which("typst") or shutil.which("typst.exe")
    if hit:
        return hit
    # winget 安装后的常见位置（当前进程 PATH 可能未刷新，故直接探目录）
    local = os.environ.get("LOCALAPPDATA", "")
    candidates = []
    if local:
        candidates.append(Path(local) / "Microsoft" / "WinGet" / "Links" / "typst.exe")
        candidates.append(Path(local) / "Microsoft" / "WindowsApps" / "typst.exe")
        # winget 实际二进制目录（兜底，名字带版本）
        pkg = Path(local) / "Microsoft" / "WinGet" / "Packages"
        if pkg.exists():
            candidates += list(pkg.glob("Typst.Typst_*/**/typst.exe"))
    # 本仓库自带（doctor 下载的单文件二进制兜底）
    candidates.append(SKILL_ROOT / "bin" / ("typst.exe" if os.name == "nt" else "typst"))
    for c in candidates:
        if Path(c).exists():
            return str(c)
    return None


# ---------------------------------------------------------------------------
# 中文字体检测（Windows：读注册表已安装字体名）
# ---------------------------------------------------------------------------

# Typst/LibreOffice 渲染中文所需的优先字体族（任意命中其一即视为可用）
PREFERRED_CJK_FONTS = [
    "Microsoft YaHei", "微软雅黑",
    "SimSun", "宋体",
    "SimHei", "黑体",
    "KaiTi", "楷体",
    "FangSong", "仿宋",
    "Source Han Sans", "Noto Sans CJK SC",
]


def installed_font_names() -> list[str]:
    """枚举已安装字体名（尽力而为，失败返回空表）。"""
    names: set[str] = set()
    if os.name == "nt":
        try:
            import winreg  # type: ignore
            for root, sub in (
                (winreg.HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
                (winreg.HKEY_CURRENT_USER,
                 r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
            ):
                try:
                    with winreg.OpenKey(root, sub) as key:
                        i = 0
                        while True:
                            try:
                                value_name, _, _ = winreg.EnumValue(key, i)
                                # 值名形如 "Microsoft YaHei & Microsoft YaHei UI (TrueType)"
                                names.add(value_name)
                                i += 1
                            except OSError:
                                break
                except OSError:
                    continue
        except Exception:
            pass
    else:
        # 非 Windows：尝试 fc-list
        fc = shutil.which("fc-list")
        if fc:
            try:
                import subprocess
                out = subprocess.run([fc, ":", "family"], capture_output=True,
                                     text=True, timeout=20)
                for line in out.stdout.splitlines():
                    for fam in line.split(","):
                        names.add(fam.strip())
            except Exception:
                pass
    return sorted(names)


def has_cjk_font() -> tuple[bool, list[str]]:
    """返回 (是否具备中文字体, 命中的字体名列表)。"""
    installed = installed_font_names()
    joined = "\n".join(installed)
    hits = [f for f in PREFERRED_CJK_FONTS if f in joined]
    return (len(hits) > 0, hits)


# ---------------------------------------------------------------------------
# 配置默认值（参考基准 / 精简力度 / 选中产物）
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "reference_base": "source",   # "source"=带原件打印 | "l0"=带 L0 打印
    "compression": "conservative",  # conservative | standard | aggressive
    "products": ["L0", "L1"],     # 本期纵切片默认产物
    "cjk_font": "Microsoft YaHei",  # Typst 正文默认中文字体
    "cjk_font_serif": "SimSun",
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(read_json(CONFIG_PATH, {}) or {})
    return cfg


# ---------------------------------------------------------------------------
# 杂项
# ---------------------------------------------------------------------------

def eprint(*args: Any) -> None:
    """打印到 stderr（脚本面向用户的提示走这里，stdout 留给结构化结果）。"""
    print(*args, file=sys.stderr, flush=True)
