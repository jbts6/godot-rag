# Brainstorm Summary

- Change: semantic-search-quality-hardening
- Date: 2026-06-27

## 确认的技术方案

采用“质量闸门路线”：release DB validator、golden query fixture、模型缓存、搜索 JSON/debug metadata、diagnostics 命令都纳入本 change。

## 关键取舍与风险

- 已确认：warm-query latency 阈值采用 1s 内，只衡量模型已加载后的热查询，不把首次下载或冷启动纳入该阈值。
- 已确认：fallback 可观测性采用双通道，搜索 JSON/debug metadata 暴露本次模式与 fallback reason，同时新增 diagnostics 命令做主动环境/DB 检查。
- 已确认：不更换 embedding 模型，不重做 RAG 架构，不提交生成数据库二进制。
- 已确认：采用第 1 路线（质量闸门路线），每个 9 分短板都需要对应测试和验收。

## 测试策略

用小型 deterministic fixture 覆盖单元/集成逻辑，用本地 release DB validation 覆盖完整生成物，不让普通测试依赖 untracked DB；fallback 测试覆盖 JSON/debug metadata 和 diagnostics 命令。

## Spec Patch

将 delta spec 中的 warm-query latency 要求明确为 1s 内；将 fallback 可观测性明确为 JSON/debug metadata 与 diagnostics 命令两者都提供。
