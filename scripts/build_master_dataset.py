"""Build data/processed/master_dataset.csv from available PERD tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


TABLE_PATHS = {
    "literature": ["data/processed/literature.csv", "data/interim/literature.csv"],
    "composition": ["data/processed/composition.csv", "data/interim/composition.csv"],
    "processing": ["data/processed/processing.csv", "data/interim/processing.csv"],
    "transport": ["data/processed/transport.csv", "data/interim/transport.csv"],
    "interface": ["data/processed/interface.csv", "data/interim/interface.csv"],
    "battery": ["data/processed/battery.csv", "data/interim/battery.csv"],
}


def _read_first_existing(paths: list[str]) -> pd.DataFrame | None:
    for path in paths:
        if Path(path).exists():
            return pd.read_csv(path)
    return None


def main() -> None:
    tables = {name: _read_first_existing(paths) for name, paths in TABLE_PATHS.items()}
    if not any(table is not None for table in tables.values()):
        print("No processed/interim tables found. Fill CSV templates under data/templates/ first.")
        return
    master = tables.get("composition")
    if master is None:
        print("Missing composition table; cannot build sample-level master dataset.")
        return
    if tables.get("literature") is not None and "paper_id" in master.columns:
        master = master.merge(tables["literature"], on="paper_id", how="left", suffixes=("", "_paper"))
    for name in ["processing", "transport", "interface", "battery"]:
        table = tables.get(name)
        if table is not None and "sample_id" in table.columns:
            master = master.merge(table, on="sample_id", how="left", suffixes=("", f"_{name}"))
    output_path = Path("data/processed/master_dataset.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(output_path, index=False)
    print(f"Wrote {output_path} with {len(master)} rows.")


if __name__ == "__main__":
    main()
