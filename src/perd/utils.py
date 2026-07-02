"""Shared utilities for PERD scripts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def read_csv_if_exists(path: str | Path) -> pd.DataFrame | None:
    path = Path(path)
    if not path.exists():
        return None
    return pd.read_csv(path)


def write_json(path: str | Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def friendly_missing_file(path: str | Path) -> dict:
    return {
        "status": "missing_input",
        "message": f"Missing {path}. Fill templates under data/templates/ and run scripts/build_master_dataset.py first.",
    }
