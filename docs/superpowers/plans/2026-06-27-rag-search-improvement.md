---
change: rag-search-improvement
design-doc: docs/superpowers/specs/2026-06-27-rag-search-improvement-design.md
date: 2026-06-27
status: draft
archived-with: 2026-06-27-rag-search-improvement
---

# 实施计划: RAG 搜索质量提升

## Task 1.1: 增强 normalize_symbol

**文件**: `rst2md/rag/symbols.py`

- 新增 `_canonical_form()` 函数
- `normalize_symbol()` 改为调用 `_canonical_form()`
- 新增测试用例

**验证**: `uv run pytest -q` 通过，新增 canonical form 测试

## Task 1.2: BM25 分数映射校准

**文件**: `rst2md/rag/store.py`

- 修改 FTS 分数公式：`* 0.1` → `* 0.01`
- 验证新分布更均匀

**验证**: 手动查询确认分数分布合理

## Task 1.3: 更新测试用例

**文件**: `rst2md/tests/`

- 为 canonical form 新增测试
- 为 BM25 校准新增测试

## Task 2.1: 创建 chunk_relations 表

**文件**: `rst2md/rag/store.py`

- SCHEMA 中新增 `chunk_relations` 表
- 新增索引

**验证**: `build_database` 成功，表存在

## Task 2.2: 实现 parent 关系建图

**文件**: `rst2md/rag/chunker.py`, `rst2md/rag/models.py`

- `Chunk` 新增 `parent_symbol` 字段
- `_chunk_class_document()` 中 member chunk 设置 `parent_symbol=class_name`

**验证**: parent 关系正确建立

## Task 2.3: 实现 inherits 关系建图

**文件**: `rst2md/rag/store.py`

- 正则提取 class_summary 的 `**Inherits:**` 行
- 建立 inherits 关系

**验证**: `Node2D → Node → Object` 继承链正确

## Task 2.4: 实现 references 关系建图

**文件**: `rst2md/rag/store.py`

- 构建已知符号集合
- 扫描 chunk 文本中的符号引用
- 建立 references 关系

**验证**: references 关系正确建立

## Task 2.5: 更新测试用例

**文件**: `rst2md/tests/`

- 测试建图逻辑
- 测试关系表完整性

## Task 3.1: 实现图谱遍历查询

**文件**: `rst2md/rag/store.py`

- `search_database()` 新增 `expand_graph` 参数
- 对 top-K 主结果做图谱遍历
- 合并关联结果

**验证**: 图谱扩展返回关联结果

## Task 3.2: FTS 查询分词优化

**文件**: `rst2md/rag/store.py`

- 新增 `_smart_tokenize()` 函数
- 对含 `.` 的查询拆 token

**验证**: `"Node.add_child"` 能正确匹配

## Task 3.3: 分数体系统一

**文件**: `rst2md/rag/store.py`

- 关联结果分数 = 主结果分数 × weight × 0.5

**验证**: 分数排序合理

## Task 3.4: CLI 输出增加 relation_type 字段

**文件**: `rst2md/rag/models.py`, `rst2md/rag/cli.py`

- `SearchResult` 新增 `relation_type`, `distance` 字段
- CLI 输出显示关系类型
- JSON 输出包含新字段

**验证**: CLI 输出正确显示

## Task 3.5: 更新测试用例

**文件**: `rst2md/tests/`

- 端到端测试：图谱扩展查询
- 测试 `--no-expand` 参数

## 实施顺序

```
1.1 → 1.2 → 1.3 (Phase 1 完成)
  ↓
2.1 → 2.2 → 2.3 → 2.4 → 2.5 (Phase 2 完成)
  ↓
3.1 → 3.2 → 3.3 → 3.4 → 3.5 (Phase 3 完成)
```

每个 task 完成后 git commit，tasks.md 打勾。
