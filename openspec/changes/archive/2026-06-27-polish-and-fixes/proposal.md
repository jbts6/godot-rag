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
