# B01-0072 Extraction v1/v2 Comparison

> These metrics compare two machine secondary reviews. They are not human-validated accuracy.

## Acceptance Metrics

| Metric | v1 | v2 | Phase 3 criterion | Result |
|---|---:|---:|---:|---|
| Strict machine agreement | 76.5% | 100.0% | not below v1 | pass |
| Tolerant machine agreement | 94.1% | 100.0% | >= 94% | pass |
| Unresolved fields | 1 | 0 | <= 1 | pass |
| Human-review queue | 5 | 0 | <= 3 | pass |
| Sample-binding errors | 1 | 0 | 0 | pass |
| Measurement-condition errors | 1 | 0 | 0 | pass |
| Resistance-classification errors | 1 | 0 | 0 | pass |

## Structural Change

v1 stores one paper-level scalar per critical field. v2 first creates a sample map and then stores sample-scoped composition, processing, phase, transport, resistance, interface, and battery records. Nominal, final, and measured composition are separate. Transport measurements preserve raw and normalized values, sample identity, measurement type, temperature, electrode, and evidence.

## Iteration Record

### Iteration 1

- Changed rules: sample map first; mandatory sample binding; separate nominal/final/measured composition; typed conductivity and resistance; preserve room-temperature wording; no value inference from figures.
- Changed implementation: schema enums, v2 output template and prompt, sample consistency validator, sample-level parser, and tests.
- Metrics: strict 100.0%, tolerant 100.0%, unresolved 0, human-review queue 0, consistency issues 0.
- Remaining errors: none detected by schema validation or independent machine review.

Only one iteration was required. No new PDF was processed, no unsupported value was added, and the v1 extraction, Gold Standard, PDF, and `master_dataset.csv` remain unchanged.
