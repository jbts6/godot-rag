# Comet Design Handoff

- Change: polish-and-fixes
- Phase: design
- Mode: compact
- Context hash: af06994bcae427d6dd052c5cce72c748d2995e0b6d6a10fa27d83af28aa37ba7

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/polish-and-fixes/proposal.md

- Source: openspec/changes/polish-and-fixes/proposal.md
- Lines: 1-40
- SHA256: d56fa656f20d6f6f0738fd135edca066caa27c6388fe690ac04f9bfc5e03328c

```md
# Polish and Fixes

## 问题

godot-rag 存在多个小问题和改进机会，影响用户体验和代码质量：

1. **Bug: addon 搜索不支持 `--no-expand`** — `cmd_search_addon` 未读取 `args.no_expand` 参数
2. **Bug: addon 过滤未传给 graph expansion** — graph expansion 查询可能返回非目标 addon 的 chunk
3. **缺失功能: 无 `stats` 命令** — 用户无法查看数据库统计信息
4. **缺失功能: 搜索结果无 snippet 高亮** — 大 chunk 信息密度低
5. **代码质量: 连接管理粗糙** — 每次查询都 open/close 连接
6. **UX: 命令别名太短** — `s`、`s-class` 对人类用户不直观
7. **UX: 构建无进度条** — 处理 30k+ chunks 时无进度提示

## 目标

修复已知 bug，补充缺失功能，提升代码质量和用户体验。

## 范围

### Bug 修复
- 修复 addon 搜索的 `--no-expand` 支持
- 修复 graph expansion 的 addon 过滤

### 新增功能
- `godot-rag stats` 命令（chunk 数量、类型分布、符号数量、关系数量）
- 搜索结果 snippet 高亮（提取匹配行附近上下文）

### 代码质量
- 连接管理优化（context manager）

### UX 改进
- 添加长命令别名（`search`、`search-class` 等）
- 构建进度条

## 不在范围内

- 搜索质量改进（#2 references 噪音、#3 see_also 关系）→ 独立 change: `search-quality`
- 构建效率优化（#4 增量构建、#5 references O(n²)）→ 独立 change: `build-efficiency`
- 向量语义搜索（#1）→ 独立 change: `search-quality`
```

## openspec/changes/polish-and-fixes/design.md

- Source: openspec/changes/polish-and-fixes/design.md
- Lines: 1-47
- SHA256: 88e8db32d34d67e8fc9d9417b7bf72e9f4339d4567787525c437db9a1a99e5c0

```md
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
```

## openspec/changes/polish-and-fixes/tasks.md

- Source: openspec/changes/polish-and-fixes/tasks.md
- Lines: 1-24
- SHA256: fc9bc165c36927d8821997d8d6683c91c7ccf01d1dc9da1e384435caceab20db

```md
# Tasks: Polish and Fixes

## Bug 修复

- [ ] 1.1 修复 `cmd_search_addon` 的 `--no-expand` 支持
- [ ] 1.2 验证 graph expansion 的 addon 过滤正确性
- [ ] 1.3 为 bug 修复添加回归测试

## 新增功能

- [ ] 2.1 实现 `godot-rag stats` 命令（CLI + 数据库查询）
- [ ] 2.2 为 stats 命令添加测试
- [ ] 2.3 实现搜索结果 snippet 高亮
- [ ] 2.4 为 snippet 功能添加测试

## 代码质量

- [ ] 3.1 创建 SQLite 连接 context manager
- [ ] 3.2 重构 `search_database` 和 `build_database` 使用 context manager

## UX 改进

- [ ] 4.1 添加长命令别名（search, search-class, search-tutorial, search-engine, search-addon）
- [ ] 4.2 添加构建进度输出
```

