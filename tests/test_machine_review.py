import csv
from pathlib import Path

import pytest

from perd.machine_review import (
    build_human_review_queue,
    generate_machine_review_report,
    validate_machine_reviews,
)


def _row(**overrides):
    row = {
        "paper_id": "P1",
        "category": "transport",
        "field_name": "total_conductivity",
        "ai_value": "0.001",
        "machine_verified_value": "0.001 S/cm at 25 C",
        "match_status": "correct",
        "review_comment": "Directly reported.",
        "evidence_page": "PDF 3",
        "evidence_location": "Results",
        "evidence_sentence": "The total conductivity was 0.001 S/cm.",
        "verification_method": "body_text",
        "review_confidence": "high",
        "needs_human_review": "false",
        "question_for_human": "",
    }
    row.update(overrides)
    return row


def test_machine_review_enums_are_validated() -> None:
    assert validate_machine_reviews([_row()])[0]["match_status"] == "correct"
    with pytest.raises(ValueError, match="invalid match_status"):
        validate_machine_reviews([_row(match_status="probably_correct")])
    with pytest.raises(ValueError, match="invalid verification_method"):
        validate_machine_reviews([_row(verification_method="guess")])


def test_non_unresolved_review_requires_evidence_page() -> None:
    with pytest.raises(ValueError, match="evidence_page"):
        validate_machine_reviews([_row(evidence_page="")])
    assert validate_machine_reviews([_row(match_status="unresolved", evidence_page="")])


def test_low_confidence_and_conflict_enter_human_queue() -> None:
    rows = [
        _row(field_name="activation_energy", review_confidence="low"),
        _row(field_name="bulk_conductivity", match_status="conflict"),
        _row(field_name="total_conductivity"),
    ]
    queue = build_human_review_queue(rows)
    assert [row["field_name"] for row in queue] == ["activation_energy", "bulk_conductivity"]


def test_report_does_not_claim_human_validation(tmp_path: Path) -> None:
    report = generate_machine_review_report([_row()], tmp_path / "report.md")
    assert "不是 human gold standard" in report
    assert "不得称为 human-validated accuracy" in report
    assert "human-validated accuracy: 100" not in report.casefold()


def test_review_artifacts_do_not_overwrite_protected_inputs(tmp_path: Path) -> None:
    gold = tmp_path / "gold.csv"
    master = tmp_path / "master_dataset.csv"
    gold.write_text("paper_id,human_value\nP1,\n", encoding="utf-8")
    master.write_text("sample_id\nS1\n", encoding="utf-8")
    before = (gold.read_bytes(), master.read_bytes())

    generate_machine_review_report([_row()], tmp_path / "machine_report.md")

    assert (gold.read_bytes(), master.read_bytes()) == before


def test_repository_machine_review_has_17_valid_rows() -> None:
    path = Path("data/review/machine_review_paper001.csv")
    if not path.exists():
        pytest.skip("generated review artifact is not present")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(validate_machine_reviews(rows)) == 17
