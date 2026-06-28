# Fix Semantic Search Acceptance Gaps

## Why

`semantic-search-quality-hardening` 已合并，但验收审查发现仍有几个行为和测试可复现性缺口：

- 语义搜索质量门测试仍依赖本地生成目录 `godot_rag/docs-md`，而 `godot_rag/` 被 `.gitignore` 忽略。测试在当前机器可通过，但 fresh clone 或 CI 不保证具备该目录，违反 `semantic-search-quality` spec 中“不得依赖 untracked local-only state”的要求。
- `--debug-search` 只在 `--json` 输出时包含 metadata；文本输出下该 flag 静默无效，不利于人工排查 fallback。
- `vec_chunks` 表存在但为空或与 `chunks` 不一致时，搜索 metadata 仍可能报告 `mode="hybrid"`、`vector_available=True`，但实际没有可用 vector 结果。

## What

- 将语义搜索验收测试改为使用确定性 fixture，避免依赖 ignored/generated 本地目录。
- 让 debug search metadata 在文本模式下也可观察，或明确约束 `--debug-search` 的输出语义并补测试。
- 让搜索 metadata 能区分 vector table 存在但不可用、为空、行数不匹配、query 返回空等 degraded 状态。
- 保持生成数据库文件和 `godot_rag/` 继续被 git ignore；不要提交 generated DB。

## Non-Goals

- 不重新设计语义搜索排序架构。
- 不改变 embedding 模型。
- 不提交 `godot_rag/`、`godot_rag/docs-md`、`*.sqlite` 或 `*.db` 生成产物。
- 不扩大到 release 发布流程重构。

## Evidence

- 合并前/后全量测试均通过：`PYTHONPATH=rst2md uv run pytest -q` -> `110 passed`。
- 当前本地 release DB diagnostics 通过：`chunks_count == vec_chunks_count == 30529`。
- 审查复现：删除 `vec_chunks` 所有行后，`search_database_with_metadata()` 仍返回 `SearchMetadata(mode='hybrid', vector_available=True, fallback_reason='')`。
- 审查复现：`godot-rag s ... --debug-search` 文本输出不包含 `metadata`、`fallback` 或 `fts_only`；加 `--json` 才输出 metadata。
