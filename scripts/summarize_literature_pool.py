"""Summarize the deduplicated PERD literature candidate pool."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from perd.literature_search import read_candidate_csv, summarize_candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize literature candidates.")
    parser.add_argument("--input", default="data/processed/literature_candidates_dedup.csv", help="Deduplicated candidate CSV.")
    parser.add_argument("--json-output", default="outputs/reports/literature_pool_summary.json", help="Summary JSON path.")
    parser.add_argument("--md-output", default="outputs/reports/literature_pool_summary.md", help="Summary Markdown path.")
    args = parser.parse_args()

    records = read_candidate_csv(args.input)
    summary = summarize_candidates(records)
    json_path = Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md_path = Path(args.md_output)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    distribution = "\n".join(
        f"- {family}: {count}" for family, count in summary["material_family_distribution"].items()
    )
    md_path.write_text(
        "\n".join(
            [
                "# Literature Pool Summary",
                "",
                f"- Candidate count: {summary['candidate_count']}",
                f"- LLZO/LLZTO/garnet ratio: {summary['llzo_llzto_garnet_ratio']}",
                f"- DOI coverage: {summary['doi_coverage']}",
                f"- Abstract coverage: {summary['abstract_coverage']}",
                f"- High relevance count: {summary['high_relevance_count']}",
                f"- Medium relevance count: {summary['medium_relevance_count']}",
                f"- Low relevance count: {summary['low_relevance_count']}",
                f"- Likely irrelevant count: {summary['likely_irrelevant_count']}",
                "",
                "## Material Family Distribution",
                distribution or "- none",
                "",
                "Records are public metadata candidates for manual screening; no PDFs were downloaded.",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    print(f"json_output={json_path}")
    print(f"md_output={md_path}")


if __name__ == "__main__":
    main()
