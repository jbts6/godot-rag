# Addon RAG — 详细指令稿

## 1. 背景与目标

Godot 插件（addons/）各自带有独立的文档和示例代码。当前 RAG 系统只覆盖 Godot 官方文档（classes、tutorials、engine_details、getting_started）。本指令稿定义如何将插件内容纳入同一数据库，使 AI 能通过 `s-addon` 命令精确搜索插件文档和示例。

### 1.1 目标

- 将 8 个插件的文档和示例代码纳入 `godot_docs.sqlite`
- 通过 `addon` 字段区分插件来源
- 支持按插件名过滤搜索
- 与现有 Godot 官方文档共存于同一数据库

### 1.2 非目标

- 不处理插件的源码（addons/xxx/addons/ 下的 .gd 实现代码）
- 不处理 .tscn、.tres、.uid 等 Godot 资源文件
- 不为每个插件建独立数据库

---

## 2. 数据源分析

### 2.1 插件清单

| 插件 | 文档目录 | 文档格式 | 示例目录 | 示例格式 | 特殊说明 |
|---|---|---|---|---|---|
| dialogue_manager | docs/ (14 文件) | MD | addons/dialogue_manager/example_balloon/ | .gd .cs | .gd 有 22 条 ## 注释 |
| doctor | 无（分散在 examples README） | MD | addons/godot_doctor/examples/ (27 .gd, 27 .cs) | .gd .cs | 每个子目录有 README.md |
| gdUnit4 | documentation/ (56 文件) | MD | 无（test/ 不算示例） | — | Jekyll 站点结构，需排除脚手架 |
| input_helper | docs/ (5 文件) | MD | examples/ (2 .gd, 1 .cs) | .gd .cs | 最小示例集 |
| limboai | doc/source/ (103 文件) | **RST** | demo/ (27 .gd) | .gd | 唯一 RST 格式，需转换 |
| phantom-camera | 无 | — | dev_scenes/ (2 .gd) | .gd | 只有根 README，无 docs/ |
| sound_manager | docs/ (4 文件) | MD | examples/ (1 .gd, 1 .cs) | .gd .cs | 最小文档集 |
| statecharts | docs/_docs/ (12 文件) | MD | godot_state_charts_examples/ (19 .gd, 2 .cs) | .gd .cs | 示例目录有 README.md |

### 2.2 内容分类

**纳入 RAG 的内容：**

| 类型 | 来源 | chunk_type | 说明 |
|---|---|---|---|
| 文档 .md | docs/、documentation/、doc/source/ | addon_doc | 按 heading 分 chunk |
| 根 README.md | 插件根目录 | addon_doc | 按 heading 分 chunk |
| 示例 .gd | examples/、demo/、dev_scenes/ | addon_example | 整个文件一个 chunk |
| 示例 .cs | examples/、demo/、dev_scenes/ | addon_example | 整个文件一个 chunk |
| 示例 README | 示例目录内 | addon_example | 按 heading 分 chunk |

**跳过的内容：**

| 类型 | 原因 |
|---|---|
| .tscn、.tres、.uid | Godot 资源文件，非文本可搜索内容 |
| .mp3、.wav、.png、.jpg | 媒体资源 |
| CONTRIBUTING、CODE_OF_CONDUCT、SECURITY | 项目治理文件，非用户文档 |
| .github/ | issue 模板、CI 配置 |
| _includes/、_layouts/、assets/ | Jekyll 站点脚手架（gdUnit4） |
| test/ | 单元测试（gdUnit4 的 228 个 .gd 文件） |
| CHANGELOG、RELEASE_CHECKLIST | 维护文件 |

---

## 3. 数据库设计

### 3.1 Schema 变更

`chunks` 表新增一列：

```sql
addon TEXT NOT NULL DEFAULT ''
```

完整 chunks 表定义：

```sql
CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id),
  path TEXT NOT NULL,
  doc_type TEXT NOT NULL,
  chunk_type TEXT NOT NULL,
  addon TEXT NOT NULL DEFAULT '',
  symbol TEXT NOT NULL DEFAULT '',
  heading TEXT NOT NULL DEFAULT '',
  breadcrumb TEXT NOT NULL DEFAULT '',
  start_line INTEGER NOT NULL,
  end_line INTEGER NOT NULL,
  text TEXT NOT NULL
);
```

### 3.2 字段约定

| 字段 | Godot 官方文档 | 插件文档 | 插件示例 |
|---|---|---|---|
| doc_type | "class"/"tutorial"/"engine_detail"/"getting_started" | "addon" | "addon" |
| chunk_type | "class_summary"/"method"/"property"/"tutorial_section" | "addon_doc" | "addon_example" |
| addon | "" | "statecharts" | "statecharts" |
| symbol | "Node.add_child" | "" | "addons/statecharts/examples/ant.gd" |
| heading | "Methods" | "Installation" | "ant.gd" |
| breadcrumb | "classes > Node > add_child" | "addons > statecharts > Installation" | "addons > statecharts > examples/ant.gd" |

### 3.3 documents 表

`documents` 表不变，插件文档的 `doc_type` 设为 `"addon"`，`title` 取第一个 chunk 的 heading 或文件名。

### 3.4 symbols 表

插件示例代码的 symbol 为文件路径（如 `"addons/statecharts/examples/ant.gd"`），normalized 为小写。这样 `s-addon "ant.gd"` 能精确匹配。

### 3.5 FTS5 索引

`chunks_fts` 虚拟表不变，addon 列不参与 FTS 索引（addon 名通过 SQL WHERE 过滤）。

---

## 4. 自动发现算法

### 4.1 discover_addon(addon_dir: Path) -> AddonLayout

输入：单个插件根目录（如 `addons/statecharts/`）

输出：

```python
@dataclass
class AddonLayout:
    name: str                    # 插件目录名，如 "statecharts"
    root: Path                   # 插件根目录
    doc_dirs: List[Path]         # 文档目录列表
    doc_files: List[Path]        # 单独的文档文件（如根 README.md）
    example_dirs: List[Path]     # 示例目录列表
    is_rst: bool                 # 是否为 RST 格式（limboai）
```

**发现逻辑：**

```
1. name = addon_dir.name
2. doc_dirs = []
   - 若 addon_dir/docs/ 存在 → 加入 doc_dirs
   - 若 addon_dir/documentation/ 存在 → 加入 doc_dirs
   - 若 addon_dir/doc/source/ 存在 → 加入 doc_dirs
3. doc_files = []
   - 若 addon_dir/README.md 存在 → 加入 doc_files
4. example_dirs = []
   - 若 addon_dir/examples/ 存在 → 加入 example_dirs
   - 若 addon_dir/demo/ 存在 → 加入 example_dirs
   - 若 addon_dir/dev_scenes/ 存在 → 加入 example_dirs
   - 注意：gdUnit4 的 test/ 不算示例，不加入
5. is_rst = (addon_dir/doc/source/index.rst 存在)
6. 返回 AddonLayout
```

### 4.2 内容收集

**文档文件收集（collect_doc_files）：**

```
输入：doc_dirs: List[Path], doc_files: List[Path]
输出：List[Path]（所有 .md 文件，若 is_rst 则包含转换后的 .md）

对每个 doc_dir：
  递归扫描 *.md（RST 情况先转换）
  排除路径包含以下任一的文件：
    _includes/  _layouts/  assets/  .github/  pages/
    CONTRIBUTING  CODE_OF_CONDUCT  SECURITY  CHANGELOG
    _config.yml  _data/
  排除文件名以下划线开头的文件（_index.md 除外）

对每个 doc_file：
  直接加入列表
```

**示例文件收集（collect_example_files）：**

```
输入：example_dirs: List[Path]
输出：List[Path]（所有 .gd、.cs、README.md 文件）

对每个 example_dir：
  递归扫描 *.gd、*.cs
  递归扫描 README.md（每个子目录最多一个）
  排除 .tscn、.tres、.uid、.mp3、.wav、.png、.jpg
```

---

## 5. Chunking 策略

### 5.1 文档 .md 文件 → addon_doc

复用现有 `chunker.py` 的 `_chunk_tutorial_document()` 逻辑：

```
输入：addon_name: str, rel_path: str, markdown: str
输出：List[Chunk]

1. 按 markdown heading（# ## ###）分段
2. 每段一个 Chunk：
   - path = rel_path
   - doc_type = "addon"
   - chunk_type = "addon_doc"
   - addon = addon_name
   - symbol = ""
   - heading = 段落标题
   - breadcrumb = "addons > {addon_name} > {标题}"
   - start_line / end_line = 段落在原文中的行号
   - text = 段落内容
```

### 5.2 示例 .gd/.cs 文件 → addon_example

每个文件整体作为一个 chunk：

```
输入：addon_name: str, rel_path: str, code: str
输出：List[Chunk]（通常只有一个）

1. path = rel_path
2. doc_type = "addon"
3. chunk_type = "addon_example"
4. addon = addon_name
5. symbol = rel_path（如 "addons/statecharts/examples/ant.gd"）
6. heading = 文件名（如 "ant.gd"）
7. breadcrumb = "addons > {addon_name} > {相对路径}"
8. start_line = 1
9. end_line = 代码总行数
10. text = 原始代码内容（保留所有 ## 注释）
```

**特殊情况：**
- 文件超过 2000 行：按函数/类定义分段（预留，当前插件无此情况）
- 空文件：跳过

### 5.3 示例 README.md → addon_example

按 heading 分 chunk，与文档 .md 相同逻辑，但 chunk_type 为 `"addon_example"`：

```
同 5.1，但：
  chunk_type = "addon_example"
  heading = "README: {标题}"（加 README: 前缀以区分文档）
```

### 5.4 limboai RST 处理

```
1. 对 doc/source/ 下的 .rst 文件，调用 rst2md_batch.py 的转换单元
2. 转换为 .md 后，按 5.1 逻辑 chunk
3. classes/ 下的 auto-generated class ref 文件，按 class 文档逻辑处理
```

---

## 6. search_database 扩展

### 6.1 新增参数

```python
def search_database(
    db_path: Path,
    query: str,
    limit: int = 8,
    doc_types: Optional[List[str]] = None,
    addon: Optional[str] = None,       # 新增
) -> List[SearchResult]:
```

### 6.2 addon 过滤逻辑

当 `addon` 参数不为 None 时，在所有 4 层搜索中追加 SQL 条件：

```python
addon_filter = ""
addon_params: list = []
if addon:
    addon_filter = " AND c.addon = ?"
    addon_params = [addon]
```

与 doc_types 过滤组合使用：

```python
# 符号搜索
rows = conn.execute(
    "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id "
    "WHERE s.normalized_name = ?" + type_filter + addon_filter,
    [normalized] + type_params + addon_params,
).fetchall()

# FTS 搜索
fts_rows = conn.execute(
    "SELECT c.*, bm25(chunks_fts) as rank FROM chunks_fts fts "
    "JOIN chunks c ON fts.rowid = c.id "
    "WHERE chunks_fts MATCH ?" + fts_type_filter + addon_filter
    + " ORDER BY rank LIMIT ?",
    [escaped_query] + fts_type_params + addon_params + [limit * 3],
).fetchall()
```

### 6.3 SearchResult 扩展

```python
@dataclass(frozen=True)
class SearchResult:
    score: float
    path: str
    start_line: int
    end_line: int
    doc_type: str
    chunk_type: str
    addon: str          # 新增
    symbol: str
    heading: str
    breadcrumb: str
    text: str
```

---

## 7. CLI 设计

### 7.1 s-addon 子命令

```bash
godot-rag s-addon <query> [--addon NAME] [--limit N] [--json] [--db PATH]
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| query | positional | — | 搜索关键词 |
| --addon | optional | None | 按插件名过滤（如 "statecharts"） |
| --limit | optional | 8 | 最大结果数 |
| --json | flag | false | JSON 输出 |
| --db | optional | bundled db | 数据库路径 |

### 7.2 行为

```
s-addon "state machine"
  → search_database(db, "state machine", doc_types=["addon"])

s-addon "state machine" --addon statecharts
  → search_database(db, "state machine", doc_types=["addon"], addon="statecharts")

s-addon "dialogue" --limit 3 --json
  → search_database(db, "dialogue", limit=3, doc_types=["addon"])
```

### 7.3 输出格式

与现有 `s` 命令一致，额外显示 addon 字段：

```
score: 40.0
path: addons/statecharts/docs/_docs/usage/01_index.md:1-30
type: addon_doc
addon: statecharts
symbol:
heading: Usage
breadcrumb: addons > statecharts > Usage
text:
...
```

JSON 输出同样包含 `"addon"` 字段。

---

## 8. build.sh 集成

### 8.1 构建流程位置

在现有步骤 2（构建 RAG 数据库）之后、步骤 3（组装 RAG 包）之前，插入 addon 处理：

```
步骤 1: 转换 Markdown（Godot 官方文档）
步骤 2: 构建 RAG 数据库（Godot 官方文档）
步骤 2.5: 处理 addons 文档和示例 ← 新增
步骤 3: 组装 RAG 包
步骤 4: 构建 wheel
```

### 8.2 build_database 扩展

```python
def build_database(
    docs_dir: Path,
    db_path: Path,
    addons_dir: Optional[Path] = None,  # 新增
) -> None:
```

当 `addons_dir` 不为 None 时：

```
1. 遍历 addons_dir 下的子目录（跳过隐藏目录）
2. 对每个子目录：
   a. 调用 discover_addon() 获取布局
   b. 收集文档文件和示例文件
   c. 对文档文件：chunk_markdown() 或 RST 转换后 chunk
   d. 对示例文件：chunk_code_file()
   e. 写入数据库，addon = 插件名
```

### 8.3 build.sh 命令

```bash
# 步骤 2.5: 处理 addons
PYTHONPATH=rst2md uv run python3 -m rag.cli build \
    --docs godot_rag/docs-md \
    --db godot_rag/rag/godot_docs.sqlite \
    --addons addons
```

### 8.4 import 改写

`build.sh` 步骤 3 中复制 `rst2md/rag/*.py` 到 `godot_rag/rag/` 时，`addon_docs.py` 也会被复制，import 会被自动改写为 `from godot_rag.rag.xxx`。

---

## 9. 文件变更清单

| 文件 | 变更类型 | 说明 |
|---|---|---|
| rst2md/rag/models.py | 修改 | SearchResult 加 addon 字段 |
| rst2md/rag/store.py | 修改 | SCHEMA 加 addon 列，search_database 加 addon 参数，build_database 加 addons_dir 参数 |
| rst2md/rag/addon_docs.py | **新建** | discover_addon()、chunk_addon_docs()、chunk_code_file() |
| rst2md/rag/cli.py | 修改 | 新增 s-addon 子命令 |
| rst2md/tests/test_rag_addon.py | **新建** | 发现、chunk、搜索、CLI 测试 |
| rst2md/tests/test_rag_search.py | 修改 | SearchResult 构造加 addon="" |
| build.sh | 修改 | 新增 addon 处理步骤 |
| godot_rag/rag/models.py | 修改 | 同步 models.py |
| godot_rag/rag/store.py | 修改 | 同步 store.py |
| godot_rag/rag/cli.py | 修改 | 同步 cli.py |
| specs/addon-rag.md | 修改 | 本文件 |

---

## 10. 测试策略

### 10.1 单元测试

| 测试类 | 测试点 | fixture |
|---|---|---|
| TestAddonDiscovery | 发现 docs/、examples/ 目录 | 临时目录，创建 docs/、examples/、README.md |
| TestAddonDiscovery | 跳过 .github/、_includes/、test/ | 临时目录，创建这些目录含 .md 文件 |
| TestAddonDiscovery | phantom-camera（无 docs/） | 临时目录，只有 README.md |
| TestAddonChunker | MD 文档按 heading 分 chunk | 写入含 ## 的 .md 文件 |
| TestAddonChunker | .gd 文件整体为一个 chunk | 写入含 ## 注释的 .gd 文件 |
| TestAddonChunker | .cs 文件整体为一个 chunk | 写入含 /// 注释的 .cs 文件 |
| TestAddonChunker | 示例 README 按 heading 分 chunk | 写入 examples/README.md |
| TestAddonSearch | s-addon 搜所有插件 | 建库含两个插件数据 |
| TestAddonSearch | s-addon --addon 过滤单个插件 | 同上 |
| TestAddonSearch | s-addon 与 s 互不干扰 | 建库含 Godot 文档 + 插件数据 |
| TestAddonCLI | s-addon --help 输出正确 | subprocess 调用 |

### 10.2 集成测试

| 测试 | 说明 |
|---|---|
| 完整构建 | 对 addons/statecharts/ 建库，验证 addon_doc 和 addon_example 均存在 |
| 搜索验证 | 搜 "state machine" --addon statecharts，验证只返回 statecharts 结果 |

### 10.3 回归测试

现有 25 个测试必须全部通过，addon 列对旧数据为空字符串，不影响现有行为。

---

## 11. 边界情况

| 情况 | 处理 |
|---|---|
| 插件无文档、无示例（只有 README） | 只处理 README.md |
| 插件无 README | 跳过该插件，不报错 |
| .gd 文件无 ## 注释 | 仍然纳入，text 为原始代码 |
| .gd 文件超过 2000 行 | 预留分段逻辑，当前不触发 |
| 示例目录为空 | 跳过示例，只处理文档 |
| RST 文件转换失败 | 打印警告，跳过该文件 |
| addon 名与 Godot doc_type 冲突 | 不会冲突，addon 名是插件目录名 |
| 同一插件有 docs/ 和 documentation/ | 两个目录都扫描 |
| gdUnit4 的 test/ 目录 | 明确排除，不作为示例 |
