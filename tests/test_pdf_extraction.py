import json

import pytest

from perd.evidence import EvidenceRecord
from perd.evidence_validation import validate_evidence_payload
from perd.extraction_prompt import CRITICAL_EXTRACTION_FIELDS, build_extraction_prompt, extraction_output_template
from perd.pdf_extraction import (
    extract_document_input,
    extract_document_text,
    extract_text_from_pdf,
    load_document_text,
    paper_extraction_from_dict,
    run_pdf_extraction_pipeline,
    write_paper_extraction,
)


def _valid_payload() -> dict:
    payload = extraction_output_template({"paper_id": "paper-001"})
    conductivity = next(item for item in payload["transport"] if item["field"] == "total_conductivity")
    conductivity.update(
        {
            "value": "1.2 x 10^-3 S cm^-1",
            "normalized_value": 1.2e-3,
            "unit": "S/cm",
            "confidence": "high",
            "source_page": 6,
            "source_section": "Results",
            "source_sentence": "The total conductivity reached 1.2 x 10^-3 S cm^-1 at 25 C.",
        }
    )
    return payload


def test_prompt_contains_all_critical_fields_and_review_rule() -> None:
    prompt = build_extraction_prompt("[Page 1] Example electrolyte paper.")

    for fields in CRITICAL_EXTRACTION_FIELDS.values():
        assert all(field in prompt for field in fields)
    assert "Human review is mandatory" in prompt
    assert CRITICAL_EXTRACTION_FIELDS["interface"] == (
        "interfacial_resistance",
        "critical_current_density",
        "li_symmetric_lifetime",
    )


def test_direct_markdown_input_is_preserved() -> None:
    markdown = "[Page 2]\n## Experimental\nPellets were sintered at 1100 C."

    assert load_document_text(markdown, input_format="markdown") == markdown


def test_missing_document_path_is_not_treated_as_text(tmp_path) -> None:
    missing = tmp_path / "missing-paper.md"

    with pytest.raises(FileNotFoundError, match="document not found"):
        load_document_text(missing)


def test_pdf_path_is_converted_to_page_marked_text(tmp_path) -> None:
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test fixture")

    class FakePage:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self) -> str:
            return self.text

    class FakeReader:
        def __init__(self, _path) -> None:
            self.pages = [FakePage("First page text."), FakePage("Second page text.")]
            self.page_labels = ["1", "S1"]

    text = extract_text_from_pdf(pdf_path, FakeReader)

    assert "[Page 1]\nFirst page text." in text
    assert "[Page S1]\nSecond page text." in text


def test_pdf_input_interface_runs_extractor(tmp_path) -> None:
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test fixture")

    class FakePage:
        def extract_text(self) -> str:
            return "Reported electrolyte data."

    class FakeReader:
        def __init__(self, _path) -> None:
            self.pages = [FakePage()]
            self.page_labels = ["3"]

    extraction = extract_document_input(
        pdf_path,
        lambda prompt: _valid_payload() if "[Page 3]" in prompt else {},
        pdf_reader_factory=FakeReader,
    )

    assert extraction.paper_metadata["review_status"] == "pending"


def test_payload_is_converted_to_evidence_records() -> None:
    extraction = paper_extraction_from_dict(_valid_payload())

    assert all(isinstance(record, EvidenceRecord) for record in extraction.transport)
    assert {record.field_name for record in extraction.transport} == set(CRITICAL_EXTRACTION_FIELDS["transport"])
    conductivity = next(record for record in extraction.transport if record.field_name == "total_conductivity")
    assert conductivity.normalized_value == 1.2e-3
    assert conductivity.confidence == "high"


def test_missing_page_lowers_confidence_and_produces_warning() -> None:
    payload = _valid_payload()
    conductivity = next(item for item in payload["transport"] if item["field"] == "total_conductivity")
    conductivity["source_page"] = None

    extraction = paper_extraction_from_dict(payload)
    conductivity_record = next(record for record in extraction.transport if record.field_name == "total_conductivity")
    report = extraction.validation_report()

    assert conductivity_record.confidence == "medium"
    assert any(issue["field"] == "total_conductivity" for issue in report["warnings"])


def test_validation_rejects_known_value_without_source_sentence() -> None:
    payload = _valid_payload()
    conductivity = next(item for item in payload["transport"] if item["field"] == "total_conductivity")
    conductivity["source_sentence"] = None

    report = validate_evidence_payload(payload)

    assert not report["valid"]
    assert any("source_sentence" in issue["message"] for issue in report["errors"])


def test_validation_requires_normalized_value_and_unit_keys() -> None:
    payload = _valid_payload()
    conductivity = next(item for item in payload["transport"] if item["field"] == "total_conductivity")
    conductivity.pop("normalized_value")
    conductivity.pop("unit")

    report = validate_evidence_payload(payload)

    assert not report["valid"]
    messages = {issue["message"] for issue in report["errors"]}
    assert "missing evidence key: normalized_value" in messages
    assert "missing evidence key: unit" in messages


def test_pipeline_writes_review_gated_json(tmp_path) -> None:
    output = tmp_path / "paper_extraction.json"

    def fake_extractor(prompt: str) -> dict:
        assert "DOCUMENT TEXT START" in prompt
        return _valid_payload()

    extraction, report = run_pdf_extraction_pipeline(
        "[Page 6] The total conductivity reached 1.2 x 10^-3 S cm^-1 at 25 C.",
        fake_extractor,
        output,
        {"doi": "10.0000/example"},
    )
    saved = json.loads(output.read_text(encoding="utf-8"))

    assert report["valid"]
    assert extraction.paper_metadata["review_status"] == "pending"
    assert saved["paper_metadata"]["database_inclusion_status"] == "not_included"
    assert set(saved) == {"paper_metadata", *CRITICAL_EXTRACTION_FIELDS}


def test_invalid_extraction_is_not_written(tmp_path) -> None:
    extraction = extract_document_text("paper text", lambda _: _valid_payload())
    record = next(record for record in extraction.transport if record.field_name == "total_conductivity")
    record.source_sentence = None
    output = tmp_path / "paper_extraction.json"

    with pytest.raises(ValueError, match="source_sentence"):
        write_paper_extraction(extraction, output)
    assert not output.exists()
