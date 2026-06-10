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

---

# L2 排版配置参考

本文档记录 `l2.typ` 中经过调试验证的双栏关键词索引排版参数。

## 核心参数

### 页面（比 L1 稍窄边距，为双栏留余量）
```typst
#set page(
  paper: "a4",
  margin: (x: 1.8cm, top: 1.6cm, bottom: 1.3cm),
)
```

### 字体与段落
```typst
#set text(font: body-font, size: 9.5pt, lang: "zh")
#set par(justify: true, leading: 0.75em, spacing: 0.55em)
```
- 正文比 L1 小 1pt（9.5pt vs 10.5pt），使双栏词条更紧凑
- `spacing: 0.55em` 略小于 L1 的 0.72em，适合索引密度

### 双栏布局
```typst
columns(2, gutter: 1.2em)[...]
```
- 每章 navy 色块标题占全宽（位于 `columns` 块外），避免章头被折入栏内

## 词条卡间距（关键，经调试定型）

```typst
// 词条卡外框
block(above: 0.55em, below: 0.15em,
      inset: (left: 6pt, top: 5pt, bottom: 5pt, right: 3pt), ...)

// 词条名行（徽章 + 粗体术语）→ 定义文字
block(below: 0.6em, ...)    // ← 调试关键值
```

### 为什么词条名的 below 是 0.6em

`leading: 0.75em` 是正文段落换行的基线间距。词条名（粗体 10pt）与其下方定义文字（9pt）
之间的间距若小于 leading，视觉上会显得"粘连"——读者难以区分"词条名结束、定义开始"。

调试路径（依据折叠机制：实际间距 = `max(上块.below, 下块.above)`）：

| 尝试值 | 视觉效果 | 结论 |
|---|---|---|
| `below: 0.3em` | 词条名与定义粘连，层级感弱 | ✗ 过窄 |
| `below: 0.6em` | 与正文换行视觉相当，层级清晰 | ✓ 定型值 |

同时将 `inset.top/bottom` 从 3pt/4pt 调为 5pt/5pt，使每张词条卡顶底留白对称。

## 频率徽章颜色

```typst
高 = rgb("#c0392b")   // 红：核心概念，高视觉权重
中 = rgb("#1a5ca8")   // 蓝：重要术语（与 QA 简答题徽章同色，统一语义）
低 = rgb("#888888")   // 灰：一般词汇，低视觉权重
```

左色带颜色与徽章同色（`stroke: (left: 2.5pt + freq-color(t.freq))`），
使频率信息同时体现在两个位置，扫读时即可感知重要性。

---

# C 排版配置参考

本文档记录 `c.typ` 中速查卡的排版参数（单栏，卡片布局）。
参数以 L2 为基础设计；实际运行后如有调整请更新此处。

## 核心参数

### 页面（与 L1 相同边距，单栏不需要为双栏留余量）
```typst
#set page(
  paper: "a4",
  margin: (x: 2cm, top: 1.6cm, bottom: 1.3cm),
)
```

### 字体与段落（与 L2 相同）
```typst
#set text(font: body-font, size: 9.5pt, lang: "zh")
#set par(justify: true, leading: 0.75em, spacing: 0.55em)
```

## 卡片间距

```typst
// 卡片外框
block(above: 0.6em, below: 0.2em,
      inset: (left: 6pt, top: 5pt, bottom: 5pt, right: 3pt), ...)

// 标题行（徽章 + 粗体标签）→ 内容
block(below: 0.5em, ...)    // 与 L2 的 0.6em 略小；标题-内容间距略紧（速查卡密度更高）
```

设计依据：与 L2 相同的间距折叠原则（`max(above, below) ≥ leading`）。
`block.below: 0.5em` < `leading: 0.75em`，但因速查卡内容多为短行（公式/条件列表），
视觉上不会粘连。如测试后感觉标题与内容仍过近，可调为 `0.6em`。

## 卡片类型颜色语义

```typst
公式 formula = rgb("#7d3c98")  // 紫：数字/计算，最精确
规则 rule    = rgb("#d35400")  // 橙：条件判断，需注意
对比 table   = rgb("#1a5ca8")  // 蓝：对比信息（与 QA 简答题同色，统一数据类语义）
流程 flow    = rgb("#1e8449")  // 绿：操作流程，表示"动起来"
```

左色带与徽章同色（`stroke: (left: 2.5pt + type-color(t.type))`）。

## 对比表渲染

`table` 类型卡片的 body 为竖线分隔格式（` | ` 两侧带空格），在 Typst 中动态解析为表格：
- 第一行 = 表头（蓝灰底色 `#dce6f1`，加粗 8.5pt）
- 偶数数据行 = 浅灰底色 `#f5f7fa`
- 列宽由 Typst 自动均分

---

# M 排版配置参考

本文档记录 `m.typ` 中彩色思维导图卡片网格的排版参数（单栏，全局总览 + 逐章分支卡片）。

## 核心参数

### 页面（与 L1 相同，单栏不需为双栏留余量）
```typst
#set page(
  paper: "a4",
  margin: (x: 1.5cm, top: 1.4cm, bottom: 1.2cm),
)
```
- 左右边距比 L1 略窄（1.5cm vs 2cm），为 2 列分支卡片网格留更多宽度

### 字体与段落
```typst
#set text(font: body-font, size: 9pt, lang: "zh")
#set par(justify: false, leading: 0.7em, spacing: 0.45em)
```
- `justify: false`：思维导图节点为短句，强制对齐反而会拉宽
- `size: 9pt`：比 L2 小 0.5pt，节点密度更高

## 颜色系统（双调色板）

### 章节颜色（深色系，8 色循环）
```
ch-1 = rgb("#1a3a6b")  深蓝（海军）
ch-2 = rgb("#6c3483")  深紫
ch-3 = rgb("#a93226")  深红
ch-4 = rgb("#b7770d")  暗金
ch-5 = rgb("#1a6b3c")  深绿
ch-6 = rgb("#1a5296")  皇家蓝
ch-7 = rgb("#5d6d7e")  石板灰
ch-8 = rgb("#117a65")  深松石
```
章节颜色用于：页面顶部标题色块背景、全局总览 tile 标题行背景、章节卡片边框颜色。

### 分支颜色（彩色系，12 色循环）
```
br-0  = rgb("#e74c3c")  红
br-1  = rgb("#e67e22")  橙
br-2  = rgb("#d4ac0d")  金黄
br-3  = rgb("#27ae60")  绿
br-4  = rgb("#16a085")  松石
br-5  = rgb("#2980b9")  蓝
br-6  = rgb("#8e44ad")  紫
br-7  = rgb("#c0392b")  深红
br-8  = rgb("#1abc9c")  翡翠
br-9  = rgb("#d35400")  橙红
br-10 = rgb("#7d3c98")  深紫
br-11 = rgb("#1a5ca8")  皇家蓝
```
分支颜色用于：分支卡片左边框（`3pt + br-color`）、卡片浅色背景（`br-color.lighten(90%)`）、
分支标题文字、全局总览 tile 内的 pill 边框与背景（`br-color.lighten(85%)`）。

## 分支卡片间距

```typst
// 分支卡片外框
block(above: 0.5em, below: 0.2em,
      inset: (left: 7pt, top: 5pt, bottom: 5pt, right: 5pt),
      stroke: (left: 3pt + br-color), ...)

// 分支标题行 → 节点列表
block(below: 0.4em, ...)
```

设计依据：思维导图节点为短句（12–25 字），不需要 L2 词条的 `below: 0.6em`；
`0.4em` 在 `leading: 0.7em` 下有轻微折叠，标题与内容之间有可辨识的层级感。

## 布局说明

- **全局总览页**：`grid(columns: 2)` 的章节 tile 网格，每个 tile 内用 inline `box` 展示分支 pill，自动换行
- **逐章页**：`grid(columns: 2)` 的分支卡片网格，卡片高度由内容决定，Typst 自动处理高度差异
