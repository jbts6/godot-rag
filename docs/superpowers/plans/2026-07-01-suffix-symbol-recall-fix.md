---
change: suffix-symbol-recall-fix
design-doc: docs/superpowers/specs/2026-07-01-suffix-symbol-recall-fix-design.md
base-ref: 5c63e2c12884eb9bced2db7a5e954a1913879a5f
---

# Implementation Plan: suffix-symbol-recall-fix

## 概述

修复 `_canonical_form`（`rst2md/rag/symbols.py:23`）剥离 dot 导致 suffix recall 死代码的 bug。详见 [Design Doc](../specs/2026-07-01-suffix-symbol-recall-fix-design.md) 与 `openspec/changes/suffix-symbol-recall-fix/tasks.md`。

## 任务拆分

### Task 1: 修复归一化函数 + canonical 单元测试

- 1.1 `rst2md/rag/symbols.py:23`：`name.replace("_", "").replace(".", "")` → `name.replace("_", "")`；更新 docstring 去掉 "strip ."。
- 1.2 `rst2md/tests/test_rag_symbols.py::test_canonical_dotted`：`"nodeaddchild"` → `"node.addchild"`。
- 1.3 `rst2md/tests/test_rag_symbols.py::test_normalizes_method_symbols`：`"stringnameisvalidfilename"` → `"stringname.isvalidfilename"`。
- 1.4 跑 `uv run pytest -q rst2md/tests/test_rag_symbols.py`，确认 canonical 测试全绿。

**验证**：`normalize_symbol("Node.add_child") == "node.addchild"`；`normalize_symbol("StringName.is_valid_filename()") == "stringname.isvalidfilename"`。

### Task 2: 转正 suffix recall xfail 测试

- 2.1 `rst2md/tests/test_rag_search.py:1250`：移除 `@unittest.expectedFailure`。
- 2.2 更新该 test docstring，去掉 "Expected failure / deferred" 措辞。
- 2.3 检查 `rst2md/tests/test_rag_search.py` ~1561、1572 行注释，更新为已修复状态。
- 2.4 跑 `uv run pytest -q rst2md/tests/test_rag_search.py::RankingSignalTests::test_suffix_symbol_match_records_signal`，确认转正后通过。

**验证**：suffix 测试绿；`symbol_recall.suffix` 信号在 query=`add_child` 命中 `Node.add_child` 时被录制。

### Task 3: 全套测试 + baseline 刷新

- 3.1 `uv run pytest -q` 全套，预期 272 pass（原 271 pass + 1 xfail 转正），无新 fail。
- 3.2 跑 eval 刷新 `docs/search-quality/baseline.json`，记录 `resource-loader`/`node-connect-signal` matched_rank 变化。
- 3.3 baseline comparison：hit@1/hit@5/mrr@5 ≥ 0.763/0.895/0.805，无新增 gating failure。
- 3.4 若两条 gating failure 仍未进 window，按 Design Q1/Q2 记录到 tasks.md，不在本 change 扩范围。

### Task 4: 归档收尾

- 4.1 `CHANGELOG.md` 注明「升级后需重建索引以激活 suffix symbol recall」。
- 4.2 更新 `WIP.md`：本 change 移入「已完成的 Comet change」，刷新「下一步方向」。
- 4.3 提交所有改动。

## 风险与回滚

- 一行修复 + 3 个测试更新；回滚 revert 即可，无 DB schema 后果。
- 详见 Design Doc Risks/Trade-offs。
