# search-quality-review-hotfix Proposal

## Problem

Code review found that the search quality gate can pass without proving real search quality:

- `docs/search-quality/baseline.json` was generated from an empty bundled database and records `hit@5=0.0`.
- Several real-database failures were promoted to gating queries even though they still miss top-5 on `godot_rag.db`.

## Root Cause

The previous implementation refreshed the reviewed baseline against `godot_rag/rag/godot_docs.sqlite`, which currently contains zero indexed documents, chunks, and symbols. It also removed `report_only` from some queries before their real-database behavior was stable.

## Fix Goals

- Keep only currently stable real-database queries as gating queries.
- Move unstable natural-language alias, addon, and weak tutorial checks back to `report_only`.
- Refresh `docs/search-quality/baseline.json` from the populated local release database `godot_rag.db`.

## Non-Goals

- Do not change search ranking or query rewrite logic in this hotfix.
- Do not change packaging or bundled database generation in this hotfix.
