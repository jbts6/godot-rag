# 代理指南

## 项目概述

Godot RAG 是一个用于 Godot 引擎文档和插件的混合 RAG（检索增强生成）搜索系统。使用 FTS5 + 向量双重召回，配合 RRF（互惠排名融合）排序。

## 架构

### 核心组件

- **搜索器** (`rst2md/rag/searcher.py`)：混合搜索引擎，包含 FTS5、向量搜索、RRF 融合和图扩展
- **索引器** (`rst2md/rag/indexer.py`)：文档和嵌入向量的数据库索引
- **命令行接口** (`rst2md/rag/cli.py`)：命令行界面（`godot-rag` 命令）
- **查询规划器** (`rst2md/rag/query_plan.py`)：意图检测和查询路由
- **搜索评估器** (`rst2md/rag/search_eval.py`)：质量指标、延迟测量、诊断

### 数据流

1. 文档通过 `indexer.py` 索引到 SQLite，包含 FTS5 + 向量嵌入
2. 查询通过 `query_plan.py` 进行意图检测
3. `searcher.py` 执行混合搜索：FTS5 + 向量 + RRF 融合
4. 图扩展添加相关文档
5. 结果排序并返回

## 目录结构

```
rst2md/rag/           # 源代码（在此编辑)
  ├── cli.py          # CLI 入口点
  ├── searcher.py     # 混合搜索引擎
  ├── search_eval.py  # 质量评估
  ├── indexer.py      # 数据库索引
  ├── models.py       # 数据模型
  └── ...

rst2md/tests/         # 测试套件
  ├── test_rag_search.py
  ├── test_search_eval.py
  └── ...

godot_rag/            # 构建输出（切勿编辑）
docs/                 # 文档
openspec/             # 变更管理
```

## 代码智能

本项目使用 **CodeGraph** 进行代码导航和理解。`.codegraph/` 目录包含预构建的 SQLite 知识图谱，涵盖每个符号、边和文件。

### 何时使用 CodeGraph

**在使用 grep 或读取文件之前，始终先使用 CodeGraph** 来处理代码问题：
- "X 如何工作？" → `codegraph_explore("X")`
- "X 定义在哪里？" → `codegraph_explore("X")`
- "什么调用了 X？" → `codegraph_explore("X")`
- "X 影响什么？" → `codegraph_explore("X")`

### 如何查询

```bash
# 通过 MCP 工具（代理环境中首选）
codegraph_explore("search_database hybrid search")

# 通过 shell
codegraph explore "search_database hybrid search"
```

### CodeGraph 返回内容

- 按文件分组的逐行源代码
- 符号之间的调用路径（包括动态分派）
- 依赖它们的组件的影响范围摘要

### 相比 Grep 的优势

- 遵循动态分派（回调、重新导出、多态）
- 返回调用路径，而不仅仅是文本匹配
- 一次调用替代数十次 grep + 读取循环
- 比基于正则表达式的搜索更准确

### 反模式

- **不要先用 grep** — 使用 CodeGraph，然后仅对 CodeGraph 遗漏的细节使用 grep
- **不要重复验证 CodeGraph 结果** — 它们来自 AST 解析
- **不要单独读取文件** — CodeGraph 返回可直接编辑的源代码

## 开发

### 环境设置

```bash
uv sync                 # 安装依赖
uv run pytest -q        # 运行测试
```

### 测试

```bash
# 完整套件
uv run pytest -q

# 针对性测试
uv run pytest -q rst2md/tests/test_search_eval.py
uv run pytest -q rst2md/tests/test_rag_search.py
```

### 构建与发布

```bash
./build.sh              # 构建 wheel
./build.sh --publish    # 构建并发布到 PyPI
```

**重要**：`build.sh` 自动递增版本号。不要手动提交版本变更。

## 代码规范

- Python 3.10+，使用类型提示
- 使用数据类（dataclass）作为模型（`SearchMetadata`、`SearchResponse` 等）
- 使用 pytest 进行测试，fixtures 在 `rst2md/tests/fixtures/` 中
- 源代码导入使用 `from rag.module import ...`（构建时重写为 `from godot_rag.rag.module`）

## 关键模式

### 搜索流程
```python
from rag.searcher import search_database
from rag.models import SearchResponse

response: SearchResponse = search_database(db_path, query, limit=10, expand_graph=True)
```

### 评估
```python
from rag.search_eval import evaluate_database, load_queries

queries = load_queries(Path("rst2md/rag/search_eval_queries.json"))
report = evaluate_database(db_path, queries, diagnostic_window=50)
```

## 变更管理

本项目使用 OpenSpec + Comet 进行结构化变更管理：

1. **开启** — 创建变更提案和设计
2. **设计** — 通过头脑风暴进行深度设计
3. **构建** — 使用 TDD 实现
4. **验证** — 验证实现
5. **归档** — 合并规范并归档

活跃变更见 `openspec/changes/`，已完成变更见 `openspec/changes/archive/`。

## 常见任务

### 添加新的搜索功能
1. 修改 `rst2md/rag/searcher.py`
2. 如需要，更新 `rst2md/rag/models.py` 中的模型
3. 在 `rst2md/tests/test_rag_search.py` 中添加测试
4. 运行 `uv run pytest -q` 验证

### 更新搜索质量评估
1. 修改 `rst2md/rag/search_eval.py`
2. 更新 `rst2md/rag/search_eval_queries.json` 中的查询
3. 在 `rst2md/tests/test_search_eval.py` 中添加测试
4. 运行评估器测试：`uv run pytest -q rst2md/tests/test_search_eval.py`

### 添加 CLI 命令
1. 在 `rst2md/rag/cli.py` 中添加命令
2. 在 `rst2md/tests/` 中添加测试
3. 运行 `uv run pytest -q` 验证
