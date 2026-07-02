# Extraction Rules

## Core Rules

- Extract only values explicitly reported by the paper, supplementary information, or figure/table data.
- Mark figure-estimated values as estimated in `notes`.
- Write `unknown` for missing values.
- Do not infer unreported values.
- Record DOI, title, and year for every paper.
- Distinguish experimental fact, literature-derived inference, model prediction, and hypothesis in notes or downstream metadata.

## Conductivity Rules

- Keep total conductivity, bulk conductivity, and grain-boundary conductivity separate.
- Record temperature whenever conductivity is not reported at 25 C.
- Do not convert activation energy units unless the conversion is recorded.

## Li Symmetric-Cell Rules

- Always record current density and areal capacity with Li symmetric lifetime.
- Do not compare lifetimes without checking current density, areal capacity, temperature, and stack pressure.

## Confidence Rules

- `high`: directly reported and internally consistent.
- `medium`: reported but with minor ambiguity.
- `low`: estimated from figure or missing context.
- `unknown`: not enough information for confidence assignment.

## Literature Curation Workflow

The curation workflow separates paper screening, data extraction, human verification, and dataset release.

### 1. Candidate Paper Search

- Search by electrolyte family, dopant element, synthesis method, conductivity, interface stability, and battery-performance keywords.
- Record every candidate paper in `data/templates/literature_screening_log.csv` or a copied working file under `data/interim/`.
- Do not extract numerical values until the paper has passed screening.

### 2. Screening Decision

For each paper, fill:

- `include_or_exclude`: use `include`, `exclude`, or `maybe`.
- `reason`: short decision rationale, such as "reports doped LLZO conductivity and Li symmetric cell" or "review article without primary data".
- `screened_by`: curator name or initials.
- `screening_date`: ISO date, for example `2026-07-02`.

Include papers that report at least one relevant solid-state electrolyte sample with traceable composition, processing, transport, interface, or battery-performance data. Exclude papers that cannot be traced to primary data, do not study solid-state electrolytes, or only provide unsupported claims.

### 3. Metadata Extraction

For included papers, fill the literature table first:

- `paper_id`
- `title`
- `doi`
- `year`
- `journal`
- `material_family`
- `source_type`
- `notes`

The `paper_id` must be stable and must link every extracted sample back to its source paper.

### 4. Sample-Level Extraction

Extract one row per distinct electrolyte sample or composition. Fill the composition table before processing, transport, interface, and battery tables. If a paper reports multiple samples, each sample receives a unique `sample_id`.

Use `unknown` for missing fields. Do not infer missing dopant site, valence, phase, or measurement condition unless the inference is explicitly marked as `literature-derived inference`.

### 5. Unit Normalization

- Conductivity should be converted to S/cm when possible.
- Temperature-dependent conductivity should preserve the original temperature range in `eis_temperature_range`.
- Li symmetric-cell lifetime must be paired with current density and areal capacity whenever available.
- Battery capacity should preserve whether the basis is mAh/g, mAh/cm2, or another unit in notes if the main table cannot represent it.

### 6. Confidence Assignment

Assign confidence after extraction:

- `high`: directly reported numerical value with clear units and sample identity.
- `medium`: directly reported but sample mapping, unit context, or condition has minor ambiguity.
- `low`: estimated from a figure or missing key context.
- `unknown`: value is absent or confidence cannot be assigned.

### 7. Completeness Check

Run:

```bash
python scripts/check_extraction_completeness.py
```

The script checks whether each `sample_id` has the core fields needed for PERD demonstration and downstream BPRS scoring.

### 8. Human Verification

Before using rows as real scientific evidence, a human curator must verify:

- Source metadata.
- Sample identity and composition.
- Measurement conditions.
- Unit conversions.
- Whether extracted values are experimental facts, literature-derived inferences, model predictions, or hypotheses.

Rows that are not verified should not be used to claim algorithmic superiority.
