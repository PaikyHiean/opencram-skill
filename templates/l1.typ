// l1.typ — 产物 L1「核心知识手册」Typst 模板（竖向·单栏·层级大纲）。
// 数据：/work/distilled/l1.json（render.py 以 --root <skill_root> 编译，故用 root 相对路径）。
// 层级：第N章 → 一、二、节（带源指针）→ 1. 2. 点 → 明细（缩进）。源指针只在节级。

#let data = json("/work/distilled/l1.json")
#let meta = data.meta
#let head-font = (meta.cjk_font, "Microsoft YaHei", "SimHei")
#let body-font = (meta.cjk_serif, "SimSun", "Noto Serif CJK SC")
#let navy = rgb("#1a3a6b")

// 顶层辅助函数：在代码块（{}）中定义，多行 if-else 不会被误渲染为文本
#let compress-name(c) = {
  if c == "conservative" { "保守（可誊抄）" }
  else if c == "standard" { "标准（要点化）" }
  else if c == "aggressive" { "骨架" }
  else { c }
}
#let refbase-name(r) = {
  if r == "source" { "对源文件" }
  else if r == "l0" { "对L0" }
  else { r }
}

#set document(title: meta.title, author: "开卷考课件整理 skill")
#set page(
  paper: "a4",
  margin: (x: 2cm, top: 1.6cm, bottom: 1.3cm),
  footer: context [
    #set text(size: 7.5pt, fill: gray)
    核心知识手册 · 档位：#compress-name(meta.compression) · 源指针：#refbase-name(meta.reference_base)
    #h(1fr)
    #counter(page).display()
  ],
)
#set text(font: body-font, size: 10.5pt, lang: "zh")
#set par(justify: true, leading: 0.82em, spacing: 0.72em)

#let multiline(s) = {
  let lines = s.split("\n")
  for (i, ln) in lines.enumerate() {
    if i > 0 { linebreak() }
    ln
  }
}

// 表格：解析 " | " 分隔的字符串，渲染成带边框的网格
#let render-table(t) = {
  let rows = t.split("\n").filter(r => r.trim() != "")
  if rows.len() == 0 { return [] }
  let row-cells = rows.map(r => r.split(" | "))
  let n-cols = row-cells.fold(0, (mx, row) => calc.max(mx, row.len()))
  if n-cols == 0 { return [] }

  let cells = ()
  for (ri, row) in row-cells.enumerate() {
    for ci in range(n-cols) {
      let val = if ci < row.len() { row.at(ci).trim() } else { "" }
      let bg = if calc.rem(ri, 2) == 0 { rgb("#edf0f6") } else { white }
      cells.push(table.cell(fill: bg)[#text(size: 8.5pt, font: head-font)[#val]])
    }
  }
  block(above: 0.5em, below: 0.5em, width: 100%,
    table(
      columns: n-cols,
      stroke: 0.5pt + rgb("#aaa"),
      inset: (x: 5pt, y: 4pt),
      ..cells
    )
  )
}

// 一个小节：一、标题 + 〔源〕；下挂 1./2. 点与明细
#let section(sec) = {
  block(breakable: true, width: 100%, above: 0.85em, below: 0.5em, {
    // 节标题行（左标题 / 右源指针）
    block(width: 100%, {
      text(font: head-font, size: 11pt, weight: "bold", fill: navy)[#sec.label#sec.heading]
      if sec.at("ai_generated", default: false) {
        text(size: 7.5pt, fill: rgb("#aa3333"))[ 〔AI〕]
      }
      h(1fr)
      text(size: 8pt, fill: rgb("#888"))[〔#sec.pointer〕]
    })
    // 1. 2. 点
    for pt in sec.points {
      block(width: 100%, inset: (left: 1.1em), above: 0.62em, below: 0.45em, {
        [#text(weight: "bold")[#pt.num] #pt.text]
        for d in pt.details {
          block(inset: (left: (d.level * 1.1em)), above: 0.75em, below: 0.5em)[
            #text(fill: rgb("#444"))[· #d.text]
          ]
        }
      })
    }
    // 表格
    for t in sec.tables { render-table(t) }
    // 内嵌原图（原样抠取）
    for img in sec.images {
      align(center, box(image(img, width: 58%)))
    }
  })
}

// 章标题
#let chapter-head(title, first) = {
  if not first { pagebreak(weak: true) }
  block(width: 100%, fill: navy, inset: (x: 8pt, y: 6pt), radius: 2pt, below: 0.6em,
    text(font: head-font, size: 14pt, weight: "bold", fill: white)[#title])
}

// ---- 抬头 ----
#align(center)[
  #text(font: head-font, size: 19pt, weight: "bold", fill: navy)[#meta.title]
  #linebreak()
  #text(size: 9pt, fill: gray)[
    自动整理 · 共 #meta.total_sections 个小节 · 档位：#compress-name(meta.compression) · 源指针：#refbase-name(meta.reference_base)
  ]
  #linebreak()
  #text(size: 8pt, fill: rgb("#aa3333"))[本手册按课件自身层级重组源材料，未新增事实；〔AI〕标记者请核对原文]
]
#v(0.4em)

// ---- 正文 ----
#let first = true
#for ch in data.chapters {
  let secs = ch.sections.filter(s => s.points.len() > 0 or s.images.len() > 0 or s.tables.len() > 0)
  if secs.len() > 0 {
    chapter-head(ch.title, first)
    first = false
    for sec in secs { section(sec) }
  }
}
