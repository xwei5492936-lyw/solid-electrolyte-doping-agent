"""Generate all available PERD figures."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from perd.scoring import add_bprs_scores
from perd.utils import write_json
from perd.visualization import (
    plot_bprs_vs_conductivity,
    plot_candidate_map,
    plot_conductivity_distribution,
    plot_conductivity_vs_lifetime,
    plot_dopant_distribution,
)


def main() -> None:
    input_path = Path("data/processed/master_dataset.csv")
    report_path = Path("outputs/reports/figure_generation_report.json")
    if not input_path.exists():
        report = {"status": "missing_input", "message": "Missing master_dataset.csv; no figures generated."}
        write_json(report_path, report)
        print(report["message"])
        return
    df = add_bprs_scores(pd.read_csv(input_path))
    reports = {
        "dopant_distribution": plot_dopant_distribution(df),
        "conductivity_distribution": plot_conductivity_distribution(df),
        "conductivity_vs_lifetime": plot_conductivity_vs_lifetime(df),
        "bprs_vs_conductivity": plot_bprs_vs_conductivity(df),
        "candidate_map": plot_candidate_map(df),
    }
    write_json(report_path, reports)
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
