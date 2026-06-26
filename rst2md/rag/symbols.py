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


def normalize_symbol(name: str) -> str:
    """Normalize a symbol name for matching."""
    # Remove trailing ()
    name = name.rstrip("()")
    # Lowercase
    name = name.lower()
    return name


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
