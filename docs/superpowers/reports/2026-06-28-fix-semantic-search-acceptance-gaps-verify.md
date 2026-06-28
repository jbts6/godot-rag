# 验证报告：fix-semantic-search-acceptance-gaps

**日期**: 2026-06-28
**验证模式**: light
**分支**: hotfix/20260628/fix-semantic-search-acceptance-gaps

## 验证结果：PASS

### 检查项

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | tasks.md 全部任务完成 | ✅ | 9/9 任务已完成 |
| 2 | 改动文件与 tasks.md 一致 | ✅ | 5 个文件变更，259 行新增，16 行删除 |
| 3 | 编译通过 | ✅ | Python 项目无编译步骤 |
| 4 | 相关测试通过 | ✅ | 56 个测试通过 |
| 5 | 无安全问题 | ✅ | 无硬编码密钥或安全问题 |
| 6 | 代码审查 | ⏭️ | review_mode=off，跳过自动代码审查 |

### 变更摘要

1. **测试确定性 fixtures**：替换 `test_db` fixture，使用 `tmp_path` 构建小型 docs 树，消除对 `godot_rag/docs-md` 的依赖
2. **回归测试**：添加测试验证 pytest 不需要 generated state
3. **Debug metadata 可见性**：让 `--debug-search` 在文本模式下输出 metadata header
4. **CLI 测试覆盖**：添加 `--debug-search` 文本输出和 JSON 输出测试
5. **Vector availability 语义**：扩展 `_vector_availability` 检测 degraded 状态（empty_vec_chunks、vector_row_count_mismatch、vector_query_failed）
6. **回归测试**：添加空 vec_chunks 和 row-count 不匹配的测试

### 验证证据

- 聚焦测试：56 passed in 1.62s
- Release DB diagnostics：chunks_count=30529, vec_chunks_count=30529, row_parity=true, ok=true
