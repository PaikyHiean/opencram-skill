# QA 子 agent（简答/论述记录）— 待实现

**目标**：收集 PPT 中**原有**的题目与答案，逐字保留；有题无答时 AI 补答。

**输入**：按章读 `work/extracted/<stem>/content.json`（正文/备注里常藏题目与答案）。

**产出**：`work/distilled/qa.json`，条目结构建议：
```json
{ "question": "...", "answer": "...", "anchor": "<文件名>#s<N>",
  "ai_generated": false }
```

**边界（铁律）**：
- PPT 原有题目与答案 **逐字保留**，`ai_generated=false`。
- 有题无答 → AI 补答，`ai_generated=true`，渲染时标「AI 生成，待核」，
  并与抽取内容**物理分开**（模板分区或独立段落）。
- 每条挂正确源锚点；不臆造题目（只收原文里确实出现的题）。
