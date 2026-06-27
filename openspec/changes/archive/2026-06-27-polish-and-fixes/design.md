# Design: Polish and Fixes

## Bug 修复

### #9 addon 搜索不支持 `--no-expand`

**问题**: `cmd_search_addon` 未读取 `args.no_expand` 参数，默认 `expand_graph=True`。

**方案**: 在 `cmd_search_addon` 中添加 `expand = not getattr(args, 'no_expand', False)` 并传给 `search_database`。

### #6 addon 过滤未传给 graph expansion

**问题**: `store.py` 的 graph expansion 查询中 `addon_filter` 和 `type_filter` 参数作用域有限。

**方案**: 确认 graph expansion 查询正确应用 addon 过滤。当前代码已在 `store.py:456` 使用 `type_filter + addon_filter`，需验证参数传递正确。

## 新增功能

### #7 stats 命令

**方案**: 添加 `godot-rag stats` CLI 子命令，查询并展示：
- chunk 总数和按 doc_type 分布
- symbol 总数和按 kind 分布
- chunk_relations 总数和按 relation 分布
- addon 列表和 chunk 数

输出支持 `--json` 和文本格式。

### #8 snippet 高亮

**方案**: 在 `SearchResult` 模型中添加 `snippet` 字段，搜索时提取匹配行附近 ±3 行上下文。JSON 输出包含完整 text，文本输出只显示 snippet。

## 代码质量

### #10 连接管理

**方案**: 创建 `sqlite3.connect` 的 context manager wrapper，确保连接正确关闭。

## UX 改进

### #11 命令别名

**方案**: 为 `search`、`search-class`、`search-tutorial`、`search-engine`、`search-addon` 添加长别名。

### #12 构建进度条

**方案**: 在 `build_database` 中添加简单的进度输出（已处理 N 文件 / 总 M 文件）。
