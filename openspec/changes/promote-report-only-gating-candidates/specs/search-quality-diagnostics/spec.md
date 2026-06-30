## ADDED Requirements

### Requirement: Promotion-ready report-only queries can be reviewed into gating
Search quality diagnostics SHALL support a manual workflow where report-only queries classified as promotion-ready can be converted into gating queries after review.

#### Scenario: reviewed non-addon candidates are promoted
- **WHEN** report-only triage classifies a non-addon query as promotion-ready on the canonical database
- **THEN** maintainers MAY remove its `report_only` flag
- **AND** the refreshed baseline MUST include that query in the gating comparison set

#### Scenario: unstable candidates remain report-only
- **WHEN** a promotion-ready query belongs to a category with unstable data ownership, such as addon coverage
- **THEN** maintainers SHOULD keep it report-only until the data source is explicitly accepted as stable

#### Scenario: non-ready queries remain advisory
- **WHEN** a report-only query is classified as low ranking, missing recall, missing expected data, filter mismatch, or degraded search
- **THEN** it MUST remain report-only until a focused follow-up change resolves the underlying cause
