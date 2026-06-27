# Tasks: Polish and Fixes

## Bug 修复

- [x] 1.1 修复 `cmd_search_addon` 的 `--no-expand` 支持
- [x] 1.2 验证 graph expansion 的 addon 过滤正确性（已确认不是 bug，跳过）
- [x] 1.3 为 bug 修复添加回归测试

## 新增功能

- [x] 2.1 实现 `godot-rag stats` 命令（CLI + 数据库查询）
- [x] 2.2 为 stats 命令添加测试（已在 2.1 中完成）
- [x] 2.3 实现搜索结果 snippet 高亮
- [x] 2.4 为 snippet 功能添加测试（已在 2.3 中完成）

## 代码质量

- [x] 3.1 创建 SQLite 连接 context manager
- [x] 3.2 重构 `search_database` 和 `build_database` 使用 context manager

## UX 改进

- [x] 4.1 添加长命令别名（search, search-class, search-tutorial, search-engine, search-addon）
- [x] 4.2 添加构建进度输出
