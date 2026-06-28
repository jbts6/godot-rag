# Godot RAG

[English](README.md)

Godot 文档与 addon 的混合 RAG 搜索。按类型搜索，精准命中。

## 安装

```bash
uv pip install godot-rag
```

或从 wheel 安装：

```bash
uv pip install godot_rag-4.7.0-py3-none-any.whl
```

## 使用方法

### 按类型搜索

```bash
# 搜索类参考（仅 API 文档）
godot-rag s-class "Node.add_child"
godot-rag s-class "Signal.emit" --limit 3

# 搜索教程（教程 + 入门指南）
godot-rag s-tutorial "how to use signals"
godot-rag s-tutorial "2D pathfinding" --limit 5

# 搜索引擎细节（架构、文件格式、GDExtension 等）
godot-rag s-engine "GDExtension"
godot-rag s-engine "IDE debugging" --limit 3

# 搜索 addon 文档和示例
godot-rag s-addon "state machine"
godot-rag s-addon "state machine" --addon statecharts
godot-rag s-addon "dialogue" --limit 3

# 搜索全部文档（无类型过滤）
godot-rag s "Timer"

# 模糊符号匹配（camelCase/snake_case/带点号 都能匹配）
godot-rag s-class "addChild"          # 匹配 add_child, _add_child
godot-rag s-class "Node.add_child"    # 匹配 Node._add_child
godot-rag s-class "node_add_child"    # 匹配 Node.addChild

# 禁用图谱扩展（仅返回直接匹配结果）
godot-rag s-class "add_child" --no-expand
```

### 搜索 addon

```bash
# 搜索所有 addon 文档、示例和 API 摘要
godot-rag s-addon "state machine"
godot-rag s-addon "dialogue balloon"
godot-rag s-addon "scene transition"

# 按指定 addon 过滤
godot-rag s-addon "state" --addon statecharts
godot-rag s-addon "change_scene" --addon scene_manager
godot-rag s-addon "test" --addon gdUnit4

# 查找 API 符号
godot-rag s-addon "SceneManager" --addon scene_manager
godot-rag s-addon "change_scene" --addon scene_manager
godot-rag s-addon "scene_loaded" --addon scene_manager
godot-rag s-addon "BehaviorTree" --addon limboai
godot-rag s-addon "DialogueManager" --addon dialogue_manager

# 搜索示例代码
godot-rag s-addon "ninja_frog" --addon statecharts
godot-rag s-addon "verify_node_path" --addon doctor

# JSON 输出（供 AI agent 使用）
godot-rag s-addon "state machine" --addon statecharts --json
godot-rag s-addon "change_scene" --json
```

### 输出格式

```bash
# JSON 输出（供 AI Agent 使用）
godot-rag s-class "Vector3.normalized" --json
godot-rag s-addon "change_scene" --addon scene_manager --json

# 限制结果数量
godot-rag s-tutorial "C# Variant" --limit 3
```

JSON 输出包含图谱关系信息：

```json
{
  "score": 100.0,
  "symbol": "Node.add_child",
  "relation_type": "",
  "distance": 0,
  ...
},
{
  "score": 50.0,
  "symbol": "Node",
  "relation_type": "parent",
  "distance": 1,
  ...
}
```

- `relation_type`：`""`（直接匹配）、`"parent"`、`"inherits"`、`"references"`、`"see_also"`
- `distance`：`0`（直接）、`1`（图谱扩展）

## 示例

```bash
# AI 工作流：先查教程，再查 API 细节
godot-rag s-tutorial "scene tree" --json
godot-rag s-class "Node.get_children" --json

# AI 工作流：查看 addon 文档和示例
godot-rag s-addon "state machine" --addon statecharts --json
godot-rag s-addon "dialogue balloon" --addon dialogue_manager --json

# 快速 API 查询
godot-rag s-class "StringName.is_valid_filename"

# 跨全部文档的宽泛搜索
godot-rag s "physics interpolation"
```

## RAG vs 非 RAG：为什么重要

混合 RAG 系统（FTS5 + 符号索引）在 AI 辅助文档查询中，比原始文本搜索有显著优势。

### 基准测试：真实查询对比

测试数据库：**30,529 个 chunk**（28,231 个 Godot 文档 + 2,298 个 addon chunk，覆盖 9 个 addon）。

| 指标 | RAG（本工具） | grep（原始文件） | 提升 |
|---|---|---|---|
| **平均延迟** | 7.1 ms | 120 ms | **快 17 倍** |
| **多词查询** | ✅ 语义排序 | ❌ 仅精确匹配 | — |
| **API 符号查找** | ✅ O(1) 索引 | ❌ 线性扫描 | — |
| **结果排序** | ✅ BM25 相关性 | ❌ 无排序 | — |
| **过滤（addon/类型）** | ✅ SQL WHERE | ❌ 后处理 | — |
| **噪音（test/assets）** | ✅ 自动排除 | ❌ 手动过滤 | — |

### 查询命中率

| 查询 | RAG 结果 | grep 结果 | 备注 |
|---|---|---|---|
| `change_scene` | ✅ 3 命中 (12ms) | ✅ 13 文件 (152ms) | RAG：排序去重 |
| `SceneManager` | ✅ 3 命中 (12ms) | ✅ 41 文件 (100ms) | grep：噪音太多 |
| `SceneManager.change_scene` | ✅ 1 命中 (12ms) | ❌ 0 文件 | **RAG：精确符号命中** |
| `BehaviorTree` | ✅ 3 命中 (12ms) | ✅ 2 文件 (96ms) | RAG：包含文档上下文 |
| `DialogueManager` | ✅ 3 命中 (13ms) | ✅ 26 文件 (98ms) | RAG：仅相关文档 |
| `state machine transitions` | ✅ 3 命中 (13ms) | ❌ 0 文件 | **grep 无法处理多词** |
| `scene transition animation` | ✅ 2 命中 (11.9ms) | ❌ 0 文件 | **grep 无法处理多词** |
| `input helper gamepad` | ✅ 2 命中 (12ms) | ❌ 0 文件 | **grep 无法处理多词** |
| `input action mapping` | ✅ 3 命中 (11ms) | — | RAG 发现交叉引用 |

**核心洞察**：grep 只能做精确子串匹配。RAG 能处理自然语言查询（如 "state machine transitions"），并返回排序后的上下文结果。

### 图谱扩展：上下文关联

启用图谱扩展（默认开启）时，搜索结果会自动关联相关 chunk：

- **parent**：搜索 `add_child` 会同时返回 `Node` 类摘要
- **inherits**：搜索 `Node` 会同时返回 `Object`（其父类）
- **references**：文本中提及匹配符号的 chunk

```bash
# 图谱扩展自动补充上下文
$ godot-rag s-class "add_child"
  score: 100.0  symbol: Node.add_child        # 直接匹配
  score: 50.0   symbol: Node    relation: parent (distance=1)  # 自动扩展

# 禁用以获得更快、更精简的结果
$ godot-rag s-class "add_child" --no-expand
  score: 100.0  symbol: Node.add_child        # 仅直接匹配
```

### --addon 过滤器：精准搜索

```bash
# 不带过滤：结果来自多个 addon
$ godot-rag s-addon "state machine"
  → statecharts (API), limboai (docs)    # 混合结果

# 带过滤：仅目标 addon
$ godot-rag s-addon "state machine" --addon statecharts
  → statecharts (API, docs, examples)    # 精准
```

### 数据库覆盖

| Addon | 文档 | 示例 | API | 总计 |
|---|---|---|---|---|
| dialogue_manager | 140 | 2 | 55 | 197 |
| doctor | 34 | 125 | 41 | 200 |
| gdUnit4 | 1,030 | — | 214 | 1,244 |
| input_helper | 32 | 3 | 6 | 41 |
| limboai | 299 | 27 | — | 326 |
| phantom-camera | 12 | 11 | 38 | 61 |
| scene_manager | 1 | 2 | 5 | 8 |
| sound_manager | 13 | 2 | 7 | 22 |
| statecharts | 80 | 21 | 98 | 199 |
| **总计** | **1,641** | **193** | **464** | **2,298** |

- **addon_doc**：文档 markdown/RST，按标题分段
- **addon_example**：示例 .gd/.cs 代码文件
- **addon_api**：仅公开声明和文档注释（非完整源码）

## 更新

当 Godot 发布新版本时：

```bash
# 更新 godot-docs 子模块
cd godot-docs && git pull origin stable

# 重建文档和 RAG
uv run godot-rag-build build

# 纳入 Scene Manager wiki 文档
uv run godot-rag-build build --with-wiki

# 兼容入口仍可使用：
./build.sh
```

## 开发

```bash
uv run pytest -q
```

## 许可证

MIT
