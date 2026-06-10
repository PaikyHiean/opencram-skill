// l2.typ — 产物 L2「关键词索引」Typst 模板（竖向·章内双栏）。
// 数据：/work/distilled/l2.json（render.py 以 --root <skill_root> 编译，故用 root 相对路径）。
// 布局：章节分隔（navy 色块）→ 双栏词条（频率徽章 + 术语 + 定义 + 源指针）。

#let data = json("/work/distilled/l2.json")
#let meta = data.meta
#let head-font = (meta.cjk_font, "Microsoft YaHei", "SimHei")
#let body-font = (meta.cjk_serif, "SimSun", "Noto Serif CJK SC")
#let navy = rgb("#1a3a6b")

#let refbase-name(r) = {
  if r == "source" { "对源文件" }
  else if r == "l0" { "对L0" }
  else { r }
}

// 频率分级颜色：高=红、中=蓝、低=灰
#let freq-color(f) = {
  if f == "高" { rgb("#c0392b") }
  else if f == "中" { rgb("#1a5ca8") }
  else { rgb("#888888") }
}

// 频率徽章（有色圆角矩形）
#let freq-badge(f) = box(
  fill: freq-color(f),
  inset: (x: 4pt, y: 2pt),
  radius: 2pt,
  text(font: head-font, size: 7.5pt, weight: "bold", fill: white)[#f]
)

#set document(title: meta.title, author: "开卷考课件整理 skill")
#set page(
  paper: "a4",
  margin: (x: 1.8cm, top: 1.6cm, bottom: 1.3cm),
  footer: context [
    #set text(size: 7.5pt, fill: gray)
    关键词索引 · 源指针：#refbase-name(meta.reference_base)
    #h(1fr)
    #counter(page).display()
  ],
)
#set text(font: body-font, size: 9.5pt, lang: "zh")
#set par(justify: true, leading: 0.75em, spacing: 0.55em)

// 单个词条块：左色带 + 术语 + 定义 + 源指针
#let term-block(t) = {
  block(
    width: 100%,
    above: 0.55em,
    below: 0.15em,
    stroke: (left: 2.5pt + freq-color(t.freq)),
    inset: (left: 6pt, top: 3pt, bottom: 4pt, right: 3pt),
    {
      // 行1：频率徽章 + 术语（粗体）
      block(below: 0.3em, {
        freq-badge(t.freq)
        h(4pt)
        text(font: head-font, size: 10pt, weight: "bold")[#t.term]
      })
      // 行2：定义（若有，来自 PPT 原文）
      if t.definition != "" {
        block(
          below: 0.25em,
          text(size: 9pt, fill: rgb("#333333"))[#t.definition]
        )
      }
      // 行3：源指针（淡灰小字）
      text(size: 7.5pt, fill: rgb("#999999"))[〔#t.pointer〕]
    }
  )
}

// 章标题（复用 L1/QA 的 navy 色块样式）
#let chapter-head(title, first) = {
  if not first { pagebreak(weak: true) }
  block(
    width: 100%, fill: navy,
    inset: (x: 8pt, y: 6pt), radius: 2pt, below: 0.7em,
    text(font: head-font, size: 14pt, weight: "bold", fill: white)[#title]
  )
}

// ---- 抬头 ----
#align(center)[
  #text(font: head-font, size: 19pt, weight: "bold", fill: navy)[#meta.title]
  #linebreak()
  #text(size: 9pt, fill: gray)[
    自动整理 · 共 #meta.total_terms 个词条 · 源指针：#refbase-name(meta.reference_base)
  ]
  #linebreak()
  #text(size: 8pt, fill: rgb("#aa3333"))[词条与定义均来自 PPT 原文逐字提取；无定义者仅标页码来源]
]
#v(0.4em)

// 频率图例
#block(above: 0.3em, below: 0.9em, {
  freq-badge("高")
  text(size: 8.5pt, font: head-font)[ 核心概念  ]
  h(6pt)
  freq-badge("中")
  text(size: 8.5pt, font: head-font)[ 重要术语  ]
  h(6pt)
  freq-badge("低")
  text(size: 8.5pt, font: head-font)[ 一般词汇]
})

// ---- 正文（每章：章头全宽 + 双栏词条）----
#let first = true
#for ch in data.chapters {
  if ch.terms.len() > 0 {
    chapter-head(ch.title, first)
    first = false
    columns(2, gutter: 1.2em)[
      #for t in ch.terms {
        term-block(t)
      }
    ]
  }
}
