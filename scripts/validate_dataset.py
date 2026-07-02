"""Validate data/processed/master_dataset.csv."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from perd.schema import MASTER_REQUIRED_FIELDS
from perd.utils import friendly_missing_file, write_json
from perd.validation import validate_dataset


def main() -> None:
    input_path = Path("data/processed/master_dataset.csv")
    output_path = Path("outputs/reports/validation_report.json")
    if not input_path.exists():
        report = friendly_missing_file(input_path)
        write_json(output_path, report)
        print(report["message"])
        return
    df = pd.read_csv(input_path)
    report = validate_dataset(df, MASTER_REQUIRED_FIELDS)
    write_json(output_path, report)
    print(f"Wrote {output_path}; valid={report['valid']}")


if __name__ == "__main__":
    main()
