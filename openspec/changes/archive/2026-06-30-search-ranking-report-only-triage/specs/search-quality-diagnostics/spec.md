## ADDED Requirements

### Requirement: Report-only query triage is summarized
Search quality diagnostics SHALL produce a triage summary for report-only evaluation queries when diagnostics are requested.

#### Scenario: report-only queries are classified
- **WHEN** search quality evaluation runs with report-only queries and a diagnostic window
- **THEN** each report-only query MUST be assigned a triage classification
- **AND** the classification MUST distinguish missing expected data, missing recall, low ranking, filter mismatch, degraded search execution, and promotion-ready results

#### Scenario: triage output includes evidence
- **WHEN** a report-only query is classified
- **THEN** the triage output MUST include the evidence used for the decision, including expected target presence, best observed rank when available, search mode, fallback reason, and observed top results

#### Scenario: promotion-ready queries are explicit
- **WHEN** a report-only query's expected target is present and matches within its required rank without degraded search execution
- **THEN** diagnostics MUST mark the query as eligible for gating promotion
- **AND** the output MUST identify that promotion as a candidate recommendation rather than silently changing the query suite

#### Scenario: follow-up ownership is identified
- **WHEN** a report-only query is not promotion-ready
- **THEN** diagnostics MUST identify the likely follow-up type as data or fixture work, recall work, ranking work, filter work, or degraded search investigation
