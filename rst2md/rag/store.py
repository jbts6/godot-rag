import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional

from rag.chunker import chunk_markdown
from rag.models import SearchResult
from rag.symbols import extract_symbols, normalize_symbol


@contextmanager
def get_connection(db_path):
    """Context manager for SQLite connections."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    # Enable extension loading for sqlite-vec
    conn.enable_load_extension(True)
    try:
        import sqlite_vec
        sqlite_vec.load(conn)
    except Exception:
        pass  # sqlite-vec not available, skip
    try:
        yield conn
    finally:
        conn.close()

# Patterns for cleaning text
CLASSREF_LINE_RE = re.compile(r"^\s*classref-\S+\s*$", re.MULTILINE)
ANCHOR_RE = re.compile(r"`([^`<]+)<class_[^>]+>`")


_FTS5_SPECIAL = set('"*+-:()^')

def _smart_tokenize(query: str) -> str:
    """Split dotted/snake_case symbols into separate tokens for FTS5.

    "Node.add_child" → '"Node" AND "add" AND "child"'
    Plain queries pass through unchanged.
    """
    # Only split if query contains . or _ (likely a symbol)
    if '.' not in query and '_' not in query:
        return _escape_fts5(query)

    tokens = re.split(r'[._]', query)
    fts_tokens = []
    for t in tokens:
        if not t:
            continue
        if any(c in _FTS5_SPECIAL for c in t):
            escaped = t.replace('"', '""')
            fts_tokens.append(f'"{escaped}"')
        else:
            fts_tokens.append(t)
    return " AND ".join(fts_tokens) if fts_tokens else _escape_fts5(query)


def _escape_fts5(query: str) -> str:
    """Escape FTS5 special characters so the query is treated as literal text.

    FTS5 does not support backslash escaping. Tokens containing special
    characters are wrapped in double quotes (phrase matching). Plain tokens
    are left as-is so multi-word queries retain implicit AND semantics.
    """
    tokens = []
    for token in query.split():
        if any(c in _FTS5_SPECIAL for c in token):
            escaped = token.replace('"', '""')
            tokens.append(f'"{escaped}"')
        else:
            tokens.append(token)
    return ' '.join(tokens)


def clean_chunk_text(text: str) -> str:
    """Clean chunk text by removing classref noise and internal anchors."""
    # Remove standalone classref-* lines
    text = CLASSREF_LINE_RE.sub("", text)
    # Remove <class_*> anchors, keep display text
    text = ANCHOR_RE.sub(r"`\1`", text)
    # Remove image references (Markdown and HTML) — invisible to LLM
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'<img\b[^>]*/?\s*>', '', text)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  doc_type TEXT NOT NULL,
  title TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id),
  path TEXT NOT NULL,
  doc_type TEXT NOT NULL,
  chunk_type TEXT NOT NULL,
  addon TEXT NOT NULL DEFAULT '',
  addon_name TEXT NOT NULL DEFAULT '',
  symbol TEXT NOT NULL DEFAULT '',
  heading TEXT NOT NULL DEFAULT '',
  breadcrumb TEXT NOT NULL DEFAULT '',
  start_line INTEGER NOT NULL,
  end_line INTEGER NOT NULL,
  text TEXT NOT NULL,
  parent_symbol TEXT NOT NULL DEFAULT ''
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  text,
  symbol,
  heading,
  breadcrumb,
  content='chunks',
  content_rowid='id',
  tokenize='unicode61'
);

CREATE TABLE IF NOT EXISTS symbols (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  kind TEXT NOT NULL,
  chunk_id INTEGER NOT NULL REFERENCES chunks(id),
  path TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_symbols_normalized_name ON symbols(normalized_name);
CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);

CREATE TABLE IF NOT EXISTS chunk_relations (
  source_id INTEGER NOT NULL REFERENCES chunks(id),
  target_id INTEGER NOT NULL REFERENCES chunks(id),
  relation  TEXT NOT NULL,
  weight    REAL DEFAULT 1.0,
  PRIMARY KEY (source_id, target_id, relation)
);
CREATE INDEX IF NOT EXISTS idx_relations_source ON chunk_relations(source_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON chunk_relations(target_id);
"""

# SQL to create vec_chunks virtual table (requires sqlite-vec extension)
VEC_CHUNKS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding float[256]
);
"""

FTS_SYNC = """
INSERT INTO chunks_fts(rowid, text, symbol, heading, breadcrumb)
SELECT id, text, symbol, heading, breadcrumb FROM chunks;
"""

INHERITS_RE = re.compile(r'\*\*Inherits:\*\*(.+)')


def _extract_inherits(text: str) -> List[str]:
    """Extract class names from an '**Inherits:**' line."""
    match = INHERITS_RE.search(text)
    if not match:
        return []
    return re.findall(r'`([A-Za-z_][A-Za-z0-9_]*)`', match.group(1))


def _build_chunk_relations(conn) -> None:
    """Build parent, inherits, and references relations between chunks."""
    rows = conn.execute("SELECT id, path, doc_type, chunk_type, symbol, parent_symbol, text FROM chunks").fetchall()

    # Index: normalized_symbol -> chunk_id
    sym_to_id = {}
    for row in rows:
        if row[4]:  # symbol
            sym_to_id[normalize_symbol(row[4])] = row[0]

    for row in rows:
        chunk_id, path, doc_type, chunk_type, symbol, parent_symbol, text = row

        # 1. Parent relation: member -> class_summary
        if parent_symbol:
            parent_norm = normalize_symbol(parent_symbol)
            if parent_norm in sym_to_id:
                conn.execute(
                    "INSERT OR IGNORE INTO chunk_relations (source_id, target_id, relation, weight) VALUES (?, ?, 'parent', 1.0)",
                    (chunk_id, sym_to_id[parent_norm])
                )

        # 2. Inherits relation: class_summary -> parent class_summary
        if chunk_type == "class_summary":
            parents = _extract_inherits(text)
            for parent_name in parents:
                parent_norm = normalize_symbol(parent_name)
                if parent_norm in sym_to_id:
                    conn.execute(
                        "INSERT OR IGNORE INTO chunk_relations (source_id, target_id, relation, weight) VALUES (?, ?, 'inherits', 0.8)",
                        (chunk_id, sym_to_id[parent_norm])
                    )

        # 3. References relation: text mentions of other symbols
        tokens = set(re.findall(r'[A-Za-z_][A-Za-z0-9_.]+', text))
        for token in tokens:
            token_norm = normalize_symbol(token)
            if token_norm and token_norm in sym_to_id and token_norm != normalize_symbol(symbol):
                target_id = sym_to_id[token_norm]
                conn.execute(
                    "INSERT OR IGNORE INTO chunk_relations (source_id, target_id, relation, weight) VALUES (?, ?, 'references', 0.5)",
                    (chunk_id, target_id)
                )

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


def build_database(docs_dir: Path, db_path: Path, addons_dir: Optional[Path] = None) -> None:
    """Build the RAG database from markdown docs.

    Args:
        docs_dir: Path to the markdown docs directory (Godot official docs).
        db_path: Path to output SQLite database.
        addons_dir: Optional path to addons directory. If provided, addon docs
                    and examples are included in the database.
    """
    # Remove existing db
    if db_path.exists():
        db_path.unlink()

    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)

        # Create vec_chunks table if sqlite-vec extension is available
        try:
            conn.executescript(VEC_CHUNKS_SCHEMA)
        except sqlite3.OperationalError:
            # sqlite-vec not available, skip vector table creation
            pass

        md_files = sorted(docs_dir.rglob("*.md"))
        total_files = len(md_files)
        for i, md_file in enumerate(md_files):
            if i % 100 == 0 or i == total_files - 1:
                print(f"Building database... ({i+1}/{total_files} files)")
            rel_path = str(md_file.relative_to(docs_dir))
            markdown = md_file.read_text(encoding="utf-8")
            chunks = chunk_markdown(rel_path, markdown)

            if not chunks:
                continue

            # Detect doc_type from first chunk
            doc_type = chunks[0].doc_type if chunks else "other"

            # Extract title from first chunk or path
            title = chunks[0].heading if chunks else Path(rel_path).stem

            # Insert document
            cur = conn.execute(
                "INSERT OR IGNORE INTO documents (path, doc_type, title) VALUES (?, ?, ?)",
                (rel_path, doc_type, title),
            )
            doc_id = cur.lastrowid
            if doc_id == 0:
                row = conn.execute("SELECT id FROM documents WHERE path = ?", (rel_path,)).fetchone()
                doc_id = row[0]

            # Insert chunks
            for chunk in chunks:
                cleaned_text = clean_chunk_text(chunk.text)
                conn.execute(
                    "INSERT INTO chunks (document_id, path, doc_type, chunk_type, addon, addon_name, symbol, heading, breadcrumb, start_line, end_line, text, parent_symbol) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (doc_id, chunk.path, chunk.doc_type, chunk.chunk_type, chunk.addon, chunk.addon_name, chunk.symbol, chunk.heading, chunk.breadcrumb, chunk.start_line, chunk.end_line, cleaned_text, chunk.parent_symbol),
                )

            # Extract and insert symbols
            chunk_ids = [row[0] for row in conn.execute(
                "SELECT id FROM chunks WHERE document_id = ? ORDER BY id",
                (doc_id,),
            ).fetchall()]

            symbols = extract_symbols(chunks)
            for sym in symbols:
                if sym.chunk_id >= len(chunk_ids):
                    continue
                conn.execute(
                    "INSERT INTO symbols (name, normalized_name, kind, chunk_id, path) VALUES (?, ?, ?, ?, ?)",
                    (sym.name, sym.normalized_name, sym.kind, chunk_ids[sym.chunk_id], sym.path),
                )

        # Process addons
        if addons_dir and addons_dir.is_dir():
            from rag.addon_docs import chunk_addon

            for addon_subdir in sorted(addons_dir.iterdir()):
                if not addon_subdir.is_dir() or addon_subdir.name.startswith('.'):
                    continue
                addon_name = addon_subdir.name
                addon_chunks = chunk_addon(addon_subdir)
                if not addon_chunks:
                    continue

                # Insert document (one per addon)
                first = addon_chunks[0]
                cur = conn.execute(
                    "INSERT OR IGNORE INTO documents (path, doc_type, title) VALUES (?, ?, ?)",
                    (f"addons/{addon_name}", "addon", first.addon_name or addon_name),
                )
                doc_id = cur.lastrowid
                if doc_id == 0:
                    row = conn.execute("SELECT id FROM documents WHERE path = ?", (f"addons/{addon_name}",)).fetchone()
                    doc_id = row[0]

                # Insert chunks
                for chunk in addon_chunks:
                    cleaned_text = clean_chunk_text(chunk.text)
                    conn.execute(
                        "INSERT INTO chunks (document_id, path, doc_type, chunk_type, addon, addon_name, symbol, heading, breadcrumb, start_line, end_line, text, parent_symbol) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (doc_id, chunk.path, chunk.doc_type, chunk.chunk_type, chunk.addon, chunk.addon_name, chunk.symbol, chunk.heading, chunk.breadcrumb, chunk.start_line, chunk.end_line, cleaned_text, chunk.parent_symbol),
                    )

                # Extract and insert symbols
                chunk_ids = [row[0] for row in conn.execute(
                    "SELECT id FROM chunks WHERE document_id = ? ORDER BY id",
                    (doc_id,),
                ).fetchall()]

                symbols = extract_symbols(addon_chunks)
                for sym in symbols:
                    if sym.chunk_id >= len(chunk_ids):
                        continue
                    conn.execute(
                        "INSERT INTO symbols (name, normalized_name, kind, chunk_id, path) VALUES (?, ?, ?, ?, ?)",
                        (sym.name, sym.normalized_name, sym.kind, chunk_ids[sym.chunk_id], sym.path),
                    )

        # Build chunk relations (graph)
        _build_chunk_relations(conn)

        # Generate and store embeddings (requires sqlite-vec extension)
        try:
            conn.execute("SELECT COUNT(*) FROM vec_chunks LIMIT 1")
        except sqlite3.OperationalError:
            # vec_chunks table not available, skip embedding generation
            pass
        else:
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

        # Sync FTS index
        conn.executescript(FTS_SYNC)
        conn.commit()


def list_addons(db_path: Path) -> List[dict]:
    """List all addons indexed in the database.

    Returns a list of dicts with keys: addon, addon_name, chunk_count.
    """
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT addon, addon_name, COUNT(*) as chunk_count "
            "FROM chunks WHERE addon != '' GROUP BY addon ORDER BY addon"
        ).fetchall()
        return [{"addon": r["addon"], "addon_name": r["addon_name"], "chunk_count": r["chunk_count"]} for r in rows]


def get_stats(db_path: Path) -> dict:
    """Get database statistics.

    Returns a dict with keys: chunks, symbols, relations, addons.
    """
    with get_connection(db_path) as conn:
        # Chunk stats
        chunk_total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        chunk_by_type = {}
        for row in conn.execute("SELECT doc_type, COUNT(*) as cnt FROM chunks GROUP BY doc_type"):
            chunk_by_type[row["doc_type"]] = row["cnt"]

        # Symbol stats
        symbol_total = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        symbol_by_kind = {}
        for row in conn.execute("SELECT kind, COUNT(*) as cnt FROM symbols GROUP BY kind"):
            symbol_by_kind[row["kind"]] = row["cnt"]

        # Relation stats
        relation_total = conn.execute("SELECT COUNT(*) FROM chunk_relations").fetchone()[0]
        relation_by_type = {}
        for row in conn.execute("SELECT relation, COUNT(*) as cnt FROM chunk_relations GROUP BY relation"):
            relation_by_type[row["relation"]] = row["cnt"]

        # Addon stats
        addon_rows = conn.execute(
            "SELECT addon, addon_name, COUNT(*) as chunk_count "
            "FROM chunks WHERE addon != '' GROUP BY addon ORDER BY addon"
        ).fetchall()
        addons = [{"addon": r["addon"], "addon_name": r["addon_name"], "chunk_count": r["chunk_count"]} for r in addon_rows]

        return {
            "chunks": {"total": chunk_total, "by_type": chunk_by_type},
            "symbols": {"total": symbol_total, "by_kind": symbol_by_kind},
            "relations": {"total": relation_total, "by_type": relation_by_type},
            "addons": addons,
        }


def _extract_snippet(text: str, query: str, context_lines: int = 3) -> str:
    """Extract a snippet from text around the first line containing query keywords."""
    lines = text.split('\n')
    query_lower = query.lower()
    keywords = query_lower.split()

    # Find first line containing any keyword
    match_idx = None
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            match_idx = i
            break

    if match_idx is None:
        # No match found, return first few lines
        return '\n'.join(lines[:context_lines * 2 + 1])

    # Extract context around match
    start = max(0, match_idx - context_lines)
    end = min(len(lines), match_idx + context_lines + 1)

    snippet_lines = []
    if start > 0:
        snippet_lines.append('...')
    snippet_lines.extend(lines[start:end])
    if end < len(lines):
        snippet_lines.append('...')

    return '\n'.join(snippet_lines)


def search_database(
    db_path: Path, query: str, limit: int = 8,
    doc_types: Optional[List[str]] = None, addon: Optional[str] = None,
    expand_graph: bool = True,
) -> List[SearchResult]:
    """Search the RAG database.

    Args:
        db_path: Path to the SQLite database.
        query: Search query string.
        limit: Maximum number of results to return.
        doc_types: If provided, only search chunks whose doc_type is in this list.
        addon: If provided, only search chunks belonging to this addon.
        expand_graph: If True, expand top results via chunk_relations graph.
        doc_types: If provided, only search chunks whose doc_type is in this list.
                   Common values: "class", "tutorial", "getting_started", "engine_detail", "addon".
        addon: If provided, only search chunks belonging to this addon (e.g. "statecharts").
    """
    with get_connection(db_path) as conn:
        normalized = normalize_symbol(query)
        results = {}

        # Build optional doc_type filter
        type_filter = ""
        type_params: list = []
        if doc_types:
            placeholders = ",".join("?" for _ in doc_types)
            type_filter = f" AND c.doc_type IN ({placeholders})"
            type_params = list(doc_types)

        # Build optional addon filter
        addon_filter = ""
        addon_params: list = []
        if addon:
            addon_filter = " AND c.addon = ?"
            addon_params = [addon]

        def _make_result(row, score):
            return {
                "id": row["id"],
                "score": score,
                "path": row["path"],
                "start_line": row["start_line"],
                "end_line": row["end_line"],
                "doc_type": row["doc_type"],
                "chunk_type": row["chunk_type"],
                "addon": row["addon"],
                "addon_name": row["addon_name"],
                "symbol": row["symbol"],
                "heading": row["heading"],
                "breadcrumb": row["breadcrumb"],
                "text": clean_chunk_text(row["text"]),
                "relation_type": "",
                "distance": 0,
            }

        # 0. Vector search + RRF fusion (respects doc_type and addon filters)
        fused_ids = set()
        try:
            conn.execute("SELECT 1 FROM vec_chunks LIMIT 1").fetchone()

            from rag.embeddings import generate_embeddings
            query_embedding = generate_embeddings([query])[0]

            # Vector search with doc_type/addon filtering via subquery
            vec_query = (
                "SELECT vc.chunk_id, vc.distance FROM vec_chunks vc "
                "JOIN chunks c ON vc.chunk_id = c.id "
                "WHERE vc.embedding MATCH ? AND k = ?"
                + type_filter + addon_filter
            )
            vec_rows = conn.execute(
                vec_query,
                [str(query_embedding), limit * 3] + type_params + addon_params
            ).fetchall()
            vec_results_raw = [{'id': row[0], 'distance': row[1]} for row in vec_rows]

            # FTS5 search for RRF fusion (with doc_type/addon filters)
            fts_results_raw = []
            try:
                escaped_query = _smart_tokenize(query)
                fts_rows = conn.execute(
                    "SELECT c.id, bm25(chunks_fts) as rank FROM chunks_fts fts JOIN chunks c ON fts.rowid = c.id WHERE chunks_fts MATCH ?"
                    + type_filter + addon_filter
                    + " ORDER BY rank LIMIT ?",
                    [escaped_query] + type_params + addon_params + [limit * 3]
                ).fetchall()
                for row in fts_rows:
                    fts_results_raw.append({'id': row['id'], 'rank': row['rank']})
            except sqlite3.OperationalError:
                pass

            # RRF fusion
            fused_results = rrf_fusion(fts_results_raw, vec_results_raw)
            fused_ids = {r['id'] for r in fused_results[:limit * 3]}

            # Add fused results to results dict with RRF scores
            for rank, fused in enumerate(fused_results[:limit * 3]):
                cid = fused['id']
                rrf_score = fused['rrf_score'] * 40.0  # Scale RRF to 0-40 range
                if cid not in results or results[cid]["score"] < rrf_score:
                    row = conn.execute("SELECT * FROM chunks WHERE id = ?", (cid,)).fetchone()
                    if row:
                        results[cid] = _make_result(row, rrf_score)
        except Exception:
            # Vector search not available, skip
            pass

        # 1. Exact symbol match (+100)
        rows = conn.execute(
            "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id WHERE s.normalized_name = ?"
            + type_filter + addon_filter,
            [normalized] + type_params + addon_params,
        ).fetchall()
        for row in rows:
            cid = row["id"]
            if cid not in results or results[cid]["score"] < 100:
                results[cid] = _make_result(row, 100.0)

        # 2. Suffix symbol match (+80)
        rows = conn.execute(
            "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id WHERE s.normalized_name LIKE ?"
            + type_filter + addon_filter,
            [f"%.{normalized}"] + type_params + addon_params,
        ).fetchall()
        for row in rows:
            cid = row["id"]
            if cid not in results or results[cid]["score"] < 80:
                results[cid] = _make_result(row, 80.0)

        # 3. Prefix symbol match (+40)
        rows = conn.execute(
            "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id WHERE s.normalized_name LIKE ?"
            + type_filter + addon_filter,
            [f"{normalized}%"] + type_params + addon_params,
        ).fetchall()
        for row in rows:
            cid = row["id"]
            if cid not in results or results[cid]["score"] < 40:
                results[cid] = _make_result(row, 40.0)

        # 4. FTS5 search (bm25 → 0-40 score, skip chunks already in fused results)
        try:
            escaped_query = _smart_tokenize(query)
            fts_type_filter = ""
            fts_type_params: list = []
            if doc_types:
                placeholders = ",".join("?" for _ in doc_types)
                fts_type_filter = f" AND c.doc_type IN ({placeholders})"
                fts_type_params = list(doc_types)

            fts_addon_filter = ""
            fts_addon_params: list = []
            if addon:
                fts_addon_filter = " AND c.addon = ?"
                fts_addon_params = [addon]

            # Exclude chunks already in fused results
            fused_exclude = ""
            fused_exclude_params: list = []
            if fused_ids:
                placeholders = ",".join("?" for _ in fused_ids)
                fused_exclude = f" AND c.id NOT IN ({placeholders})"
                fused_exclude_params = list(fused_ids)

            fts_rows = conn.execute(
                "SELECT c.*, bm25(chunks_fts) as rank FROM chunks_fts fts JOIN chunks c ON fts.rowid = c.id WHERE chunks_fts MATCH ?"
                + fts_type_filter + fts_addon_filter + fused_exclude
                + " ORDER BY rank LIMIT ?",
                [escaped_query] + fts_type_params + fts_addon_params + fused_exclude_params + [limit * 3],
            ).fetchall()
            for row in fts_rows:
                cid = row["id"]
                bm25 = abs(row["rank"])
                fts_score = min(40.0, max(0.0, 40.0 / (1.0 + bm25 * 0.01)))
                if cid not in results or results[cid]["score"] < fts_score:
                    results[cid] = _make_result(row, fts_score)
        except sqlite3.OperationalError:
            # FTS match syntax error, skip
            pass

        # Sort by score descending
        sorted_results = sorted(results.values(), key=lambda r: r["score"], reverse=True)

        # Graph expansion: expand top-K results via chunk_relations
        if expand_graph:
            top_k = min(3, len(sorted_results))
            expanded_ids = {r["id"] for r in sorted_results[:top_k]}

            for result in sorted_results[:top_k]:
                graph_query = (
                    "SELECT c.*, r.relation, r.weight FROM chunk_relations r "
                    "JOIN chunks c ON c.id = r.target_id "
                    "WHERE r.source_id = ?"
                    + type_filter + addon_filter
                    + " ORDER BY r.weight DESC LIMIT 5"
                )
                related_rows = conn.execute(
                    graph_query,
                    [result["id"]] + type_params + addon_params
                ).fetchall()
                for rel_row in related_rows:
                    rel_id = rel_row["id"]
                    if rel_id not in expanded_ids:
                        expanded_ids.add(rel_id)
                        if rel_id in results:
                            # Chunk already found by vector/FTS search, update relation metadata
                            results[rel_id]["relation_type"] = rel_row["relation"]
                            results[rel_id]["distance"] = 1
                        else:
                            # New chunk from graph expansion
                            rel_score = result["score"] * rel_row["weight"] * 0.5
                            results[rel_id] = {
                                "id": rel_id,
                                "score": rel_score,
                                "path": rel_row["path"],
                                "start_line": rel_row["start_line"],
                                "end_line": rel_row["end_line"],
                                "doc_type": rel_row["doc_type"],
                                "chunk_type": rel_row["chunk_type"],
                                "addon": rel_row["addon"],
                                "addon_name": rel_row["addon_name"],
                                "symbol": rel_row["symbol"],
                                "heading": rel_row["heading"],
                                "breadcrumb": rel_row["breadcrumb"],
                                "text": clean_chunk_text(rel_row["text"]),
                                "relation_type": rel_row["relation"],
                                "distance": 1,
                            }

            # Re-sort after expansion
            sorted_results = sorted(results.values(), key=lambda r: r["score"], reverse=True)

        return [
            SearchResult(
                score=r["score"],
                path=r["path"],
                start_line=r["start_line"],
                end_line=r["end_line"],
                doc_type=r["doc_type"],
                chunk_type=r["chunk_type"],
                addon=r["addon"],
                addon_name=r["addon_name"],
                symbol=r["symbol"],
                heading=r["heading"],
                breadcrumb=r["breadcrumb"],
                text=r["text"],
                relation_type=r.get("relation_type", ""),
                distance=r.get("distance", 0),
                snippet=_extract_snippet(r["text"], query),
            )
            for r in sorted_results[:limit]
        ]
