// qa.typ — 产物 QA「简答/论述 QA 记录」Typst 模板（竖向·单栏）。
// 数据：/work/distilled/qa.json。
// 布局：章节分隔 → 每题：[类型徽章] Q编号 + 源指针 / 题目文字 / 答案文字（AI 标注）。

#let data = json("/work/distilled/qa.json")
#let meta = data.meta
#let head-font = (meta.cjk_font, "Microsoft YaHei", "SimHei")
#let body-font = (meta.cjk_serif, "SimSun", "Noto Serif CJK SC")
#let navy = rgb("#1a3a6b")

// 与 l1.typ 复用相同的 refbase 辅助函数
#let refbase-name(r) = {
  if r == "source" { "对源文件" }
  else if r == "l0" { "对L0" }
  else { r }
}

// 题目类型徽章颜色
#let type-color(t) = {
  if t == "简答题" { rgb("#1a5ca8") }
  else if t == "论述题" { rgb("#6b2fa0") }
  else if t == "案例题" { rgb("#007070") }
  else { rgb("#555555") }
}

#set document(title: meta.title, author: "开卷考课件整理 skill")
#set page(
  paper: "a4",
  margin: (x: 2cm, top: 1.6cm, bottom: 1.3cm),
  footer: context [
    #set text(size: 7.5pt, fill: gray)
    简答/论述 QA 记录 · 源指针：#refbase-name(meta.reference_base)
    #h(1fr)
    #counter(page).display()
  ],
)
#set text(font: body-font, size: 10.5pt, lang: "zh")
#set par(justify: true, leading: 0.82em, spacing: 0.72em)

// 多行文本：将 \n 转换为 Typst 换行
#let multiline(s) = {
  let lines = s.split("\n")
  for (i, ln) in lines.enumerate() {
    if i > 0 { linebreak() }
    ln
  }
}

// 类型徽章（有色圆角矩形）
#let type-badge(t) = box(
  fill: type-color(t),
  inset: (x: 5pt, y: 2.5pt),
  radius: 2pt,
  text(font: head-font, size: 8pt, weight: "bold", fill: white)[#t]
)

// 单条 QA 题目块
#let qa-item(item) = {
  block(breakable: true, width: 100%, above: 1em, below: 0.3em, {
    // 题头行：类型徽章 + 编号 + 源指针（右对齐）
    block(width: 100%, below: 0.45em, {
      type-badge(item.type)
      text(font: head-font, size: 10pt, weight: "bold")[ #item.num]
      h(1fr)
      text(size: 8pt, fill: rgb("#888"))[〔#item.pointer〕]
    })
    // 题目正文（加粗，稍大）
    block(
      inset: (left: 0.6em),
      below: 0.5em,
      text(font: head-font, size: 10.5pt, weight: "bold")[#multiline(item.question)]
    )
    // 细分隔线
    line(length: 100%, stroke: 0.5pt + rgb("#d0d0d0"))
    // 答案区（左侧竖线标注，与题目视觉分离）
    block(
      above: 0.45em,
      below: 0.3em,
      width: 100%,
      {
        // "答：" 前缀 + AI 徽章（若有）
        text(font: head-font, weight: "bold")[答：]
        if item.at("ai_answer", default: false) {
          text(size: 7.5pt, fill: rgb("#aa3333"))[ 〔AI〕]
        }
        [ ]
        text(fill: rgb("#1a1a1a"))[#multiline(item.answer)]
      }
    )
  })
  // 题目间淡分隔线
  line(length: 100%, stroke: (paint: rgb("#ebebeb"), thickness: 1pt))
}

// 章标题（与 L1 相同的 navy 色块）
#let chapter-head(title, first) = {
  if not first { pagebreak(weak: true) }
  block(
    width: 100%, fill: navy,
    inset: (x: 8pt, y: 6pt), radius: 2pt, below: 0.6em,
    text(font: head-font, size: 14pt, weight: "bold", fill: white)[#title]
  )
}

// ---- 抬头 ----
#align(center)[
  #text(font: head-font, size: 19pt, weight: "bold", fill: navy)[#meta.title]
  #linebreak()
  #text(size: 9pt, fill: gray)[
    自动整理 · 共 #meta.total_items 题 · 源指针：#refbase-name(meta.reference_base)
  ]
  #linebreak()
  #text(size: 8pt, fill: rgb("#aa3333"))[PPT 原有题目与答案逐字保留；〔AI〕标记表示答案为 AI 补充，考场使用前请核对原文]
]
#v(0.5em)

// ---- 正文 ----
#for (i, ch) in data.chapters.enumerate() {
  if ch.items.len() > 0 {
    chapter-head(ch.title, i == 0)
    for item in ch.items { qa-item(item) }
  }
}
