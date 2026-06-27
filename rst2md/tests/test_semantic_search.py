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
