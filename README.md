# Solid Electrolyte Doping Agent

A research prototype for literature-mined and physics-constrained dopant recommendation in solid-state electrolytes, starting from LLZO/LLZTO.

## Goals
1. Extract dopant cases from literature.
2. Build a structured LLZO doping database.
3. Distinguish experimental facts from model predictions.
4. Generate physics-constrained candidate dopant schemes.
5. Train interpretable ML models for ranking candidates.

## Project Structure

```text
src/llzo_doping_agent/   Core data models, constraints, and storage helpers.
scripts/                 Command-line utilities for database initialization.
tests/                   Pytest test suite.
data/processed/          Example/generated structured data.
```

## Quick Start

```bash
python -m pip install -r requirements.txt
python scripts/init_database.py
python -m pytest
```

## Data Model

The initial database schema separates experimental facts from model predictions:

- `DopantCase`: a literature-mined experimental record for an LLZO/LLZTO dopant.
- `CandidateScheme`: a model-generated dopant proposal with explicit constraint status.

The first implemented constraints check common LLZO design rules: known substitution site, positive dopant fraction, and charge-balancing valence difference.
