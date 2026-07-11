"""Evidence-aware extraction pipeline for PDF-derived text or Markdown."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from perd.evidence import EvidenceRecord
from perd.evidence_validation import validate_evidence_payload
from perd.extraction_prompt import CRITICAL_EXTRACTION_FIELDS, build_extraction_prompt


SECTION_NAMES = tuple(CRITICAL_EXTRACTION_FIELDS)
Extractor = Callable[[str], str | Mapping[str, Any]]


def _record_to_output(record: EvidenceRecord) -> dict[str, Any]:
    value = record.normalized_value if record.normalized_value is not None else record.extracted_value
    return {
        "field": record.field_name,
        "value": value,
        "extracted_value": record.extracted_value,
        "normalized_value": record.normalized_value,
        "unit": record.unit,
        "confidence": record.confidence,
        "source_page": record.source_page,
        "source_section": record.source_section,
        "source_sentence": record.source_sentence,
        "extraction_method": record.extraction_method,
    }


def _record_from_output(data: Mapping[str, Any]) -> EvidenceRecord:
    extracted_value = data.get("extracted_value", data.get("value", "unknown"))
    normalized_value = data.get("normalized_value")
    return EvidenceRecord(
        field_name=str(data.get("field", "")).strip(),
        extracted_value=extracted_value,
        normalized_value=normalized_value,
        unit=data.get("unit"),
        source_page=data.get("source_page"),
        source_section=data.get("source_section"),
        source_sentence=data.get("source_sentence"),
        extraction_method=str(data.get("extraction_method", "ai_extraction")),
        confidence=str(data.get("confidence", "unknown")),
    )


def _unknown_record(field_name: str) -> EvidenceRecord:
    return EvidenceRecord(
        field_name=field_name,
        extracted_value="unknown",
        normalized_value=None,
        extraction_method="ai_extraction",
        confidence="unknown",
    )


@dataclass(slots=True)
class PaperExtraction:
    """A paper-level extraction that remains gated for human review."""

    paper_metadata: dict[str, Any] = field(default_factory=dict)
    composition: list[EvidenceRecord] = field(default_factory=list)
    processing: list[EvidenceRecord] = field(default_factory=list)
    transport: list[EvidenceRecord] = field(default_factory=list)
    interface: list[EvidenceRecord] = field(default_factory=list)
    battery: list[EvidenceRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.paper_metadata = dict(self.paper_metadata)
        self.paper_metadata["review_status"] = "pending"
        self.paper_metadata["database_inclusion_status"] = "not_included"

        for section, fields in CRITICAL_EXTRACTION_FIELDS.items():
            records = list(getattr(self, section))
            by_field = {record.field_name: record for record in records}
            setattr(self, section, [by_field.get(name, _unknown_record(name)) for name in fields])

    def to_dict(self) -> dict[str, Any]:
        """Return the required paper_extraction.json structure."""

        payload: dict[str, Any] = {"paper_metadata": dict(self.paper_metadata)}
        for section in SECTION_NAMES:
            payload[section] = [_record_to_output(record) for record in getattr(self, section)]
        return payload

    def validation_report(self) -> dict[str, Any]:
        """Validate evidence coverage without changing review state."""

        return validate_evidence_payload(self.to_dict())


def parse_extraction_json(response: str | Mapping[str, Any]) -> dict[str, Any]:
    """Parse a model response, accepting plain JSON or a fenced JSON block."""

    if isinstance(response, Mapping):
        return dict(response)
    text = response.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1)
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("extraction response must be a JSON object")
    return parsed


def paper_extraction_from_dict(payload: Mapping[str, Any]) -> PaperExtraction:
    """Convert a JSON-like extraction payload to EvidenceRecord objects."""

    metadata = payload.get("paper_metadata", {})
    if not isinstance(metadata, Mapping):
        raise ValueError("paper_metadata must be an object")

    sections: dict[str, list[EvidenceRecord]] = {}
    for section in SECTION_NAMES:
        raw_records = payload.get(section, [])
        if not isinstance(raw_records, list):
            raise ValueError(f"{section} must be a list")
        sections[section] = [_record_from_output(item) for item in raw_records]

    return PaperExtraction(paper_metadata=dict(metadata), **sections)


def extract_document_text(
    document_text: str,
    extractor: Extractor,
    paper_metadata: Mapping[str, Any] | None = None,
) -> PaperExtraction:
    """Run an injected extractor on PDF text or Markdown and bind evidence."""

    prompt = build_extraction_prompt(document_text, paper_metadata)
    response = extractor(prompt)
    extraction = paper_extraction_from_dict(parse_extraction_json(response))
    if paper_metadata:
        extraction.paper_metadata.update(dict(paper_metadata))
        extraction.paper_metadata["review_status"] = "pending"
        extraction.paper_metadata["database_inclusion_status"] = "not_included"
    return extraction


def write_paper_extraction(
    extraction: PaperExtraction,
    output_path: str | Path = "paper_extraction.json",
) -> Path:
    """Validate and write a review-gated extraction JSON file."""

    report = extraction.validation_report()
    if not report["valid"]:
        messages = "; ".join(issue["message"] for issue in report["errors"])
        raise ValueError(f"invalid paper extraction: {messages}")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(extraction.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_pdf_extraction_pipeline(
    document_text: str,
    extractor: Extractor,
    output_path: str | Path = "paper_extraction.json",
    paper_metadata: Mapping[str, Any] | None = None,
) -> tuple[PaperExtraction, dict[str, Any]]:
    """Extract, validate, and write a pending-review paper extraction."""

    extraction = extract_document_text(document_text, extractor, paper_metadata)
    report = extraction.validation_report()
    if report["valid"]:
        write_paper_extraction(extraction, output_path)
    return extraction, report
