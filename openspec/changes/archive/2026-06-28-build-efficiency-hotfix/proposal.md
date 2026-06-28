# Build Efficiency Hotfix

## Why

`build-efficiency` 已归档，但完成情况审核发现 5 个缺陷：

- 缓存指纹没有覆盖 `rst2md/`、README、addon、wiki、工具版本等设计要求输入，可能复用过期构建产物。
- `godot-rag-build diagnostics` 子命令缺少 `PYTHONPATH=rst2md`，入口实际会因找不到 `rag.cli` 失败。
- `publish` 在测试、diagnostics 或 upload gate 失败时直接抛异常，`last-run.json` 仍可能保留上一条 build 成功报告。
- wheel 阶段在 `uv build` 后未找到目标 wheel 时会创建空文件，掩盖构建产物错误。
- 归档后的主 spec `Purpose` 仍是占位文本。

## Root Cause

`build-efficiency` 实现把阶段 fingerprint 简化成通用 helper，遗漏了阶段特有输入；CLI diagnostics 复用了 build 阶段命令但没有复用其环境；publish gate 失败路径没有统一写失败报告；wheel 验证为了让 fake runner 测试通过而触碰了真实产物路径；归档后没有补主 spec purpose。

## What

- 扩展阶段 fingerprint，覆盖设计要求的主要输入和工具版本。
- 让 standalone diagnostics 使用与构建阶段一致的 `PYTHONPATH` 环境。
- 让 publish 所有 gate 失败都返回并持久化 publish 失败报告。
- wheel 缺失时失败，不创建空 wheel。
- 更新 `build-release-efficiency` 主 spec purpose。

## Non-Goals

- 不改变发布命令的公共参数。
- 不改变 RAG 数据库 schema 或搜索行为。
- 不重做 build-efficiency 的整体架构。
