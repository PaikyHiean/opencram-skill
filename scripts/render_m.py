"""
render_m.py — 用 matplotlib 渲染思维导图 PDF（树形布局）。

布局（A4 横向，11.69 × 8.27 英寸）：
  根节点（章节名，章色块）在左 → 分支节点（彩色）居中 → 叶节点文字在右
  连接线：肘形折线（水平→垂直干线→水平），风格参考 XMind 标准树形图。

  第1页：全局总览（章节 tile 网格 + 分支 pill 预览）
  后续页：逐章树形思维导图

不依赖 Typst，直接用 PdfPages 生成多页 PDF。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common as C  # noqa: E402

# ── CJK 字体 ──
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ── 颜色调色板 ──
CH_PALETTE = [
    "#1a3a6b", "#6c3483", "#a93226", "#b7770d",
    "#1a6b3c", "#1a5296", "#5d6d7e", "#117a65",
]
BR_PALETTE = [
    "#e74c3c", "#e67e22", "#d4ac0d", "#27ae60",
    "#16a085", "#2980b9", "#8e44ad", "#c0392b",
    "#1abc9c", "#d35400", "#7d3c98", "#1a5ca8",
]


def ch_color(idx: int) -> str:
    return CH_PALETTE[(idx - 1) % len(CH_PALETTE)]


def br_color(i: int) -> str:
    return BR_PALETTE[i % len(BR_PALETTE)]


def lighten(hex_color: str, factor: float = 0.82) -> tuple:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[k:k+2], 16) / 255 for k in (0, 2, 4))
    return (r + (1 - r) * factor, g + (1 - g) * factor, b + (1 - b) * factor)


def make_ax(fig_w: float, fig_h: float):
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_position([0, 0, 1, 1])   # 填满整张图，数据坐标=英寸
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    return fig, ax


def rbox(ax, x: float, y: float, w: float, h: float,
         color: str, text: str,
         fontsize: float = 9, fc: str = "white",
         bold: bool = True, zorder: int = 3, lw: float = 0,
         ec: str = "#ffffff"):
    """填色圆角矩形 + 居中多行文字。"""
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.03",
        linewidth=lw, edgecolor=ec,
        facecolor=color, zorder=zorder,
        clip_on=False,
    ))
    lines = text.split("\n")
    n = len(lines)
    for k, line in enumerate(lines):
        ty = y + h * (n - k - 0.5) / n
        ax.text(x + w / 2, ty, line,
                ha="center", va="center",
                fontsize=fontsize, color=fc,
                fontweight="bold" if bold else "normal",
                zorder=zorder + 1, clip_on=True)


def wrap_cn(text: str, width: int) -> str:
    """按字符数换行（中文每字等宽）。"""
    lines, i = [], 0
    while i < len(text):
        lines.append(text[i:i+width])
        i += width
    return "\n".join(lines)


def split_chapter_title(title: str) -> str:
    """在"章"处断行，使根节点标题自然换行。"""
    if "章" in title:
        idx = title.index("章")
        first = title[:idx + 1]          # 如 "第14章"
        rest = title[idx + 1:].strip()   # 如 "责任保险"
        if not rest:
            return first
        if len(rest) <= 8:
            return first + "\n" + rest
        return first + "\n" + rest[:8] + "\n" + rest[8:]
    return wrap_cn(title, 6)


def trunc(text: str, max_len: int = 20) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


# ──────────────────────────────────────────────────────────
# 第1页：全局总览
# ──────────────────────────────────────────────────────────

def draw_global_overview(ax, global_data: dict, FW: float, FH: float):
    chapters = global_data.get("chapters", [])
    course_title = global_data.get("course_title", "课程总览")

    # 顶部标题栏
    hh = 0.52
    rbox(ax, 0.18, FH - hh - 0.18, FW - 0.36, hh,
         "#1a3a6b", f"{course_title}  ·  全局总览",
         fontsize=13, fc="white")

    n = len(chapters)
    ncols = 2
    nrows = (n + 1) // 2
    gx, gy = 0.15, 0.12
    tile_w = (FW - gx * (ncols + 1)) / ncols
    content_top = FH - hh - 0.40
    content_h = content_top - 0.12
    tile_h = (content_h - gy * (nrows + 1)) / nrows

    for idx, ch in enumerate(chapters):
        col = idx % ncols
        row = idx // ncols
        tx = gx + col * (tile_w + gx)
        ty = content_top - gy - row * (tile_h + gy) - tile_h

        cc = ch_color(ch.get("chapter_index", idx + 1))

        # 卡片边框
        ax.add_patch(FancyBboxPatch(
            (tx, ty), tile_w, tile_h,
            boxstyle="round,pad=0.02",
            linewidth=0.6, edgecolor=cc,
            facecolor="#fafafa", zorder=2,
        ))

        # 章节标题栏
        th = tile_h * 0.24
        rbox(ax, tx, ty + tile_h - th, tile_w, th, cc,
             ch["chapter_title"], fontsize=8.5, fc="white", zorder=3)

        # 分支 pill（每行 2 个）
        branches = ch.get("branches", [])
        pill_h = 0.18
        pill_gap_x, pill_gap_y = 0.06, 0.05
        pill_w = (tile_w - 0.10) / 2 - pill_gap_x / 2
        row_start_y = ty + tile_h - th - pill_h - 0.08

        for j, b in enumerate(branches):
            pc, pr = j % 2, j // 2
            px = tx + 0.05 + pc * (pill_w + pill_gap_x)
            py = row_start_y - pr * (pill_h + pill_gap_y)
            if py < ty + 0.04:
                break
            bc = br_color(j)
            ax.add_patch(FancyBboxPatch(
                (px, py), pill_w, pill_h,
                boxstyle="round,pad=0.01",
                linewidth=0.4, edgecolor=bc,
                facecolor=lighten(bc, 0.82), zorder=3,
            ))
            label = b if len(b) <= 9 else b[:8] + "…"
            ax.text(px + pill_w / 2, py + pill_h / 2, label,
                    ha="center", va="center",
                    fontsize=6.5, color=bc, fontweight="bold", zorder=4)


# ──────────────────────────────────────────────────────────
# 逐章页：树形思维导图
# ──────────────────────────────────────────────────────────

def draw_chapter_mindmap(ax, chapter: dict, FW: float, FH: float):
    branches = chapter.get("branches", [])
    ch_idx = chapter.get("chapter_index", 1)
    ch_title = chapter.get("chapter_title", "")
    cc = ch_color(ch_idx)

    if not branches:
        return

    # ── 几何常量（英寸） ──
    ML, MR, MT, MB = 0.28, 0.22, 0.28, 0.28
    ROOT_W = 1.25
    ROOT_X = ML
    T1_X   = ROOT_X + ROOT_W + 0.20   # 第一垂直干线 x
    BR_X   = T1_X + 0.15              # 分支节点左边
    BR_W   = 1.62
    T2_X   = BR_X + BR_W + 0.18       # 第二垂直干线 x
    NODE_X = T2_X + 0.12              # 叶节点文字左边

    Y_TOP, Y_BOT = FH - MT, MB
    AVAIL_H = Y_TOP - Y_BOT

    # ── 自适应节点数：保证最小槽高可读 ──
    MIN_SLOT_H = 0.21    # 最小 0.21 英寸/节点，确保单行可读
    raw_counts = [len(b.get("nodes", [])) for b in branches]
    total_raw = sum(max(n, 1) for n in raw_counts)
    max_total = max(int(AVAIL_H / MIN_SLOT_H), len(branches))  # 至少每分支1槽

    if total_raw > max_total:
        # 等比例缩减：每分支至少保留 2 个节点
        ratio = max_total / total_raw
        node_counts = [max(int(n * ratio), min(2, n)) for n in raw_counts]
    else:
        node_counts = [max(n, 1) for n in raw_counts]

    # 剩余节点数（用于 "+N" 提示）
    extra_counts = [max(raw_counts[i] - node_counts[i], 0) for i in range(len(branches))]

    total_slots = sum(node_counts)
    slot_h = AVAIL_H / total_slots

    # 节点字号：根据槽高动态调整
    if slot_h >= 0.26:
        node_fs, max_chars = 8.0, 24
    elif slot_h >= 0.20:
        node_fs, max_chars = 7.5, 22
    else:
        node_fs, max_chars = 7.0, 20

    # 计算各分支中心 y 和各叶节点 y
    branch_cys, all_node_ys = [], []
    cursor = 0
    for nc in node_counts:
        top_y = Y_TOP - cursor * slot_h
        bot_y = Y_TOP - (cursor + nc) * slot_h
        branch_cys.append((top_y + bot_y) / 2)
        nys = [Y_TOP - (cursor + j + 0.5) * slot_h for j in range(nc)]
        all_node_ys.append(nys)
        cursor += nc

    root_cy = (Y_TOP + Y_BOT) / 2
    root_h = max(min(AVAIL_H * 0.36, slot_h * 8), 0.9)
    root_y = root_cy - root_h / 2

    # ── 根节点 ──
    root_text = split_chapter_title(ch_title)
    rbox(ax, ROOT_X, root_y, ROOT_W, root_h,
         cc, root_text, fontsize=9, fc="white", zorder=4)

    # 根→T1 水平线
    ax.plot([ROOT_X + ROOT_W, T1_X], [root_cy, root_cy],
            color=cc, lw=1.8, solid_capstyle="round", zorder=2)

    # T1 垂直干线
    if len(branches) > 1:
        ax.plot([T1_X, T1_X], [branch_cys[-1], branch_cys[0]],
                color=cc, lw=1.8, solid_capstyle="round", zorder=2)

    for i, (b, br_cy, node_ys) in enumerate(zip(branches, branch_cys, all_node_ys)):
        bc = br_color(i)
        nc = node_counts[i]
        extra = extra_counts[i]

        # T1 → 分支节点
        ax.plot([T1_X, BR_X], [br_cy, br_cy],
                color=cc, lw=1.8, solid_capstyle="round", zorder=2)

        # 分支节点框
        br_h = max(min(slot_h * nc * 0.55, 0.40), 0.22)
        rbox(ax, BR_X, br_cy - br_h / 2, BR_W, br_h,
             bc, b["title"], fontsize=8, fc="white", zorder=4)

        nodes = b.get("nodes", [])[:nc]   # 只取限定数量
        if not nodes:
            continue

        # 分支→T2 水平线
        ax.plot([BR_X + BR_W, T2_X], [br_cy, br_cy],
                color=bc, lw=1.0, solid_capstyle="round", zorder=2)

        # T2 垂直干线
        if len(node_ys) > 1:
            ax.plot([T2_X, T2_X], [node_ys[-1], node_ys[0]],
                    color=bc, lw=1.0, solid_capstyle="round", zorder=2)

        for j, (node_text, ny) in enumerate(zip(nodes, node_ys)):
            # T2 → 叶节点水平线
            ax.plot([T2_X, NODE_X], [ny, ny],
                    color=bc, lw=0.8, solid_capstyle="round", zorder=2)

            # 叶节点文字
            is_last = (j == len(nodes) - 1)
            if is_last and extra > 0:
                display = trunc(node_text, max_chars - 4) + f" +{extra}"
            else:
                display = trunc(node_text, max_chars)

            ax.text(NODE_X + 0.06, ny, display,
                    ha="left", va="center",
                    fontsize=node_fs, color="#1a1a1a", zorder=4)


# ──────────────────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────────────────

def main() -> int:
    M_JSON = C.WORK_DIR / "distilled" / "m.json"
    if not M_JSON.exists():
        raise SystemExit(f"未找到 {M_JSON}，请先运行 merge_m.py。")

    data = json.loads(M_JSON.read_text("utf-8"))
    global_data = data.get("global", {})
    chapters_data = data.get("chapters", [])

    C.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = C.OUTPUTS_DIR / "M.pdf"

    FW, FH = 11.69, 8.27   # A4 横向（英寸）

    with PdfPages(str(out_path)) as pdf:
        # 第 1 页：全局总览
        fig, ax = make_ax(FW, FH)
        draw_global_overview(ax, global_data, FW, FH)
        pdf.savefig(fig, dpi=150)
        plt.close(fig)

        # 后续页：逐章树形图
        for ch in chapters_data:
            fig, ax = make_ax(FW, FH)
            draw_chapter_mindmap(ax, ch, FW, FH)
            pdf.savefig(fig, dpi=150)
            plt.close(fig)

    size_kb = out_path.stat().st_size // 1024
    print(f"=== 渲染完成 ===\n  → {out_path}  ({size_kb} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
