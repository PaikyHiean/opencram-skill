# Distillation 子 agent（L1 蒸馏增强）

**何时用**：Phase 6，当确定性基线 `distill_l1.py` 的结果需要更聪明的语义去重/压缩/
补标题时。orchestrator **按单章**派一个 Task 子 agent，每个只领一章，控制上下文。

**输入**（子 agent 自己读盘，orchestrator 告知 k 值）：
- `work/distilled/ai/in_<k>.json`（该章已过滤的幻灯片摘要，废页已剔除）
- `work/config.json`（`compression` 精简档）

**产出**：写 `work/distilled/ai/out_<k>.json`，schema 见 SKILL.md Phase 6b。
**不要直接写 `l1.json`**——`merge_ai_l1.py` 会做确定性合并。
每个 section = `{label:"一、", heading, pointer, points:[{num,text,details}], tables, images, ai_generated}`。
确定性基线已按"幻灯片标题+缩进层级"重建层级；AI 增强是在此之上做**语义归并/补标题**。

**边界（铁律）**：
- **绝不臆造**：只重组/裁剪/合并 `in_<k>.json` 里已有的文本，不新增事实、不"补全"知识。
- 每个 section 必须保留正确源锚点（节级指针不可指错页）。
- 凡 AI 改写/合并产生、已非逐字原文的 section，置 `"ai_generated": true`（模板会标「AI 生成，待核」）。
- 源指针只标在**节级**（一、二…），节内 1./2. 小点不再逐条标注。
- 按 `compression` 控制力度：conservative≈全保留可誊抄；standard≈裁深层明细；aggressive≈仅点标题。
- 只回简报给主控（本章小节数、合并了多少、有无存疑），不回全文。
