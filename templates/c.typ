// c.typ — 产物 C「速查卡」Typst 模板（单栏，按章分组）。
// 数据：/work/distilled/c.json（render.py 以 --root <skill_root> 编译，故用 root 相对路径）。
// 布局：章节分隔（navy 色块）→ 单栏卡片（类型徽章 + 标题 + 内容 + 源指针）。

#let data = json("/work/distilled/c.json")
#let meta = data.meta
#let head-font = (meta.cjk_font, "Microsoft YaHei", "SimHei")
#let body-font = (meta.cjk_serif, "SimSun", "Noto Serif CJK SC")
#let navy = rgb("#1a3a6b")

// 卡片类型颜色：公式=紫、规则=橙、对比=蓝、流程=绿
#let type-color(t) = {
  if t == "formula" { rgb("#7d3c98") }
  else if t == "rule"    { rgb("#d35400") }
  else if t == "table"   { rgb("#1a5ca8") }
  else if t == "flow"    { rgb("#1e8449") }
  else { rgb("#888888") }
}

// 类型中文名
#let type-zh(t) = {
  if t == "formula" { "公式" }
  else if t == "rule"    { "规则" }
  else if t == "table"   { "对比" }
  else if t == "flow"    { "流程" }
  else { t }
}

// 类型徽章
#let type-badge(t) = box(
  fill: type-color(t),
  inset: (x: 4pt, y: 2pt),
  radius: 2pt,
  text(font: head-font, size: 7.5pt, weight: "bold", fill: white)[#type-zh(t)]
)

// 渲染 table 类型的 body（竖线分隔格式）
#let render-table-body(body-str) = {
  let rows = body-str.split("\n").filter(r => r.trim() != "")
  if rows.len() == 0 { return }
  let cells-2d = rows.map(r => r.split(" | "))
  let ncols = cells-2d.first().len()
  let header = cells-2d.first()
  let data-rows = if cells-2d.len() > 1 { cells-2d.slice(1) } else { () }
  let header-cells = header.map(h => text(font: head-font, size: 8.5pt, weight: "bold")[#h.trim()])
  let data-cells = data-rows.flatten().map(c => text(size: 8.5pt)[#c.trim()])
  table(
    columns: ncols,
    stroke: 0.4pt + rgb("#ccc"),
    inset: (x: 4pt, y: 3pt),
    fill: (_, row) => if row == 0 { rgb("#dce6f1") } else if calc.rem(row, 2) == 0 { rgb("#f5f7fa") } else { white },
    ..(header-cells + data-cells)
  )
}

// 渲染非表格 body（多行文字，保留换行）
#let render-text-body(body-str) = {
  let lines = body-str.split("\n")
  let n = lines.len()
  for i in range(n) {
    text(size: 9pt)[#lines.at(i)]
    if i < n - 1 { linebreak() }
  }
}

// 单张卡片块
#let card-block(t) = {
  block(
    width: 100%,
    above: 0.6em,
    below: 0.2em,
    stroke: (left: 2.5pt + type-color(t.type)),
    inset: (left: 6pt, top: 5pt, bottom: 5pt, right: 3pt),
    {
      // 行1：类型徽章 + 卡片标题（粗体）
      // below: 0.5em 使标题与内容间有清晰分隔（参见 TYPOGRAPHY.md §间距折叠原则）
      block(below: 0.5em, {
        type-badge(t.type)
        h(4pt)
        text(font: head-font, size: 10pt, weight: "bold")[#t.label]
      })
      // 行2：卡片内容
      if t.type == "table" {
        render-table-body(t.body)
      } else {
        render-text-body(t.body)
      }
      // 行3：源指针（淡灰小字）
      v(0.2em)
      text(size: 7.5pt, fill: rgb("#999999"))[〔#t.pointer〕]
    }
  )
}

// 章标题（复用 L1/L2/QA 的 navy 色块样式）
#let chapter-head(title, first) = {
  if not first { pagebreak(weak: true) }
  block(
    width: 100%, fill: navy,
    inset: (x: 8pt, y: 6pt), radius: 2pt, below: 0.8em,
    text(font: head-font, size: 14pt, weight: "bold", fill: white)[#title]
  )
}

#set document(title: meta.title, author: "开卷考课件整理 skill")
#set page(
  paper: "a4",
  margin: (x: 2cm, top: 1.6cm, bottom: 1.3cm),
  footer: context [
    #set text(size: 7.5pt, fill: gray)
    速查卡 · 公式 / 规则 / 对比 / 流程
    #h(1fr)
    #counter(page).display()
  ],
)
#set text(font: body-font, size: 9.5pt, lang: "zh")
#set par(justify: true, leading: 0.75em, spacing: 0.55em)

// ---- 抬头 ----
#align(center)[
  #text(font: head-font, size: 19pt, weight: "bold", fill: navy)[#meta.title]
  #linebreak()
  #text(size: 9pt, fill: gray)[
    自动整理 · 共 #meta.total_cards 张卡片 · #meta.total_chapters 章
  ]
  #linebreak()
  #text(size: 8pt, fill: rgb("#aa3333"))[内容均来自 PPT 原文逐字提取，以判断/操作为中心]
]
#v(0.4em)

// 类型图例
#block(above: 0.3em, below: 0.9em, {
  type-badge("formula")
  text(size: 8.5pt, font: head-font)[ 公式  ]
  h(6pt)
  type-badge("rule")
  text(size: 8.5pt, font: head-font)[ 规则  ]
  h(6pt)
  type-badge("table")
  text(size: 8.5pt, font: head-font)[ 对比  ]
  h(6pt)
  type-badge("flow")
  text(size: 8.5pt, font: head-font)[ 流程]
})

// ---- 正文（每章：章头 + 卡片列表）----
#let first = true
#for ch in data.chapters {
  if ch.cards.len() > 0 {
    chapter-head(ch.title, first)
    first = false
    for t in ch.cards {
      card-block(t)
    }
  }
}
