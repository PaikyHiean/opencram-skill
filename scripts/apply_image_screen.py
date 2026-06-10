"""
apply_image_screen.py — 把图片筛查子 agent 的裁决写回 l1.json。

读 work/distilled/ai/image_screen_out.json（子 agent 产出），
按 sec_id 找到对应小节，把 keep=false 的图片从 images 列表中移除。
未出现在裁决中的图片默认保留。

用法：
    python scripts/screen_images.py          # 1. 生成输入包
    # 2. 子 agent 读图产出 image_screen_out.json
    python scripts/apply_image_screen.py     # 3. 写回 l1.json
    python scripts/render.py l1              # 4. 重渲染
"""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C

AI_DIR = C.WORK_DIR / "distilled" / "ai"
L1_JSON = C.WORK_DIR / "distilled" / "l1.json"


def main() -> int:
    decisions_raw = C.read_json(AI_DIR / "image_screen_out.json")
    if not decisions_raw:
        raise SystemExit(f"未找到 {AI_DIR/'image_screen_out.json'}，请先运行图片筛查子 agent。")

    # 构建 {sec_id: {img_path: keep}} 索引
    decisions: dict[str, dict[str, bool]] = {}
    for d in decisions_raw.get("decisions", []):
        sid = d["sec_id"]
        decisions.setdefault(sid, {})[d["img"]] = bool(d.get("keep", True))

    l1 = C.read_json(L1_JSON)
    if not l1:
        raise SystemExit("l1.json not found")

    removed = 0
    kept = 0
    for ci, ch in enumerate(l1["chapters"]):
        for si, sec in enumerate(ch["sections"]):
            sid = f"ch{ci}_sec{si}"
            if sid not in decisions:
                continue
            orig = sec.get("images", [])
            filtered = [img for img in orig if decisions[sid].get(img, True)]
            removed += len(orig) - len(filtered)
            kept += len(filtered)
            sec["images"] = filtered

    C.write_json(L1_JSON, l1)
    total = removed + kept
    print("=== 图片筛查已应用 ===")
    print(f"  保留: {kept} 张  移除: {removed} 张  总计: {total} 张")
    print(f"  → {L1_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
