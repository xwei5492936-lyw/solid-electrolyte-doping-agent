"""Run a public-metadata literature discovery batch."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from perd.literature_search import search_batch


def main() -> None:
    parser = argparse.ArgumentParser(description="Search literature candidates for a PERD batch.")
    parser.add_argument("--batch", type=int, required=True, help="Batch id to run, currently 1.")
    parser.add_argument("--target", type=int, default=100, help="Target number of raw candidates.")
    parser.add_argument("--mailto", default=os.environ.get("OPENALEX_MAILTO"), help="Optional polite-pool email for OpenAlex.")
    args = parser.parse_args()

    output_path = Path(f"data/interim/literature_candidates_batch_{args.batch}_raw.csv")
    report_path = Path(f"outputs/reports/literature_search_batch_{args.batch}_report.json")
    result = search_batch(args.batch, args.target, output_path, report_path, mailto=args.mailto)
    print(f"status={result.status}")
    print(f"fetched_candidate_count={len(result.records)}")
    print(f"output_path={result.output_path}")
    print(f"report_path={result.report_path}")
    if result.error:
        print("errors:")
        print(result.error)


if __name__ == "__main__":
    main()
