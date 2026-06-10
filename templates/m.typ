// m.typ — 产物 M「思维导图」Typst 模板（单栏，全局总览 + 逐章卡片网格）。
// 数据：/work/distilled/m.json（render.py 以 --root <skill_root> 编译，故用 root 相对路径）。
// 布局：第1页全局总览（章节 tile 网格）→ 每章一页（分支卡片 2 列网格，彩色左边框）。

#let data = json("/work/distilled/m.json")
#let meta = data.meta
#let head-font = (meta.cjk_font, "Microsoft YaHei", "SimHei")
#let body-font = (meta.cjk_serif, "SimSun", "Noto Serif CJK SC")

// 章节颜色调色板（深色系，8 色循环）
#let ch-palette = (
  rgb("#1a3a6b"),  // 深蓝（海军）
  rgb("#6c3483"),  // 深紫
  rgb("#a93226"),  // 深红
  rgb("#b7770d"),  // 暗金
  rgb("#1a6b3c"),  // 深绿
  rgb("#1a5296"),  // 皇家蓝
  rgb("#5d6d7e"),  // 石板灰
  rgb("#117a65"),  // 深松石
)

// 分支颜色调色板（彩色系，12 色循环）
#let br-palette = (
  rgb("#e74c3c"),  // 红
  rgb("#e67e22"),  // 橙
  rgb("#d4ac0d"),  // 金黄
  rgb("#27ae60"),  // 绿
  rgb("#16a085"),  // 松石
  rgb("#2980b9"),  // 蓝
  rgb("#8e44ad"),  // 紫
  rgb("#c0392b"),  // 深红
  rgb("#1abc9c"),  // 翡翠
  rgb("#d35400"),  // 橙红
  rgb("#7d3c98"),  // 深紫
  rgb("#1a5ca8"),  // 皇家蓝
)

#let ch-color(idx) = ch-palette.at(calc.rem(idx - 1, ch-palette.len()))
#let br-color(i)   = br-palette.at(calc.rem(i,       br-palette.len()))

// --- 页面设置 ---
#set document(title: meta.title, author: "开卷考课件整理 skill")
#set page(
  paper: "a4",
  margin: (x: 1.5cm, top: 1.4cm, bottom: 1.2cm),
  footer: context [
    #set text(size: 7pt, fill: gray)
    #meta.course_title · 思维导图
    #h(1fr)
    #counter(page).display()
  ],
)
#set text(font: body-font, size: 9pt, lang: "zh")
#set par(justify: false, leading: 0.7em, spacing: 0.45em)

// --- 组件 ---

// 章页顶部色块标题
#let page-header(title, color) = block(
  width: 100%,
  fill: color,
  inset: (x: 10pt, y: 7pt),
  radius: (top-left: 4pt, top-right: 4pt),
)[
  #text(font: head-font, size: 13pt, weight: "bold", fill: white)[#title]
]

// 全局总览的章节卡片（带章节色背景标题 + 彩色分支 pill）
#let global-tile(ch) = {
  let cc = ch-color(ch.chapter_index)
  block(
    width: 100%,
    stroke: 0.4pt + cc,
    radius: 4pt,
    clip: true,
  )[
    #block(
      width: 100%,
      fill: cc,
      inset: (x: 7pt, y: 5pt),
    )[
      #text(font: head-font, size: 9.5pt, weight: "bold", fill: white)[#ch.chapter_title]
    ]
    #block(inset: (x: 6pt, top: 5pt, bottom: 5pt, right: 4pt))[
      #for (i, b) in ch.branches.enumerate() {
        let bc = br-color(i)
        box(
          fill: bc.lighten(85%),
          stroke: 0.3pt + bc,
          inset: (x: 4pt, y: 2pt),
          radius: 3pt,
        )[
          #text(font: head-font, size: 7.5pt, fill: bc.darken(15%))[#b]
        ]
        h(3pt)
      }
    ]
  ]
}

// 每章的单个分支卡片（彩色左边框 + 浅色背景 + 节点列表）
#let branch-card(b, b-idx) = {
  let bc = br-color(b-idx)
  let nodes = b.nodes
  let n = nodes.len()
  block(
    width: 100%,
    stroke: (left: 3pt + bc),
    fill: bc.lighten(90%),
    inset: (left: 7pt, top: 5pt, bottom: 5pt, right: 5pt),
    radius: (right: 3pt),
    above: 0.5em,
    below: 0.2em,
  )[
    #block(below: 0.4em)[
      #text(font: head-font, size: 9.5pt, weight: "bold", fill: bc)[#b.title]
    ]
    #for i in range(n) {
      text(size: 8.5pt)[• #nodes.at(i)]
      if i < n - 1 { linebreak() }
    }
  ]
}

// 把一章所有分支渲染为卡片数组（供 grid 展开）
#let branch-cards(branches) = branches.enumerate().map(item => {
  let i = item.at(0)
  let b = item.at(1)
  branch-card(b, i)
})

// =====================
// === 渲染全局总览页 ===
// =====================
#let g = data.global

#page-header(g.course_title + " — 全局总览", rgb("#1a3a6b"))
#v(5pt)
#grid(
  columns: 2,
  gutter: 0.65em,
  ..g.chapters.map(ch => global-tile(ch))
)

// ========================
// === 渲染逐章思维导图 ===
// ========================
#for ch in data.chapters {
  pagebreak()

  let cc = ch-color(ch.chapter_index)
  page-header(ch.chapter_title, cc)
  v(5pt)

  grid(
    columns: 2,
    gutter: 0.55em,
    ..branch-cards(ch.branches)
  )
}
