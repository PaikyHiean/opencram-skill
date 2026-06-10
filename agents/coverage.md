# Coverage / 防臆造复核子 agent（Phase 9）

**目标**：交付前体检，保证完整与不臆造。

**检查项**（读 `work/` 下 JSON，不读全文）：
- **章节覆盖**：`chapters.json` 里每章在所选产物中都有对应内容。
- **对齐**：`work/maps/*.json` 中 `aligned=false` 的源列出待复核（页码映射可能不准）。
- **文字层**：`manifest.json` 中 `suspect_none` / 抽取文本近零的源标红（疑似扫描件，未 OCR）。
- **删页复核**：`l0_deleted.json` 删页清单交用户确认。
- **AI 生成**：`l1.json`/`qa.json` 中 `ai_generated=true` 的条目汇总，提示用户逐条核对。`l2.json`/`c.json` 无字段级标记，但其 agent 要求逐字原文——若 definition/points 含明显推断性语言（"可能""建议""通常"等），也应在报告中标出。

**产出**：一份简短复核报告（计数 + 待核清单），不改产物，只提示。
