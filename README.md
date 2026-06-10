# 开卷考课件整理 Skill

把一整个文件夹的文科课件（`.ppt` / `.pptx` / `.pdf`）自动整理成可带入开卷考考场的
PDF，并保证每条知识点可溯源回手里那份打印件的页码。**只重组不臆造、全程可溯源、零代码一键。**

> 设计规格见 [`TODO.md`](TODO.md)；编排说明见 [`SKILL.md`](SKILL.md)。

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

```powershell
# Windows 控制台先设 UTF-8
$env:PYTHONUTF8=1; [Console]::OutputEncoding=[Text.UTF8Encoding]::new()

python scripts/doctor.py --install          # 1. 体检/装依赖（征求同意）
python scripts/inventory.py "PPT"           # 2. 盘点
python scripts/detect_chapters.py           # 3. 章节草稿 → 人工确认 chapters.json
# 4. 写 work/config.json 选参考基准/精简档
python scripts/extract.py                   # 5. 抽取 + 建页码映射
python scripts/build_l0.py                  # 6. 出 L0.pdf
python scripts/distill_l1.py                # 7. 蒸馏（纯抽取）
python scripts/render.py l1                 # 8. 出 L1.pdf
```

产物在 `outputs/`，中间产物在 `work/`。

## 依赖

- Python + `python-pptx`、`pypdf`、`reportlab`（pip）
- **LibreOffice**（headless 转 PDF/pptx）
- **Typst**（渲染 L1 等，单文件二进制）
- 中文字体（雅黑/宋体/黑体等，转 PDF 防乱码）

`scripts/doctor.py --install` 会自动检测并（征同意后）安装缺失项。

## 设计要点

- **内部真值锚点** = `(源文件名, 源内页序号)`，永不漂移；显示指针按"参考基准"换算
  （带原件→`源：文件名 s.N`；带 L0→`L0 p.X`）。
- **抽取与生成分离**：默认确定性蒸馏纯抽取、零臆造；AI 增强的条目一律标「AI 生成，待核」。
- **图原样抠取**：从原 PPT 抠内嵌图，绝不重绘（Typst 不支持的 EMF/WMF 等会被过滤）。
- **Token 纪律**：主控不加载原文，脚本落盘、按需读盘、可并行可重跑。

## 目录

```
SKILL.md      编排脊柱（给运行该 skill 的 Claude 看）
scripts/      doctor / inventory / detect_chapters / extract / build_l0 / distill_l1 / render + lib/
templates/    Typst 模板（l1.typ；l2/card/mindmap/qa 待补）
agents/       AI 判断子 agent 角色与边界（distillation/qa/coverage）
PPT/          测试夹具（保险课件，非 skill 一部分）
work/ outputs/ 运行时中间产物 / 最终 PDF
```
