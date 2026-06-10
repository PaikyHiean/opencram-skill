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
   必须物理分开并显式标注 `〔AI〕`。
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
- 需要 AI 判断时（见下），**按单章**读 `work/distilled/ai/in_<k>.json`，
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

> ⚠ 若后续 AI 增强管线已运行后才修改章节图，需重新运行 `prep_ai_distill.py`
> 并由子 agent 对受影响章重新蒸馏。

### Phase 2 · 产物勾选与参数（必须用户确认）
向用户给出 6 产物清单（默认勾 L0+L1），并设两项参数，写入 `work/config.json`：
```json
{ "reference_base": "source",  "compression": "conservative",
  "products": ["L0","L1"] }
```
- `reference_base`：`source`（带原件打印，默认）/ `l0`（带 L0 打印，显示 L0 页码）。
- `compression`：`conservative`（默认，可誊抄）/ `standard`（要点化）/ `aggressive`（骨架）。

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

#### 6a · 确定性基线（快速，纯抽取零臆造）
```
python scripts/distill_l1.py
python scripts/render.py l1
```
按 PPT 自身「幻灯片标题 + 项目符号缩进层级」机械重建大纲：
**章 → 一、二、节（带源指针）→ 1. 2. 点 → 明细（缩进）**；连续同标题幻灯片自动合并。
适合快速出初稿或不需要 AI 的情况。

#### 6b · AI 语义增强（推荐，语义归并 + 图片筛查）

**步骤一：切输入包**
```
python scripts/prep_ai_distill.py
```
把每章内容切为 `work/distilled/ai/in_<k>.json`，并写 `ai/index.json`。
每包只含该章幻灯片的标题/段落/表格/图片名，不含二进制。

**步骤二：子 agent 逐章蒸馏**
按 `ai/index.json` 逐章（或并行）派子 agent（角色定义见 `agents/distillation.md`），
每个只读自己那章的 `in_<k>.json`，产出 `out_<k>.json`：
```json
{
  "chapter_title": "...",
  "sections": [
    { "heading": "概念", "anchors": ["文件名#s2", ...],
      "points": [ {"text": "...", "details": ["..."]}, ... ],
      "tables": ["col1 | col2\n值 | 值"],
      "ai_generated": true }
  ]
}
```
- 子 agent 只负责**内容**：挑核心、去重、凝练、写小节标题，正文逐字。
- 编号（一、二）、源指针、图片路径由 `merge_ai_l1.py` 确定性添加，子 agent 不碰。

**步骤三：合并**
```
python scripts/merge_ai_l1.py
```
有 `out_<k>.json` 的章用 AI 版覆盖，其余保留确定性基线。结果写回 `work/distilled/l1.json`。

**步骤四：图片筛查（可选，显著减小 PDF 体积）**
```
python scripts/screen_images.py
```
生成 `work/distilled/ai/image_screen_in.json`（每节：文字摘要 + 图片路径列表）。
派子 agent（角色定义见 `agents/image_screening.md`）逐图裁决，产出 `image_screen_out.json`：
```json
{ "decisions": [
    { "sec_id": "ch0_sec2", "img": "work/extracted/.../xxx.png",
      "keep": true, "reason": "流程图，文字未涵盖" }
  ] }
```
然后写回：
```
python scripts/apply_image_screen.py
```

**步骤五：渲染与验证**
```
python scripts/render.py l1          # → outputs/L1.pdf
python scripts/verify_l1.py          # 可选：检查每节有源指针、锚点可解析
```
AI 生成的小节在 PDF 中以 `〔AI〕` 红色小字标注（不影响阅读，提示需核对原文）。

### Phase 7 · QA（简答/论述 QA 记录）

#### 步骤一：切输入包
```
python scripts/prep_qa.py
```
读 `chapters.json` + 各章 `content.json`，输出 `work/distilled/qa/in_<k>.json`（每章一包，
含正文 + 备注 `notes`——答案常藏在备注里）；并写 `qa/index.json`。

#### 步骤二：子 agent 逐章抽题
按 `qa/index.json` 逐章派子 agent（角色定义见 `agents/qa.md`），
每个只读自己那章的 `in_<k>.json`，产出 `out_<k>.json`：
```json
{
  "chapter_title": "...",
  "items": [
    { "type": "简答题",
      "question": "题目原文（逐字）",
      "answer":   "答案原文（或 AI 补充）",
      "anchors":  ["文件名#s5"],
      "ai_answer": false }
  ]
}
```
- 只收 PPT 原文里**确实出现的题目**，不自行出题。
- 有题无答 → AI 补答，`ai_answer: true`；逐字题目与 AI 答案保持物理分离（字段分离）。
- 子 agent 只回简报（题目数/AI 补答数），不回全文。

#### 步骤三：合并
```
python scripts/merge_qa.py
```
读所有 `out_<k>.json`，添加编号（`Q1.`/`Q2.`...）与源指针，写 `work/distilled/qa.json`。

#### 步骤四：渲染
```
python scripts/render.py qa           # → outputs/QA.pdf
```
AI 补答在 PDF 中以 `〔AI〕` 红色小字标注；题目/答案区之间用细横线分隔。

### Phase 8 · 其余产物（L2/C/M）
**本版尚未实现**，留作下一迭代：L2 关键词索引、C 速查卡、M 思维导图。
实现时复用同一套锚点/映射/参考基准机制，渲染同样走 Typst（`render.py <target>`）。

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
| `work/extracted/<stem>/content.json` | 幻灯片结构化数据（锚点/标题/段落/表/图名） |
| `work/extracted/<stem>/slides.md` | 人读版归一化 Markdown |
| `work/extracted/<stem>/images/` | 从 PPT 抠出的内嵌图 |
| `work/maps/<stem>.json` | 锚点↔PDF页映射、对齐状态 |
| `work/l0_pagemap.json` | 锚点→L0页（`reference_base=l0` 换算用） |
| `work/l0_deleted.json` | build_l0 删除的废页清单（供复核） |
| `work/distilled/l1.json` | L1 主数据（基线或 AI 合并后的最终版） |
| `work/distilled/ai/index.json` | 各章 k 值→输入/输出文件映射 |
| `work/distilled/ai/in_<k>.json` | 第 k 章的 AI 输入包（幻灯片摘要） |
| `work/distilled/ai/out_<k>.json` | 第 k 章的 AI 蒸馏输出 |
| `work/distilled/ai/image_screen_in.json` | 图片筛查 agent 输入包 |
| `work/distilled/ai/image_screen_out.json` | 图片筛查 agent 裁决 |
| `work/distilled/qa/index.json` | QA 各章 k 值→输入/输出文件映射 |
| `work/distilled/qa/in_<k>.json` | 第 k 章的 QA agent 输入包（含备注） |
| `work/distilled/qa/out_<k>.json` | 第 k 章的 QA agent 产出（原题+答案） |
| `work/distilled/qa.json` | QA 主数据（合并后，供渲染） |
| `outputs/L0.pdf` | 带书签清洗版全集 |
| `outputs/L1.pdf` | 核心知识手册 |
| `outputs/QA.pdf` | 简答/论述 QA 记录 |

## 安装为全局 skill
把 `SKILL.md scripts/ templates/ agents/` 复制到 `~/.claude/skills/open-book-exam-courseware/`。
`work/`、`outputs/`、课件文件夹是运行时/测试数据，不必随 skill 分发。
