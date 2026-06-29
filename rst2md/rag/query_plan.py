from __future__ import annotations

import re
from dataclasses import dataclass

from rag.query_rewrite import _ALIAS_RULES, _tokens, expand_query_variants
from rag.symbols import normalize_symbol


def _doc_type_intent(query: str) -> str | None:
    lowered = query.lower()
    if "." in query or "_" in query:
        return None
    if (
        lowered.startswith("how to ")
        or " tutorial" in lowered
        or " guide" in lowered
        or "learn " in lowered
    ):
        return "tutorial"
    return None


def _addon_intent(query: str) -> str | None:
    tokens = _tokens(query)
    if "addon" in tokens or "plugin" in tokens:
        return "addon"
    return None


def _symbol_candidates(query: str) -> tuple[str, ...]:
    variants = expand_query_variants(query)
    seen: set[str] = set()
    result: list[str] = []
    for v in variants:
        norm = normalize_symbol(v)
        if norm not in seen:
            seen.add(norm)
            result.append(v)
    return tuple(result)


def _alias_symbol_candidates(query: str) -> tuple[str, ...]:
    query_tokens = _tokens(query)
    result: list[str] = []
    for required_tokens, alias in _ALIAS_RULES:
        if required_tokens.issubset(query_tokens):
            result.append(alias)
    return tuple(result)


@dataclass(frozen=True)
class QueryPlan:
    original: str
    fts_variants: tuple[str, ...]
    symbol_candidates: tuple[str, ...]
    alias_symbol_candidates: tuple[str, ...]
    doc_type_intent: str | None
    addon_intent: str | None


def build_query_plan(query: str) -> QueryPlan:
    variants = expand_query_variants(query)
    return QueryPlan(
        original=query,
        fts_variants=tuple(variants),
        symbol_candidates=_symbol_candidates(query),
        alias_symbol_candidates=_alias_symbol_candidates(query),
        doc_type_intent=_doc_type_intent(query),
        addon_intent=_addon_intent(query),
    )
