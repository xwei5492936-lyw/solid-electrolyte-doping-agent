"""Evidence provenance records for extracted PERD fields."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from perd.schema import CONFIDENCE_VALUES


_MISSING_PAGE_CONFIDENCE = {
    "high": "medium",
    "medium": "low",
    "low": "unknown",
    "unknown": "unknown",
}


@dataclass(slots=True)
class EvidenceRecord:
    """Trace one extracted field back to its source context."""

    field_name: str
    extracted_value: Any
    normalized_value: Any = None
    unit: str | None = None
    source_page: int | str | None = None
    source_section: str | None = None
    source_sentence: str | None = None
    extraction_method: str = "unknown"
    confidence: str = "unknown"

    def __post_init__(self) -> None:
        self.field_name = str(self.field_name).strip()
        if not self.field_name:
            raise ValueError("field_name must not be empty")

        self.confidence = str(self.confidence).strip().lower()
        if self.confidence not in CONFIDENCE_VALUES:
            raise ValueError(f"confidence must be one of {CONFIDENCE_VALUES}")

        if self.source_page is None or str(self.source_page).strip() == "":
            self.source_page = None
            self.confidence = _MISSING_PAGE_CONFIDENCE[self.confidence]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary representation."""

        return asdict(self)

    def to_json(self, **kwargs: Any) -> str:
        """Serialize the evidence record to JSON."""

        options = {"ensure_ascii": False}
        options.update(kwargs)
        return json.dumps(self.to_dict(), **options)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EvidenceRecord":
        """Construct an evidence record from a mapping."""

        return cls(**dict(data))
