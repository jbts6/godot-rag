import re
from dataclasses import dataclass
from typing import List

from rag.models import Chunk


@dataclass(frozen=True)
class Symbol:
    name: str
    normalized_name: str
    kind: str
    chunk_id: int
    path: str


def _canonical_form(name: str) -> str:
    """Unified symbol form: split camelCase, strip _ and ., lowercase."""
    name = name.rstrip("()")
    # Insert separator at camelCase boundaries
    name = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
    name = name.lower()
    name = name.replace("_", "").replace(".", "")
    return name


def normalize_symbol(name: str) -> str:
    """Normalize a symbol name for matching."""
    return _canonical_form(name)


def extract_symbols(chunks: List[Chunk]) -> List[Symbol]:
    """Extract symbols from chunks."""
    symbols = []
    for i, chunk in enumerate(chunks):
        kind = chunk.chunk_type
        names = []
        if chunk.symbol:
            names.append(chunk.symbol)
        names.extend(chunk.symbols)

        seen = set()
        for name in names:
            if not name or name in seen:
                continue
            seen.add(name)
            normalized = normalize_symbol(name)

            symbols.append(Symbol(
                name=name,
                normalized_name=normalized,
                kind=kind,
                chunk_id=i,
                path=chunk.path,
            ))

    return symbols
