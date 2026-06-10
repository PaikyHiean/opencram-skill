# 开卷考课件整理 Skill

> 把你的课件 PPT 变成真正能在考场用的 PDF——每条知识点都知道自己在你手里那份打印件的第几页。

---

## 为什么不直接用豆包 / DeepSeek？

你肯定用过 AI 总结 PPT。效果嘛……差强人意。核心问题：

| 场景 | 豆包 / DS | 本 Skill |
|---|---|---|
| 课件有 10 个 PPT，每个 100 页 | 经常卡死、截断、只看了前半 | 全量处理，每页都不漏 |
| "第三章知识点在打印件第几页？" | 不知道，瞎蒙 | 精确到页，每条都标 |
| 对话窗口关掉 | 内容消失，下次重新喂 | 输出 PDF，永久保存 |
| AI 帮你"补充完善"了课件没有的内容 | 很常见，考场写了反扣分 | 只抠原文，0 字臆造 |
| 输出格式 | 聊天框里的文字 | 可直接打印的带书签 PDF |

**一句话：豆包帮你读完了课件；这个 skill 帮你把课件变成考场武器。**

---

## 你会得到什么

给它一个装满课件的文件夹，自动产出最多 6 种可打印 PDF：

| | 产物 | 干嘛用 |
|---|---|---|
| ✅ 已可用 | **清洗版PPT全集** | 删封面/过场页，加章节书签，每页印来源戳 |
| ✅ 已可用 | **核心知识手册** | 按章整理的可誊抄条目，内嵌原图（省得手画 ER 图），每条标原始页码 |
| ✅ 已可用 | **简答库** | PPT 原题原答逐字整理（简答/论述/案例），无答案时 AI 补充并标 〔AI〕 |
| ✅ 已可用 | **关键词索引** | 按章整理专业术语，标注高/中/低频，附 PPT 原文定义与页码来源 |
| ✅ 已可用 | **速查卡** | 规则/条件/流程/公式，以判断与操作为中心，附源指针 |
| ✅ 已可用 | **思维导图** | 全局总览 + 逐章彩色分支卡片网格，快速定位知识脉络 |

---

## 你需要做的，一共 3 步

```
1. 把所有课件 PPT 放进同一个文件夹

2. 打开 Claude Code，告诉它：
   "帮我整理这个文件夹里的课件：D:\我的课件"

3. 和 Claude 对话几分钟（确认章节、选产物）
   → 去喝杯水 → 回来取 PDF
```

**不需要写代码，不需要懂命令行，不需要装任何你看不懂的东西。**

---

## 工作流程

```
你：给一个文件夹路径
         │
         ▼
  📋 Phase 0  扫描文件清单，告诉你有哪些课件、文字层是否完整
         │
         ▼
  🗂  Phase 1  推断章节结构，展示草稿给你确认
              ↩ 你可以调整：合并同一章的多个文件、指定无章号文件归属
         │
         ▼
  ☑️  Phase 2  勾选需要哪几种 PDF，选精简力度（默认：保守·可誊抄）
         │
         ▼
  ⚙️  Phase 3  自动装好所有工具（首次约 3 分钟，之后秒过）
         │
         ▼
  📖  Phase 4  抽取每一页文字、表格、图片，建立页码映射表
         │
         ▼
  📄  Phase 5  L0.pdf（带书签清洗版）
         │
         ▼
  🤖  Phase 6  AI 按章蒸馏，筛掉装饰图，保留知识图
         │
         ▼
  📘  L1.pdf  核心知识手册  ✓ 完成
         │
         ▼
  🤖  Phase 7  AI 按章识别题目/答案（含 PPT 备注），有题无答时 AI 补充并标注
         │
         ▼
  📋  QA.pdf   简答/论述 QA 记录  ✓ 完成
         │
         ▼
  🤖  Phase 8  AI 按章抽取专业术语，标注高/中/低频，摘录 PPT 原文定义
         │
         ▼
  🔑  L2.pdf   关键词索引  ✓ 完成
         │
         ▼
  🤖  Phase 9  AI 按章识别规则/流程/公式/对比表（以判断/操作为中心）
         │
         ▼
  📋  C.pdf    速查卡  ✓ 完成
         │
         ▼
  🤖  Phase 10  AI 按章归纳主题分支（来自 L1 蒸馏结果，无需回溯 PPT）
         │
         ▼
  🗺  M.pdf    思维导图  ✓ 完成
```

### 精简力度有三档可选

| 档位 | 体积 | 特点 | 适合 |
|---|---|---|---|
| **保守**（默认） | 原文 80-90% | 论证链完整，可直接誊抄 | 需要背完整段落的科目 |
| **标准** | 原文 40-50% | 要点化，压缩举例 | 大多数文科科目 |
| **骨架** | 原文 15-20% | 只留核心论断 | 仅作为定位工具 |

---

## 怎么开始

### 前提条件

- [Claude Code](https://claude.ai/code) — 安装好，能正常运行
- Windows / macOS / Linux 均可

其余依赖（LibreOffice、Typst、Python 库）在 Phase 3 体检时可用 `--install` 安装。**Windows 支持全自动安装**（winget）；macOS / Linux 会打印对应的 `brew` / `apt` 命令，需手动执行。首次安装大约需要下载 350MB（主要是 LibreOffice）。

### 第一次使用

1. 克隆或下载本仓库到任意位置：
   ```
   git clone https://github.com/PaikyHiean/opencram-skill.git
   ```
   或者直接点页面右上角的 **Code → Download ZIP** 解压。

2. 把这个 skill 复制到 Claude Code 的 skills 目录：

   **Windows PowerShell**
   ```powershell
   Copy-Item -Recurse ".\opencram-skill" "$env:USERPROFILE\.claude\skills\"
   ```

   **macOS / Linux**
   ```bash
   cp -r ./opencram-skill ~/.claude/skills/
   ```

3. 把所有课件 PPT 放进一个文件夹（比如 `D:\期末复习\财产保险`）。

4. 在 Claude Code 里说一句话：
   ```
   帮我整理 D:\期末复习\财产保险 里的开卷考课件
   ```

Claude 会一步一步引导你完成后续配置。

---

## 对话示例

这是一段真实的交互流程，让你知道大概会聊什么：

```
你：帮我整理 D:\期末复习\财产保险 里的开卷考课件

Claude：好的，扫描完毕。发现 11 个 .ppt 文件，共约 1200 张幻灯片。
        以下是推断出的章节结构，请确认：

        第1章  财产保险概论（2个文件合并）
        第3章  人身保险合同
        第4章  人寿保险
        第6章  企业财产保险（3个文件合并，含补充材料）
        ...

        ⚠ 以下文件没有章节编号，请指定归属：
        · 财产保险原则.ppt
        · 财产保险合同.ppt

你：这两个归到第1章

Claude：明白。你希望生成哪些产物？默认帮你勾了 L0 和 L1，
        其他还需要吗？精简力度用默认的"保守·可誊抄"就好？

你：就要 L0 和 L1，精简力度用默认的

Claude：好，开始处理。预计几分钟……
        ✅ 清洗版PPT全集.pdf 已生成（973 页，含章节书签）
        ✅ 核心知识手册.pdf 已生成（约 55 页，191 个知识点，7 张图）
        ✅ 简答库.pdf 已生成（56 题，7 章，含原题原答与 AI 补充标注）
        ✅ 关键词索引.pdf 已生成（约 12 页，214 个词条，7 章，含频率分级与页码来源）
        ✅ 速查卡.pdf  已生成（约 10 页，139 张卡片，7 章，公式/规则/对比/流程分类）
        ✅ 思维导图.pdf  已生成（约 8 页，全局总览 + 7 章思维导图，71 个分支，380 条节点）
        产物在 outputs/ 文件夹里。
```

---

## 关于"可溯源"

L1 里每一个小节标题旁都有一个灰色的来源指针，比如：

> **一、财产保险的概念与标的**  〔源：第一章财产保险概论.ppt s.2–5〕

`s.2–5` 的意思是：这段内容来自那个 PPT 文件的第 2–5 张幻灯片。
如果你打印的是 L0，指针会自动换算成 L0 的页码。

这样考场上遇到拿不准的题，你知道翻自己打印件的哪一页去抄。

---

## 技术细节（给想了解的人）

- 所有文字均从 PPT 原文提取，不改写、不补全——AI 增强只做归并和去重，改写的条目都标 `〔AI〕`
- 页码映射基于 `(源文件名, 源内页序号)` 锚点，清洗规则变化时不漂移
- 排版引擎：[Typst](https://typst.app/)（单文件二进制，无需 LaTeX 环境）
- 图片从 PPT 原始嵌入数据抠取，EMF/WMF 等 Typst 不支持的格式自动过滤
- 详细编排说明见 [`SKILL.md`](SKILL.md)；排版参数见 [`templates/TYPOGRAPHY.md`](templates/TYPOGRAPHY.md)

---

## 常见问题排查

### ❌ LibreOffice 转换失败 / `soffice` 找不到

**原因**：LibreOffice 未安装，或安装路径含中文/空格导致脚本找不到可执行文件。

**解决**：
1. 确认 LibreOffice 已安装：运行 `python scripts/doctor.py`，看 `LibreOffice` 一行是否为 ✅。
2. 若仍失败，手动在 `work/config.json` 中添加绝对路径：
   ```json
   { "soffice_path": "C:/Program Files/LibreOffice/program/soffice.exe" }
   ```
3. Windows 用户：安装路径建议保持默认（`C:\Program Files\LibreOffice`），不要改到含中文或空格的目录。

---

### ❌ Typst 渲染失败：`font not found` / 中文变方块

**原因**：Typst 找不到 `work/config.json` 中指定的 `cjk_font` 字体族名。

**解决**：
1. 运行 `python scripts/doctor.py`，查看 `中文字体` 一行命中了哪些字体名。
2. 把 `work/config.json` 的 `cjk_font` 改为命中列表中的某个名字（常见值：`Microsoft YaHei`、`SimHei`、`Noto Sans CJK SC`）：
   ```json
   { "cjk_font": "Microsoft YaHei" }
   ```
3. 重新运行 `python scripts/render.py l1`（或对应产物）。

---

### ⚠️ 某个 PPT 文字抽取近零 / L1 里该章内容为空

**原因**：该 PPT 是**扫描版**（图片 PDF 转的 PPT），没有可识别的文字层。本 skill 不做 OCR，无法从图片中提取文字。

**解决**：
- 运行 `python scripts/doctor.py` 或查看 `work/manifest.json`，`text_layer: "suspect_none"` 的文件即为疑似扫描件。
- 这类文件会被加入 L0（保留原页），但 L1/L2/C/QA/M 里不会有对应内容。
- 如果原版有文字版 PPT，换用文字版重新运行；或手动把关键内容粘贴进一个新 PPT 再处理。

---

### ⚠️ L1 某些章节没有 AI 增强 / `work/distilled/ai/out_<k>.json` 缺失

**原因**：AI 蒸馏子 agent 需要 orchestrator（你与 Claude 的对话）**显式派发**。如果你直接运行了 `merge_ai_l1.py` 但没有先派发子 agent，对应的 `out_k.json` 文件就不存在，该章会回退到确定性基线。

**解决**：
- 在 Claude Code 对话中，告诉 Claude："帮我对第 k 章运行 AI 蒸馏 agent"，Claude 会按 `agents/distillation.md` 的角色说明派发 Task 子 agent。
- 派发完成后再运行 `python scripts/merge_ai_l1.py`，缺失的章节会用基线版兜底，有 `out_k.json` 的章节用 AI 版覆盖。
- 缺哪几章可以查 `work/distilled/ai/` 目录，不存在 `out_<k>.json` 的 k 值即为待派发。

---

## 参与贡献 / 反馈

有 bug、想要新产物（L2/C/M/QA）、或者遇到某些课件处理出错？
欢迎提 [Issue](https://github.com/PaikyHiean/opencram-skill/issues) 或 Pull Request。
