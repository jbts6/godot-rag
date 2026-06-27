from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Chunk:
    path: str
    doc_type: str
    chunk_type: str
    addon: str
    addon_name: str
    symbol: str
    heading: str
    breadcrumb: str
    start_line: int
    end_line: int
    text: str
    symbols: List[str] = field(default_factory=list)
    parent_symbol: str = ""


@dataclass(frozen=True)
class SearchResult:
    score: float
    path: str
    start_line: int
    end_line: int
    doc_type: str
    chunk_type: str
    addon: str
    addon_name: str
    symbol: str
    heading: str
    breadcrumb: str
    text: str
    relation_type: str = ''
    distance: int = 0
