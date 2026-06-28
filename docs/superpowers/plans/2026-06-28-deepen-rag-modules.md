---
change: deepen-rag-modules
design-doc: docs/superpowers/specs/2026-06-28-deepen-rag-modules-design.md
base-ref: 41c9839784385cc6749e48149000687789958f47
---

# Deepen RAG Modules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deepen the RAG runtime modules while preserving existing public `rag.store`, addon chunking, and CLI search behavior.

**Architecture:** Keep `rag.store` as a compatibility facade and move implementation details into focused internal modules: `db.py`, `relations.py`, `indexer.py`, `searcher.py`, and `addon_discovery.py`. Consolidate duplicated CLI search orchestration into one helper without changing parser commands, arguments, output shape, scoring, vector fallback metadata, graph expansion, database schema semantics, or addon chunk semantics.

**Tech Stack:** Python 3.10+, sqlite3, sqlite-vec optional extension, dataclasses, pathlib, argparse, pytest, uv, OpenSpec, Comet.

---

## File Structure

- Create: `rst2md/rag/db.py`
  - Own SQLite connection setup, schema constants, vector table schema, FTS sync SQL, and chunk text cleanup helpers.
- Create: `rst2md/rag/relations.py`
  - Own inheritance extraction and `build_chunk_relations(conn)`.
- Create: `rst2md/rag/indexer.py`
  - Own `build_database(docs_dir, db_path, addons_dir=None)` and private insertion helpers for documents, chunks, addons, symbols, FTS sync, and embeddings.
- Create: `rst2md/rag/searcher.py`
  - Own `search_database`, `search_database_with_metadata`, vector availability checks, vector query, FTS query, RRF fusion, graph expansion, snippet extraction, and result mapping.
- Create: `rst2md/rag/addon_discovery.py`
  - Own `AddonLayout`, addon exclusion rules, plugin root/name discovery, and file collection functions.
- Modify: `rst2md/rag/store.py`
  - Convert to a compatibility facade that imports and exposes existing public functions.
- Modify: `rst2md/rag/addon_docs.py`
  - Remove discovery/file collection implementation and import it from `addon_discovery.py`.
- Modify: `rst2md/rag/cli.py`
  - Add shared database guard and shared search runner; replace duplicated search command bodies with thin wrappers.
- Test: `rst2md/tests/test_rag_search.py`
  - Existing public search, CLI, vector fallback, FTS, graph expansion, and metadata coverage.
- Test: `rst2md/tests/test_rag_addon.py`
  - Existing addon discovery, file collection, chunking, and addon CLI coverage.
- Test: `rst2md/tests/test_semantic_search.py`
  - Existing semantic/vector availability and diagnostics coverage.
- Test: `rst2md/tests/test_build_release_cli.py`
  - Existing project script and CLI parser coverage.

## Global Constraints

- Do not change CLI commands, aliases, arguments, text output, or JSON output shape.
- Do not change search scoring, RRF formula, vector fallback reason values, graph expansion limits, or FTS query semantics.
- Do not change database schema behavior; moving schema constants is allowed.
- Do not change addon chunk paths, document types, chunk types, addon identifiers, symbols, headings, breadcrumbs, line spans, or text semantics.
- Do not edit vendored `addons/` sources or `godot-docs/`.
- Keep `rag.store` public imports valid.
- Prefer mechanical moves first; only rename private helpers when doing so reduces import ambiguity.
- Use TDD/verification discipline: establish baseline before moving code and run focused tests after each slice.

## Task 1: Baseline and Import Coverage

**Files:**
- Test: `rst2md/tests/test_rag_search.py`
- Test: `rst2md/tests/test_rag_addon.py`
- Test: `rst2md/tests/test_build_release_cli.py`
- Read only: `rst2md/rag/store.py`
- Read only: `rst2md/rag/cli.py`

- [x] **Step 1: Run focused baseline tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_rag_search.py rst2md/tests/test_rag_addon.py
```

Expected: all collected tests pass. Record the count in the implementation notes or task update.

- [x] **Step 2: Confirm public import coverage**

Run:

```bash
rtk rg -n "from rag.store import|import rag.store|search_database|search_database_with_metadata|build_database|list_addons|get_stats" rst2md/tests rst2md/rag
```

Expected: tests cover `build_database`, `search_database`, `search_database_with_metadata`, `list_addons`, and `get_stats` through public import paths or CLI commands.

- [x] **Step 3: Confirm CLI search coverage**

Run:

```bash
rtk rg -n "cmd_search|search-class|search-tutorial|search-engine|search-addon|--no-expand|debug_search|list_addons|get_stats" rst2md/tests/test_rag_search.py rst2md/tests/test_rag_addon.py rst2md/tests/test_build_release_cli.py
```

Expected: search command help, aliases, `--no-expand`, debug metadata, addon CLI, and stats/addons paths are represented in tests.

- [x] **Step 4: Update OpenSpec task status**

After Steps 1-3 pass, check off OpenSpec tasks `1.1` and `1.2` in `openspec/changes/deepen-rag-modules/tasks.md`.

## Task 2: Extract Shared Database Module

**Files:**
- Create: `rst2md/rag/db.py`
- Modify: `rst2md/rag/store.py`
- Test: `rst2md/tests/test_rag_search.py`

- [x] **Step 1: Create `rst2md/rag/db.py` by moving shared database primitives**

Move these existing definitions from `store.py` into `db.py` with identical behavior:

```python
import re
import sqlite3
from contextlib import contextmanager


@contextmanager
def get_connection(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    try:
        import sqlite_vec
        sqlite_vec.load(conn)
    except Exception:
        pass
    try:
        yield conn
    finally:
        conn.close()


CLASSREF_LINE_RE = re.compile(r"^\s*classref-\S+\s*$", re.MULTILINE)
ANCHOR_RE = re.compile(r"`([^`<]+)<class_[^>]+>`")


def clean_chunk_text(text: str) -> str:
    text = CLASSREF_LINE_RE.sub("", text)
    text = ANCHOR_RE.sub(r"`\1`", text)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'<img\b[^>]*/?\s*>', '', text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
```

Also move `SCHEMA`, `VEC_CHUNKS_SCHEMA`, and `FTS_SYNC` unchanged.

- [x] **Step 2: Re-export shared primitives from `store.py`**

Update `rst2md/rag/store.py` imports so existing callers still work:

```python
from rag.db import FTS_SYNC, SCHEMA, VEC_CHUNKS_SCHEMA, clean_chunk_text, get_connection
```

Remove the moved definitions from `store.py` only after the import is in place.

- [x] **Step 3: Run focused tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_rag_search.py::SearchTests rst2md/tests/test_rag_search.py::CliTests
```

Expected: selected tests pass.

## Task 3: Extract Relation Builder

**Files:**
- Create: `rst2md/rag/relations.py`
- Modify: `rst2md/rag/store.py`
- Test: `rst2md/tests/test_rag_search.py`
- Test: `rst2md/tests/test_semantic_search.py`

- [x] **Step 1: Create `rst2md/rag/relations.py`**

Move these responsibilities from `store.py` into `relations.py`:

```python
import re
from typing import List

from rag.symbols import normalize_symbol

INHERITS_RE = re.compile(r'\*\*Inherits:\*\*(.+)')


def extract_inherits(text: str) -> List[str]:
    match = INHERITS_RE.search(text)
    if not match:
        return []
    return re.findall(r'`([A-Za-z_][A-Za-z0-9_]*)`', match.group(1))


def build_chunk_relations(conn) -> None:
    # Move the existing _build_chunk_relations implementation here.
    # Preserve relation names, weights, token regexes, and insertion SQL.
```

Use the current `_build_chunk_relations` body exactly, replacing `_extract_inherits` calls with `extract_inherits`.

- [x] **Step 2: Delegate relation building from `store.py`**

Import the new function:

```python
from rag.relations import build_chunk_relations
```

Change the call in database build from:

```python
_build_chunk_relations(conn)
```

to:

```python
build_chunk_relations(conn)
```

Remove `_extract_inherits`, `INHERITS_RE`, and `_build_chunk_relations` from `store.py`.

- [x] **Step 3: Run graph and semantic relation tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_rag_search.py::ChunkRelationTests rst2md/tests/test_rag_search.py::GraphExpansionTests rst2md/tests/test_semantic_search.py::test_see_also_relations
```

Expected: selected tests pass.

- [x] **Step 4: Update OpenSpec task status**

After Task 2 and Task 3 are green, check off OpenSpec tasks `2.1` and `2.2`.

## Task 4: Extract Database Indexer

**Files:**
- Create: `rst2md/rag/indexer.py`
- Modify: `rst2md/rag/store.py`
- Test: `rst2md/tests/test_rag_search.py`
- Test: `rst2md/tests/test_semantic_search.py`

- [x] **Step 1: Create `rst2md/rag/indexer.py`**

Move `build_database` from `store.py` into `indexer.py`.

Required imports in `indexer.py`:

```python
import sqlite3
from pathlib import Path
from typing import Optional

from rag.chunker import chunk_markdown
from rag.db import FTS_SYNC, SCHEMA, VEC_CHUNKS_SCHEMA, clean_chunk_text, get_connection
from rag.relations import build_chunk_relations
from rag.symbols import extract_symbols
```

Keep optional imports local:

```python
from rag.addon_docs import chunk_addon
from rag.embeddings import generate_embeddings
```

Preserve existing progress `print()` calls, sqlite-vec fallback behavior, insertion SQL, and commit timing.

- [x] **Step 2: Delegate `build_database` from `store.py`**

In `store.py`, import:

```python
from rag.indexer import build_database
```

Remove the old `build_database` implementation from `store.py`.

- [x] **Step 3: Run database build/search tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_rag_search.py::SearchTests rst2md/tests/test_rag_search.py::FtsEscapeTests rst2md/tests/test_rag_search.py::CliTests rst2md/tests/test_semantic_search.py::test_vec_chunks_populated
```

Expected: selected tests pass.

- [x] **Step 4: Update OpenSpec task status**

After selected tests pass, check off OpenSpec task `2.3`.

## Task 5: Extract Searcher

**Files:**
- Create: `rst2md/rag/searcher.py`
- Modify: `rst2md/rag/store.py`
- Test: `rst2md/tests/test_rag_search.py`
- Test: `rst2md/tests/test_semantic_search.py`

- [x] **Step 1: Create `rst2md/rag/searcher.py`**

Move these definitions from `store.py` into `searcher.py`:

- `_FTS5_SPECIAL`
- `_smart_tokenize`
- `_escape_fts5`
- `vector_search`
- `rrf_fusion`
- `_extract_snippet`
- `_vector_availability`
- `_run_vector_query`
- `search_database_with_metadata`
- `search_database`
- `_search_database_impl`

Required imports in `searcher.py`:

```python
import sqlite3
import re
from pathlib import Path
from typing import List, Optional

from rag.db import clean_chunk_text, get_connection
from rag.models import SearchMetadata, SearchResponse, SearchResult
from rag.symbols import normalize_symbol
```

Keep this optional import local inside the vector path:

```python
from rag.embeddings import generate_embeddings
```

Preserve existing scores, query SQL, fallback reasons, result fields, graph expansion logic, and snippet behavior.

- [x] **Step 2: Delegate search public functions from `store.py`**

In `store.py`, import:

```python
from rag.searcher import rrf_fusion, search_database, search_database_with_metadata, vector_search
```

Remove moved search implementations from `store.py`.

- [x] **Step 3: Keep stats and addons in `store.py`**

Leave `list_addons` and `get_stats` in `store.py` for now, using `get_connection` from `rag.db`.

- [x] **Step 4: Run focused search and semantic tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py
```

Expected: both files pass.

- [x] **Step 5: Update OpenSpec task status**

After tests pass, check off OpenSpec tasks `2.4` and `2.5`.

## Task 6: Extract Addon Discovery

**Files:**
- Create: `rst2md/rag/addon_discovery.py`
- Modify: `rst2md/rag/addon_docs.py`
- Test: `rst2md/tests/test_rag_addon.py`

- [x] **Step 1: Create `rst2md/rag/addon_discovery.py`**

Move these definitions from `addon_docs.py` into `addon_discovery.py`:

- `_EXCLUDE_DIRS`
- `_ALLOWED_UNDERSCORE_DIRS`
- `_SKIP_FILES`
- `_CODE_EXTENSIONS`
- `_DOC_EXTENSIONS`
- `_DOC_DIR_CANDIDATES`
- `_EXAMPLE_DIR_CANDIDATES`
- `_API_SKIP_PARTS`
- `AddonLayout`
- `_is_excluded`
- `_same_path`
- `_existing_path`
- `_append_unique`
- `_plugin_roots`
- `_read_plugin_name`
- `discover_addon`
- `collect_doc_files`
- `collect_example_files`
- `collect_api_files`

Required imports:

```python
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
```

Keep the existing local import inside `discover_addon`:

```python
from rag.addon_configs import get_config
```

- [x] **Step 2: Import discovery functions in `addon_docs.py`**

Replace moved definitions with:

```python
from rag.addon_discovery import (
    _CODE_EXTENSIONS,
    AddonLayout,
    collect_api_files,
    collect_doc_files,
    collect_example_files,
    discover_addon,
)
```

If `AddonLayout` is no longer used directly in `addon_docs.py`, do not import it.

- [x] **Step 3: Preserve code chunking behavior**

Keep these definitions in `addon_docs.py` unchanged except for imports:

- C# and GDScript regexes
- `chunk_addon_markdown`
- `chunk_code_file`
- `_doc_comment_start`
- `_extract_api_lines`
- `chunk_api_file`
- `_read_doc_as_markdown`
- `chunk_addon`

- [x] **Step 4: Run addon tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_rag_addon.py
```

Expected: addon tests pass.

- [x] **Step 5: Update OpenSpec task status**

After tests pass, check off OpenSpec tasks `3.1`, `3.2`, and `3.3`.

## Task 7: Consolidate CLI Search Orchestration

**Files:**
- Modify: `rst2md/rag/cli.py`
- Test: `rst2md/tests/test_rag_search.py`
- Test: `rst2md/tests/test_rag_addon.py`
- Test: `rst2md/tests/test_build_release_cli.py`

- [x] **Step 1: Add shared database guard**

Add this helper near `_db_path_from_args`:

```python
def _require_db(args) -> Path:
    db_path = _db_path_from_args(args)
    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)
    return db_path
```

- [x] **Step 2: Add shared search runner**

Add this helper after `_print_results`:

```python
def _run_search(args, doc_types=None, addon=None):
    db_path = _require_db(args)
    expand = not getattr(args, "no_expand", False)
    if args.debug_search:
        response = search_database_with_metadata(
            db_path,
            args.query,
            limit=args.limit,
            doc_types=doc_types,
            addon=addon,
            expand_graph=expand,
        )
        _print_results(response.results, args.json, response.metadata, debug_search=True)
        return

    results = search_database(
        db_path,
        args.query,
        limit=args.limit,
        doc_types=doc_types,
        addon=addon,
        expand_graph=expand,
    )
    _print_results(results, args.json)
```

- [x] **Step 3: Replace duplicated search command bodies**

Update command functions to thin wrappers:

```python
def cmd_search(args):
    _run_search(args)


def cmd_search_class(args):
    _run_search(args, doc_types=["class"])


def cmd_search_tutorial(args):
    _run_search(args, doc_types=["tutorial", "getting_started"])


def cmd_search_engine(args):
    _run_search(args, doc_types=["engine_detail"])


def cmd_search_addon(args):
    _run_search(args, doc_types=["addon"], addon=getattr(args, "addon", None))
```

- [x] **Step 4: Use `_require_db` in non-search read commands**

Update `cmd_addons`, `cmd_stats`, and `cmd_diagnostics` to use `_require_db(args)` where they require an existing database. Keep `cmd_build` unchanged because it creates a database.

- [x] **Step 5: Run CLI/search tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_rag_search.py rst2md/tests/test_rag_addon.py rst2md/tests/test_build_release_cli.py
```

Expected: selected tests pass.

- [x] **Step 6: Update OpenSpec task status**

After tests pass, check off OpenSpec tasks `4.1`, `4.2`, `4.3`, and `4.4`.

## Task 8: Final Verification and Diff Review

**Files:**
- Modify: `openspec/changes/deepen-rag-modules/tasks.md`
- Verify: all changed files

- [x] **Step 1: Run final relevant tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_rag_search.py rst2md/tests/test_rag_addon.py rst2md/tests/test_semantic_search.py rst2md/tests/test_build_release_cli.py
```

Expected: all selected tests pass.

- [x] **Step 2: Run OpenSpec validation**

Run:

```bash
rtk openspec validate deepen-rag-modules
```

Expected: `Change 'deepen-rag-modules' is valid`.

- [x] **Step 3: Review changed files**

Run:

```bash
rtk git status --short
rtk git diff --stat
rtk git diff -- rst2md/rag/store.py rst2md/rag/db.py rst2md/rag/relations.py rst2md/rag/indexer.py rst2md/rag/searcher.py rst2md/rag/addon_docs.py rst2md/rag/addon_discovery.py rst2md/rag/cli.py
```

Expected:

- no generated database files
- no vendored `addons/` or `godot-docs/` edits
- `store.py` is a compatibility facade plus stats/addons helpers
- new modules contain the moved responsibilities
- CLI parser definitions remain unchanged except command function bodies

- [x] **Step 4: Check off final OpenSpec tasks**

After final tests and diff review pass, check off OpenSpec tasks `5.1`, `5.2`, and `5.3`.

## Self-Review

- Spec coverage: covers public interface stability, search CLI behavior, addon chunking semantics, and internal responsibility localization from `rag-module-architecture`.
- Placeholder scan: no TBD/TODO placeholders. Implementation move instructions refer to exact existing symbols and exact target files.
- Type consistency: function names and module names match the Design Doc and OpenSpec tasks.
