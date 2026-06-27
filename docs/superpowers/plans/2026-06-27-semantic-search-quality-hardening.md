---
change: semantic-search-quality-hardening
design-doc: docs/superpowers/specs/2026-06-27-semantic-search-quality-hardening-design.md
base-ref: 4faaf40b2e5d72840e11be8e67687814f63e514d
---

# Semantic Search Quality Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 semantic search 从“结构可用”提升为有发布 DB 校验、黄金查询、模型复用、fallback 可观测性的 release-ready 能力。

**Architecture:** 保留现有 `search_database(...) -> list[SearchResult]` 兼容接口，新增可返回元数据的搜索接口供 CLI JSON/debug 和诊断使用。发布校验复用同一套 diagnostics 逻辑，避免 build 脚本和 CLI 各自维护一份 `vec_chunks` 检查。

**Tech Stack:** Python 3.10+, SQLite/FTS5, sqlite-vec, model2vec, pytest, existing argparse CLI, `uv run`.

## Global Constraints

- 普通 text 搜索输出必须保持干净；fallback 信息只进入 JSON/debug/diagnostics 路径。
- `search_database(...)` 的现有调用者必须继续获得 `List[SearchResult]`，不需要改调用代码。
- 生成数据库是 ignored artifact：`*.sqlite`、`*.db` 和 `godot_rag/` 不得进入 git 跟踪。
- 相关性测试不得依赖未跟踪的本地默认数据库；必须构建小 fixture DB 或使用确定性 fixture。
- warm-query latency 门槛只适用于模型已加载后的热查询，阈值为 1 秒。
- 每个任务完成后运行对应测试并提交；提交前检查 `git status --short`，不要提交生成数据库。

---

## File Structure

- Modify: `rst2md/rag/models.py`
  - Add `SearchMetadata` and `SearchResponse` dataclasses. Keep `SearchResult` unchanged for compatibility.
- Modify: `rst2md/rag/store.py`
  - Add vector availability checks, fallback reason reporting, `search_database_with_metadata(...)`, and release DB validation helpers if not placed in diagnostics.
- Create: `rst2md/rag/diagnostics.py`
  - Own DB diagnostics: path exists, sqlite-vec extension load, `vec_chunks` existence, row parity, model availability.
- Modify: `rst2md/rag/embeddings.py`
  - Cache the model2vec model per process and expose a test-only cache reset helper.
- Modify: `rst2md/rag/cli.py`
  - Add `--debug-search` common search flag and a `diagnostics` subcommand.
  - Use metadata search when JSON/debug metadata is requested.
- Modify: `build.sh`
  - Run diagnostics after building `godot_rag/rag/godot_docs.sqlite`.
  - Verify the generated DB path is ignored by git.
- Modify: `rst2md/tests/test_semantic_search.py`
  - Add fallback metadata, vector failure, model cache, latency, and golden query tests.
- Modify or create: `rst2md/tests/test_rag_cli.py`
  - If there is no dedicated CLI test file, add CLI diagnostics/debug tests to `rst2md/tests/test_rag_search.py` near existing CLI regression tests.

## Task 1: Search Metadata And Diagnostics Foundation

**Files:**
- Modify: `rst2md/rag/models.py`
- Create: `rst2md/rag/diagnostics.py`
- Modify: `rst2md/rag/store.py`
- Modify: `rst2md/rag/cli.py`
- Test: `rst2md/tests/test_semantic_search.py`

**Interfaces:**
- Produces: `SearchMetadata(mode: str, vector_available: bool, fallback_reason: str = "")`
- Produces: `SearchResponse(results: List[SearchResult], metadata: SearchMetadata)`
- Produces: `search_database_with_metadata(db_path: Path, query: str, limit: int = 8, doc_types: Optional[List[str]] = None, addon: Optional[str] = None, expand_graph: bool = True) -> SearchResponse`
- Produces: `run_diagnostics(db_path: Path, check_model: bool = True) -> dict`
- Consumes: existing `SearchResult`, `get_connection`, `search_database`

- [ ] **Step 1: Write failing metadata tests**

Add these tests to `rst2md/tests/test_semantic_search.py`:

```python
def test_search_metadata_reports_hybrid_when_vectors_work(tmp_path, monkeypatch):
    from rag import embeddings
    from rag.store import search_database_with_metadata

    docs = tmp_path / "docs"
    classes = docs / "classes"
    classes.mkdir(parents=True)
    (classes / "class_timer.md").write_text(
        "# Timer\n\n"
        "## Methods\n\n"
        "`bool` **is_stopped**() `const`\n\n"
        "Returns true if the timer is stopped.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts])
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)

    response = search_database_with_metadata(db_path, "timer stopped", limit=3, expand_graph=False)

    assert response.results
    assert response.metadata.mode == "hybrid"
    assert response.metadata.vector_available is True
    assert response.metadata.fallback_reason == ""
```

Add a second failing test for a missing vector table:

```python
def test_search_metadata_reports_fts_only_when_vec_table_missing(tmp_path, monkeypatch):
    from rag import embeddings
    from rag.store import search_database_with_metadata

    docs = tmp_path / "docs"
    classes = docs / "classes"
    classes.mkdir(parents=True)
    (classes / "class_timer.md").write_text(
        "# Timer\n\n"
        "## Methods\n\n"
        "`bool` **is_stopped**() `const`\n\n"
        "Returns true if the timer is stopped.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts])
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)
    with get_connection(db_path) as conn:
        conn.execute("DROP TABLE IF EXISTS vec_chunks")
        conn.commit()

    response = search_database_with_metadata(db_path, "timer stopped", limit=3, expand_graph=False)

    assert response.results
    assert response.metadata.mode == "fts_only"
    assert response.metadata.vector_available is False
    assert response.metadata.fallback_reason == "missing_vec_chunks"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk env PYTHONPATH=rst2md uv run pytest rst2md/tests/test_semantic_search.py::test_search_metadata_reports_hybrid_when_vectors_work rst2md/tests/test_semantic_search.py::test_search_metadata_reports_fts_only_when_vec_table_missing -q
```

Expected: FAIL because `search_database_with_metadata` and metadata dataclasses do not exist.

- [ ] **Step 3: Add model dataclasses**

In `rst2md/rag/models.py`, add below `SearchResult`:

```python
@dataclass(frozen=True)
class SearchMetadata:
    mode: str
    vector_available: bool
    fallback_reason: str = ""


@dataclass(frozen=True)
class SearchResponse:
    results: List[SearchResult]
    metadata: SearchMetadata
```

- [ ] **Step 4: Implement metadata search wrapper**

In `rst2md/rag/store.py`, import the new models:

```python
from rag.models import SearchMetadata, SearchResponse, SearchResult
```

Add a private helper before `search_database`:

```python
def _vector_availability(conn) -> tuple[bool, str]:
    try:
        conn.execute("SELECT 1 FROM vec_chunks LIMIT 1").fetchone()
    except sqlite3.OperationalError as exc:
        message = str(exc).lower()
        if "no such table" in message or "no such module" in message:
            return False, "missing_vec_chunks"
        return False, "vector_unavailable"
    return True, ""
```

Refactor `search_database` into an internal implementation:

```python
def search_database_with_metadata(
    db_path: Path, query: str, limit: int = 8,
    doc_types: Optional[List[str]] = None, addon: Optional[str] = None,
    expand_graph: bool = True,
) -> SearchResponse:
    results, metadata = _search_database_impl(
        db_path=db_path,
        query=query,
        limit=limit,
        doc_types=doc_types,
        addon=addon,
        expand_graph=expand_graph,
    )
    return SearchResponse(results=results, metadata=metadata)


def search_database(
    db_path: Path, query: str, limit: int = 8,
    doc_types: Optional[List[str]] = None, addon: Optional[str] = None,
    expand_graph: bool = True,
) -> List[SearchResult]:
    return search_database_with_metadata(
        db_path, query, limit=limit, doc_types=doc_types, addon=addon, expand_graph=expand_graph
    ).results
```

Move the existing body of `search_database` into `_search_database_impl(...) -> tuple[List[SearchResult], SearchMetadata]`. Inside the vector block:

```python
vector_available, fallback_reason = _vector_availability(conn)
metadata = SearchMetadata(mode="fts_only", vector_available=False, fallback_reason=fallback_reason)
if vector_available:
    try:
        from rag.embeddings import generate_embeddings
        query_embedding = generate_embeddings([query])[0]
        ...
        metadata = SearchMetadata(mode="hybrid", vector_available=True)
    except Exception:
        metadata = SearchMetadata(mode="fts_only", vector_available=False, fallback_reason="vector_query_failed")
```

At the final return, return `(results_list, metadata)` instead of only `results_list`.

- [ ] **Step 5: Add diagnostics module**

Create `rst2md/rag/diagnostics.py`:

```python
from pathlib import Path
import sqlite3


def run_diagnostics(db_path: Path, check_model: bool = True) -> dict:
    report = {
        "db_path": str(db_path),
        "db_exists": db_path.exists(),
        "sqlite_vec_available": False,
        "vec_chunks_exists": False,
        "chunks_count": None,
        "vec_chunks_count": None,
        "row_parity": False,
        "model_available": None,
        "ok": False,
        "errors": [],
    }
    if not db_path.exists():
        report["errors"].append("database_not_found")
        return report

    conn = sqlite3.connect(str(db_path))
    try:
        conn.enable_load_extension(True)
        try:
            import sqlite_vec
            sqlite_vec.load(conn)
            report["sqlite_vec_available"] = True
        except Exception:
            report["errors"].append("sqlite_vec_unavailable")

        try:
            report["chunks_count"] = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        except sqlite3.OperationalError:
            report["errors"].append("missing_chunks")

        try:
            report["vec_chunks_count"] = conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
            report["vec_chunks_exists"] = True
        except sqlite3.OperationalError:
            report["errors"].append("missing_vec_chunks")

        if report["chunks_count"] is not None and report["vec_chunks_count"] is not None:
            report["row_parity"] = report["chunks_count"] == report["vec_chunks_count"]
            if not report["row_parity"]:
                report["errors"].append("vector_row_count_mismatch")

        if check_model:
            try:
                from rag.embeddings import get_embedding_model
                get_embedding_model()
                report["model_available"] = True
            except Exception:
                report["model_available"] = False
                report["errors"].append("model_unavailable")

        report["ok"] = (
            report["db_exists"]
            and report["sqlite_vec_available"]
            and report["vec_chunks_exists"]
            and report["row_parity"]
            and report["model_available"] is not False
        )
        return report
    finally:
        conn.close()
```

- [ ] **Step 6: Add CLI diagnostics/debug surface**

In `rst2md/rag/cli.py`, import `run_diagnostics` and `search_database_with_metadata`.

Update `_add_search_args`:

```python
parser.add_argument("--debug-search", action="store_true", help="Include search-path metadata")
```

Add helper:

```python
def _result_to_dict(r):
    return {
        "score": r.score,
        "path": r.path,
        "start_line": r.start_line,
        "end_line": r.end_line,
        "doc_type": r.doc_type,
        "chunk_type": r.chunk_type,
        "addon": r.addon,
        "addon_name": r.addon_name,
        "symbol": r.symbol,
        "heading": r.heading,
        "breadcrumb": r.breadcrumb,
        "text": r.text,
        "relation_type": r.relation_type,
        "distance": r.distance,
    }
```

Update `_print_results` so `--json --debug-search` prints:

```python
{
  "metadata": {"mode": "...", "vector_available": true, "fallback_reason": ""},
  "results": [...]
}
```

Keep plain `--json` as the existing list for backwards compatibility. Add `cmd_diagnostics(args)`:

```python
def cmd_diagnostics(args):
    db_path = _db_path_from_args(args)
    report = run_diagnostics(db_path, check_model=not args.no_model)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"database: {report['db_path']}")
        print(f"ok: {report['ok']}")
        print(f"sqlite_vec_available: {report['sqlite_vec_available']}")
        print(f"vec_chunks: {report['vec_chunks_count']}")
        print(f"chunks: {report['chunks_count']}")
        print(f"row_parity: {report['row_parity']}")
        print(f"model_available: {report['model_available']}")
        if report["errors"]:
            print("errors: " + ", ".join(report["errors"]))
    if not report["ok"]:
        sys.exit(1)
```

Register subparser:

```python
diagnostics_parser = subparsers.add_parser("diagnostics", help="Validate semantic search readiness")
diagnostics_parser.add_argument("--db", help="Path to SQLite database")
diagnostics_parser.add_argument("--json", action="store_true", help="Output as JSON")
diagnostics_parser.add_argument("--no-model", action="store_true", help="Skip embedding model availability check")
diagnostics_parser.set_defaults(func=cmd_diagnostics)
```

- [ ] **Step 7: Run focused tests**

Run:

```bash
rtk env PYTHONPATH=rst2md uv run pytest rst2md/tests/test_semantic_search.py -q
```

Expected: PASS for metadata tests and existing semantic tests.

- [ ] **Step 8: Commit**

```bash
rtk git add rst2md/rag/models.py rst2md/rag/store.py rst2md/rag/diagnostics.py rst2md/rag/cli.py rst2md/tests/test_semantic_search.py
rtk git commit -m "feat: expose semantic search diagnostics metadata"
```

## Task 2: Fallback Behavior Coverage

**Files:**
- Modify: `rst2md/rag/store.py`
- Modify: `rst2md/rag/diagnostics.py`
- Modify: `rst2md/tests/test_semantic_search.py`

**Interfaces:**
- Consumes: `search_database_with_metadata(...)`
- Consumes: `run_diagnostics(...)`
- Produces fallback reasons: `missing_vec_chunks`, `missing_extension`, `vector_query_failed`

- [ ] **Step 1: Write failing fallback tests**

Add tests to `rst2md/tests/test_semantic_search.py`:

```python
def test_search_metadata_reports_vector_query_failure(tmp_path, monkeypatch):
    from rag import embeddings
    from rag import store

    docs = tmp_path / "docs"
    classes = docs / "classes"
    classes.mkdir(parents=True)
    (classes / "class_node.md").write_text(
        "# Node\n\n"
        "## Methods\n\n"
        "`void` **add_child**(`Node` node)\n\nAdds a child node.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts])
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)

    def fail_vector_search(*args, **kwargs):
        raise RuntimeError("vector query failed")

    monkeypatch.setattr(store, "_run_vector_query", fail_vector_search)
    response = store.search_database_with_metadata(db_path, "child node", limit=3, expand_graph=False)

    assert response.results
    assert response.metadata.mode == "fts_only"
    assert response.metadata.fallback_reason == "vector_query_failed"
```

Add diagnostics row-parity test:

```python
def test_diagnostics_reports_vector_row_count_mismatch(tmp_path, monkeypatch):
    from rag import embeddings
    from rag.diagnostics import run_diagnostics

    docs = tmp_path / "docs"
    classes = docs / "classes"
    classes.mkdir(parents=True)
    (classes / "class_node.md").write_text(
        "# Node\n\n"
        "## Methods\n\n"
        "`void` **add_child**(`Node` node)\n\nAdds a child node.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts])
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM vec_chunks WHERE chunk_id = (SELECT MIN(id) FROM chunks)")
        conn.commit()

    report = run_diagnostics(db_path, check_model=False)

    assert report["ok"] is False
    assert report["row_parity"] is False
    assert "vector_row_count_mismatch" in report["errors"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk env PYTHONPATH=rst2md uv run pytest rst2md/tests/test_semantic_search.py::test_search_metadata_reports_vector_query_failure rst2md/tests/test_semantic_search.py::test_diagnostics_reports_vector_row_count_mismatch -q
```

Expected: FAIL until `_run_vector_query` exists and diagnostics row mismatch is implemented.

- [ ] **Step 3: Extract vector query helper**

In `rst2md/rag/store.py`, add:

```python
def _run_vector_query(conn, query_embedding: List[float], limit: int, type_filter: str, type_params: list, addon_filter: str, addon_params: list) -> list[dict]:
    vec_query = (
        "SELECT vc.chunk_id, vc.distance FROM vec_chunks vc "
        "JOIN chunks c ON vc.chunk_id = c.id "
        "WHERE vc.embedding MATCH ? AND k = ?"
        + type_filter + addon_filter
    )
    vec_rows = conn.execute(
        vec_query,
        [str(query_embedding), limit * 3] + type_params + addon_params,
    ).fetchall()
    return [{"id": row[0], "distance": row[1]} for row in vec_rows]
```

Call this helper from the vector block. Catch exceptions from the helper and set:

```python
metadata = SearchMetadata(mode="fts_only", vector_available=False, fallback_reason="vector_query_failed")
```

- [ ] **Step 4: Distinguish missing extension in diagnostics**

In `rst2md/rag/diagnostics.py`, when `sqlite_vec.load(conn)` fails, append `missing_extension`. If a `vec_chunks` query fails with `"no such module"` in the message, append `missing_extension` instead of only `missing_vec_chunks`.

- [ ] **Step 5: Run fallback tests**

Run:

```bash
rtk env PYTHONPATH=rst2md uv run pytest rst2md/tests/test_semantic_search.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
rtk git add rst2md/rag/store.py rst2md/rag/diagnostics.py rst2md/tests/test_semantic_search.py
rtk git commit -m "test: cover semantic vector fallback paths"
```

## Task 3: Model Cache And Warm Query Performance

**Files:**
- Modify: `rst2md/rag/embeddings.py`
- Modify: `rst2md/tests/test_semantic_search.py`

**Interfaces:**
- Produces: `get_embedding_model()`
- Produces: `reset_embedding_model_cache()`
- Consumes: `generate_embeddings(texts: List[str], batch_size: int = 1000) -> List[List[float]]`

- [ ] **Step 1: Write failing model reuse test**

Add to `rst2md/tests/test_semantic_search.py`:

```python
def test_generate_embeddings_reuses_model(monkeypatch):
    from rag import embeddings

    load_count = 0

    class FakeEncoded:
        def __init__(self, size):
            self.size = size

        def tolist(self):
            return [[0.0] * 256 for _ in range(self.size)]

    class FakeModel:
        def encode(self, batch):
            return FakeEncoded(len(batch))

    class FakeStaticModel:
        @staticmethod
        def from_pretrained(name):
            nonlocal load_count
            load_count += 1
            return FakeModel()

    monkeypatch.setattr(embeddings, "StaticModel", FakeStaticModel)
    embeddings.reset_embedding_model_cache()

    embeddings.generate_embeddings(["first"])
    embeddings.generate_embeddings(["second"])

    assert load_count == 1
```

Add warm latency test:

```python
def test_warm_query_latency_under_one_second(tmp_path, monkeypatch):
    import time
    from rag import embeddings

    docs = tmp_path / "docs"
    classes = docs / "classes"
    classes.mkdir(parents=True)
    (classes / "class_timer.md").write_text(
        "# Timer\n\n"
        "## Methods\n\n"
        "`bool` **is_stopped**() `const`\n\n"
        "Returns true if the timer is stopped.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts])
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)

    search_database(db_path, "timer stopped", limit=3, expand_graph=False)
    start = time.perf_counter()
    search_database(db_path, "timer stopped", limit=3, expand_graph=False)
    elapsed = time.perf_counter() - start

    assert elapsed < 1.0
```

- [ ] **Step 2: Run tests to verify model cache fails**

Run:

```bash
rtk env PYTHONPATH=rst2md uv run pytest rst2md/tests/test_semantic_search.py::test_generate_embeddings_reuses_model -q
```

Expected: FAIL because `reset_embedding_model_cache` and cacheable `StaticModel` binding do not exist.

- [ ] **Step 3: Implement model cache**

Replace `rst2md/rag/embeddings.py` with this structure:

```python
"""Vector embedding generation using model2vec."""

from typing import List

from model2vec import StaticModel

MODEL_NAME = "minishlab/potion-base-8M"
_MODEL = None


def get_embedding_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = StaticModel.from_pretrained(MODEL_NAME)
    return _MODEL


def reset_embedding_model_cache() -> None:
    global _MODEL
    _MODEL = None


def generate_embeddings(texts: List[str], batch_size: int = 1000) -> List[List[float]]:
    """Generate embeddings for a list of texts using model2vec."""
    model = get_embedding_model()
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch)
        embeddings.extend(batch_embeddings.tolist())
        if (i // batch_size) % 5 == 0:
            print(f"Generating embeddings... ({i + len(batch)}/{len(texts)})")
    return embeddings
```

- [ ] **Step 4: Run cache and latency tests**

Run:

```bash
rtk env PYTHONPATH=rst2md uv run pytest rst2md/tests/test_semantic_search.py::test_generate_embeddings_reuses_model rst2md/tests/test_semantic_search.py::test_warm_query_latency_under_one_second -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
rtk git add rst2md/rag/embeddings.py rst2md/tests/test_semantic_search.py
rtk git commit -m "perf: reuse semantic embedding model"
```

## Task 4: Golden Query Relevance Gates

**Files:**
- Modify: `rst2md/tests/test_semantic_search.py`

**Interfaces:**
- Consumes: `build_database(...)`
- Consumes: `search_database(...)`
- Produces deterministic top-K family assertions.

- [ ] **Step 1: Add fixture builder and failing golden tests**

Add helper to `rst2md/tests/test_semantic_search.py`:

```python
def _build_golden_search_db(tmp_path, monkeypatch):
    from rag import embeddings

    docs = tmp_path / "docs"
    classes = docs / "classes"
    tutorials = docs / "tutorials"
    classes.mkdir(parents=True)
    tutorials.mkdir(parents=True)

    (classes / "class_timer.md").write_text(
        "# Timer\n\n"
        "## Methods\n\n"
        "`void` **start**()\n\nStarts the countdown timer.\n\n"
        "`void` **stop**()\n\nStops the countdown timer.\n",
        encoding="utf-8",
    )
    (classes / "class_node.md").write_text(
        "# Node\n\n"
        "## Methods\n\n"
        "`void` **add_child**(`Node` node)\n\nAdds a child node to the scene tree.\n",
        encoding="utf-8",
    )
    (tutorials / "scene_tree.md").write_text(
        "# Scene Tree\n\n"
        "Nodes are arranged as a scene tree. Use add_child to attach nodes.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts])
    db_path = tmp_path / "golden.db"
    build_database(docs, db_path)
    return db_path
```

Add tests:

```python
@pytest.mark.parametrize(
    ("query", "expected_paths"),
    [
        ("countdown timer start stop", {"classes/class_timer.md"}),
        ("attach node to scene tree", {"classes/class_node.md", "tutorials/scene_tree.md"}),
    ],
)
def test_golden_queries_return_expected_path_family(tmp_path, monkeypatch, query, expected_paths):
    db_path = _build_golden_search_db(tmp_path, monkeypatch)

    results = search_database(db_path, query, limit=5, expand_graph=False)
    paths = {r.path for r in results}

    assert paths & expected_paths
```

- [ ] **Step 2: Run golden tests**

Run:

```bash
rtk env PYTHONPATH=rst2md uv run pytest rst2md/tests/test_semantic_search.py::test_golden_queries_return_expected_path_family -q
```

Expected: PASS or an actionable FAIL that shows ranking/FTS regressions. If it fails because fixture copy lacks enough matching text, adjust only fixture text, not production ranking.

- [ ] **Step 3: Commit**

```bash
rtk git add rst2md/tests/test_semantic_search.py
rtk git commit -m "test: add semantic search golden queries"
```

## Task 5: Release Database Validation Flow

**Files:**
- Modify: `build.sh`
- Modify: `rst2md/rag/cli.py`
- Modify: `rst2md/tests/test_rag_search.py` or create `rst2md/tests/test_rag_cli.py`
- Modify: `openspec/changes/semantic-search-quality-hardening/tasks.md`

**Interfaces:**
- Consumes: `run_diagnostics(...)`
- Produces CLI command: `godot-rag diagnostics --db <path> [--json] [--no-model]`
- Produces build validation: generated DB has `vec_chunks` row parity and ignored artifact status.

- [ ] **Step 1: Write failing CLI tests**

Add to `rst2md/tests/test_rag_search.py` near existing CLI regression tests:

```python
def test_cli_diagnostics_help():
    result = subprocess.run(
        [sys.executable, "-m", "rag.cli", "diagnostics", "--help"],
        capture_output=True,
        text=True,
        env=TEST_ENV,
    )

    assert result.returncode == 0
    assert "Validate semantic search readiness" in result.stdout
```

Add debug JSON test:

```python
def test_cli_search_debug_json_includes_metadata(tmp_path, monkeypatch, capsys):
    from rag import embeddings
    from rag.cli import cmd_search

    docs = tmp_path / "docs"
    classes = docs / "classes"
    classes.mkdir(parents=True)
    (classes / "class_timer.md").write_text(
        "# Timer\n\n"
        "## Methods\n\n"
        "`bool` **is_stopped**() `const`\n\n"
        "Returns true if the timer is stopped.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts])
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)

    class Args:
        db = str(db_path)
        query = "timer stopped"
        limit = 3
        json = True
        no_expand = True
        debug_search = True

    cmd_search(Args())
    output = json.loads(capsys.readouterr().out)

    assert output["metadata"]["mode"] in {"hybrid", "fts_only"}
    assert "results" in output
```

- [ ] **Step 2: Run CLI tests to verify failure**

Run:

```bash
rtk env PYTHONPATH=rst2md uv run pytest rst2md/tests/test_rag_search.py::RegressionTests::test_cli_diagnostics_help rst2md/tests/test_rag_search.py::RegressionTests::test_cli_search_debug_json_includes_metadata -q
```

Expected: FAIL until CLI command and debug JSON are wired.

- [ ] **Step 3: Wire release validation in `build.sh`**

After the `python3 -m rag.cli build` command, add:

```bash
echo "2b. 校验 RAG 数据库..."
PYTHONPATH=rst2md uv run python3 -m rag.cli diagnostics \
    --db godot_rag/rag/godot_docs.sqlite

if ! git check-ignore -q godot_rag/rag/godot_docs.sqlite; then
    echo "错误: godot_rag/rag/godot_docs.sqlite 必须被 git ignore"
    exit 1
fi
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
rtk env PYTHONPATH=rst2md uv run pytest rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py -q
```

Expected: PASS.

- [ ] **Step 5: Run full tests**

Run:

```bash
rtk env PYTHONPATH=rst2md uv run pytest -q
```

Expected: PASS.

- [ ] **Step 6: Run release DB validation flow**

If `godot_rag/rag/godot_docs.sqlite` already exists, run:

```bash
rtk env PYTHONPATH=rst2md uv run python3 -m rag.cli diagnostics --db godot_rag/rag/godot_docs.sqlite --no-model
rtk git check-ignore godot_rag/rag/godot_docs.sqlite
```

Expected: diagnostics exits 0, and `git check-ignore` prints `godot_rag/`.

If it does not exist, run the build without publishing:

```bash
rtk ./build.sh --no-bump
```

Expected: build reaches "=== 构建完成 ===" and diagnostics step passes.

- [ ] **Step 7: Update OpenSpec tasks**

In `openspec/changes/semantic-search-quality-hardening/tasks.md`, check off all completed tasks from sections 1 through 5 after the evidence above passes.

- [ ] **Step 8: Commit**

```bash
rtk git add build.sh rst2md/rag/cli.py rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py openspec/changes/semantic-search-quality-hardening/tasks.md
rtk git commit -m "build: validate semantic search release database"
```

## Final Verification

- [ ] Run OpenSpec validation:

```bash
rtk openspec validate semantic-search-quality-hardening --strict
```

Expected: PASS.

- [ ] Run focused semantic-search tests:

```bash
rtk env PYTHONPATH=rst2md uv run pytest rst2md/tests/test_semantic_search.py -q
```

Expected: PASS.

- [ ] Run full test suite:

```bash
rtk env PYTHONPATH=rst2md uv run pytest -q
```

Expected: PASS.

- [ ] Check generated artifacts are not staged:

```bash
rtk git status --short
```

Expected: source, tests, plan, and OpenSpec files only; no `*.db`, `*.sqlite`, `godot_rag/`, or `README_PYPI.md` staged.

## Self-Review

- Spec coverage: Task 1 and Task 2 cover fallback metadata and diagnostics; Task 3 covers model reuse and warm-query latency; Task 4 covers golden relevance; Task 5 covers release DB validation and ignored artifacts.
- Placeholder scan: No task depends on "TBD" or unspecified future work; each code-facing step includes concrete file paths, signatures, snippets, and commands.
- Type consistency: `SearchResponse.results` always contains `List[SearchResult]`; `search_database(...)` preserves the existing list return; CLI-only metadata uses `search_database_with_metadata(...)`.
