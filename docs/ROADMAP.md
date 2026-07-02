# Research Roadmap and Codex Workflow

This project is organized around a literature-to-experiment research pipeline for solid-state electrolyte dopant discovery.

## Scientific Route

```text
Large-scale literature database
↓
Structured data extraction
↓
Feature engineering
↓
Traditional baseline models
↓
PERD / BPRS algorithms
↓
Temporal extrapolation validation
↓
Candidate dopant ranking
↓
Small-scale counterfactual experimental validation
↓
Publication figures, tables, and conclusions
```

## Codex Responsibilities

Codex mainly supports reproducible software and documentation work:

- Project repository setup.
- Data table templates.
- Data cleaning scripts.
- Feature engineering scripts.
- Model training scripts.
- Algorithm scoring scripts.
- Visualization scripts.
- Test code.
- README and documentation.

## Researcher Responsibilities

The researcher remains responsible for the scientific ground truth and experimental loop:

- Manual verification of literature-mined data.
- Experimental sample preparation.
- XRD, SEM, EIS, and Li symmetric-cell data supplementation.
- Scientific judgment, interpretation, and conclusion control.

## Engineering Milestones

1. Define versioned data schemas for literature records, extracted dopant cases, processing metadata, electrochemical metrics, and cell-performance outcomes.
2. Build data validation and cleaning utilities that preserve provenance and separate verified facts from model-derived fields.
3. Implement feature builders for composition, processing, transport, interface, and battery-performance descriptors.
4. Train baseline models for composition-only, conductivity-only, and composition-plus-conductivity prediction.
5. Implement PERD and BPRS scoring pipelines with interpretable outputs.
6. Add temporal extrapolation validation, using older papers for training and newer papers for testing.
7. Generate ranked dopant candidates with explicit evidence, uncertainty, and constraint flags.
8. Produce publication-ready tables and figures from versioned analysis outputs.

## Immediate Repository Tasks

- Expand `DopantCase` into a richer literature-backed schema.
- Add CSV/JSONL templates for manual data entry and verification.
- Add cleaning scripts for unit normalization and missing-value reporting.
- Add feature engineering scripts with deterministic outputs.
- Add baseline model training scripts and pytest coverage.
- Add visualization scripts for model comparison and candidate ranking.
