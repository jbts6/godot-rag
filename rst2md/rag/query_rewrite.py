import re


_ALIAS_RULES: tuple[tuple[frozenset[str], str], ...] = (
    (frozenset({"attach", "node", "scene", "tree"}), "Node.add_child"),
    (frozenset({"child", "node", "attach"}), "Node.add_child"),
    (frozenset({"check", "timer", "stopped"}), "Timer.is_stopped"),
    (frozenset({"timer", "is", "stopped"}), "Timer.is_stopped"),
    (frozenset({"emit", "signal"}), "Object.emit_signal"),
)


def _tokens(query: str) -> frozenset[str]:
    return frozenset(re.findall(r"[a-z0-9]+", query.lower()))


def expand_query_variants(query: str) -> list[str]:
    variants = [query]
    query_tokens = _tokens(query)
    for required_tokens, alias in _ALIAS_RULES:
        if required_tokens.issubset(query_tokens) and alias not in variants:
            variants.append(alias)
    return variants
