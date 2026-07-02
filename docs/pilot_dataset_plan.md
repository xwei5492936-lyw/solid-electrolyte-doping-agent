# Pilot Dataset Plan

This document guides the first real-literature pilot dataset for PERD/BPRS. The pilot dataset is intended to test whether the PERD workflow is usable on curated LLZO/LLZTO literature data.

## Goal

Curate 30 LLZO/LLZTO doping-related papers and extract 50-100 real sample records. The pilot dataset should be large enough to test data curation, validation, BPRS scoring, baseline scripts, temporal validation, and figure generation on real literature-derived records.

The pilot dataset is not expected to prove algorithmic superiority. It is a workflow validation and first-pass pattern observation dataset.

## Literature Search Keywords

Use the following search queries across Web of Science, Scopus, Google Scholar, publisher search pages, and citation trails:

- `LLZO doped ionic conductivity`
- `LLZTO garnet electrolyte doping`
- `Ta doped LLZO conductivity`
- `Nb doped LLZO solid electrolyte`
- `Ga doped LLZO`
- `Al doped LLZO`
- `Ca doped LLZO`
- `Sr doped LLZO`
- `co-doped LLZO garnet solid electrolyte`
- `garnet solid electrolyte Li symmetric cell`

Record every candidate paper in `data/templates/literature_screening_log.csv` or a working copy under `data/interim/`.

## Inclusion Criteria

Include papers that satisfy the core criteria below:

- The material is garnet-type LLZO/LLZTO or a closely related garnet oxide solid electrolyte.
- The paper reports a clear dopant element or co-doping system.
- The paper has enough experimental information to identify at least one sample-level composition or processing-performance relationship.

Prioritize papers containing:

- `final_formula`
- `phase`
- `sintering_temperature_c`
- `total_conductivity_25c_s_cm`
- `activation_energy_ev`

Mark papers as high-priority if they include any of:

- Li symmetric-cell lifetime.
- Critical current density.
- Full-cell performance.
- Interface resistance or interface treatment data.

## Exclusion Criteria

Temporarily exclude papers that match any of the following:

- Theory-only or computation-only studies without experimental performance data.
- Composite polymer systems where the LLZO/LLZTO dopant contribution cannot be separated.
- Studies without clear composition, dopant identity, or performance metrics.
- Review articles as direct sample-data sources.

Review articles may still be used to trace original primary literature. If used this way, record them in the screening log with `include_or_exclude=exclude` or `maybe` and explain that they are citation-tracing sources only.

## Per-Paper Extraction Workflow

1. Fill `literature_screening_log.csv`.
   - Record `paper_id`, `title`, `doi`, `year`, `journal`, `material_family`, screening decision, reason, curator, date, and notes.
   - Use `include`, `exclude`, or `maybe` for `include_or_exclude`.
2. Fill the literature metadata table.
   - Every included paper must have `paper_id`, DOI, title, and year.
   - Use `unknown` only when a value is truly absent.
3. Fill the sample-level tables.
   - Composition table first.
   - Then processing, transport, interface, and battery tables.
   - Every sample record must retain `sample_id`, `paper_id`, and DOI linkage.
4. Mark missing fields as `unknown`.
   - Do not infer missing values silently.
   - If a figure-estimated value is used, mark it as `estimated` in notes.
5. Preserve measurement context.
   - Conductivity type and temperature.
   - Sintering condition and phase.
   - Li symmetric-cell current density, areal capacity, lifetime, temperature, and pressure.
   - Full-cell cathode, loading, rate, cycle number, and retention.
6. Assign confidence.
   - `high`: directly reported with clear sample identity and units.
   - `medium`: directly reported but minor ambiguity remains.
   - `low`: figure-estimated or missing context.
   - `unknown`: confidence cannot be assigned.

## Minimum Completion Standards

The pilot dataset is considered minimally complete when it satisfies all of the following:

- At least 30 papers screened and included as primary sample-data sources.
- At least 50 `sample_id` records.
- Preferably no more than 100 sample records for the first pilot round, to keep manual verification manageable.
- At least 80% of samples contain:
  - `final_formula`
  - `dopant_element_1`
  - `phase`
  - `sintering_temperature_c`
  - `total_conductivity_25c_s_cm`
- At least 30% of samples contain Li symmetric-cell lifetime or critical current density.
- At least 10 samples contain full-cell or interface-related data.

## Quality-Control Checks

Before running models, inspect:

- Duplicate `sample_id` or `paper_id` values.
- Missing DOI, title, or year.
- Samples without dopant element or dopant site.
- Conductivity values without temperature context.
- Li symmetric lifetime values without current density or areal capacity.
- `confidence` values outside `high`, `medium`, `low`, or `unknown`.
- Rows where estimated values are not clearly marked.

## Required Pipeline After Pilot Completion

After the pilot tables are filled under `data/interim/` or `data/processed/`, run:

```bash
python scripts/build_master_dataset.py
python scripts/validate_dataset.py
python scripts/check_extraction_completeness.py
python scripts/run_perd_scoring.py
python scripts/train_baselines.py
python scripts/run_temporal_validation.py
python scripts/generate_figures.py
```

Review generated outputs under:

- `outputs/reports/`
- `outputs/tables/`
- `outputs/figures/`

## Expected Pilot Outputs

The pilot should produce:

- A screened literature log.
- A merged `master_dataset.csv`.
- Validation and completeness reports.
- Ranked BPRS candidates.
- Baseline model metrics.
- Temporal validation results, if the publication years span a usable train/test split.
- Figures for dopant distribution, conductivity, BPRS, and candidate maps.

## No-Overclaim Statement

The pilot dataset can only support workflow validation and preliminary rule observation. It cannot directly support claims that PERD/BPRS outperforms existing algorithms. Any such claim requires a larger verified database, careful baseline comparisons, temporal validation on real records, and external experimental validation.
