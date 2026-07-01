## 1. 修复归一化函数

- [x] 1.1 修改 `rst2md/rag/symbols.py` 的 `_canonical_form`：去掉 `.replace(".", "")`，只保留 `name.replace("_", "")`，更新 docstring（不再说 "strip ."）。
- [x] 1.2 更新 `rst2md/tests/test_rag_symbols.py::test_canonical_dotted` 断言：`"nodeaddchild"` → `"node.addchild"`。
- [x] 1.3 更新 `rst2md/tests/test_rag_symbols.py::test_normalizes_method_symbols` 断言：`"stringnameisvalidfilename"` → `"stringname.isvalidfilename"`。
- [x] 1.4 确认其余 canonical 测试（camelCase/snake_case/leading_underscore/mixed）输出不变，无需改动。

## 2. 转正 suffix recall 测试

- [x] 2.1 移除 `rst2md/tests/test_rag_search.py::test_suffix_symbol_match_records_signal` 的 `@unittest.expectedFailure` 装饰器，保留断言不变（query=`add_child`，期望命中 `Node.add_child` 并录制 `symbol_recall.suffix` weight=80.0）。
- [x] 2.2 更新该测试的 docstring，去掉「Expected failure / deferred to a separate change」措辞，改为说明 suffix recall 现已生效。
- [x] 2.3 检查 `rst2md/tests/test_rag_search.py` 与 `rst2md/tests/test_searcher_module.py` 中引用 suffix-recall dead-code / xfail 的注释（约 1561、1572 行），更新为已修复状态。额外把 `symbol_recall.suffix` 加入 `RankingSignalCoverageTests` 的 `required` 集以强化回归保护。

## 3. 验证与 baseline 刷新

- [x] 3.1 运行 `uv run pytest -q rst2md/tests/test_rag_symbols.py rst2md/tests/test_rag_search.py`，确认 canonical 与 suffix 测试通过。
- [x] 3.2 运行 `uv run pytest -q` 全套，确认 **273 pass**（原 272 pass + 1 xfail 转正，无新 fail）。
- [x] 3.3 在迁移后的本地 `godot_rag.db`（UPDATE symbols + 重建 chunk_relations）上跑 eval：hit@5 0.895→0.921、mrr@5 0.805→0.818、`scene-tree-tutorial` 不再 failure；`resource-loader`/`node-connect-signal` 仍 `matched=null`（预期目标非 `Class.method` 形态，suffix 修复不足以打开，需后续 alias/ranking change）。
- [x] 3.4 baseline comparison（本地迁移 DB）：hit@1 0.763 持平、hit@5 0.921≥0.895、mrr@5 0.818≥0.805，无新增非 addon gating failure。canonical `docs/search-quality/baseline.json` 未刷新——本地无完整 Godot docs（`godot-docs/` 仅 6 文件），canonical DB（17858 chunks）无法重建；guard `verify_command=pytest` 不依赖 canonical baseline，pytest 全绿即通过。

## 4. 归档收尾

- [x] 4.1 在 `CHANGELOG.md` 注明「升级后需重建索引以激活 suffix symbol recall」。
- [x] 4.2 更新 `WIP.md`：本 change 移入「已完成的 Comet change」，`resource-loader`/`node-connect-signal` 记录为后续 `symbol-query-normalization-fix` change 切入点。
