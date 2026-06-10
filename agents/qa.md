# QA 子 agent（简答/论述 QA 记录）

**何时用**：Phase 7，当要生成 QA 简答库时。orchestrator 按单章派一个 Task 子 agent，
每个只领一章的 `work/distilled/qa/in_<k>.json`，控制上下文。

---

## 输入

子 agent 自己读盘（orchestrator 不传全文）：

```
work/distilled/qa/in_<k>.json
```

格式：
```json
{
  "chapter_index": 1,
  "chapter_title": "第1章 财产保险概论",
  "slide_count": 45,
  "slides": [
    {
      "anchor": "第一章财产保险概论.ppt#s5",
      "title": "思考题",
      "paragraphs": [{"text": "什么是近因原则？", "level": 0}],
      "tables": [],
      "notes": "答：近因原则是指..."
    }
  ]
}
```

---

## 任务

从该章的幻灯片内容（正文 + 备注 `notes`）中**识别并抽取**：
- 简答题（要求几句话说清楚某概念/原理/区别）
- 论述题（较长、需展开论述）
- 案例题（给定情景，要求分析/判断）
- 其他题型（填空、判断等，统归"其他"）

**只收集 PPT 原文中确实出现的题目**，不自行出题。

---

## 产出

写 `work/distilled/qa/out_<k>.json`：

```json
{
  "chapter_title": "第1章 财产保险概论",
  "items": [
    {
      "type": "简答题",
      "question": "什么是近因原则？",
      "answer": "近因原则是指...",
      "anchors": ["第一章财产保险概论.ppt#s5"],
      "ai_answer": false
    },
    {
      "type": "论述题",
      "question": "试论保险利益原则的意义。",
      "answer": "（PPT 中无对应答案，以下为 AI 补充）保险利益原则的意义在于...",
      "anchors": ["第一章财产保险概论.ppt#s12"],
      "ai_answer": true
    }
  ]
}
```

**字段说明**：
- `type`：`简答题` / `论述题` / `案例题` / `其他`
- `question`：题目原文，**逐字**来自 PPT（不改写，不增删）
- `answer`：答案原文（逐字），如 PPT 中无答案则 AI 补充并标 `ai_answer: true`
- `anchors`：题目所在幻灯片的锚点列表（至少一个），**必须来自输入包的 anchor 字段**
- `ai_answer`：`false` = 答案逐字来自 PPT；`true` = AI 补充

---

## 边界（铁律）

1. **只收原文题目**：PPT 里没有题目就输出空 `items: []`，不自行出题。
2. **题目逐字保留**：不改写、不截断、不"概括"题目文字。
3. **答案来源优先级**：同幻灯片正文 > 备注（`notes`） > 相邻幻灯片 > AI 补充。
4. **AI 补答必须标注**：一律置 `ai_answer: true`，不可混入原文答案。
5. **锚点必须真实**：只用输入包里已有的 anchor，不虚构。
6. **只回简报给主控**：本章抽出几题、有几道 AI 补答、有无存疑——不把全文 JSON 回给主控。

---

## 简报格式（回给 orchestrator）

```
=== QA k=<k> 完成 ===
  章节：<chapter_title>
  题目：<N> 题（简答 X / 论述 Y / 案例 Z / 其他 W）
  AI 补答：<M> 题
  存疑/跳过：<描述（若有）>
  → work/distilled/qa/out_<k>.json
```
