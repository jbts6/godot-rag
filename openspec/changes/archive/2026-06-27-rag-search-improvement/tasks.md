# Tasks: RAG 搜索质量提升

> 设计完成后细化任务列表。

## Phase 1: 基础优化

- [x] 1.1 增强 `normalize_symbol`：支持 camelCase 拆分、去 `_` 模糊匹配
- [x] 1.2 统计 BM25 原始值分布，校准分数映射公式
- [x] 1.3 更新测试用例（已在 1.1 和 1.2 中完成）

## Phase 2: 图谱核心

- [x] 2.1 设计并创建 `chunk_relations` 表
- [x] 2.2 实现 parent 关系建图（chunker 阶段）
- [x] 2.3 实现 inherits 关系建图（正则提取继承链）
- [x] 2.4 实现 references 关系建图（FTS 交叉匹配）
- [x] 2.5 更新测试用例

## Phase 3: 检索增强

- [x] 3.1 实现图谱遍历查询（命中 top-K → 关联扩展）
- [x] 3.2 优化 FTS 查询分词（拆 token、处理 `.` 分隔符）
- [x] 3.3 统一分数体系（主结果 + 图谱结果融合排序）
- [x] 3.4 CLI 输出增加 relation_type 字段
- [x] 3.5 更新测试用例（已在 3.1-3.4 中完成）
