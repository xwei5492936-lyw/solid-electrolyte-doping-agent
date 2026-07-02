"""Train PERD baseline models from master_dataset.csv."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from perd.features import create_high_conductivity_label, create_long_lifetime_label
from perd.models import compare_baseline_models
from perd.utils import friendly_missing_file, write_json


def main() -> None:
    input_path = Path("data/processed/master_dataset.csv")
    output_path = Path("outputs/reports/baseline_metrics.json")
    if not input_path.exists():
        report = friendly_missing_file(input_path)
        write_json(output_path, report)
        print(report["message"])
        return
    df = pd.read_csv(input_path)
    df = create_high_conductivity_label(create_long_lifetime_label(df))
    label = "long_lifetime" if df["long_lifetime"].nunique() > 1 else "high_conductivity"
    report = compare_baseline_models(df, label)
    write_json(output_path, report)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
