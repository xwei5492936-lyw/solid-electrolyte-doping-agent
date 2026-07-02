"""Dataset validation for PERD tables."""

from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd

from perd.schema import CONFIDENCE_VALUES


def _result(errors: list[dict], warnings: list[dict]) -> dict:
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def _issue(field: str, message: str, rows: list[int] | None = None) -> dict:
    item = {"field": field, "message": message}
    if rows is not None:
        item["rows"] = rows
    return item


def validate_required_columns(df: pd.DataFrame, required_columns: Iterable[str]) -> dict:
    errors = [_issue(column, "missing required column") for column in required_columns if column not in df.columns]
    return _result(errors, [])


def validate_confidence_values(df: pd.DataFrame) -> dict:
    errors: list[dict] = []
    confidence_columns = [column for column in df.columns if column == "confidence" or column.endswith("_confidence")]
    for column in confidence_columns:
        values = df[column].fillna("unknown").astype(str).str.strip().str.lower()
        invalid = values[~values.isin(CONFIDENCE_VALUES)]
        if not invalid.empty:
            errors.append(_issue(column, f"confidence must be one of {CONFIDENCE_VALUES}", invalid.index.tolist()))
    return _result(errors, [])


def validate_year_range(df: pd.DataFrame, min_year: int = 1990, max_year: int | None = None) -> dict:
    warnings: list[dict] = []
    if "year" not in df.columns:
        return _result([], warnings)
    max_year = max_year or date.today().year + 1
    years = pd.to_numeric(df["year"], errors="coerce")
    invalid = years[(years.notna()) & ((years < min_year) | (years > max_year))]
    if not invalid.empty:
        warnings.append(_issue("year", f"year is outside expected range [{min_year}, {max_year}]", invalid.index.tolist()))
    return _result([], warnings)


def validate_numeric_ranges(df: pd.DataFrame) -> dict:
    warnings: list[dict] = []
    range_rules = {
        "dopant_concentration_1": (0, 1),
        "dopant_concentration_2": (0, 1),
        "li_content": (0, 20),
        "relative_density_percent": (0, 100),
        "grain_size_um": (0, None),
        "capacity_retention_percent": (0, 150),
        "coulombic_efficiency_percent": (0, 110),
        "critical_current_density_ma_cm2": (0, None),
        "li_symmetric_lifetime_h": (0, None),
    }
    for column, (lower, upper) in range_rules.items():
        if column not in df.columns:
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        mask = values.notna()
        if lower is not None:
            mask &= values < lower
        if upper is not None:
            mask |= values > upper
        bad = values[mask & values.notna()]
        if not bad.empty:
            warnings.append(_issue(column, "numeric value is outside expected range", bad.index.tolist()))
    return _result([], warnings)


def validate_conductivity_values(df: pd.DataFrame) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    for column in [c for c in df.columns if "conductivity" in c]:
        values = pd.to_numeric(df[column], errors="coerce")
        non_positive = values[(values.notna()) & (values <= 0)]
        if non_positive.empty:
            continue
        target = errors if column == "total_conductivity_25c_s_cm" else warnings
        target.append(_issue(column, "conductivity should be positive", non_positive.index.tolist()))
    return _result(errors, warnings)


def validate_dataset(df: pd.DataFrame, required_columns: Iterable[str] | None = None) -> dict:
    """Validate a DataFrame and return structured errors and warnings."""

    errors: list[dict] = []
    warnings: list[dict] = []
    checks = [
        validate_required_columns(df, required_columns or []),
        validate_confidence_values(df),
        validate_year_range(df),
        validate_numeric_ranges(df),
        validate_conductivity_values(df),
    ]
    for check in checks:
        errors.extend(check["errors"])
        warnings.extend(check["warnings"])
    return _result(errors, warnings)
