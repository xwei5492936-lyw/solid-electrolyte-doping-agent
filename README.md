# PERD: Performance-aware Electrolyte Rule Discovery

## Project Overview

PERD is a research software framework for discovering performance-relevant dopant rules in solid-state electrolytes. It builds a data chain from `composition -> processing -> structure/transport -> interface -> battery performance`, rather than optimizing ionic conductivity alone.

This repository implements the non-experimental part of the project: data templates, validation, feature engineering, baseline models, rule-based PERD/BPRS scoring, temporal extrapolation validation, candidate ranking, visualization scripts, tests, and documentation.

## Scientific Motivation

Solid-state electrolyte dopant studies often focus on conductivity, but real battery performance also depends on processing quality, phase stability, grain-boundary behavior, Li interface behavior, cathode pairing, cycling conditions, and evidence quality. PERD is designed to compare performance-aware rule discovery against narrower composition-only and conductivity-only baselines.

## Repository Structure

```text
data/       Raw, interim, processed, and template data tables.
src/perd/   Schema, validation, feature, scoring, model, temporal, and plotting modules.
scripts/    Reproducible command-line pipeline stages.
notebooks/  Optional exploratory notebooks.
outputs/    Generated figures, models, reports, and tables.
tests/      Pytest coverage for core behavior.
docs/       Database, extraction, algorithm, experiment, and paper notes.
```

## Data Templates

Templates live in `data/templates/`:

- `literature_extraction_template.csv`
- `composition_table_template.csv`
- `processing_table_template.csv`
- `transport_table_template.csv`
- `interface_table_template.csv`
- `battery_table_template.csv`

Each template contains one synthetic / fictitious example row. Replace those rows with manually verified literature data. Use `unknown` for missing values and keep `confidence` limited to `high`, `medium`, `low`, or `unknown`.

## Installation

```bash
python -m pip install -r requirements.txt
```

## How To Run Tests

```bash
python -m pytest
```

## How To Build Master Dataset

Fill CSV files under `data/interim/` or `data/processed/` with these names: `literature.csv`, `composition.csv`, `processing.csv`, `transport.csv`, `interface.csv`, and `battery.csv`.

```bash
python scripts/build_master_dataset.py
```

## How To Validate Dataset

```bash
python scripts/validate_dataset.py
```

The report is written to `outputs/reports/validation_report.json`.

## How To Train Baseline Models

```bash
python scripts/train_baselines.py
```

The script creates labels when possible, compares conductivity-only ranking and feature-set baselines, writes metrics to `outputs/reports/baseline_metrics.json`, and saves models under `outputs/models/`.

## How To Run PERD/BPRS Scoring

```bash
python scripts/run_perd_scoring.py
```

Ranked candidates are written to `outputs/tables/ranked_candidates.csv`.

## How To Run Temporal Validation

```bash
python scripts/run_temporal_validation.py
```

Results are written to `outputs/reports/temporal_validation_results.json`.

## How To Generate Figures

```bash
python scripts/generate_figures.py
```

Available figures are written to `outputs/figures/`. Missing fields are skipped with a report rather than causing a hard crash.

## Manual Data Required

The repository does not contain real literature data. The user must manually provide and verify:

- Literature metadata: DOI, title, year, journal, source type.
- Composition data: formula, dopant elements, sites, valence, concentration, Li content.
- Processing data: synthesis method, calcination, sintering, atmosphere, density, phase.
- Transport data: total/bulk/grain-boundary conductivity, activation energy, EIS details.
- Interface data: Li contact, interfacial resistance, CCD, Li symmetric-cell conditions.
- Battery data: cathode, loading, rate, cycle number, capacity, retention, efficiency.

## Limitations And No-Overclaim Statement

This repository contains no real literature database by default. Real data must be manually filled, checked, and versioned.

Current BPRS is a first-version rule-based scoring algorithm. Its weights are transparent starting assumptions, not learned scientific truth. Later versions can learn weights from verified real data.

Without a real database, baseline comparison, temporal validation, and external experimental validation, this project cannot claim that PERD/BPRS outperforms existing methods.
