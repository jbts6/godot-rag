---
change: fix-semantic-search-acceptance-gaps
design-doc: openspec/changes/fix-semantic-search-acceptance-gaps/design.md
base-ref: 36ffe17a6d139ac095f2fcd21b2888a90bae9216
archived-with: 2026-06-28-fix-semantic-search-acceptance-gaps
---

# Fix Semantic Search Acceptance Gaps - 实施计划

## 概述

修复 `semantic-search-quality-hardening` 合并后的验收缺口，包括：
1. 测试依赖本地生成目录的问题
2. `--debug-search` 文本模式不可见
3. vector availability 语义不完整

## 任务分组

### 阶段 1: 确定性语义测试 fixtures（任务 1-2）

**目标**：消除测试对 `godot_rag/docs-md` 的依赖

**任务 1**: 替换 `rst2md/tests/test_semantic_search.py` 中依赖 `godot_rag/docs-md` 的测试
- 在 `tmp_path` 下构建小型 docs 树
- 包含足够的 class/tutorial 内容以测试：
  - `see_also` 关系提取（确定性预期计数）
  - vector row parity/population（小型 DB）
  - golden query expected path families
- 保持大型 release DB 验证在 `build.sh` diagnostics 中

**任务 2**: 添加回归测试证明普通 pytest 不需要 `godot_rag/`
- 验证测试可在没有 `godot_rag/docs-md` 的环境中运行
- 确保 fresh clone 后测试通过

### 阶段 2: Debug Metadata 可见性（任务 3-4）

**目标**：让 `--debug-search` 在文本模式下可见

**任务 3**: 让 `--debug-search` metadata 在文本模式下可见
- JSON 模式：保持现有 envelope（metadata + results）
- 文本模式：在结果前打印简短 metadata header
  - `search_mode: fts_only`
  - `vector_available: false`
  - `fallback_reason: missing_vec_chunks`

**任务 4**: 添加 CLI 覆盖 `--debug-search` 文本输出和 JSON 输出
- 测试文本模式输出
- 测试 JSON 模式输出
- 确保无 `--debug-search` 时不改变正常输出

### 阶段 3: Vector Availability 语义（任务 5-6）

**目标**：改进 vector readiness 检测

**任务 5**: 更新 vector readiness/search metadata 检测
- 比较 `chunks` 和 `vec_chunks` 行数
- 检测扩展/表可查询性
- 使用明确原因标记 degraded 状态：
  - `missing_vec_chunks`
  - `empty_vec_chunks`
  - `vector_row_count_mismatch`
  - `vector_query_failed`

**任务 6**: 添加回归覆盖
- 测试空 `vec_chunks` 的搜索 metadata
- 测试 vector row-count 不匹配的搜索 metadata

### 阶段 4: 验证（任务 7-9）

**目标**：确保所有修改正确

**任务 7**: 运行聚焦的 semantic/search 测试
```bash
PYTHONPATH=rst2md uv run pytest -q rst2md/tests/test_semantic_search.py rst2md/tests/test_rag_search.py
```

**任务 8**: 运行完整测试套件
```bash
PYTHONPATH=rst2md uv run pytest -q
```

**任务 9**: 重新运行 release DB diagnostics（当本地 release DB 可用时）
```bash
PYTHONPATH=rst2md uv run python -m rag.cli diagnostics --db godot_rag/rag/godot_docs.sqlite --no-model --json
```

## 执行顺序

1. 阶段 1 → 阶段 2 → 阶段 3（可并行，但建议顺序执行以便调试）
2. 阶段 4 验证

## 风险与注意事项

- 小型确定性 fixtures 不应意外断言 release-db 规模属性（如 `>= 28000` 行）
- 更改 metadata 名称可能影响消费者。优先添加明确原因，保持现有 JSON keys
- 文本 debug 输出不应在 `--debug-search` 不存在时改变正常输出
