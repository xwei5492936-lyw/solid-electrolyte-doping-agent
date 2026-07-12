"""Evidence-aware extraction pipeline for PDF-derived text or Markdown."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from perd.evidence import EvidenceRecord
from perd.evidence_validation import validate_evidence_payload
from perd.extraction_prompt import CRITICAL_EXTRACTION_FIELDS, build_extraction_prompt
from perd.sample_consistency import validate_sample_consistency


SECTION_NAMES = tuple(CRITICAL_EXTRACTION_FIELDS)
Extractor = Callable[[str], str | Mapping[str, Any]]
PdfReaderFactory = Callable[[str | Path], Any]
InputFormat = Literal["pdf", "text", "markdown"]

FIELD_ALIASES = {
    "CCD": "critical_current_density",
    "Li_symmetric_lifetime": "li_symmetric_lifetime",
}


def extract_text_from_pdf(
    pdf_path: str | Path,
    reader_factory: PdfReaderFactory | None = None,
) -> str:
    """Extract page-marked text from a local PDF without downloading it."""

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"expected a .pdf file: {path}")

    if reader_factory is None:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF input requires pypdf; install project requirements") from exc
        reader_factory = PdfReader

    reader = reader_factory(path)
    page_labels = getattr(reader, "page_labels", None)
    page_blocks: list[str] = []
    has_extractable_text = False
    for index, page in enumerate(reader.pages):
        label = page_labels[index] if page_labels and index < len(page_labels) else str(index + 1)
        page_text = (page.extract_text() or "").strip()
        has_extractable_text = has_extractable_text or bool(page_text)
        page_blocks.append(f"[Page {label}]\n{page_text}")

    document_text = "\n\n".join(page_blocks).strip()
    if not has_extractable_text:
        raise ValueError(f"PDF contains no extractable text: {path}; OCR is required before extraction")
    return document_text


def load_document_text(
    document_input: str | Path,
    input_format: InputFormat | None = None,
    pdf_reader_factory: PdfReaderFactory | None = None,
) -> str:
    """Load a PDF path, text/Markdown path, or direct text/Markdown content."""

    if input_format not in {None, "pdf", "text", "markdown"}:
        raise ValueError(f"unsupported input_format: {input_format}")

    if input_format == "pdf":
        return extract_text_from_pdf(document_input, pdf_reader_factory)

    if isinstance(document_input, Path):
        path = document_input
    else:
        candidate = document_input.strip()
        if input_format in {"text", "markdown"}:
            if not candidate:
                raise ValueError("document text must not be empty")
            return document_input
        path = Path(candidate) if "\n" not in candidate and len(candidate) < 1024 else None

    if path is not None:
        if path.exists():
            if path.suffix.lower() == ".pdf":
                return extract_text_from_pdf(path, pdf_reader_factory)
            if path.suffix.lower() not in {".md", ".markdown", ".txt"}:
                raise ValueError(f"unsupported document file type: {path.suffix or '<none>'}")
            text = path.read_text(encoding="utf-8")
            if not text.strip():
                raise ValueError(f"document file is empty: {path}")
            return text
        if path.suffix.lower() in {".pdf", ".md", ".markdown", ".txt"}:
            raise FileNotFoundError(f"document not found: {path}")

    text = str(document_input)
    if not text.strip():
        raise ValueError("document text must not be empty")
    return text


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
    field_name = str(data.get("field", "")).strip()
    return EvidenceRecord(
        field_name=FIELD_ALIASES.get(field_name, field_name),
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


@dataclass(slots=True)
class SampleLevelPaperExtraction:
    """A review-gated v2 extraction with sample-scoped measurements."""

    paper_metadata: dict[str, Any] = field(default_factory=dict)
    sample_records: list[dict[str, Any]] = field(default_factory=list)
    schema_version: str = "2.0"

    def __post_init__(self) -> None:
        self.paper_metadata = dict(self.paper_metadata)
        self.paper_metadata["review_status"] = "pending"
        self.paper_metadata["database_inclusion_status"] = "not_included"
        self.sample_records = [dict(sample) for sample in self.sample_records]
        for sample in self.sample_records:
            sample.setdefault("review_status", "pending")
            if sample.get("sample_id") == "unresolved":
                for group in ("transport_measurements", "resistance_measurements", "interface_measurements", "battery_measurements"):
                    for record in sample.get(group, []):
                        if isinstance(record, dict) and record.get("confidence") == "high":
                            record["confidence"] = "medium"
                            record["needs_human_review"] = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "paper_metadata": dict(self.paper_metadata),
            "sample_records": self.sample_records,
        }

    def validation_report(self) -> dict[str, Any]:
        report = validate_sample_consistency(self.to_dict())
        errors = [issue for issue in report["issues"] if issue["severity"] == "error"]
        warnings = [issue for issue in report["issues"] if issue["severity"] != "error"]
        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "review_required": True,
            "database_inclusion_allowed": False,
            "consistency": report,
        }


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


def paper_extraction_from_dict(payload: Mapping[str, Any]) -> PaperExtraction | SampleLevelPaperExtraction:
    """Convert a JSON-like extraction payload to EvidenceRecord objects."""

    metadata = payload.get("paper_metadata", {})
    if not isinstance(metadata, Mapping):
        raise ValueError("paper_metadata must be an object")

    if "sample_records" in payload:
        samples = payload.get("sample_records")
        if not isinstance(samples, list):
            raise ValueError("sample_records must be a list")
        if not all(isinstance(sample, Mapping) for sample in samples):
            raise ValueError("every sample record must be an object")
        return SampleLevelPaperExtraction(
            paper_metadata=dict(metadata),
            sample_records=[dict(sample) for sample in samples],
            schema_version=str(payload.get("schema_version", "2.0")),
        )

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
) -> PaperExtraction | SampleLevelPaperExtraction:
    """Run an injected extractor on PDF text or Markdown and bind evidence."""

    prompt = build_extraction_prompt(document_text, paper_metadata)
    response = extractor(prompt)
    extraction = paper_extraction_from_dict(parse_extraction_json(response))
    if paper_metadata:
        extraction.paper_metadata.update(dict(paper_metadata))
        extraction.paper_metadata["review_status"] = "pending"
        extraction.paper_metadata["database_inclusion_status"] = "not_included"
    return extraction


def extract_document_input(
    document_input: str | Path,
    extractor: Extractor,
    paper_metadata: Mapping[str, Any] | None = None,
    input_format: InputFormat | None = None,
    pdf_reader_factory: PdfReaderFactory | None = None,
) -> PaperExtraction | SampleLevelPaperExtraction:
    """Load PDF/text/Markdown input, then run evidence-aware extraction."""

    document_text = load_document_text(document_input, input_format, pdf_reader_factory)
    return extract_document_text(document_text, extractor, paper_metadata)


def write_paper_extraction(
    extraction: PaperExtraction | SampleLevelPaperExtraction,
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
    document_input: str | Path,
    extractor: Extractor,
    output_path: str | Path = "paper_extraction.json",
    paper_metadata: Mapping[str, Any] | None = None,
    input_format: InputFormat | None = None,
    pdf_reader_factory: PdfReaderFactory | None = None,
) -> tuple[PaperExtraction | SampleLevelPaperExtraction, dict[str, Any]]:
    """Load, extract, validate, and write a pending-review paper extraction."""

    extraction = extract_document_input(
        document_input,
        extractor,
        paper_metadata,
        input_format,
        pdf_reader_factory,
    )
    report = extraction.validation_report()
    if report["valid"]:
        write_paper_extraction(extraction, output_path)
    return extraction, report
