---
change: semantic-search
design-doc: docs/superpowers/specs/2026-06-27-semantic-search-design.md
base-ref: a2b5f75fa6b1c4cdc5de07b80ff684d66363c482
---

# 语义搜索实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 godot-rag 添加向量语义搜索能力，实现 FTS5 + 向量双路召回，RRF 融合排序，同时提取 see_also 关系。

**Architecture:** 使用 model2vec 生成 256 维向量，sqlite-vec 存储和检索，RRF 融合 FTS5 和向量两路结果。

**Tech Stack:** sqlite-vec, model2vec, pytest

## Global Constraints

- Python >= 3.9（pyproject.toml 要求）
- 测试运行：`uv run pytest -q`
- 源码目录：`rst2md/rag/`
- 测试目录：`rst2md/tests/`

---

### Task 1: 添加依赖

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: sqlite-vec 和 model2vec 依赖可用

- [x] **Step 1: 在 pyproject.toml 添加依赖**

```toml
[project]
name = "godot-rag"
version = "4.7.0.post10"
description = "Hybrid RAG search for Godot documentation"
readme = "README_PYPI.md"
requires-python = ">=3.9"
dependencies = [
    "sqlite-vec>=0.1.9",
    "model2vec>=0.8.2",
]
```

- [x] **Step 2: 验证依赖安装**

Run: `uv sync`
Expected: 无报错

- [x] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add sqlite-vec and model2vec dependencies"
```

---

### Task 2: 新增 vec_chunks 虚拟表

**Files:**
- Modify: `rst2md/rag/store.py:82-138` (SCHEMA 常量)

**Interfaces:**
- Produces: vec_chunks 虚拟表 schema

- [x] **Step 1: 在 SCHEMA 常量末尾添加 vec_chunks 表**

在 `store.py` 的 `SCHEMA` 常量末尾（`idx_relations_target` 之后）添加：

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding float[256]
);
```

- [x] **Step 2: 验证 schema 正确**

Run: `uv run python -c "from rag.store import SCHEMA; print('vec_chunks' in SCHEMA)"`
Expected: `True`

- [x] **Step 3: Commit**

```bash
git add rst2md/rag/store.py
git commit -m "feat: add vec_chunks virtual table schema"
```

---

### Task 3: 实现 see_also 关系提取

**Files:**
- Modify: `rst2md/rag/store.py:156-198` (_build_chunk_relations 函数)

**Interfaces:**
- Consumes: sym_to_id 字典（normalized_symbol -> chunk_id）
- Produces: chunk_relations 表中 see_also 类型关系

- [x] **Step 1: 在 _build_chunk_relations 函数末尾添加 see_also 提取逻辑**

在 `_build_chunk_relations` 函数的 `# 3. References relation` 循环之后添加：

```python
        # 4. See also relation: See also `xxx` references
        see_also_matches = re.findall(r'See also `([^`]+)`', text)
        for match in see_also_matches:
            target_norm = normalize_symbol(match)
            if target_norm and target_norm in sym_to_id and target_norm != normalize_symbol(symbol):
                target_id = sym_to_id[target_norm]
                conn.execute(
                    "INSERT OR IGNORE INTO chunk_relations (source_id, target_id, relation, weight) VALUES (?, ?, 'see_also', 0.6)",
                    (chunk_id, target_id)
                )
```

- [x] **Step 2: 构建数据库并验证 see_also 数量**

Run: `uv run python -c "
from pathlib import Path
from rag.store import build_database, get_connection
build_database(Path('godot_rag/docs-md'), Path('test_see_also.db'))
with get_connection(Path('test_see_also.db')) as conn:
    count = conn.execute(\"SELECT COUNT(*) FROM chunk_relations WHERE relation = 'see_also'\").fetchone()[0]
    print(f'see_also relations: {count}')
    assert count >= 100, f'Expected >= 100, got {count}'
"`
Expected: `see_also relations: >= 100`

- [x] **Step 3: 清理测试文件并 Commit**

```bash
rm -f test_see_also.db
git add rst2md/rag/store.py
git commit -m "feat: extract see_also relations from See also references"
```

---

### Task 4: 实现向量生成函数

**Files:**
- Create: `rst2md/rag/embeddings.py`

**Interfaces:**
- Produces: generate_embeddings(chunks, batch_size) -> List[List[float]]

- [x] **Step 1: 创建 embeddings.py 文件**

```python
"""Vector embedding generation using model2vec."""

from typing import List


def generate_embeddings(texts: List[str], batch_size: int = 1000) -> List[List[float]]:
    """Generate embeddings for a list of texts using model2vec.

    Args:
        texts: List of text strings to embed.
        batch_size: Number of texts to process per batch.

    Returns:
        List of embedding vectors, one per input text.
    """
    from model2vec import StaticModel

    model = StaticModel.from_pretrained("minishlab/potion-base-8M")
    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch)
        embeddings.extend(batch_embeddings.tolist())

        if (i // batch_size) % 5 == 0:
            print(f"Generating embeddings... ({i + len(batch)}/{len(texts)})")

    return embeddings
```

- [x] **Step 2: 验证函数可调用**

Run: `uv run python -c "from rag.embeddings import generate_embeddings; print('OK')"`
Expected: `OK`

- [x] **Step 3: Commit**

```bash
git add rst2md/rag/embeddings.py
git commit -m "feat: add generate_embeddings function"
```

---

### Task 5: 在 build_database 中集成向量生成

**Files:**
- Modify: `rst2md/rag/store.py:201-319` (build_database 函数)

**Interfaces:**
- Consumes: generate_embeddings 函数
- Produces: vec_chunks 表填充

- [x] **Step 1: 在 build_database 函数末尾添加向量生成逻辑**

在 `conn.executescript(FTS_SYNC)` 之前添加：

```python
        # Generate and store embeddings
        from rag.embeddings import generate_embeddings

        chunk_rows = conn.execute("SELECT id, text FROM chunks ORDER BY id").fetchall()
        chunk_ids = [row[0] for row in chunk_rows]
        chunk_texts = [row[1] for row in chunk_rows]

        print(f"Generating embeddings for {len(chunk_texts)} chunks...")
        embeddings = generate_embeddings(chunk_texts)

        for chunk_id, embedding in zip(chunk_ids, embeddings):
            conn.execute(
                "INSERT INTO vec_chunks (chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, str(embedding))
            )
```

- [x] **Step 2: 构建数据库并验证 vec_chunks 记录数**

Run: `uv run python -c "
from pathlib import Path
from rag.store import build_database, get_connection
build_database(Path('godot_rag/docs-md'), Path('test_vec.db'))
with get_connection(Path('test_vec.db')) as conn:
    count = conn.execute('SELECT COUNT(*) FROM vec_chunks').fetchone()[0]
    print(f'vec_chunks records: {count}')
    assert count >= 28000, f'Expected >= 28000, got {count}'
"`
Expected: `vec_chunks records: >= 28000`

- [x] **Step 3: 清理测试文件并 Commit**

```bash
rm -f test_vec.db
git add rst2md/rag/store.py
git commit -m "feat: integrate embedding generation into build_database"
```

---

### Task 6: 实现向量搜索函数

**Files:**
- Modify: `rst2md/rag/store.py` (新增 vector_search 函数)

**Interfaces:**
- Consumes: conn, query_embedding, limit
- Produces: List[dict] with 'id' and 'distance' keys

- [x] **Step 1: 在 store.py 中添加 vector_search 函数**

在 `_build_chunk_relations` 函数之后添加：

```python
def vector_search(conn, query_embedding: List[float], limit: int = 10) -> List[dict]:
    """Search for similar chunks using vector embeddings.

    Args:
        conn: SQLite connection.
        query_embedding: Query vector (256 dimensions).
        limit: Maximum number of results.

    Returns:
        List of dicts with 'id' and 'distance' keys.
    """
    results = conn.execute(
        "SELECT chunk_id, distance FROM vec_chunks WHERE embedding MATCH ? AND k = ?",
        (str(query_embedding), limit)
    ).fetchall()

    return [{'id': row[0], 'distance': row[1]} for row in results]
```

- [x] **Step 2: 验证函数可调用**

Run: `uv run python -c "from rag.store import vector_search; print('OK')"`
Expected: `OK`

- [x] **Step 3: Commit**

```bash
git add rst2md/rag/store.py
git commit -m "feat: add vector_search function"
```

---

### Task 7: 实现 RRF 融合函数

**Files:**
- Modify: `rst2md/rag/store.py` (新增 rrf_fusion 函数)

**Interfaces:**
- Consumes: fts_results, vec_results, k
- Produces: List[dict] with 'rrf_score' key

- [ ] **Step 1: 在 store.py 中添加 rrf_fusion 函数**

在 `vector_search` 函数之后添加：

```python
def rrf_fusion(fts_results: List[dict], vec_results: List[dict], k: int = 60) -> List[dict]:
    """Fuse FTS5 and vector search results using Reciprocal Rank Fusion.

    Args:
        fts_results: FTS5 results with 'id' key.
        vec_results: Vector results with 'id' and 'distance' keys.
        k: RRF parameter (default 60).

    Returns:
        Fused results sorted by RRF score, with 'rrf_score' key added.
    """
    scores = {}

    for rank, result in enumerate(fts_results):
        chunk_id = result['id']
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)

    for rank, result in enumerate(vec_results):
        chunk_id = result['id']
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    results = []
    for chunk_id in sorted_ids:
        result = next((r for r in fts_results if r['id'] == chunk_id), None)
        if result is None:
            result = next((r for r in vec_results if r['id'] == chunk_id), None)
        if result:
            result = dict(result)
            result['rrf_score'] = scores[chunk_id]
            results.append(result)

    return results
```

- [ ] **Step 2: 验证函数可调用**

Run: `uv run python -c "from rag.store import rrf_fusion; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add rst2md/rag/store.py
git commit -m "feat: add rrf_fusion function"
```

---

### Task 8: 修改 search_database 集成向量搜索

**Files:**
- Modify: `rst2md/rag/store.py:406-592` (search_database 函数)

**Interfaces:**
- Consumes: vector_search, rrf_fusion, generate_embeddings
- Produces: 融合后的搜索结果

- [ ] **Step 1: 修改 search_database 函数**

在 `search_database` 函数中，在 `# 1. Exact symbol match` 之前添加向量搜索逻辑：

```python
    with get_connection(db_path) as conn:
        normalized = normalize_symbol(query)
        results = {}

        # 0. Vector search + RRF fusion
        from rag.embeddings import generate_embeddings
        query_embedding = generate_embeddings([query])[0]
        vec_results_raw = vector_search(conn, query_embedding, limit=limit * 3)

        # FTS5 search for RRF fusion
        fts_results_raw = []
        try:
            escaped_query = _smart_tokenize(query)
            fts_rows = conn.execute(
                "SELECT c.id, bm25(chunks_fts) as rank FROM chunks_fts fts JOIN chunks c ON fts.rowid = c.id WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?",
                [escaped_query, limit * 3]
            ).fetchall()
            for row in fts_rows:
                fts_results_raw.append({'id': row['id'], 'rank': row['rank']})
        except sqlite3.OperationalError:
            pass

        # RRF fusion
        fused_results = rrf_fusion(fts_results_raw, vec_results_raw)
        fused_ids = {r['id'] for r in fused_results[:limit * 3]}
```

然后在 `# 4. FTS5 search` 部分，只对未在融合结果中的 chunk 进行 FTS5 搜索：

```python
        # 4. FTS5 search (only for chunks not in fused results)
        try:
            escaped_query = _smart_tokenize(query)
            # ... 现有 FTS5 逻辑，但跳过已在 fused_ids 中的 chunk ...
        except sqlite3.OperationalError:
            pass
```

- [ ] **Step 2: 验证搜索功能**

Run: `uv run python -c "
from pathlib import Path
from rag.store import search_database
results = search_database(Path('godot_rag.db'), 'how to make a button', limit=3)
for r in results:
    print(f'{r.symbol or r.heading}: {r.score:.2f}')
"`
Expected: 返回语义相关结果

- [ ] **Step 3: Commit**

```bash
git add rst2md/rag/store.py
git commit -m "feat: integrate vector search and RRF fusion into search_database"
```

---

### Task 9: 编写单元测试

**Files:**
- Create: `rst2md/tests/test_semantic_search.py`

**Interfaces:**
- Tests: see_also 关系构建、向量搜索、RRF 融合

- [ ] **Step 1: 创建测试文件**

```python
"""Tests for semantic search features."""

import pytest
from pathlib import Path
from rag.store import (
    get_connection,
    build_database,
    vector_search,
    rrf_fusion,
)


@pytest.fixture
def test_db(tmp_path):
    """Build a small test database."""
    db_path = tmp_path / "test.db"
    build_database(Path("godot_rag/docs-md"), db_path)
    return db_path


def test_see_also_relations(test_db):
    """Verify see_also relations are extracted."""
    with get_connection(test_db) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM chunk_relations WHERE relation = 'see_also'"
        ).fetchone()[0]
        assert count >= 100, f"Expected >= 100 see_also relations, got {count}"


def test_vec_chunks_populated(test_db):
    """Verify vec_chunks table is populated."""
    with get_connection(test_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
        assert count >= 28000, f"Expected >= 28000 vec_chunks, got {count}"


def test_rrf_fusion():
    """Test RRF fusion algorithm."""
    fts_results = [
        {'id': 1, 'rank': 0.5},
        {'id': 2, 'rank': 0.3},
        {'id': 3, 'rank': 0.1},
    ]
    vec_results = [
        {'id': 2, 'distance': 0.1},
        {'id': 4, 'distance': 0.2},
        {'id': 1, 'distance': 0.3},
    ]

    fused = rrf_fusion(fts_results, vec_results, k=60)

    # id=2 appears in both, should rank highest
    assert fused[0]['id'] == 2
    assert 'rrf_score' in fused[0]
```

- [ ] **Step 2: 运行测试**

Run: `uv run pytest rst2md/tests/test_semantic_search.py -v`
Expected: ALL PASSED

- [ ] **Step 3: Commit**

```bash
git add rst2md/tests/test_semantic_search.py
git commit -m "test: add semantic search unit tests"
```

---

### Task 10: 端到端验证

**Files:**
- None (验证任务)

**Interfaces:**
- Consumes: search_database 函数

- [ ] **Step 1: 验证语义搜索效果**

Run: `uv run python -c "
from pathlib import Path
from rag.store import search_database

queries = [
    'how to make a button',
    'physics body collision',
    'scene tree child nodes',
]

for query in queries:
    print(f'Query: {query}')
    results = search_database(Path('godot_rag.db'), query, limit=3)
    for r in results:
        print(f'  {r.symbol or r.heading}: {r.score:.2f}')
    print()
"`
Expected: 返回语义相关结果

- [ ] **Step 2: 验证 see_also 关系数量**

Run: `uv run python -c "
from pathlib import Path
from rag.store import get_connection

with get_connection(Path('godot_rag.db')) as conn:
    count = conn.execute(\"SELECT COUNT(*) FROM chunk_relations WHERE relation = 'see_also'\").fetchone()[0]
    print(f'see_also relations: {count}')
    assert count >= 100
"`
Expected: `see_also relations: >= 100`

- [ ] **Step 3: Commit 验证结果**

```bash
git add -A
git commit -m "feat: semantic search implementation complete"
```
