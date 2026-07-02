# Solid Electrolyte Doping Agent

A research prototype for literature-mined and physics-constrained dopant recommendation in solid-state electrolytes, starting from LLZO/LLZTO.

## Research Tracks

### Track 1: LLZO Doping Database and Candidate Recommendation

Build a structured literature database for LLZO/LLZTO dopants, distinguish experimental facts from model predictions, and generate physics-constrained candidate dopant schemes.

### Track 2: PERD

PERD, short for Performance-aware Electrolyte Rule Discovery, is a second research track for discovering solid-state electrolyte doping rules that are aware of real battery performance.

The central hypothesis is that dopant rules discovered from composition, processing, transport, interface, and cell-performance features should predict practical battery performance better than traditional composition-only or conductivity-only models.

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
docs/                    Research plans and algorithm notes.
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
