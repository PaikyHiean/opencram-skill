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
- 依赖：python-pptx、pypdf、reportlab、matplotlib（pip）；LibreOffice（转 PDF/pptx）；
  Typst（渲染 L1/QA/L2/C）。**M 思维导图用 matplotlib 渲染（render_m.py），不走 Typst。**
  缺中文字体会导致转 PDF 乱码。

---

## 编排流程（Phase 0–11）

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
产出 `outputs/清洗版PPT全集.pdf`（中间名 `L0.pdf`，最终自动改名）、`work/l0_pagemap.json`（锚点→L0页，L1/L2 换算用）、
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
python scripts/render.py l1          # → outputs/核心知识手册.pdf
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
python scripts/render.py qa           # → outputs/简答库.pdf
```
AI 补答在 PDF 中以 `〔AI〕` 红色小字标注；题目/答案区之间用细横线分隔。

### Phase 8 · L2（关键词索引）

#### 步骤一：切输入包
```
python scripts/prep_l2.py
```
读 `chapters.json` + 各章 `content.json`，输出 `work/distilled/l2/in_<k>.json`（每章一包，
含正文 + 表格，**不含备注**——关键词判断不依赖备注）；并写 `l2/index.json`。

#### 步骤二：子 agent 逐章抽词
按 `l2/index.json` 逐章派子 agent（角色定义见 `agents/keyword.md`），
每个只读自己那章的 `in_<k>.json`，产出 `out_<k>.json`：
```json
{
  "chapter_title": "...",
  "terms": [
    { "term": "近因原则",
      "freq": "高",
      "definition": "保险赔偿应基于直接有效地导致损失的最近原因",
      "anchors":  ["文件名#s5", "文件名#s8"] }
  ]
}
```
- 只收专业/学科特定术语，不自行出题、不 AI 补充定义。
- `definition` 来自 PPT 原文逐字摘录；无定义则留空字符串。
- 子 agent 只回简报（词条数/频率分布），不回全文 JSON。

#### 步骤三：合并
```
python scripts/merge_l2.py
```
读所有 `out_<k>.json`，章内按频率排序（高>中>低），添加源指针，写 `work/distilled/l2.json`。

#### 步骤四：渲染
```
python scripts/render.py l2           # → outputs/关键词索引.pdf
```
双栏布局，每章 navy 色块标题；每个词条带频率徽章（红/蓝/灰）、左色带、定义与源指针。

### Phase 9 · C（速查卡）

#### 步骤一：切输入包
```
python scripts/prep_c.py
```
读 `chapters.json` + 各章 `content.json`，输出 `work/distilled/c/in_<k>.json`（每章一包，
含正文 + 表格 + **备注**——规则/流程条件常藏在备注里）；并写 `c/index.json`。

#### 步骤二：子 agent 逐章抽取
按 `c/index.json` 逐章派子 agent（角色定义见 `agents/cheatsheet.md`），
每个只读自己那章的 `in_<k>.json`，产出 `out_<k>.json`：
```json
{
  "chapter_title": "...",
  "cards": [
    { "type": "formula",
      "label": "保费计算公式",
      "body": "应缴保费 = 保险金额 × 保险费率",
      "anchors": ["文件名#s12"] },
    { "type": "rule",
      "label": "近因原则适用条件",
      "body": "① 须为直接原因\n② 原因须连续，无新原因介入",
      "anchors": ["文件名#s5"] },
    { "type": "table",
      "label": "财产险 vs 责任险",
      "body": "项目 | 财产险 | 责任险\n承保对象 | 有形财产 | 法律责任",
      "anchors": ["文件名#s18"] },
    { "type": "flow",
      "label": "理赔基本流程",
      "body": "① 出险报案\n② 现场查勘\n③ 提交材料\n④ 审核赔付",
      "anchors": ["文件名#s30"] }
  ]
}
```
- 只收**以判断/操作为中心**的内容（条件规则、流程步骤、对比表、公式/数字门槛）
- 纯定义不收（定义属于 L2 关键词索引）
- body 来自 PPT 原文，表格用 ` | ` 分隔列，流程用 `①②③\n` 分隔步骤
- 子 agent 只回简报（各类型卡片数），不回全文 JSON

#### 步骤三：合并
```
python scripts/merge_c.py
```
读所有 `out_<k>.json`，章内按类型排序（公式>规则>对比>流程），添加源指针，写 `work/distilled/c.json`。

#### 步骤四：渲染
```
python scripts/render.py c            # → outputs/速查卡.pdf
```
单栏布局，每章 navy 色块标题；每张卡片带类型徽章（紫/橙/蓝/绿）、左色带、内容与源指针；
对比表类型自动解析为 Typst 表格。

### Phase 10 · M（思维导图）

M 以 **L1 蒸馏结果**为源（无需回溯原始 PPT），通过子 agent 按主题归纳分支，
生成全局总览 + 逐章彩色卡片网格。

#### 步骤一：切输入包
```
python scripts/prep_m.py
```
读 `work/distilled/l1.json`，按章提取小节标题/知识点，
输出 `work/distilled/m/in_<k>.json` + `m/index.json`。

#### 步骤二：子 agent 逐章归纳分支
按 `m/index.json` 逐章派子 agent（角色定义见 `agents/mindmap.md`），
每个只读自己那章的 `in_<k>.json`，把该章小节按主题归纳为 **4 层结构**
（L2 分支 → L3 子分支 → L4 叶节点），产出 `out_<k>.json`：
```json
{
  "chapter_index": 1,
  "chapter_title": "第1章 财产保险概论",
  "branches": [
    {
      "title": "业务体系与分类",
      "subbranches": [
        {
          "title": "财产损失险",
          "nodes": [
            "火灾险：企业财产险、家庭财产险",
            "运输险：车辆、船舶、货物运输"
          ]
        }
      ]
    }
  ]
}
```
- L2 分支 4–8 字（每章 4–6 个）；L3 子分支 4–7 字（每 L2 ≤3 个）；L4 叶节点 8–20 字（每 L3 ≤3 个，全章 ≤54）
- 节点来自 PPT 原文精简，禁止 AI 补充；`render_m.py` 按 `branches` 是否含 `subbranches` 自动选 4 层渲染
- 子 agent 只回简报（L2/L3/L4 计数），不回全文 JSON

#### 步骤三：全局总览 agent
由一个独立 agent（角色定义见 `agents/mindmap_global.md`）读取所有 `out_<k>.json` 的分支标题，
推断课程名，产出 `out_global.json`（不修改任何分支标题）。

#### 步骤四：合并
```
python scripts/merge_m.py
```
读 `out_global.json` + 所有 `out_<k>.json`，写 `work/distilled/m.json`。

#### 步骤五：渲染
```
python scripts/render.py m            # → outputs/思维导图.pdf
```
M 由 `render_m.py` 用 matplotlib 渲染（不走 Typst）。第一页为全局总览
（章节 tile 网格，每章带彩色分支 pill）；后续每章一页为 **XMind 式树形导图**
（根节点章色块在左 → L2/L3 分支节点居中 → L4 叶节点文字在右，肘形折线连接，12 色循环）。

### Phase 11 · 复核（Coverage / 防臆造）
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
| `work/distilled/l2/index.json` | L2 各章 k 值→输入/输出文件映射 |
| `work/distilled/l2/in_<k>.json` | 第 k 章的关键词 agent 输入包（含表格，不含备注） |
| `work/distilled/l2/out_<k>.json` | 第 k 章的关键词 agent 产出（术语+频率+定义） |
| `work/distilled/l2.json` | L2 主数据（合并后，供渲染） |
| `work/distilled/c/index.json` | C 速查卡各章 k 值→输入/输出文件映射 |
| `work/distilled/c/in_<k>.json` | 第 k 章的速查卡 agent 输入包（含备注） |
| `work/distilled/c/out_<k>.json` | 第 k 章的速查卡 agent 产出（规则/流程/对比/公式） |
| `work/distilled/c.json` | C 速查卡主数据（合并后，供渲染） |
| `work/distilled/m/index.json` | M 各章 k 值→输入/输出文件映射 |
| `work/distilled/m/in_<k>.json` | 第 k 章的思维导图 agent 输入包（来自 l1.json） |
| `work/distilled/m/out_<k>.json` | 第 k 章的思维导图 agent 产出（分支+节点） |
| `work/distilled/m/out_global.json` | 全局总览 agent 产出（课程名+各章分支标题列表） |
| `work/distilled/m.json` | M 思维导图主数据（合并后，供渲染） |
| `outputs/清洗版PPT全集.pdf` | L0 带书签清洗版全集（中间名 `L0.pdf`） |
| `outputs/核心知识手册.pdf` | L1 核心知识手册 |
| `outputs/简答库.pdf` | QA 简答/论述记录 |
| `outputs/关键词索引.pdf` | L2 关键词索引 |
| `outputs/速查卡.pdf` | C 速查卡 |
| `outputs/思维导图.pdf` | M 思维导图 |

## 安装为全局 skill
把 `SKILL.md scripts/ templates/ agents/` 复制到 `~/.claude/skills/open-book-exam-courseware/`。
`work/`、`outputs/`、课件文件夹是运行时/测试数据，不必随 skill 分发。
