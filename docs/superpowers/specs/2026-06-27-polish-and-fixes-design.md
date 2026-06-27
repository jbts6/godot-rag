---
comet_change: polish-and-fixes
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-27-polish-and-fixes
status: final
---

# Design: Polish and Fixes

## 概述

修复已知 bug，补充缺失功能，提升代码质量和用户体验。

## Bug 修复

### #9 addon 搜索不支持 `--no-expand`

**问题**：`cli.py:162` 的 `cmd_search_addon` 没有读取 `args.no_expand` 参数。

**方案**：在 `cmd_search_addon` 中添加：
```python
expand = not getattr(args, 'no_expand', False)
results = search_database(..., expand_graph=expand)
```

**影响范围**：仅 `cli.py` 的 `cmd_search_addon` 函数。

**测试**：添加测试用例验证 `--no-expand` 参数生效。

## 新增功能

### #7 stats 命令

**功能**：`godot-rag stats` 显示数据库统计信息。

**输出内容**：
- chunk 总数和按 `doc_type` 分布（class / tutorial / engine_detail / addon / other）
- symbol 总数和按 `kind` 分布
- chunk_relations 总数和按 `relation` 分布（parent / inherits / references）
- addon 列表和 chunk 数

**实现**：
- `cli.py`：添加 `cmd_stats` 函数和 `stats` 子命令
- `store.py`：添加 `get_stats(db_path)` 函数，返回统计数据字典
- 支持 `--json` 和文本格式输出

**测试**：验证 stats 命令输出正确的统计数据。

### #8 snippet 高亮

**功能**：文本输出时，大 chunk 只显示匹配行附近的上下文，而不是完整 text。

**实现**：
- `SearchResult` 模型添加 `snippet` 字段（可选，默认空字符串）
- `store.py` 的 `search_database` 中，对每个结果提取 snippet：
  - 在 chunk text 中查找包含 query 关键词的行
  - 提取该行 ±3 行上下文
  - 用 `...` 标记截断位置
- `cli.py` 的 `_print_results`：
  - JSON 输出：包含完整 `text` 和 `snippet`
  - 文本输出：显示 `snippet`（如果有），否则显示完整 `text`

**测试**：验证 snippet 包含匹配行和上下文。

## 代码质量

### #10 连接管理

**方案**：在 `store.py` 中添加 context manager：

```python
from contextlib import contextmanager

@contextmanager
def get_connection(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

重构 `search_database`、`build_database`、`list_addons` 使用此 wrapper。

**测试**：确保所有现有测试通过。

## UX 改进

### #11 命令别名

**方案**：在 `cli.py` 中为每个搜索命令添加长别名：

| 短命令 | 长别名 |
|--------|--------|
| `s` | `search` |
| `s-class` | `search-class` |
| `s-tutorial` | `search-tutorial` |
| `s-engine` | `search-engine` |
| `s-addon` | `search-addon` |

使用 `add_parser` 的 `aliases` 参数实现。

### #12 构建进度条

**方案**：在 `build_database` 中添加简单进度输出：

```python
print(f"Building database... ({i+1}/{total} files)")
```

每处理 100 个文件输出一次进度。

## 测试策略

- 每个 bug 修复添加回归测试
- stats 命令验证输出格式和数据正确性
- snippet 验证包含匹配行和上下文
- 连接管理重构后确保所有现有测试通过

## 依赖关系

无外部依赖变更。所有功能使用 Python 标准库实现。
