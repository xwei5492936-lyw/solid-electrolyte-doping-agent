# Agent Notes

## Project Goal

PERD aims to discover performance-relevant dopant rules for solid-state electrolytes.

## Rules

- Do not fabricate literature data.
- Mark missing values as `unknown`.
- Separate experimental facts, literature-derived inference, model prediction, and hypothesis.
- Prefer small, testable changes.
- Do not commit raw PDFs, private data, or API keys.
- Treat conductivity-only ranking as a baseline, not the final objective.
- Battery-performance relevance should include transport, grain boundary, interface, processing, and evidence quality.

## Commands

```bash
pip install -r requirements.txt
pytest
python scripts/validate_dataset.py
python scripts/build_master_dataset.py
python scripts/train_baselines.py
python scripts/run_perd_scoring.py
python scripts/run_temporal_validation.py
python scripts/generate_figures.py
```
