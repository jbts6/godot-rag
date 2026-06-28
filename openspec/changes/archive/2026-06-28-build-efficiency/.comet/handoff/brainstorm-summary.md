# Brainstorm Summary

- Change: build-efficiency
- Date: 2026-06-28

## 确认的技术方案

采用 Python release build orchestrator 作为主实现，暴露项目脚本入口 `godot-rag-build`，支持 `build`、`publish`、`diagnostics`、`clean-cache` 子命令。`build.sh` 降级为薄 wrapper，只负责把旧入口映射到新工具。

核心构建流程按阶段建模：版本/配置解析、docs 转换、wiki 准备、RAG DB 构建、diagnostics、包组装、README 合并、wheel 构建、发布前测试、包版本检查、上传。每个可缓存阶段记录输入指纹、输出检查、状态、耗时和原因。

## 候选技术方案

已确认，无未决候选方案。

## 关键取舍与风险

- 将构建工具放在 `scripts/build_release.py`，并通过 `pyproject.toml` 的 project script 暴露为 `godot-rag-build`。这样不会把构建工具放进运行时 `godot_rag` 包。
- 缓存只在指纹完全匹配且输出存在时命中；任何不确定状态都重跑。
- 风险：大目录 hash 可能有成本。缓解：只纳入相关文件、稳定排序，并在阶段耗时中暴露。
- 风险：发布涉及凭据和网络。缓解：上传前强制通过 build/test/diagnostics/version-check，且不记录 secrets。
- 风险：旧 `build.sh` 习惯可能变化。缓解：保留薄 wrapper 并明确支持主要旧参数。

## 测试策略

- 单元测试 CLI 参数解析、stage cache hit/miss、manifest/last-run JSON 写入、publish gate 顺序。
- 使用 mock/subprocess adapter 测试外部命令调用，不在单元测试中真实上传或重建完整 DB。
- 集成/冒烟测试覆盖 `build.sh` wrapper、`godot-rag-build --help`、`clean-cache`。
- 保留全量 `pytest` 作为最终验证。

## Spec Patch

无。OpenSpec delta spec 已覆盖入口、保守缓存、阶段报告、安全发布、wiki 支持和 cache cleanup。
