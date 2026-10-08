# 数据模型 v1.0

所有文件为 UTF-8 JSON。`examples/sample.reviewed.json` 是完整实例；`sample.draft.json` 是提取输出。[schema.json](schema.json) 提供 Draft 2020-12 形状约束，供编辑器或可选 JSON Schema 工具使用。运行期验证器在 scripts/mindmap.py，检查引用、溯源、树顺序及正式门禁，不依赖第三方 JSON Schema 引擎。

|字段|结构/约束|
|---|---|
|schema_version|固定字符串 1.0|
|book|title、edition、publisher、pdf_name、sha256、page_count、printed_page_offset|
|pages|按 PDF 从 1 开始连续编号；pdf_page、printed_page（字符串，允许封面/罗马页）、text、extraction、review、reviewer、note|
|nodes|唯一 id、title、kind、origin=textbook/teacher/metadata、sources 数组、formula_ids 数组、review；teacher 需 rationale|
|sources|pdf_page（1-based）、line（该页提取文本的 1-based 行号）、quote（去首尾空白后的原文）；不等同 PDF 视觉行号或坐标|
|formulas|唯一 id、raw、latex（字符串或 null）、source、review、reviewer、note|
|textbook / exam|递归分支 `{node_id, children:[]}`；各自不能循环或重复节点；允许两模式复用同一知识节点|
|relations|from、to、type=prerequisite/equivalent/application/contrast、rationale、review；允许网络关系成环，不影响树布局|
|structure_review|textbook、exam、reviewer、note|

review 只有 pending 和 approved。签署是人工声明，验证器仅检查声明存在。

严格教材模式必须覆盖全部教材和元数据节点，标题需与其至少一个 source.quote 完全相同，前序遍历不能逆转原文页/行顺序，不允许教师补充节点。自动提取的普通原文行作为 excerpt 挂在当前节下，并非已识别知识点。

复习树可选择教材节点并增添教师分组；关系的依据必须写清。未经真题/考纲证据核对的连接是教师教学设计，不应命名为“高考必考规律”。即便复习树只使用部分内容，正式导出仍要求整个数据集完成复核。

printed_page_offset 仅用于初始线性映射。封面、目录、跨册拼接或非连续书页需逐页编辑 printed_page。传入选章 PDF 时，在配置中设置适当偏移并在 edition/note 写明原书页范围。PDF 指纹针对所用的选章文件。

未保存 bbox、公式图片或 PDF 本体；HTML 携带全部 pages.text，因此其体积和文本传播范围应在交付前检查。
