"""Validation for evidence-aware PDF extraction payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from perd.extraction_prompt import CRITICAL_EXTRACTION_FIELDS
from perd.schema import CONFIDENCE_VALUES


MISSING_VALUES = {"", "unknown", "none", "null", "n/a", "na"}
REQUIRED_EVIDENCE_KEYS = (
    "field",
    "value",
    "normalized_value",
    "unit",
    "confidence",
    "source_page",
    "source_sentence",
)


def _is_missing(value: Any) -> bool:
    return value is None or str(value).strip().lower() in MISSING_VALUES


def _issue(section: str, field: str, message: str) -> dict[str, str]:
    return {"section": section, "field": field, "message": message}


def validate_evidence_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate extraction structure, evidence coverage, and review gating."""

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    metadata = payload.get("paper_metadata")
    if not isinstance(metadata, Mapping):
        errors.append(_issue("paper_metadata", "paper_metadata", "must be an object"))
        metadata = {}

    for section, required_fields in CRITICAL_EXTRACTION_FIELDS.items():
        records = payload.get(section)
        if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
            errors.append(_issue(section, section, "must be a list of evidence records"))
            continue

        seen: set[str] = set()
        for index, record in enumerate(records):
            if not isinstance(record, Mapping):
                errors.append(_issue(section, str(index), "evidence record must be an object"))
                continue

            field = str(record.get("field", "")).strip()
            if not field:
                errors.append(_issue(section, str(index), "field must not be empty"))
                continue
            if field in seen:
                errors.append(_issue(section, field, "duplicate evidence record"))
            seen.add(field)

            for key in REQUIRED_EVIDENCE_KEYS:
                if key not in record:
                    errors.append(_issue(section, field, f"missing evidence key: {key}"))

            confidence = str(record.get("confidence", "unknown")).strip().lower()
            if confidence not in CONFIDENCE_VALUES:
                errors.append(_issue(section, field, f"confidence must be one of {CONFIDENCE_VALUES}"))

            value = record.get("value")
            if not _is_missing(value):
                if _is_missing(record.get("source_sentence")):
                    errors.append(_issue(section, field, "reported value requires source_sentence"))
                if _is_missing(record.get("source_page")):
                    warnings.append(_issue(section, field, "source_page missing; confidence must be reduced"))
                if confidence == "unknown":
                    warnings.append(_issue(section, field, "reported value has unknown confidence"))

        missing_fields = set(required_fields) - seen
        extra_fields = seen - set(required_fields)
        for field in sorted(missing_fields):
            errors.append(_issue(section, field, "missing critical field evidence record"))
        for field in sorted(extra_fields):
            warnings.append(_issue(section, field, "field is outside the critical extraction schema"))

    review_status = str(metadata.get("review_status", "pending")).strip().lower()
    inclusion_status = str(metadata.get("database_inclusion_status", "not_included")).strip().lower()
    if review_status not in {"pending", "in_review", "approved", "rejected"}:
        errors.append(_issue("paper_metadata", "review_status", "invalid review status"))
    if inclusion_status != "not_included":
        errors.append(
            _issue(
                "paper_metadata",
                "database_inclusion_status",
                "extraction output must remain not_included until a separate reviewed inclusion step",
            )
        )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "review_required": review_status != "approved",
        "database_inclusion_allowed": False,
    }
