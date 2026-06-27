---
change: polish-and-fixes
design-doc: docs/superpowers/specs/2026-06-27-polish-and-fixes-design.md
base-ref: 728129184d7a752f5feb12c23d20df926f1272b2
archived-with: 2026-06-27-polish-and-fixes
---

# Implementation Plan: Polish and Fixes

## 概述

修复已知 bug，补充缺失功能，提升代码质量和用户体验。共 11 个任务（跳过 #6 验证）。

## 执行顺序

按依赖关系排序：先独立模块，再依赖模块。

### Phase 1: 独立修改（无依赖）

#### Task 1.1: 修复 `cmd_search_addon` 的 `--no-expand` 支持
- 文件：`rst2md/rag/cli.py`
- 修改：在 `cmd_search_addon` 中添加 `expand = not getattr(args, 'no_expand', False)` 并传给 `search_database`
- 验证：运行 `uv run pytest -q` 确保现有测试通过

#### Task 4.1: 添加长命令别名
- 文件：`rst2md/rag/cli.py`
- 修改：为每个搜索命令添加 `aliases` 参数
- 验证：运行 `uv run pytest -q` 确保现有测试通过

#### Task 4.2: 添加构建进度输出
- 文件：`rst2md/rag/store.py`
- 修改：在 `build_database` 中每 100 个文件输出一次进度
- 验证：运行 `uv run pytest -q` 确保现有测试通过

### Phase 2: 连接管理重构

#### Task 3.1: 创建 SQLite 连接 context manager
- 文件：`rst2md/rag/store.py`
- 修改：添加 `get_connection` context manager
- 验证：运行 `uv run pytest -q` 确保现有测试通过

#### Task 3.2: 重构数据库操作使用 context manager
- 文件：`rst2md/rag/store.py`
- 修改：重构 `search_database`、`build_database`、`list_addons` 使用 `get_connection`
- 验证：运行 `uv run pytest -q` 确保所有测试通过

### Phase 3: 新增功能

#### Task 2.1: 实现 `godot-rag stats` 命令
- 文件：`rst2md/rag/cli.py`、`rst2md/rag/store.py`
- 修改：
  - `store.py`：添加 `get_stats(db_path)` 函数
  - `cli.py`：添加 `cmd_stats` 函数和 `stats` 子命令
- 验证：运行 `uv run pytest -q` 确保现有测试通过

#### Task 2.2: 为 stats 命令添加测试
- 文件：`rst2md/tests/test_rag_search.py`（或新建 `test_rag_stats.py`）
- 修改：添加测试用例验证 stats 命令输出
- 验证：运行 `uv run pytest -q` 确保测试通过

#### Task 2.3: 实现搜索结果 snippet 高亮
- 文件：`rst2md/rag/models.py`、`rst2md/rag/store.py`、`rst2md/rag/cli.py`
- 修改：
  - `models.py`：`SearchResult` 添加 `snippet` 字段
  - `store.py`：在 `search_database` 中提取 snippet
  - `cli.py`：文本输出显示 snippet
- 验证：运行 `uv run pytest -q` 确保现有测试通过

#### Task 2.4: 为 snippet 功能添加测试
- 文件：`rst2md/tests/test_rag_search.py`
- 修改：添加测试用例验证 snippet 包含匹配行和上下文
- 验证：运行 `uv run pytest -q` 确保测试通过

### Phase 4: 回归测试

#### Task 1.3: 为 bug 修复添加回归测试
- 文件：`rst2md/tests/test_rag_search.py`
- 修改：添加测试用例验证 `--no-expand` 参数生效
- 验证：运行 `uv run pytest -q` 确保所有测试通过

## 依赖关系

```
1.1 (bug fix) ──→ 1.3 (regression test)
4.1 (aliases) ──→ 无依赖
4.2 (progress) ──→ 无依赖
3.1 (context manager) ──→ 3.2 (refactor)
2.1 (stats) ──→ 2.2 (stats test)
2.3 (snippet) ──→ 2.4 (snippet test)
```

## 风险与缓解

- **连接管理重构**：可能影响现有功能 → 先运行现有测试确认基线，重构后再次验证
- **snippet 提取**：可能影响搜索性能 → 只对 top-K 结果提取 snippet，开销可控
