"""Deduplicate raw PERD literature candidate batches."""

from __future__ import annotations

import argparse
from pathlib import Path

from perd.literature_search import deduplicate_candidates, read_candidate_csv, write_candidate_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Deduplicate literature candidate CSV files.")
    parser.add_argument("--input-dir", default="data/interim", help="Directory containing raw batch CSV files.")
    parser.add_argument("--output", default="data/processed/literature_candidates_dedup.csv", help="Deduplicated output CSV.")
    args = parser.parse_args()

    input_paths = sorted(Path(args.input_dir).glob("literature_candidates_batch_*_raw.csv"))
    records = []
    for path in input_paths:
        records.extend(read_candidate_csv(path))
    deduped = deduplicate_candidates(records)
    output_path = write_candidate_csv(args.output, deduped)
    print(f"raw_candidate_count={len(records)}")
    print(f"deduplicated_count={len(deduped)}")
    print(f"output_path={output_path}")


if __name__ == "__main__":
    main()
