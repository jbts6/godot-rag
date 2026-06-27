# Brainstorm Summary

- Change: polish-and-fixes
- Date: 2026-06-27

## 确认的技术方案

### Bug 修复
- #9: 在 `cmd_search_addon` 中添加 `expand = not getattr(args, 'no_expand', False)` 并传给 `search_database`
- #6: 确认代码已正确传递 addon 过滤，跳过此项

### 新增功能
- #7 stats 命令: `cli.py` 添加 `cmd_stats` + `stats` 子命令；`store.py` 添加 `get_stats(db_path)` 函数
- #8 snippet 高亮: `SearchResult` 添加 `snippet` 字段；搜索时提取匹配行 ±3 行上下文

### 代码质量
- #10 连接管理: 添加 `get_connection` context manager，重构所有数据库操作

### UX 改进
- #11 命令别名: 使用 argparse 的 `aliases` 参数添加长别名
- #12 构建进度条: 在 `build_database` 中每 100 个文件输出进度

## 关键取舍与风险

- snippet 实现行级截断，可能丢失跨行上下文，但简单高效
- 连接管理重构需要修改多个函数签名，但不影响外部 API

## 测试策略

- 每个 bug 修复添加回归测试
- stats 命令验证输出格式和数据正确性
- snippet 验证包含匹配行和上下文
- 连接管理重构后确保所有现有测试通过

## Spec Patch

无
