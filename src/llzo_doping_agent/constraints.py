"""Physics-inspired screening rules for LLZO dopant candidates."""

from __future__ import annotations

from dataclasses import dataclass

from llzo_doping_agent.schema import CandidateScheme

KNOWN_SUBSTITUTION_SITES = {"Li", "La", "Zr"}


@dataclass(frozen=True)
class ConstraintResult:
    """Result of checking a candidate against simple design constraints."""

    passed: bool
    reasons: tuple[str, ...]


def evaluate_candidate(candidate: CandidateScheme) -> ConstraintResult:
    """Evaluate a candidate against conservative LLZO dopant constraints."""

    reasons: list[str] = []

    if candidate.site not in KNOWN_SUBSTITUTION_SITES:
        reasons.append(f"unsupported substitution site: {candidate.site}")

    if candidate.dopant_fraction <= 0:
        reasons.append("dopant fraction must be positive")

    if candidate.dopant_fraction > 1:
        reasons.append("dopant fraction must not exceed 1")

    if candidate.assumed_valence == candidate.host_valence:
        reasons.append("dopant valence should differ from host valence for charge compensation")

    return ConstraintResult(passed=not reasons, reasons=tuple(reasons))
