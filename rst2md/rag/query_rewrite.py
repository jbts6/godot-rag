import re


_ALIAS_RULES: tuple[tuple[frozenset[str], str], ...] = (
    (frozenset({"attach", "node", "scene", "tree"}), "Node.add_child"),
    (frozenset({"child", "node", "attach"}), "Node.add_child"),
    (frozenset({"check", "timer", "stopped"}), "Timer.is_stopped"),
    (frozenset({"timer", "is", "stopped"}), "Timer.is_stopped"),
    (frozenset({"emit", "signal"}), "Object.emit_signal"),
)

_ALIAS_FORMS = frozenset(alias for _, alias in _ALIAS_RULES)

_DOT_NOTATION_RE = re.compile(r'^([A-Z][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\(?\)?\s*$')


def _tokens(query: str) -> frozenset[str]:
    return frozenset(re.findall(r"[a-z0-9]+", query.lower()))


def doc_type_boost(query: str, doc_type: str) -> float:
    lowered = query.lower()
    if "." in query or "_" in query:
        return 0.0
    tutorial_intent = (
        lowered.startswith("how to ")
        or " tutorial" in lowered
        or " guide" in lowered
        or "learn " in lowered
    )
    if tutorial_intent and doc_type == "tutorial":
        return 0.05
    return 0.0


def expand_query_variants(query: str) -> list[str]:
    variants = [query]
    query_tokens = _tokens(query)
    for required_tokens, alias in _ALIAS_RULES:
        if required_tokens.issubset(query_tokens) and alias not in variants:
            variants.append(alias)
    m = _DOT_NOTATION_RE.match(query.strip())
    if m and f"{m.group(1)}.{m.group(2)}" not in _ALIAS_FORMS:
        method_suffix = m.group(2)
        if method_suffix not in variants:
            variants.append(method_suffix)
    return variants
