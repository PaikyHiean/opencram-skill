"""verify_l1.py — 验证 l1.json 质量：指针格式、ai_generated 标记、锚点可回源。"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C


def main() -> int:
    l1 = C.read_json(C.WORK_DIR / "distilled" / "l1.json")
    if not l1:
        raise SystemExit("l1.json not found")
    l0map = C.read_json(C.L0_PAGEMAP_PATH, {}) or {}
    extracted = C.WORK_EXTRACTED

    all_secs = [s for ch in l1["chapters"] for s in ch["sections"]]
    ai_count = sum(1 for s in all_secs if s.get("ai_generated"))
    bad_pointer: list[str] = []
    bad_anchor: list[str] = []

    for ch in l1["chapters"]:
        for sec in ch["sections"]:
            # 指针不应为空
            ptr = sec.get("pointer", "")
            if not ptr or ptr == "源：—":
                bad_pointer.append(f"{ch['title']} / {sec['label']}{sec['heading']}")
            # 锚点必须能解析且来源存在
            for a in sec.get("points", []):
                pass  # points 本身不存锚点
            for a in (sec.get("anchors") or []):
                try:
                    name, idx = C.parse_anchor(a)
                except Exception:
                    bad_anchor.append(f"无法解析: {a}")
                    continue
                stem = Path(name).stem
                content_path = extracted / stem / "content.json"
                if not content_path.exists():
                    bad_anchor.append(f"content.json 缺失: {stem}")

    print("=== L1 验证报告 ===")
    print(f"  章节数: {len(l1['chapters'])}")
    print(f"  总小节: {len(all_secs)}")
    print(f"  ai_generated=True: {ai_count} / {len(all_secs)}")
    if bad_pointer:
        print(f"  [!] 无指针小节 ({len(bad_pointer)}): {bad_pointer[:5]}")
    else:
        print("  [OK] 所有小节均有源指针")
    if bad_anchor:
        print(f"  [!] 锚点问题 ({len(bad_anchor)}): {bad_anchor[:5]}")
    else:
        print("  [OK] 所有锚点可解析、content.json 存在")

    print()
    print("=== 各章首节预览 ===")
    for ch in l1["chapters"]:
        sec = ch["sections"][0]
        print(f"  {ch['title']}")
        print(f"    {sec['label']}{sec['heading']}")
        print(f"    {sec['pointer']}")
        pts = sec.get("points", [])
        if pts:
            first_pt = pts[0].get("text", "")[:60]
            print(f"    首点: {first_pt}...")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
