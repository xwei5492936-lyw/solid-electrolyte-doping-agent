"""Calculate BPRS scores and ranked candidates."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from perd.scoring import rank_candidates


def main() -> None:
    input_path = Path("data/processed/master_dataset.csv")
    output_path = Path("outputs/tables/ranked_candidates.csv")
    if not input_path.exists():
        print("Missing data/processed/master_dataset.csv. Run scripts/build_master_dataset.py after filling templates.")
        return
    ranked = rank_candidates(pd.read_csv(input_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ranked.to_csv(output_path, index=False)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
