import sqlite3
from pathlib import Path
from typing import Optional

from rag.chunker import chunk_markdown
from rag.db import FTS_SYNC, SCHEMA, VEC_CHUNKS_SCHEMA, clean_chunk_text, get_connection
from rag.relations import build_chunk_relations
from rag.symbols import extract_symbols


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
        build_chunk_relations(conn)

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
