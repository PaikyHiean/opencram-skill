# L1 排版配置参考

本文档记录 `l1.typ` 中经过调试验证的中文 PDF 排版参数，供开源复用或迁移至其他 Typst 模板时参考。

## 核心参数

### 页面
```typst
#set page(
  paper: "a4",
  margin: (x: 2cm, top: 1.6cm, bottom: 1.3cm),
)
```

### 字体
```typst
#let head-font = ("Microsoft YaHei", "SimHei")   // 标题、表格：黑体系
#let body-font = ("SimSun", "Noto Serif CJK SC")  // 正文：宋体系（衬线，适合大段阅读）
#set text(font: body-font, size: 10.5pt, lang: "zh")
```

### 段落间距
```typst
#set par(justify: true, leading: 0.82em, spacing: 0.72em)
```
- `leading`：同一段落内换行的行间距（基线到基线的额外间距）
- `spacing`：段落间距，控制相邻段落的自然间距

## 层级间距（关键）

```typst
// 小节块（一、二、…）
block(above: 0.85em, below: 0.5em)

// 知识点块（1. 2. …）
block(above: 0.62em, below: 0.45em)

// 明细块（· 子项）
block(above: 0.75em, below: 0.5em)
```

### 为什么这样设置——Typst 间距折叠机制

Typst 对相邻 block 做 **间距折叠**（同 CSS margin collapse）：
两个相邻块之间的实际间距 = `max(上块.below, 下块.above)`，而非相加。

因此，要让相邻条目的视觉间距与段落内换行行距（`leading: 0.82em`）保持一致：
- 需要 `max(detail.below, detail.above) ≈ leading`
- 即 `detail.above ≥ leading` → 设为 `0.75em`

| 位置 | 折叠前 | 折叠后实际间距 | 对比 leading |
|---|---|---|---|
| 相邻明细（· 子项之间） | above=0.75, below=0.50 | **0.75em** | ≈ leading 0.82em ✓ |
| 相邻知识点（1./2. 之间） | above=0.62, below=0.45 | **0.62em** | 略小，提供层级感 |
| 相邻小节（一、二、之间） | above=0.85, below=0.50 | **0.85em** | 略大，提供章内分隔感 |

**原则**：`detail.above` 对齐 `leading`，层级越高间距越大，保证相邻条目间距不窄于行内换行。

## 表格渲染

```typst
table(
  columns: n-cols,          // 等宽列（整数参数），n-cols 从数据解析
  stroke: 0.5pt + rgb("#aaa"),
  inset: (x: 5pt, y: 4pt),
  // 偶数行（0, 2, 4…）填浅蓝灰，奇数行白色
  fill per cell: if calc.rem(ri, 2) == 0 { rgb("#edf0f6") } else { white }
)
```

数据格式：每张表为一个字符串，行间 `\n` 分隔，列间 ` | ` 分隔（含空格）。

## 徽章与颜色

```typst
navy = rgb("#1a3a6b")      // 章标题背景、节标题文字
ai-badge = rgb("#aa3333")  // 〔AI〕标记
pointer = rgb("#888")      // 〔源：…〕指针
detail-text = rgb("#444")  // 明细文字（略淡，区分主次）
```
