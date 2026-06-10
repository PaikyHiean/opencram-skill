"""
doctor.py — 依赖与环境体检（Phase 3 bootstrap）。

默认只"检测并报告"，不擅自安装。安装动作须由上层编排（SKILL.md）在征得
用户一次同意后，用 --install 触发，或直接给出安装命令让用户执行。

用法：
    python scripts/doctor.py                # 仅检测，打印人类可读 + JSON 摘要
    python scripts/doctor.py --json         # 仅打印 JSON（供编排解析）
    python scripts/doctor.py --install       # 检测后尝试安装缺失项（需事先取得同意）

检测项：
    - Python 版本
    - python-pptx / pypdf（import 测试）
    - LibreOffice（soffice 可执行）
    - Typst（typst 可执行）
    - 中文字体（至少命中一个 CJK 字体族）
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402


def _check_pymod(modname: str) -> dict:
    try:
        m = importlib.import_module(modname)
        ver = getattr(m, "__version__", "?")
        return {"ok": True, "version": ver}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


def diagnose() -> dict:
    py_ok = sys.version_info >= (3, 9)
    pptx = _check_pymod("pptx")
    pypdf = _check_pymod("pypdf")
    reportlab = _check_pymod("reportlab")
    matplotlib = _check_pymod("matplotlib")

    soffice = C.find_soffice()
    typst = C.find_typst()
    cjk_ok, cjk_hits = C.has_cjk_font()

    report = {
        "python": {
            "ok": py_ok,
            "version": sys.version.split()[0],
            "executable": sys.executable,
        },
        "python-pptx": pptx,
        "pypdf": pypdf,
        "reportlab": reportlab,
        "matplotlib": matplotlib,
        "libreoffice": {"ok": soffice is not None, "path": soffice},
        "typst": {"ok": typst is not None, "path": typst},
        "cjk_font": {"ok": cjk_ok, "hits": cjk_hits},
    }
    report["all_ok"] = all([
        py_ok, pptx["ok"], pypdf["ok"], reportlab["ok"], matplotlib["ok"],
        report["libreoffice"]["ok"], report["typst"]["ok"], cjk_ok,
    ])
    return report


def _run(cmd: list[str]) -> int:
    C.eprint(f"  $ {' '.join(cmd)}")
    try:
        return subprocess.call(cmd)
    except FileNotFoundError as e:  # noqa: BLE001
        C.eprint(f"  ! 找不到命令：{e}")
        return 127


def install_missing(report: dict) -> None:
    """尝试安装缺失项。须在取得用户同意后调用。"""
    # 1) pip 包
    missing_py = [name for name in ("python-pptx", "pypdf", "reportlab", "matplotlib")
                  if not report[name]["ok"]]
    if missing_py:
        C.eprint(f"[install] pip 安装：{missing_py}")
        _run([sys.executable, "-m", "pip", "install", "--quiet", *missing_py])

    # 2) LibreOffice
    if not report["libreoffice"]["ok"]:
        _os = platform.system()
        if _os == "Windows":
            C.eprint("[install] winget 安装 LibreOffice ...")
            _run(["winget", "install", "-e", "--id", "TheDocumentFoundation.LibreOffice",
                  "--accept-package-agreements", "--accept-source-agreements",
                  "--disable-interactivity"])
        elif _os == "Darwin":
            C.eprint("[install] 请手动运行：brew install --cask libreoffice")
        else:
            C.eprint("[install] 请手动运行：sudo apt install libreoffice  # 或对应包管理器")

    # 3) Typst
    if not report["typst"]["ok"]:
        _os = platform.system()
        if _os == "Windows":
            C.eprint("[install] winget 安装 Typst ...")
            _run(["winget", "install", "-e", "--id", "Typst.Typst",
                  "--accept-package-agreements", "--accept-source-agreements",
                  "--disable-interactivity"])
        elif _os == "Darwin":
            C.eprint("[install] 请手动运行：brew install typst")
        else:
            C.eprint("[install] 请手动运行：snap install typst  # 或从 https://github.com/typst/typst/releases 下载")


def _human(report: dict) -> str:
    def mark(ok: bool) -> str:
        return "✅" if ok else "❌"

    lines = ["=== 开卷考 skill 依赖体检 ==="]
    p = report["python"]
    lines.append(f"{mark(p['ok'])} Python {p['version']}  ({p['executable']})")
    for key, label in (("python-pptx", "python-pptx"), ("pypdf", "pypdf"),
                       ("reportlab", "reportlab"), ("matplotlib", "matplotlib")):
        r = report[key]
        extra = r.get("version", "") if r["ok"] else r.get("error", "")
        lines.append(f"{mark(r['ok'])} {label}  {extra}")
    lo = report["libreoffice"]
    lines.append(f"{mark(lo['ok'])} LibreOffice  {lo['path'] or '未找到'}")
    ty = report["typst"]
    lines.append(f"{mark(ty['ok'])} Typst  {ty['path'] or '未找到'}")
    cj = report["cjk_font"]
    lines.append(f"{mark(cj['ok'])} 中文字体  命中: {', '.join(cj['hits']) or '无'}")
    lines.append("")
    lines.append("全部就绪 ✅" if report["all_ok"] else "存在缺失，见上 ❌。可用 --install 安装（须先征得同意）。")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="开卷考 skill 依赖体检")
    ap.add_argument("--install", action="store_true", help="检测后尝试安装缺失项")
    ap.add_argument("--json", action="store_true", help="仅输出 JSON")
    args = ap.parse_args()

    report = diagnose()

    if args.install and not report["all_ok"]:
        install_missing(report)
        report = diagnose()  # 重测

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_human(report))

    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
