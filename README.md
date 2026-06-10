# 开卷考课件整理 Skill

把一整个文件夹的文科课件（`.ppt` / `.pptx` / `.pdf`）自动整理成可带入开卷考考场的
PDF，并保证每条知识点可溯源回考场上那份打印件的页码。**只重组不臆造、全程可溯源。**

> 编排说明见 [`SKILL.md`](SKILL.md)；排版参数参考 [`templates/TYPOGRAPHY.md`](templates/TYPOGRAPHY.md)。

## 6 种产物

| 代号 | 名称 | 状态 |
|---|---|---|
| **L0** | 带书签的清洗版全集（删废页 + 章节书签 + 每页来源戳） | ✅ 已实现 |
| **L1** | 核心知识手册（按章重组、可誊抄、带源指针、内嵌原图） | ✅ 已实现 |
| **L2** | 关键词速查索引 | ⏳ 待实现 |
| **C** | 核心定义/命题速查卡 | ⏳ 待实现 |
| **M** | 思维导图 PDF | ⏳ 待实现 |
| **QA** | 简答/论述记录 | ⏳ 待实现 |

## 快速上手

> Windows PowerShell 执行脚本前先设 UTF-8，避免中文乱码：
> ```powershell
> $env:PYTHONUTF8=1; [Console]::OutputEncoding=[Text.UTF8Encoding]::new()
> ```

### 基础路径（纯确定性，零 AI，快速出初稿）

```powershell
python scripts/doctor.py --install        # 1. 体检/装依赖（LibreOffice / Typst / pip）
python scripts/inventory.py "课件文件夹"  # 2. 盘点文件
python scripts/detect_chapters.py        # 3. 推断章节 → 人工确认 chapters.json
# 4. 按需编辑 work/config.json（参考基准 / 精简档）
python scripts/extract.py                # 5. 抽取文字/表/图 + 建锚点映射
python scripts/build_l0.py               # 6. 生成 L0.pdf（带书签 + 来源戳）
python scripts/distill_l1.py             # 7. 确定性蒸馏（结构保留，纯抽取）
python scripts/render.py l1              # 8. 渲染 → outputs/L1.pdf
```

### AI 增强路径（推荐，语义归并 + 图片筛查）

在步骤 7–8 之前插入以下 AI 增强步骤：

```powershell
python scripts/distill_l1.py             # 7a. 先建确定性基线（兜底）
python scripts/prep_ai_distill.py        # 7b. 切每章输入包 → work/distilled/ai/in_<k>.json
# 7c. 逐章派子 agent（见 agents/distillation.md）读 in_<k>.json
#     产出 work/distilled/ai/out_<k>.json
python scripts/merge_ai_l1.py            # 7d. 合并 AI 结果 → work/distilled/l1.json
python scripts/screen_images.py          # 7e. 生成图片筛查包
# 7f. 派子 agent（见 agents/image_screening.md）裁决图片去留
#     产出 work/distilled/ai/image_screen_out.json
python scripts/apply_image_screen.py     # 7g. 写回筛查结果
python scripts/render.py l1              # 8.  渲染 → outputs/L1.pdf
python scripts/verify_l1.py             # 9.  可选：质量核查
```

AI 生成的小节在 PDF 中以红色 `〔AI〕` 小字标注，提示需对照原文核查。

## 依赖

- Python + `python-pptx`、`pypdf`、`reportlab`（pip 自动安装）
- **LibreOffice**（headless 转 PDF/pptx，~350MB，`doctor.py --install` 会征求同意后安装）
- **Typst**（渲染 L1 等，单文件二进制，`doctor.py --install` 安装）
- 中文字体（雅黑/宋体/黑体等，Windows 通常已内置）

## 目录结构

```
SKILL.md              编排脊柱（给运行该 skill 的 Claude 看）
README.md             本文件
scripts/
  doctor.py           依赖体检/安装
  inventory.py        文件盘点
  detect_chapters.py  章节推断
  extract.py          内容抽取 + 锚点映射
  build_l0.py         生成 L0.pdf
  distill_l1.py       确定性蒸馏（L1 基线）
  prep_ai_distill.py  切 AI 输入包
  merge_ai_l1.py      合并 AI 蒸馏结果
  screen_images.py    图片筛查输入包
  apply_image_screen.py  写回筛查裁决
  render.py           Typst 渲染（l1 / 后续产物）
  verify_l1.py        质量核查
  lib/common.py       共享工具（路径/锚点/工具定位）
templates/
  l1.typ              L1 Typst 模板
  TYPOGRAPHY.md       排版参数说明（供迁移参考）
agents/
  distillation.md     L1 AI 蒸馏子 agent 角色定义
  image_screening.md  图片筛查子 agent 角色定义
  qa.md               QA 子 agent 角色定义（待实现）
  coverage.md         覆盖核查子 agent 角色定义
work/                 运行时中间产物（.gitignore 忽略）
outputs/              最终 PDF（.gitignore 忽略）
```

## 设计要点

- **内部真值锚点** = `(源文件名, 源内页序号)`，永不漂移；显示指针按"参考基准"换算
  （带原件→`源：文件名 s.N`；带 L0→`L0 p.X`）。
- **抽取与生成分离**：默认确定性蒸馏纯抽取、零臆造；AI 增强的条目一律标 `〔AI〕`。
- **图原样抠取**：从原 PPT 抠内嵌图，Typst 不支持的 EMF/WMF 等格式自动过滤。
- **Token 纪律**：主控不加载原文；脚本落盘、按需读盘、可并行可重跑。
- **Typst 排版**：中文 10.5pt 宋体正文，行距 0.82em；间距折叠感知设计（见 TYPOGRAPHY.md）。
