import re
from typing import List

from rag.symbols import normalize_symbol

INHERITS_RE = re.compile(r'\*\*Inherits:\*\*(.+)')


def extract_inherits(text: str) -> List[str]:
    """Extract class names from an '**Inherits:**' line."""
    match = INHERITS_RE.search(text)
    if not match:
        return []
    return re.findall(r'`([A-Za-z_][A-Za-z0-9_]*)`', match.group(1))


def build_chunk_relations(conn) -> None:
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
            parents = extract_inherits(text)
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
