"""
render.py — 渲染产物 PDF。

L1/QA/L2/C 用 Typst；M 思维导图用 matplotlib（render_m.py），不依赖 Typst。

用法：
    python scripts/render.py l1            # 渲染 outputs/L1.pdf
    python scripts/render.py qa            # 渲染 outputs/QA.pdf
    python scripts/render.py l2            # 渲染 outputs/L2.pdf
    python scripts/render.py c             # 渲染 outputs/C.pdf
    python scripts/render.py m             # 渲染 outputs/M.pdf（树形思维导图）
    python scripts/render.py l1 --open     # 渲染后打开
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402

# Typst 渲染目标：产物代号 → (模板文件, 输出文件, 数据文件)
TYPST_TARGETS = {
    "l1": ("l1.typ", "L1.pdf", C.WORK_DIR / "distilled" / "l1.json"),
    "qa": ("qa.typ", "QA.pdf", C.WORK_DIR / "distilled" / "qa.json"),
    "l2": ("l2.typ", "L2.pdf", C.WORK_DIR / "distilled" / "l2.json"),
    "c":  ("c.typ",  "C.pdf",  C.WORK_DIR / "distilled" / "c.json"),
}


def render_typst(target: str) -> Path:
    typst = C.find_typst()
    if not typst:
        raise SystemExit("未找到 Typst。请先运行 doctor.py --install。")

    tmpl_name, out_name, data_path = TYPST_TARGETS[target]
    tmpl = C.TEMPLATES_DIR / tmpl_name
    if not tmpl.exists():
        raise SystemExit(f"模板缺失：{tmpl}")
    if data_path and not Path(data_path).exists():
        raise SystemExit(f"数据缺失：{data_path}（请先运行对应的蒸馏/索引脚本）")

    C.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out = C.OUTPUTS_DIR / out_name
    cmd = [typst, "compile", "--root", str(C.SKILL_ROOT), str(tmpl), str(out)]
    C.eprint(f"  $ {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"Typst 渲染失败：\n{r.stdout}\n{r.stderr}")
    return out


def render_m() -> Path:
    """M 思维导图用 matplotlib 渲染，不走 Typst。"""
    m_json = C.WORK_DIR / "distilled" / "m.json"
    if not m_json.exists():
        raise SystemExit(f"数据缺失：{m_json}（请先运行 merge_m.py）")
    import render_m as rm  # noqa: PLC0415
    rm.main()
    return C.OUTPUTS_DIR / "M.pdf"


def render(target: str) -> Path:
    all_targets = list(TYPST_TARGETS) + ["m"]
    if target not in all_targets:
        raise SystemExit(f"未知产物 '{target}'，可选：{', '.join(all_targets)}")
    if target == "m":
        return render_m()
    return render_typst(target)


def main() -> int:
    ap = argparse.ArgumentParser(description="开卷考 skill 渲染")
    ap.add_argument("target", help="产物代号：l1 | qa | l2 | c | m")
    ap.add_argument("--open", action="store_true", help="渲染后用系统默认程序打开")
    args = ap.parse_args()

    out = render(args.target)
    print(f"=== 渲染完成 ===\n  → {out}")
    if args.open:
        import os
        os.startfile(str(out))  # noqa: S606  (Windows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
