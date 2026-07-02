"""Core records for LLZO dopant literature mining."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

EvidenceType = Literal["experimental_fact", "model_prediction"]
Site = Literal["Li", "La", "Zr", "O", "unknown"]


@dataclass(frozen=True)
class DopantCase:
    """A structured dopant record extracted from a source paper."""

    material: str
    dopant: str
    site: Site
    dopant_fraction: float
    evidence_type: EvidenceType
    source_id: str
    conductivity_s_cm: float | None = None
    synthesis_route: str | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CandidateScheme:
    """A generated dopant proposal to rank after constraint checks."""

    material: str
    dopant: str
    site: Site
    dopant_fraction: float
    assumed_valence: int
    host_valence: int
    rationale: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
