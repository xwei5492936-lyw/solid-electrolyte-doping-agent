"""Check core PERD extraction completeness by sample_id."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from perd.utils import friendly_missing_file, write_json

CORE_FIELDS = (
    "final_formula",
    "dopant_element_1",
    "dopant_site_1",
    "sintering_temperature_c",
    "phase",
    "total_conductivity_25c_s_cm",
    "activation_energy_ev",
    "li_symmetric_lifetime_h",
    "confidence",
)

MISSING_MARKERS = {"", "unknown", "nan", "none", "na", "n/a", "null"}


def _is_missing(value) -> bool:
    if pd.isna(value):
        return True
    return str(value).strip().lower() in MISSING_MARKERS


def check_completeness(df: pd.DataFrame, core_fields: tuple[str, ...] = CORE_FIELDS) -> dict:
    """Return structured completeness report for core PERD fields."""

    errors: list[dict] = []
    warnings: list[dict] = []

    if "sample_id" not in df.columns:
        return {
            "valid": False,
            "errors": [{"field": "sample_id", "message": "missing required sample_id column"}],
            "warnings": [],
            "summary": {"row_count": int(len(df)), "complete_sample_count": 0, "incomplete_sample_count": int(len(df))},
            "samples": [],
        }

    missing_columns = [field for field in core_fields if field not in df.columns]
    for field in missing_columns:
        errors.append({"field": field, "message": "missing core completeness column"})

    samples: list[dict] = []
    checked_fields = [field for field in core_fields if field in df.columns]
    for _, row in df.iterrows():
        missing_fields = [field for field in checked_fields if _is_missing(row[field])]
        sample_report = {
            "sample_id": str(row["sample_id"]),
            "complete": not missing_fields and not missing_columns,
            "missing_fields": missing_columns + missing_fields,
        }
        samples.append(sample_report)
        if missing_fields:
            warnings.append(
                {
                    "sample_id": str(row["sample_id"]),
                    "message": "sample is missing core extraction fields",
                    "missing_fields": missing_fields,
                }
            )

    complete_count = sum(1 for sample in samples if sample["complete"])
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "row_count": int(len(df)),
            "complete_sample_count": int(complete_count),
            "incomplete_sample_count": int(len(samples) - complete_count),
            "core_fields": list(core_fields),
        },
        "samples": samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check PERD extraction completeness.")
    parser.add_argument("--input", default="data/processed/master_dataset.csv", help="Input master dataset CSV.")
    parser.add_argument(
        "--output",
        default="outputs/reports/extraction_completeness_report.json",
        help="Output JSON completeness report.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        report = friendly_missing_file(input_path)
        write_json(output_path, report)
        print(report["message"])
        return

    report = check_completeness(pd.read_csv(input_path))
    write_json(output_path, report)
    summary = report["summary"]
    print(
        "Checked {row_count} samples; complete={complete_sample_count}; incomplete={incomplete_sample_count}".format(
            **summary
        )
    )
    if report["errors"]:
        print(f"Errors: {len(report['errors'])}")
    if report["warnings"]:
        print(f"Warnings: {len(report['warnings'])}")


if __name__ == "__main__":
    main()
