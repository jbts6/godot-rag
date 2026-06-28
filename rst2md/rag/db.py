import re
import sqlite3
from contextlib import contextmanager


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
