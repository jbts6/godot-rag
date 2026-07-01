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
class RankingSignal:
    name: str
    weight: float
    value: float | int | str | None = None
    details: dict[str, object] = field(default_factory=dict)


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
    snippet: str = ''
    ranking_signals: List[RankingSignal] = field(default_factory=list)


@dataclass(frozen=True)
class SearchMetadata:
    mode: str
    vector_available: bool
    fallback_reason: str = ""


@dataclass(frozen=True)
class SearchResponse:
    results: List[SearchResult]
    metadata: SearchMetadata
