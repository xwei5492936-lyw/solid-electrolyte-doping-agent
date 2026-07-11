import csv
import json
from pathlib import Path

from perd.extraction_prompt import extraction_output_template
from scripts.prepare_pdf_extraction_pilot import (
    ACCESS_FIELDS,
    build_access_log,
    inspect_extraction,
    prepare_pilot,
    select_priority_papers,
)


def _pilot_rows() -> list[dict[str, str]]:
    return [
        {"candidate_id": f"paper-{priority}", "title": f"Paper {priority}", "doi": f"10.test/{priority}", "priority": str(priority)}
        for priority in (4, 2, 1, 3)
    ]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_selects_only_priorities_one_to_three() -> None:
    selected = select_priority_papers(_pilot_rows())

    assert [row["priority"] for row in selected] == ["1", "2", "3"]
    assert len(selected) == 3


def test_access_log_defaults_to_pending_without_verified_source() -> None:
    selected = select_priority_papers(_pilot_rows())

    access_log = build_access_log(selected, [])

    assert tuple(access_log[0]) == ACCESS_FIELDS
    assert {row["access_status"] for row in access_log} == {"access_pending"}


def test_inspect_extraction_counts_known_and_missing_fields(tmp_path) -> None:
    payload = extraction_output_template({"paper_id": "paper-1", "pdf_metadata_warning": "Title mismatch"})
    record = next(item for item in payload["composition"] if item["field"] == "final_formula")
    record.update(
        {
            "value": "Li6.5La3Zr1.5Ta0.5O12",
            "normalized_value": "Li6.5La3Zr1.5Ta0.5O12",
            "unit": None,
            "confidence": "high",
            "source_page": 2,
            "source_sentence": "The final formula was Li6.5La3Zr1.5Ta0.5O12.",
        }
    )
    path = tmp_path / "paper-1_extraction.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    summary = inspect_extraction(path)

    assert summary["valid"]
    assert summary["extracted_fields"] == ["composition.final_formula"]
    assert len(summary["missing_fields"]) == 16
    assert summary["metadata_warnings"] == ["Title mismatch"]


def test_prepare_pilot_creates_outputs_without_master_dataset(tmp_path) -> None:
    input_csv = tmp_path / "pilot10.csv"
    registry_csv = tmp_path / "registry.csv"
    _write_csv(input_csv, _pilot_rows())
    registry = [
        {
            "paper_id": f"paper-{priority}",
            "title": f"Paper {priority}",
            "doi": f"10.test/{priority}",
            "source": f"https://doi.org/10.test/{priority}",
            "access_status": "access_pending",
            "notes": "test",
        }
        for priority in (1, 2, 3)
    ]
    _write_csv(registry_csv, registry)

    counts = prepare_pilot(
        input_csv,
        registry_csv,
        tmp_path / "pilot3.csv",
        tmp_path / "access.csv",
        tmp_path / "report.md",
        tmp_path / "raw" / "pdf",
        tmp_path / "raw" / "extraction_json",
        tmp_path / "review" / "human_validation",
    )

    assert counts == {"selected": 3, "local_pdfs": 0, "extractions": 0}
    assert len(list(csv.DictReader((tmp_path / "pilot3.csv").open(encoding="utf-8-sig")))) == 3
    assert "Processed papers (valid extraction JSON present): **0**" in (tmp_path / "report.md").read_text()
    assert not (tmp_path / "master_dataset.csv").exists()
