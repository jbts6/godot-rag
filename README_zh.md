# Godot RAG

[English](README.md)

Godot 文档与 addon 的混合 RAG 搜索。按类型搜索，精准命中。

## 安装

```bash
# 作为全局工具（推荐）
uv tool install godot-rag

# 或安装到当前环境
uv pip install godot-rag
```

### AI Agent Skill

为 AI 编程助手（Claude Code、opencode、Cursor 等）安装 godot-rag skill：

```bash
npx skills add jbts6/skills --skill godot-rag
```

该 skill 会引导 AI 在编写 Godot 代码前先查询文档，并对自然语言查询启用 HyDE 增强搜索。

## 使用方法

> **语言说明**：查询必须使用英文。非英文查询请先翻译为英文（例如："怎么做二段跳" → "how to double jump"）。Embedding 模型仅支持英文。

### 按类型搜索

所有搜索命令都有长别名：`search`、`search-class`、`search-tutorial`、`search-engine`、`search-addon`。

**默认行为**：`s`、`s-class`、`s-tutorial`、`s-engine` 排除 addon 结果。使用 `s-addon` 搜索 addon。

```bash
# 搜索类参考（仅 API 文档）
godot-rag s-class "Node.add_child"
godot-rag s-class "Signal.emit" --limit 3

# class.method 查询可用 — 自动找到类
godot-rag s-class "ResourceLoader.load"

# 搜索教程（教程 + 入门指南）
godot-rag s-tutorial "how to use signals"

# 搜索引擎细节（架构、文件格式、GDExtension 等）
godot-rag s-engine "GDExtension"

# 搜索 addon 文档和示例（必须使用 s-addon）
godot-rag s-addon "state machine"
godot-rag s-addon "state machine" --addon statecharts

# 搜索全部文档（无类型过滤，排除 addon）
godot-rag s "Timer"

# 模糊符号匹配（camelCase/snake_case/带点号 都能匹配）
godot-rag s-class "addChild"          # 匹配 add_child, _add_child
godot-rag s-class "Node.add_child"    # 匹配 Node._add_child

# 禁用图谱扩展（仅返回直接匹配结果）
godot-rag s-class "add_child" --no-expand
```

### 搜索 addon

```bash
# 搜索所有 addon 文档、示例和 API 摘要
godot-rag s-addon "state machine"

# 按指定 addon 过滤
godot-rag s-addon "state" --addon statecharts
godot-rag s-addon "change_scene" --addon scene_manager

# JSON 输出（供 AI agent 使用）
godot-rag s-addon "state machine" --addon statecharts --json
```

### 列出 addon

```bash
godot-rag addons
godot-rag addons --json
```

### 输出格式

```bash
# JSON 输出（供 AI Agent 使用）
godot-rag s-class "Vector3.normalized" --json

# 限制结果数量
godot-rag s-tutorial "C# Variant" --limit 3

# 调试搜索元数据
godot-rag s-class "Node.add_child" --debug-search
```

## 更新

当 Godot 发布新版本时：

```bash
# 更新 godot-docs 子模块
cd godot-docs && git pull origin stable

# 重建文档和 RAG
uv run godot-rag-build build

# 构建并发布到 PyPI
uv run godot-rag-build publish --target pypi

# 构建并发布到 TestPyPI
uv run godot-rag-build publish --target testpypi
```

## 开发

```bash
uv run pytest -q
```

## 许可证

MIT
