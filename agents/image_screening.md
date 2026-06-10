# Image Screening 子 agent（L1 图片筛查）

**何时用**：Phase 6，在 `merge_ai_l1.py` 之后、`render.py l1` 之前。
由主控运行 `screen_images.py` 生成输入包，派本 agent 逐节审查图片，
产出 `image_screen_out.json`，再由 `apply_image_screen.py` 写回 l1.json。

**输入**：读 `work/distilled/ai/image_screen_in.json`，包含：
- `sec_id`：小节唯一标识符（用于输出中定位）
- `chapter_title` / `heading`：所属章节和标题
- `text_summary`：该节的文字蒸馏内容（前 600 字）
- `images`：该节的图片路径列表

对每个图片路径，用 Read tool 读取图片文件（Claude 支持多模态，可直接查看）。

**产出**：写 `work/distilled/ai/image_screen_out.json`：
```json
{
  "decisions": [
    { "sec_id": "ch0_sec2", "img": "work/extracted/.../xxx.png", "keep": true,  "reason": "流程图，文字未涵盖" },
    { "sec_id": "ch0_sec2", "img": "work/extracted/.../yyy.png", "keep": false, "reason": "卡通插图，无实质信息" }
  ]
}
```

**裁决标准（keep=true 的条件，满足其一即保留）**：
1. **结构信息**：图中含文字未能表达的层级/流程/对比结构（如：树形图、流程图、矩阵对比表）
2. **数据图表**：折线图/柱状图/饼图，含原文未摘录的数字或趋势
3. **表格型图**：以图形方式呈现的对比表，文字版本丢失了对齐关系

**裁决标准（keep=false 的条件，满足其一即移除）**：
- 卡通/装饰性插图（如漫画人物、场景图）
- 仅有大段文字的 PPT 截图（文字已在 text_summary 中体现）
- 标题页/封面/感谢页截图
- 低分辨率、内容模糊、无法辨读的图片
- 图中信息已被 text_summary 完整覆盖

**边界（铁律）**：
- 对不确定的图，默认 keep=true（宁多勿漏）
- 不修改 text_summary 内容，只决定图片去留
- 只回简报给主控（保留/移除数量），不回图片内容原文
