"""
screen_images.py — 为图片筛查子 agent 切出输入包。

把 l1.json 中所有带图片的小节汇成 work/distilled/ai/image_screen_in.json，
供子 agent 逐图做 keep/remove 裁决，产出 image_screen_out.json。
再跑 apply_image_screen.py 把裁决写回 l1.json。

image_screen_in.json 格式：
{
  "sections": [
    {
      "sec_id": "ch0_sec2",         // 章索引_节索引（0-based）
      "chapter_title": "...",
      "heading": "...",
      "text_summary": "...",        // 该节所有 points 的文字拼接（供 agent 判断文图是否重叠）
      "images": ["work/extracted/...png", ...]   // 相对 skill root 的路径
    }, ...
  ]
}

image_screen_out.json 格式（子 agent 写）：
{
  "decisions": [
    { "sec_id": "ch0_sec2", "img": "work/extracted/.../xxx.png", "keep": true,  "reason": "..." },
    { "sec_id": "ch0_sec2", "img": "work/extracted/.../yyy.png", "keep": false, "reason": "..." }
  ]
}
"""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C

AI_DIR = C.WORK_DIR / "distilled" / "ai"


def _text_summary(sec: dict) -> str:
    parts: list[str] = []
    for pt in sec.get("points", []):
        parts.append(pt.get("text", ""))
        for d in pt.get("details", []):
            parts.append("  · " + d.get("text", ""))
    return "\n".join(parts)[:600]


def main() -> int:
    l1 = C.read_json(C.WORK_DIR / "distilled" / "l1.json")
    if not l1:
        raise SystemExit("l1.json not found; run merge_ai_l1.py first.")
    AI_DIR.mkdir(parents=True, exist_ok=True)

    sections = []
    for ci, ch in enumerate(l1["chapters"]):
        for si, sec in enumerate(ch["sections"]):
            imgs = sec.get("images", [])
            if not imgs:
                continue
            sections.append({
                "sec_id": f"ch{ci}_sec{si}",
                "chapter_title": ch.get("title", ""),
                "heading": sec.get("label", "") + sec.get("heading", ""),
                "text_summary": _text_summary(sec),
                "images": imgs,
            })

    out_path = AI_DIR / "image_screen_in.json"
    C.write_json(out_path, {"sections": sections})
    print("=== 图片筛查输入包已生成 ===")
    print(f"  待筛查小节: {len(sections)}")
    total = sum(len(s['images']) for s in sections)
    print(f"  待筛查图片: {total} 张")
    for s in sections:
        print(f"    {s['chapter_title']} / {s['heading']}  ({len(s['images'])} 张)")
    print(f"\n→ {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
