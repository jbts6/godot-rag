# Addon RAG — 执行计划

基于 `addon-rag.md` 指令稿，按依赖顺序执行。

---

## Phase 1: Schema 扩展

**目标**：chunks 表加 addon 列，SearchResult 加 addon 字段。

**变更文件**：
- `rst2md/rag/models.py` — SearchResult 加 `addon: str`
- `rst2md/rag/store.py` — SCHEMA 加列，search_database/build_database 签名扩展
- `godot_rag/rag/models.py` — 同步
- `godot_rag/rag/store.py` — 同步

**具体改动**：

models.py:
```python
@dataclass(frozen=True)
class SearchResult:
    ...
    addon: str          # 新增
    symbol: str
    ...
```

store.py SCHEMA:
```sql
CREATE TABLE IF NOT EXISTS chunks (
  ...
  addon TEXT NOT NULL DEFAULT '',
  ...
);
```

store.py search_database:
```python
def search_database(
    db_path: Path, query: str, limit: int = 8,
    doc_types: Optional[List[str]] = None,
    addon: Optional[str] = None,       # 新增
) -> List[SearchResult]:
```

**验证**：
- [ ] 现有 25 个测试全部通过（addon 列默认空字符串，不影响）
- [ ] 建库后 PRAGMA table_info(chunks) 包含 addon 列

---

## Phase 2: Addon 发现与 Chunk 逻辑

**目标**：实现 addon 文档和示例的自动发现、chunking。

**变更文件**：
- `rst2md/rag/addon_docs.py` — **新建**

**核心函数**：

```python
@dataclass
class AddonLayout:
    name: str
    root: Path
    doc_dirs: List[Path]
    doc_files: List[Path]
    example_dirs: List[Path]
    is_rst: bool

def discover_addon(addon_dir: Path) -> AddonLayout:
    """自动发现单个插件的文档和示例目录。"""
    ...

def collect_doc_files(layout: AddonLayout) -> List[Path]:
    """收集所有文档 .md 文件，排除脚手架和非文档文件。"""
    ...

def collect_example_files(layout: AddonLayout) -> List[Path]:
    """收集所有示例 .gd/.cs 文件和示例 README。"""
    ...

def chunk_addon_markdown(addon_name: str, rel_path: str, markdown: str) -> List[Chunk]:
    """文档 .md 按 heading 分 chunk，chunk_type="addon_doc"。"""
    ...

def chunk_code_file(addon_name: str, rel_path: str, code: str) -> List[Chunk]:
    """示例 .gd/.cs 整体为一个 chunk，chunk_type="addon_example"。"""
    ...

def chunk_addon(addon_dir: Path) -> List[Chunk]:
    """对单个插件，发现 + 收集 + chunk，返回所有 chunks。"""
    ...
```

**chunk_addon_markdown 逻辑**（见 spec §5.1）：
- 复用 `_chunk_tutorial_document` 的 heading 分割逻辑
- 但 doc_type="addon"，chunk_type="addon_doc"，addon=插件名

**chunk_code_file 逻辑**（见 spec §5.2）：
- 整个文件一个 chunk
- symbol = rel_path
- heading = 文件名
- breadcrumb = "addons > {addon_name} > {相对路径}"

**验证**：
- [ ] 对 statecharts 插件，discover_addon 发现 docs/_docs/ 和 godot_state_charts_examples/
- [ ] 对 phantom-camera，discover_addon 只发现 README.md
- [ ] 对 gdUnit4，discover_addon 发现 documentation/ 但不包含 test/
- [ ] chunk_code_file 对含 ## 注释的 .gd 文件，chunk 包含完整注释
- [ ] chunk_addon_markdown 对含 ## 的 .md 文件，按 heading 分成多 chunk

---

## Phase 3: Build 集成

**目标**：build_database 支持处理 addons，build.sh 调用。

**变更文件**：
- `rst2md/rag/store.py` — build_database 加 addons_dir 参数
- `build.sh` — 步骤 2 后插入 addon 处理

**build_database 扩展**：

```python
def build_database(
    docs_dir: Path,
    db_path: Path,
    addons_dir: Optional[Path] = None,
) -> None:
    ...
    # 原有逻辑：处理 docs_dir
    ...

    # 新增：处理 addons
    if addons_dir and addons_dir.is_dir():
        for addon_subdir in sorted(addons_dir.iterdir()):
            if not addon_subdir.is_dir() or addon_subdir.name.startswith('.'):
                continue
            chunks = chunk_addon(addon_subdir)
            if not chunks:
                continue
            addon_name = addon_subdir.name
            doc_type = "addon"
            title = chunks[0].heading or addon_name
            # 插入 documents 行
            # 插入 chunks 行（addon = addon_name）
            # 插入 symbols 行
```

**build.sh 改动**：

```bash
# 步骤 2.5: 处理 addons
echo "2.5. 处理 addons..."
PYTHONPATH=rst2md uv run python3 -m rag.cli build \
    --docs godot_rag/docs-md \
    --db godot_rag/rag/godot_docs.sqlite \
    --addons addons
```

**验证**：
- [ ] build.sh 执行后，godot_docs.sqlite 包含 addon 类型数据
- [ ] 查询 SELECT DISTINCT addon FROM chunks WHERE doc_type='addon' 返回 8 个插件名

---

## Phase 4: CLI s-addon 命令

**目标**：实现 s-addon 子命令。

**变更文件**：
- `rst2md/rag/cli.py` — 新增 cmd_search_addon、s-addon 子命令
- `godot_rag/rag/cli.py` — 同步

**cmd_search_addon 逻辑**：

```python
def cmd_search_addon(args):
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)
    results = search_database(
        db_path, args.query, limit=args.limit,
        doc_types=["addon"], addon=getattr(args, 'addon', None),
    )
    _print_results(results, args.json)
```

**子命令注册**：

```python
addon_parser = subparsers.add_parser("s-addon", help="Search addon docs and examples")
_add_search_args(addon_parser)
addon_parser.add_argument("--addon", help="Filter by addon name (e.g. statecharts)")
addon_parser.set_defaults(func=cmd_search_addon)
```

**验证**：
- [ ] `s-addon --help` 显示正确
- [ ] `s-addon "state" --addon statecharts` 只返回 statecharts 结果
- [ ] `s-addon "state" --json` 输出包含 addon 字段

---

## Phase 5: 测试

**目标**：全面测试覆盖。

**变更文件**：
- `rst2md/tests/test_rag_addon.py` — **新建**

**测试类和用例**（见 spec §10.1）：

```python
class TestAddonDiscovery(unittest.TestCase):
    def test_finds_docs_and_examples_dirs(self): ...
    def test_skips_github_includes_test(self): ...
    def test_phantom_camera_no_docs_dir(self): ...
    def test_gdunit4_excludes_test_dir(self): ...

class TestAddonChunker(unittest.TestCase):
    def test_markdown_split_by_heading(self): ...
    def test_gd_file_as_single_chunk(self): ...
    def test_cs_file_as_single_chunk(self): ...
    def test_example_readme_split_by_heading(self): ...
    def test_empty_gd_file_skipped(self): ...

class TestAddonSearch(unittest.TestCase):
    def test_search_all_addons(self): ...
    def test_search_specific_addon(self): ...
    def test_addon_search_does_not_affect_main_search(self): ...

class TestAddonCLI(unittest.TestCase):
    def test_saddon_help(self): ...
```

**验证**：
- [ ] 全部新增测试通过
- [ ] 现有 25 个测试全部通过（回归验证）

---

## Phase 6: 收尾

- [ ] 更新 README.md，加 s-addon 使用说明
- [ ] 更新 specs/addon-rag.md 中的验证清单
- [ ] 两个副本（rst2md/ 和 godot_rag/）代码同步
- [ ] git commit

---

## 执行顺序

```
Phase 1 (schema)
  ↓
Phase 2 (chunker)
  ↓
Phase 3 (build)
  ↓
Phase 4 (CLI)
  ↓
Phase 5 (tests)
  ↓
Phase 6 (收尾)
```

每 Phase 完成后跑全部测试，确认无回归再进入下一 Phase。
