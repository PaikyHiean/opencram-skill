---
name: open-book-exam-courseware
description: >
  把一整个文件夹的文科课件（.ppt/.pptx/.pdf）整理成可带入开卷考考场的 PDF：
  L0 带书签清洗版全集、L1 核心知识手册、L2 关键词索引、C 速查卡、M 思维导图、
  QA 简答记录。强调"只重组不臆造、全程可溯源、零代码一键"。当用户提到"开卷考、
  整理课件、复习资料、把 PPT 做成手册/索引/速查、考试 PDF、课件溯源"等时使用。
---

# 开卷考课件整理 Skill

把用户指定文件夹里的课件（.ppt/.pptx/.pdf）自动整理成最多 6 种可打印带考的 PDF，
每条知识点都能溯源回考场上手里那份打印件的页码。

## 不可妥协的铁律（每一步都遵守）

1. **抽取与生成严格分离，绝不臆造。** 只重组、压缩、组织源材料；任何 AI 生成内容
   必须物理分开并显式标注「AI 生成，待核」。
2. **全程可溯源。** 每条知识点挂一个来源锚点 = `(源文件名, 源内页序号)`，永不漂移。
3. **显示指针按"参考基准"换算。** 带原件打印→显示「源：文件名 s.N」；带 L0 打印→
   显示「L0 p.X」（用 `work/l0_pagemap.json` 换算）。不要把 L0 页码硬编码进知识点。
4. **图原样抠取，绝不重绘。** ER 图/概念图从原图抠出内嵌。
5. **文科默认保守压缩**（可直接誊抄）。
6. **开工前必须先与用户确认**章节结构与所需产物（Phase 0–2，不可跳过）。

## Token 纪律（重要）

**主控（你）永不加载课件原文。** 全程"脚本落盘 → 读盘 → 只看简报"：
- 所有重活由 `scripts/` 下的 Python 脚本做，结果写到 `work/`。
- 你只读脚本打印的**简报**与 `work/*.json`，绝不把 `work/extracted/*/slides.md`
  的全文一次性读进上下文。
- 需要 AI 判断时（见下），**按单章**读 `work/extracted/<stem>/content.json`，
  用完即弃；章多可派 Task 子 agent 并行，每个只领一章。

## 运行环境

- 所有脚本用 Python 跨平台运行。Windows 控制台调用时先设 UTF-8：
  PowerShell 里 `$env:PYTHONUTF8=1; [Console]::OutputEncoding=[Text.UTF8Encoding]::new()`。
- 依赖：python-pptx、pypdf、reportlab（pip）；LibreOffice（转 PDF/pptx）；Typst（渲染）。
  缺中文字体会导致转 PDF 乱码。

---

## 编排流程（Phase 0–9）

> 命令均在 skill 根目录执行。`<课件文件夹>` 是用户给的路径。

### Phase 0 · 盘点
```
python scripts/inventory.py "<课件文件夹>"
```
读简报：文件清单、类型、文字层探测。`.ppt` 会显示"文字层待定"（正常，旧格式留待抽取确认）。
若出现"疑似无文字层"警告（扫描件）→ **本期不做 OCR**，提示用户该文件抽取会很少，问是否仍纳入。

### Phase 1 · 章节识别（必须用户确认）
```
python scripts/detect_chapters.py
```
向用户**展示草稿章节图**，逐条提示需确认项（多文件同章？无章号文件归属？）。
用户可合并/拆分/重命名/标记附录或习题。按用户意见**直接编辑 `work/drafts/chapters.json`**
（改 `chapters[].title`、移动 `files`、把项移入/移出 `unfiled`）后再继续。**不要替用户拍板。**

### Phase 2 · 产物勾选与参数（必须用户确认）
向用户给出 6 产物清单（默认勾 L0+L1），并设两项参数，写入 `work/config.json`：
```json
{ "reference_base": "source",  "compression": "conservative",
  "products": ["L0","L1"] }
```
- `reference_base`：`source`（带原件打印，默认）/ `l0`（带 L0 打印，显示 L0 页码）。
- `compression`：`conservative`（默认，可誊抄）/ `standard`（要点化）/ `aggressive`（骨架）。
- 给用户看 §"三档对比"示例帮助理解（见 TODO.md §5）。

### Phase 3 · bootstrap（依赖体检/安装，征求一次同意）
```
python scripts/doctor.py            # 仅检测
python scripts/doctor.py --install  # 取得同意后安装缺失项（pip + winget）
```
全绿再继续。LibreOffice ~350MB，安装前**明确征求一次用户同意**。

### Phase 4 · 抽取（建 L0 页空间 + 锚点映射）
```
python scripts/extract.py
```
每源：LibreOffice 转 PDF（建 L0 页空间）+ 转 pptx 抽文字/表/备注/内嵌图；
建 `(文件名,序号)→PDF页` 映射 + `content.json`。读简报核对：每源"X 张 / PDF Y 页"
应**对齐**；不齐或文本近零会标⚠，需复核。

### Phase 5 · L0（带书签清洗版全集）
```
python scripts/build_l0.py            # 默认删空白等废页 + 盖来源戳
python scripts/build_l0.py --keep-all # 一页不删（最保守）
```
产出 `outputs/L0.pdf`、`work/l0_pagemap.json`（锚点→L0页，L1/L2 换算用）、
`work/l0_deleted.json`（删了哪些页，**请向用户复核删页清单**）。

### Phase 6 · L1（核心知识手册）
```
python scripts/distill_l1.py          # 确定性·结构保留蒸馏（纯抽取，零臆造）
python scripts/render.py l1           # Typst 渲染（竖向单栏）→ outputs/L1.pdf
```
- 按 PPT 自身「幻灯片标题 + 项目符号缩进层级」机械重建大纲：
  **章 → 一、二、节（带源指针）→ 1. 2. 点 → 明细（缩进）**；连续同标题幻灯片自动合并；
  源指针只标在**节级**。`config.compression` 只裁明细深度、不改写文本，**不新增事实**。
- **AI 增强（可选）**：要更聪明的语义归并/补标题时，按单章读
  `work/extracted/<stem>/content.json`，产出更优的 `work/distilled/l1.json`
  （结构同基线：`chapters[].sections[]`）再 `render.py l1`。AI 改写的小节须置
  `"ai_generated": true`，模板会标「AI 生成，待核」。

### Phase 7–8 · 其余产物（L2/C/M/QA）
**本版尚未实现**，留作下一迭代：L2 关键词索引、C 速查卡、M 思维导图、QA 简答记录。
实现时复用同一套锚点/映射/参考基准机制，渲染同样走 Typst（`render.py <target>`）。
QA 中 PPT 原有题目与答案**逐字保留**；有题无答时 AI 补答并标「AI 生成，待核」、与抽取物理分开。

### Phase 9 · 复核（Coverage / 防臆造）
- 每章都有产物？对照 `chapters.json`。
- L1 抽取条目无臆造（基线天然满足；AI 增强条目逐条可回源核对）。
- 低置信处（页数不齐、疑似扫描件、AI 生成）向用户标出待核。

---

## 关键产物与文件

| 路径 | 含义 |
|---|---|
| `work/manifest.json` | Phase 0 盘点 |
| `work/drafts/chapters.json` | 章节图（**用户确认后**锁定） |
| `work/config.json` | 参考基准 / 精简档 / 选中产物 |
| `work/extracted/<stem>/{content.json,slides.md,images/}` | 抽取产物（结构化+人读+原图） |
| `work/maps/<stem>.json` | 锚点↔PDF页映射、对齐状态 |
| `work/l0_pagemap.json` | 锚点→L0页（参考基准=l0 时换算用） |
| `outputs/L0.pdf` … `outputs/L1.pdf` | 最终产物 |

## 安装为全局 skill
把 `SKILL.md scripts/ templates/ agents/` 复制到 `~/.claude/skills/open-book-exam-courseware/`。
`work/`、`outputs/`、`PPT/` 是运行时/测试数据，不必随 skill 分发。
