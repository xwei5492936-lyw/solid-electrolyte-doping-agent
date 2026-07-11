# Evidence Tracking

## Why PERD Needs Evidence Tracking

PERD combines composition, processing, transport, interface, and battery-performance data extracted from papers. A normalized number alone is insufficient because apparently identical values can refer to different temperatures, sample geometries, fitting assumptions, cell conditions, or figure estimates. Every critical extracted field therefore needs a traceable link to the page, section, and sentence from which it was obtained.

Evidence tracking supports:

- manual verification without rereading an entire paper;
- correction of extraction or unit-normalization errors;
- distinction between reported measurements and derived interpretations;
- confidence-aware modeling and sensitivity analysis;
- auditable comparison of conflicting values across the main text, figures, tables, and supplementary information.

The value remains in the existing table column. Its companion `*_evidence` field stores one or more serialized `EvidenceRecord` objects. Each record preserves the raw extracted value, normalized value, unit, PDF location, extraction method, and confidence. Multiple records should be retained when a field is supported by several passages or when sources disagree.

## Evidence Record

An `EvidenceRecord` contains:

- `field_name`: destination PERD field;
- `extracted_value`: source wording or raw value;
- `normalized_value`: machine-readable normalized value;
- `unit`: normalized unit;
- `source_page`: PDF page label or number;
- `source_section`: section, table, or figure context;
- `source_sentence`: exact supporting sentence or concise transcribed figure evidence;
- `extraction_method`: for example `manual`, `ai_extraction`, `ocr`, `figure_estimate`, `ai_inference`, or `prediction`;
- `confidence`: `high`, `medium`, `low`, or `unknown`.

Missing page provenance reduces confidence by one level. Figure-derived values must use an extraction method such as `figure_estimate`, retain the figure/page locator, and must not be labeled as directly reported text.

## Evidence Classes

### Experimental Fact

An experimental fact is explicitly reported by the paper as a measured value, stated composition, or processing condition. Store the reported wording in `extracted_value`, the converted value in `normalized_value`, and a precise source locator. Use `manual`, `ai_extraction`, `ocr`, or `figure_estimate` as appropriate. AI-assisted transcription does not change the evidence class when the source directly reports the fact.

### AI Inference

An AI inference is derived from source facts but is not explicitly stated. Examples include assigning a dopant site from charge balance, inferring a phase from an unlabeled diffraction pattern, or converting an ambiguous cycling trace into a lifetime. Use `ai_inference`, explain the inference in the evidence sentence or associated notes, and do not give it the same status as a reported experimental fact. Confidence should reflect both source quality and inference uncertainty.

### Prediction

A prediction is produced by PERD/BPRS or another model and is not literature evidence. Use `prediction`, retain the model/version and input provenance outside or alongside the record, and keep the result in prediction outputs rather than overwriting experimental fields. Predictions must never be presented as extracted measurements.

## Extraction Rules

1. Preserve the source value before normalization.
2. Record the PDF page label, not only the viewer's zero-based page index.
3. Include enough sentence, table, or figure context to interpret conditions.
4. Keep experimental facts, AI inferences, and predictions as separate records.
5. Use `unknown` for unavailable values; do not invent a value to complete the schema.
6. Resolve conflicting evidence during manual curation and retain the rejected evidence with an explanatory note when scientifically relevant.
