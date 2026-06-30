"""Snippet extraction for search results.

Focused sub-module split from searcher.py (change: split-searcher-modules).
Behavior is byte-for-byte identical to the previous searcher.py implementation.
"""


def _extract_snippet(text: str, query: str, context_lines: int = 3) -> str:
    """Extract a snippet from text around the first line containing query keywords."""
    lines = text.split('\n')
    query_lower = query.lower()
    keywords = query_lower.split()

    # Find first line containing any keyword
    match_idx = None
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            match_idx = i
            break

    if match_idx is None:
        # No match found, return first few lines
        return '\n'.join(lines[:context_lines * 2 + 1])

    # Extract context around match
    start = max(0, match_idx - context_lines)
    end = min(len(lines), match_idx + context_lines + 1)

    snippet_lines = []
    if start > 0:
        snippet_lines.append('...')
    snippet_lines.extend(lines[start:end])
    if end < len(lines):
        snippet_lines.append('...')

    return '\n'.join(snippet_lines)
