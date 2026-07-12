# Sample-Level Evidence Extraction

PERD schema v2 represents each distinct composition or processing variant as a `sample_record`. Paper-level metadata is shared, but performance values are never stored as context-free paper scalars.

## Composition

`nominal_formula`, `final_formula`, and `measured_composition` are independent fields. A nominal recipe must not populate measured composition. Measured composition requires an analytical or refinement method. Each dopant record stores its sample, concentration basis, site-assignment basis, and direct evidence. Valence-based site assignment is not experimental confirmation.

## Measurements

Transport records bind property type, sample, raw and normalized values, units, temperature, conditions, source type, evidence, and confidence. `room temperature` is retained verbatim unless the paper reports a numeric temperature. Figure-derived values are labeled `estimated_from_figure`.

Resistance records distinguish grain-boundary, electrode-interface, total-cell, and area-specific resistance. Blocking-electrode EIS is not evidence of a lithium-metal interface. Ambiguous attribution is `unresolved` and requires human review.

## Validation

`validate_sample_consistency()` reports `error`, `warning`, and `review_required` issues. It never repairs data silently. Extraction artifacts remain `pending` and `not_included`; database inclusion is a separate human-reviewed action.
