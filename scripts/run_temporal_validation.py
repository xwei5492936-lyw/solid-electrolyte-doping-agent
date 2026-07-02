"""Run temporal validation for PERD feature sets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from perd.features import create_high_conductivity_label, create_long_lifetime_label
from perd.temporal_validation import compare_models_temporal
from perd.utils import friendly_missing_file, write_json


def main() -> None:
    input_path = Path("data/processed/master_dataset.csv")
    output_path = Path("outputs/reports/temporal_validation_results.json")
    if not input_path.exists():
        report = friendly_missing_file(input_path)
        write_json(output_path, report)
        print(report["message"])
        return
    df = create_high_conductivity_label(create_long_lifetime_label(pd.read_csv(input_path)))
    label = "long_lifetime" if df["long_lifetime"].nunique() > 1 else "high_conductivity"
    results = compare_models_temporal(
        df,
        ["composition_only", "processing_aware", "structure_transport_aware", "perd_predictive"],
        label,
    )
    write_json(output_path, results)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
