"""Tests for semantic search features."""

import pytest
from pathlib import Path
from rag.store import (
    get_connection,
    build_database,
    rrf_fusion,
    search_database,
)


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Build a small test database with deterministic fixtures."""
    from rag import embeddings

    docs = tmp_path / "docs"
    classes = docs / "classes"
    tutorials = docs / "tutorials"
    classes.mkdir(parents=True)
    tutorials.mkdir(parents=True)

    # Create class docs with see_also relations
    (classes / "class_timer.md").write_text(
        "# Timer\n\n"
        "## Methods\n\n"
        "`void` **start**()\n\nStarts the countdown timer.\n\n"
        "`void` **stop**()\n\nStops the countdown timer.\n\n"
        "See also `SceneTree` and `Node`\n",
        encoding="utf-8",
    )
    (classes / "class_node.md").write_text(
        "# Node\n\n"
        "## Methods\n\n"
        "`void` **add_child**(`Node` node)\n\nAdds a child node to the scene tree.\n\n"
        "See also `Timer` and `SceneTree`\n",
        encoding="utf-8",
    )
    (classes / "class_scene_tree.md").write_text(
        "# SceneTree\n\n"
        "## Methods\n\n"
        "`void` **quit**()\n\nQuits the application.\n\n"
        "See also `Node` and `Timer`\n",
        encoding="utf-8",
    )
    (tutorials / "scene_tree.md").write_text(
        "# Scene Tree\n\n"
        "Nodes are arranged as a scene tree. Use add_child to attach nodes.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts]
    )
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)
    return db_path


def test_see_also_relations(test_db):
    """Verify see_also relations are extracted."""
    with get_connection(test_db) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM chunk_relations WHERE relation = 'see_also'"
        ).fetchone()[0]
        assert count >= 3, f"Expected >= 3 see_also relations, got {count}"


def test_vec_chunks_populated(test_db):
    """Verify vec_chunks table is populated."""
    with get_connection(test_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
        assert count >= 1, f"Expected >= 1 vec_chunks, got {count}"


def test_search_skips_embeddings_when_vec_table_missing(tmp_path, monkeypatch):
    """Search should not pay semantic-query cost when the DB has no vector table."""
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

    monkeypatch.setattr(
        embeddings,
        "generate_embeddings",
        lambda texts: [[0.0] * 256 for _ in texts],
    )
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)

    with get_connection(db_path) as conn:
        conn.execute("DROP TABLE IF EXISTS vec_chunks")
        conn.commit()

    called = False

    def fail_if_called(texts):
        nonlocal called
        called = True
        return [[0.0] * 256 for _ in texts]

    monkeypatch.setattr(embeddings, "generate_embeddings", fail_if_called)

    results = search_database(db_path, "timer stopped", limit=3, expand_graph=False)

    assert results
    assert not called


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
    monkeypatch.setattr(
        embeddings,
        "generate_embeddings",
        lambda texts: [[0.0] * 256 for _ in texts],
    )
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)

    response = search_database_with_metadata(
        db_path, "timer stopped", limit=3, expand_graph=False
    )

    assert response.results
    assert response.metadata.mode == "hybrid"
    assert response.metadata.vector_available is True
    assert response.metadata.fallback_reason == ""


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
    monkeypatch.setattr(
        embeddings,
        "generate_embeddings",
        lambda texts: [[0.0] * 256 for _ in texts],
    )
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)
    with get_connection(db_path) as conn:
        conn.execute("DROP TABLE IF EXISTS vec_chunks")
        conn.commit()

    response = search_database_with_metadata(
        db_path, "timer stopped", limit=3, expand_graph=False
    )

    assert response.results
    assert response.metadata.mode == "fts_only"
    assert response.metadata.vector_available is False
    assert response.metadata.fallback_reason == "missing_vec_chunks"


def test_rrf_fusion():
    """Test RRF fusion algorithm."""
    fts_results = [
        {'id': 1},
        {'id': 2},
        {'id': 3},
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

    # All unique IDs should be present
    ids = [r['id'] for r in fused]
    assert set(ids) == {1, 2, 3, 4}


def test_rrf_fusion_empty():
    """Test RRF fusion with empty inputs."""
    assert rrf_fusion([], []) == []


def test_rrf_fusion_single_source():
    """Test RRF fusion with results from only one source."""
    fts_results = [{'id': 1}, {'id': 2}]
    fused = rrf_fusion(fts_results, [], k=60)
    assert len(fused) == 2
    assert fused[0]['id'] == 1  # rank 0 scores higher than rank 1


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

    from rag import searcher
    monkeypatch.setattr(searcher, "_run_vector_query", fail_vector_search)
    response = store.search_database_with_metadata(db_path, "child node", limit=3, expand_graph=False)

    assert response.results
    assert response.metadata.mode == "fts_only"
    assert response.metadata.fallback_reason == "vector_query_failed"


def test_search_metadata_reports_empty_vec_chunks(tmp_path, monkeypatch):
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
    monkeypatch.setattr(
        embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts]
    )
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)

    # Empty vec_chunks table
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM vec_chunks")
        conn.commit()

    response = search_database_with_metadata(
        db_path, "timer stopped", limit=3, expand_graph=False
    )

    assert response.results
    assert response.metadata.mode == "fts_only"
    assert response.metadata.vector_available is False
    assert response.metadata.fallback_reason == "empty_vec_chunks"


def test_search_metadata_reports_vector_row_count_mismatch(tmp_path, monkeypatch):
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
    (classes / "class_node.md").write_text(
        "# Node\n\n"
        "## Methods\n\n"
        "`void` **add_child**(`Node` node)\n\nAdds a child node.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts]
    )
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)

    # Delete one vec_chunks row to create mismatch
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM vec_chunks WHERE chunk_id = (SELECT MIN(id) FROM chunks)")
        conn.commit()

    response = search_database_with_metadata(
        db_path, "timer stopped", limit=3, expand_graph=False
    )

    assert response.results
    assert response.metadata.mode == "fts_only"
    assert response.metadata.vector_available is False
    assert response.metadata.fallback_reason == "vector_row_count_mismatch"


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


def test_pytest_does_not_require_generated_state(tmp_path, monkeypatch):
    """Verify that ordinary pytest does not require godot_rag/docs-md or other generated state."""
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

    monkeypatch.setattr(
        embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts]
    )
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)

    # Verify we can search without godot_rag/docs-md
    results = search_database(db_path, "timer stopped", limit=3, expand_graph=False)
    assert results
    assert any("timer" in r.path.lower() for r in results)


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


def test_alias_query_uses_symbol_recall(tmp_path, monkeypatch):
    """Query with alias tokens should find the aliased symbol even when FTS text doesn't match."""
    from rag import embeddings

    docs = tmp_path / "docs"
    classes = docs / "classes"
    classes.mkdir(parents=True)

    (classes / "class_node.md").write_text(
        "# Node\n\n## Methods\n\n`void` **add_child**(`Node` node)\n\nRegisters a sub-element.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts]
    )
    db_path = tmp_path / "test.db"
    build_database(docs, db_path)

    results = search_database(db_path, "attach child node", limit=5, expand_graph=False)

    assert any(result.symbol == "Node.add_child" for result in results)
