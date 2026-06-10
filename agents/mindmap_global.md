# M 子 agent（思维导图·全局总览）

**何时用**：Phase 10 的最后一步。当所有章节的 `out_<k>.json` 都生成后，
orchestrator 派这一个 agent 读取所有章节输出，生成全局总览。

---

## 输入

子 agent 自己读盘（orchestrator 不传全文）：

读取 `work/distilled/m/index.json` 获取章节列表，再逐一读取对应的 `out_<k>.json`。

**只需读取每章的 `branches[*].title`，无需读 nodes。**

---

## 任务

生成全局总览数据，用于思维导图 PDF 的第一页（课程全局鸟瞰图）。

**要求**：
- 从 `index.json` 获取课程名（取第一章 chapter_title 去掉章号后推断，或直接用 source_folder 最后一段）
- 为每个章节，记录其 chapter_index、chapter_title 和全部分支标题（branches）
- 分支标题直接从 `out_<k>.json` 的 `branches[*].title` 取出，**不改写**
- 顺序与 index.json 的 k 值一致

---

## 产出

写 `work/distilled/m/out_global.json`：

```json
{
  "course_title": "财产保险学",
  "chapters": [
    {
      "chapter_index": 1,
      "chapter_title": "第1章 财产保险概论",
      "branches": ["概念与保险标的", "保险四项基本原则", "保险价值与金额", "保险合同要素", "财产险分类"]
    },
    {
      "chapter_index": 3,
      "chapter_title": "第3章 人身保险合同",
      "branches": ["合同当事人", "合同订立", "合同效力", "合同变更", "合同终止"]
    }
  ]
}
```

**字段说明**：
- `course_title`：从章节标题推断课程名，如"财产保险学"（去掉"第N章"部分取公因）
- `chapters[*].branches`：该章所有分支标题的字符串列表，直接从 out_k.json 取出

**推断 course_title 的规则**（降序优先）：
1. 如果多个章节标题含有相同的名词（如"财产保险"），用它加"学"构成课程名
2. 如果看不出规律，用"课程总览"代替

---

## 边界（铁律）

1. **不修改分支标题**：直接从 out_k.json 取 branch title，不改写
2. **不漏章**：index.json 里所有 k 都必须包含在输出中
3. **只回简报**：不把全文 JSON 回给主控

---

## 简报格式（回给 orchestrator）

```
=== M global 完成 ===
  课程：<course_title>
  章数：<N> 章，共 <M> 个分支
  → work/distilled/m/out_global.json
```
