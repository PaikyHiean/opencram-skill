"""
render.py — 用 Typst 渲染产物 PDF。

本期实现 L1（核心知识手册）；后续扩 L2/C/M/QA 分支。
Typst 以 --root <skill_root> 编译，模板内用 root 相对路径读取 work/ 下的数据与图片。

用法：
    python scripts/render.py l1            # 渲染 outputs/L1.pdf
    python scripts/render.py l1 --open     # 渲染后打开
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402

# 产物代号 → (模板文件, 输出文件, 该产物依赖的数据文件)
TARGETS = {
    "l1": ("l1.typ", "L1.pdf", C.WORK_DIR / "distilled" / "l1.json"),
    "qa": ("qa.typ", "QA.pdf", C.WORK_DIR / "distilled" / "qa.json"),
}


def render(target: str) -> Path:
    if target not in TARGETS:
        raise SystemExit(f"未知产物 '{target}'，可选：{', '.join(TARGETS)}")
    typst = C.find_typst()
    if not typst:
        raise SystemExit("未找到 Typst。请先运行 doctor.py --install。")

    tmpl_name, out_name, data_path = TARGETS[target]
    tmpl = C.TEMPLATES_DIR / tmpl_name
    if not tmpl.exists():
        raise SystemExit(f"模板缺失：{tmpl}")
    if data_path and not Path(data_path).exists():
        raise SystemExit(f"数据缺失：{data_path}（请先运行对应的蒸馏/索引脚本）")

    C.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out = C.OUTPUTS_DIR / out_name
    cmd = [typst, "compile", "--root", str(C.SKILL_ROOT),
           str(tmpl), str(out)]
    C.eprint(f"  $ {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"Typst 渲染失败：\n{r.stdout}\n{r.stderr}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="开卷考 skill 渲染")
    ap.add_argument("target", help="产物代号：l1 | qa（后续 l2/card/mindmap）")
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
