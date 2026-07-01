# Comet Subagent Dispatch Checkpoint

Change: search-ranking-signal-explanations
Plan: docs/superpowers/plans/2026-06-30-search-ranking-signal-explanations.md
Review mode: standard (no per-task reviewer; one final lightweight reviewer after all tasks)
TDD mode: tdd
Build mode: subagent-driven-development
Isolation: branch feature/20260701/search-ranking-signal-explanations
Base-ref: fb5491a279abb9c03f90f5e6b7fc25b7bf63a555

## OpenSpec Task Mapping
- Plan Task 1 → OpenSpec 1.1, 1.2, 1.3  ✅ complete (commit d2e1592)
- Plan Task 2 → OpenSpec 2.1  ✅ complete (commit 2c8b9f0; 2.4 partial, spans Tasks 2-5)
- Plan Task 3 → OpenSpec 2.2 (+ 2.4 RRF→symbol)
- Plan Task 4 → OpenSpec 2.3 (+ 2.4 FTS→graph)
- Plan Task 5 → OpenSpec 3.1, 3.2 (+ 2.4 rerank list-copy)
- Plan Task 6 → OpenSpec 4.1, 4.2
- Plan Task 7 → OpenSpec 5.1, 5.2, 5.3

## Deferred Issues
- Suffix-recall dead-code bug (normalize_symbol strips dots → suffix LIKE never matches). test_suffix_symbol_match_records_signal marked @unittest.expectedFailure in Task 2. symbol_recall.suffix recording kept dormant. Fix deferred to a SEPARATE change (ranking-behavior change).

## Current State
- Current task: Task 3 (Record hybrid/RRF and FTS scoring signals)
- Phase: implementing
- Implementer dispatch: in flight
- Review-fix round: 0 (standard mode: final review only, max 1 fix round)
