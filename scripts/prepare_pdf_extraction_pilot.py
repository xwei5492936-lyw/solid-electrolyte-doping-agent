"""Prepare and summarize the first three-paper PDF extraction pilot."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from perd.evidence_validation import MISSING_VALUES, validate_evidence_payload
from perd.extraction_prompt import CRITICAL_EXTRACTION_FIELDS


ACCESS_FIELDS = ("paper_id", "title", "doi", "source", "access_status")
HUMAN_REVIEW_FIELDS = (
    "paper_id",
    "field_name",
    "ai_value",
    "human_value",
    "match",
    "correction_reason",
    "review_status",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def select_priority_papers(rows: Iterable[dict[str, str]], limit: int = 3) -> list[dict[str, str]]:
    """Select exactly the lowest numeric priorities without expanding the pilot."""

    ranked = sorted(rows, key=lambda row: int(row["priority"]))
    selected = ranked[:limit]
    if len(selected) != limit:
        raise ValueError(f"expected at least {limit} pilot rows, found {len(selected)}")
    expected = list(range(1, limit + 1))
    priorities = [int(row["priority"]) for row in selected]
    if priorities != expected:
        raise ValueError(f"pilot priorities must be {expected}, found {priorities}")
    return selected


def build_access_log(
    selected: Iterable[dict[str, str]],
    registry_rows: Iterable[dict[str, str]],
) -> list[dict[str, str]]:
    """Join selected candidates to manually verified access metadata."""

    registry = {row["paper_id"]: row for row in registry_rows}
    access_log: list[dict[str, str]] = []
    for paper in selected:
        paper_id = paper["candidate_id"]
        access = registry.get(paper_id)
        if access is None:
            access = {
                "paper_id": paper_id,
                "source": f"https://doi.org/{paper['doi']}",
                "access_status": "access_pending",
            }
        access_log.append(
            {
                "paper_id": paper_id,
                "title": paper["title"],
                "doi": paper["doi"],
                "source": access.get("source", f"https://doi.org/{paper['doi']}"),
                "access_status": access.get("access_status", "access_pending"),
            }
        )
    return access_log


def _is_missing(value: Any) -> bool:
    return value is None or str(value).strip().lower() in MISSING_VALUES


def inspect_extraction(path: Path) -> dict[str, Any]:
    """Validate one extraction JSON and summarize field/confidence coverage."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    report = validate_evidence_payload(payload)
    extracted_fields: list[str] = []
    missing_fields: list[str] = []
    confidence = Counter()
    metadata_warnings: list[str] = []
    metadata = payload.get("paper_metadata", {})
    if isinstance(metadata, dict):
        metadata_warnings = [
            str(value)
            for key, value in metadata.items()
            if key.endswith("_warning") and str(value).strip()
        ]
    for section, required_fields in CRITICAL_EXTRACTION_FIELDS.items():
        records = {record.get("field"): record for record in payload.get(section, []) if isinstance(record, dict)}
        for field in required_fields:
            record = records.get(field, {})
            confidence[str(record.get("confidence", "unknown")).lower()] += 1
            qualified = f"{section}.{field}"
            if _is_missing(record.get("value")):
                missing_fields.append(qualified)
            else:
                extracted_fields.append(qualified)
    return {
        "valid": report["valid"],
        "errors": report["errors"],
        "warnings": report["warnings"],
        "extracted_fields": extracted_fields,
        "missing_fields": missing_fields,
        "confidence": confidence,
        "metadata_warnings": metadata_warnings,
    }


def build_report(
    selected: list[dict[str, str]],
    access_log: list[dict[str, str]],
    pdf_dir: Path,
    extraction_dir: Path,
    registry_rows: Iterable[dict[str, str]],
) -> str:
    """Build a Markdown report without treating pending papers as extracted."""

    registry = {row["paper_id"]: row for row in registry_rows}
    processed: list[str] = []
    accessible: list[str] = []
    inaccessible: list[str] = []
    extraction_summaries: dict[str, dict[str, Any]] = {}
    potential_errors: list[str] = []

    for access in access_log:
        paper_id = access["paper_id"]
        pdf_path = pdf_dir / f"{paper_id}.pdf"
        json_path = extraction_dir / f"{paper_id}_extraction.json"
        if pdf_path.exists():
            accessible.append(paper_id)
        else:
            inaccessible.append(paper_id)
        if json_path.exists():
            summary = inspect_extraction(json_path)
            extraction_summaries[paper_id] = summary
            processed.append(paper_id)
            potential_errors.extend(
                f"{paper_id}: {issue['field']} - {issue['message']}"
                for issue in summary["errors"] + summary["warnings"]
            )
            potential_errors.extend(f"{paper_id}: {message}" for message in summary["metadata_warnings"])
        elif pdf_path.exists():
            potential_errors.append(f"{paper_id}: local PDF exists but no extraction JSON has been produced")
        note = registry.get(paper_id, {}).get("notes", "").strip()
        if note and access["access_status"] == "access_pending":
            potential_errors.append(f"{paper_id}: {note}")

    extracted_count = sum(len(item["extracted_fields"]) for item in extraction_summaries.values())
    confidence = Counter()
    for item in extraction_summaries.values():
        confidence.update(item["confidence"])

    lines = [
        "# PDF Extraction Pilot 3 Report",
        "",
        "This report covers only priorities 1-3 from `pdf_extraction_pilot10.csv`. Extraction artifacts remain pending human review and are not included in `master_dataset.csv`.",
        "",
        "## Summary",
        "",
        f"- Selected papers: **{len(selected)}**",
        f"- Processed papers (valid extraction JSON present): **{len(processed)}**",
        f"- Accessible papers (authorized local PDF present): **{len(accessible)}**",
        f"- Inaccessible or access-pending papers: **{len(inaccessible)}**",
        f"- Extracted non-missing fields: **{extracted_count}**",
        "- Automatic database inclusion: **disabled**",
        "",
        "## Paper Status",
        "",
        "| Priority | Paper ID | Access status | Local PDF | Extraction JSON |",
        "|---:|---|---|---|---|",
    ]
    access_by_id = {row["paper_id"]: row for row in access_log}
    for paper in selected:
        paper_id = paper["candidate_id"]
        lines.append(
            f"| {paper['priority']} | {paper_id} | {access_by_id[paper_id]['access_status']} | "
            f"{'yes' if (pdf_dir / f'{paper_id}.pdf').exists() else 'no'} | "
            f"{'yes' if (extraction_dir / f'{paper_id}_extraction.json').exists() else 'no'} |"
        )

    lines.extend(["", "## Extracted And Missing Fields", ""])
    for paper in selected:
        paper_id = paper["candidate_id"]
        summary = extraction_summaries.get(paper_id)
        if summary is None:
            lines.append(f"### {paper_id}")
            lines.append("")
            lines.append("Extraction not run; all critical fields remain pending.")
            lines.append("")
            continue
        lines.append(f"### {paper_id}")
        lines.append("")
        lines.append(f"- Extracted fields ({len(summary['extracted_fields'])}): {', '.join(summary['extracted_fields'])}")
        lines.append(f"- Missing fields ({len(summary['missing_fields'])}): {', '.join(summary['missing_fields'])}")
        lines.append(f"- Evidence validation: {'valid' if summary['valid'] else 'invalid'}")
        lines.append("")

    distribution = ", ".join(f"{key}: {value}" for key, value in sorted(confidence.items())) or "none"
    lines.extend(["## Confidence Distribution", "", f"- All critical records in processed JSON: {distribution}", ""])
    lines.extend(["## Potential Extraction Errors", ""])
    if potential_errors:
        lines.extend(f"- {message}" for message in potential_errors)
    else:
        lines.append("- None detected automatically; human source verification is still required.")
    lines.extend(
        [
            "",
            "## Review Gate",
            "",
            "No extraction has been written to the master dataset. Every non-missing value must be checked against its PDF page and source sentence using `data/review/human_validation_template.csv`.",
            "",
        ]
    )
    return "\n".join(lines)


def prepare_pilot(
    input_csv: Path,
    access_registry: Path,
    output_csv: Path,
    access_output_csv: Path,
    report_path: Path,
    pdf_dir: Path,
    extraction_dir: Path,
    human_validation_dir: Path,
) -> dict[str, int]:
    """Prepare pilot artifacts and return basic counts."""

    pdf_dir.mkdir(parents=True, exist_ok=True)
    extraction_dir.mkdir(parents=True, exist_ok=True)
    human_validation_dir.mkdir(parents=True, exist_ok=True)

    source_rows = _read_csv(input_csv)
    selected = select_priority_papers(source_rows)
    registry_rows = _read_csv(access_registry)
    access_log = build_access_log(selected, registry_rows)
    _write_csv(output_csv, selected, source_rows[0].keys())
    _write_csv(access_output_csv, access_log, ACCESS_FIELDS)

    report = build_report(selected, access_log, pdf_dir, extraction_dir, registry_rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return {
        "selected": len(selected),
        "local_pdfs": sum((pdf_dir / f"{row['paper_id']}.pdf").exists() for row in access_log),
        "extractions": sum((extraction_dir / f"{row['paper_id']}_extraction.json").exists() for row in access_log),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare the first three-paper PERD PDF extraction pilot.")
    parser.add_argument("--input", default="outputs/tables/pdf_extraction_pilot10.csv")
    parser.add_argument("--access-registry", default="data/review/pdf_access_registry.csv")
    parser.add_argument("--output", default="outputs/tables/pdf_extraction_pilot3.csv")
    parser.add_argument("--access-output", default="outputs/tables/pdf_acquisition_pilot3.csv")
    parser.add_argument("--report", default="outputs/reports/pdf_extraction_pilot3_report.md")
    parser.add_argument("--pdf-dir", default="data/raw/pdf")
    parser.add_argument("--extraction-dir", default="data/raw/extraction_json")
    parser.add_argument("--human-validation-dir", default="data/review/human_validation")
    args = parser.parse_args()

    counts = prepare_pilot(
        Path(args.input),
        Path(args.access_registry),
        Path(args.output),
        Path(args.access_output),
        Path(args.report),
        Path(args.pdf_dir),
        Path(args.extraction_dir),
        Path(args.human_validation_dir),
    )
    print(
        "Prepared PDF pilot: selected={selected}, local_pdfs={local_pdfs}, extractions={extractions}".format(**counts)
    )


if __name__ == "__main__":
    main()
