"""Consistency checks for sample-level evidence extraction payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from perd.schema import (
    COMPOSITION_METHOD_VALUES,
    CONCENTRATION_BASIS_VALUES,
    RESISTANCE_TYPES,
    SITE_ASSIGNMENT_BASIS_VALUES,
    TRANSPORT_PROPERTY_TYPES,
)

MISSING = {"", "unknown", "none", "null", "n/a"}
CONDUCTIVITY_TYPES = {"total_ionic_conductivity", "bulk_ionic_conductivity", "grain_boundary_conductivity", "electronic_conductivity"}
ACTIVATION_TYPES = {"activation_energy_total", "activation_energy_bulk", "activation_energy_grain_boundary"}


def _missing(value: Any) -> bool:
    return value is None or str(value).strip().casefold() in MISSING


def _issue(severity: str, sample_id: str, field: str, message: str) -> dict[str, str]:
    return {"severity": severity, "sample_id": sample_id, "field": field, "message": message}


def _records(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _check_evidence(issues: list[dict[str, str]], sample_id: str, field: str, record: Mapping[str, Any]) -> None:
    evidence = record.get("evidence")
    if not isinstance(evidence, Mapping) or _missing(evidence.get("source_page")) or _missing(evidence.get("source_sentence")):
        issues.append(_issue("error", sample_id, field, "reported record requires evidence page and source sentence"))


def validate_sample_consistency(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Report sample-binding and condition problems without modifying the payload."""

    issues: list[dict[str, str]] = []
    samples = payload.get("sample_records")
    if not isinstance(samples, Sequence) or isinstance(samples, (str, bytes)):
        issues.append(_issue("error", "unresolved", "sample_records", "sample_records must be a list"))
        samples = []

    seen_ids: set[str] = set()
    for index, sample in enumerate(samples):
        if not isinstance(sample, Mapping):
            issues.append(_issue("error", "unresolved", str(index), "sample record must be an object"))
            continue
        sample_id = str(sample.get("sample_id", "")).strip() or "unresolved"
        if sample_id == "unresolved":
            issues.append(_issue("review_required", sample_id, "sample_id", "sample association is unresolved"))
        elif sample_id in seen_ids:
            issues.append(_issue("error", sample_id, "sample_id", "duplicate sample_id"))
        seen_ids.add(sample_id)

        formulas = {str(sample.get(name)).strip() for name in ("nominal_formula", "final_formula", "measured_composition") if not _missing(sample.get(name))}
        if len(formulas) > 1 and _missing(sample.get("composition_explanation")):
            issues.append(_issue("warning", sample_id, "composition", "multiple formulas require composition_explanation"))

        measured = sample.get("measured_composition")
        method = str(sample.get("composition_method", "unknown"))
        if method not in COMPOSITION_METHOD_VALUES:
            issues.append(_issue("error", sample_id, "composition_method", "invalid composition_method"))
        if not _missing(measured) and method in {"nominal", "unknown"}:
            issues.append(_issue("error", sample_id, "measured_composition", "measured composition requires a measurement method"))

        for dopant in _records(sample.get("dopants")):
            dopant_sample = str(dopant.get("sample_id", "")).strip()
            if not dopant_sample:
                issues.append(_issue("error", sample_id, "dopants.sample_id", "dopant record lacks sample_id"))
            elif dopant_sample != sample_id:
                issues.append(_issue("review_required", sample_id, "dopants.sample_id", "dopant record is bound to a different sample"))
            basis = str(dopant.get("site_assignment_basis", "unknown"))
            if basis not in SITE_ASSIGNMENT_BASIS_VALUES:
                issues.append(_issue("error", sample_id, "site_assignment_basis", "invalid site assignment basis"))
            if str(dopant.get("concentration_basis", "unknown")) not in CONCENTRATION_BASIS_VALUES:
                issues.append(_issue("error", sample_id, "concentration_basis", "invalid concentration basis"))
            evidence = dopant.get("evidence")
            if basis == "explicitly_reported" and (not isinstance(evidence, Mapping) or _missing(evidence.get("source_sentence"))):
                issues.append(_issue("error", sample_id, "dopant.site", "explicit dopant site requires direct evidence"))
            if not _missing(dopant.get("element")):
                _check_evidence(issues, sample_id, "dopants.evidence", dopant)

        for measurement in _records(sample.get("transport_measurements")):
            bound_id = str(measurement.get("sample_id", "")).strip()
            property_type = str(measurement.get("property_type", "unknown"))
            if not bound_id:
                issues.append(_issue("error", sample_id, "transport.sample_id", "performance value lacks sample_id"))
            elif bound_id == "unresolved" or bound_id != sample_id:
                issues.append(_issue("review_required", sample_id, "transport.sample_id", "transport sample binding requires review"))
            if property_type not in TRANSPORT_PROPERTY_TYPES:
                issues.append(_issue("error", sample_id, "transport.property_type", "invalid transport property type"))
            if property_type in CONDUCTIVITY_TYPES:
                temperature = measurement.get("temperature_value")
                if temperature is None or str(temperature).strip() == "":
                    issues.append(_issue("error", sample_id, "transport.temperature", "conductivity requires temperature or explicit unknown"))
                elif str(temperature).strip().casefold() == "unknown":
                    issues.append(_issue("review_required", sample_id, "transport.temperature", "conductivity temperature is explicitly unknown"))
            if property_type in ACTIVATION_TYPES and _missing(measurement.get("activation_process_type")):
                issues.append(_issue("error", sample_id, "transport.activation_process_type", "activation energy requires process type"))
            if not _missing(measurement.get("value")):
                _check_evidence(issues, sample_id, "transport.evidence", measurement)

        for resistance in _records(sample.get("resistance_measurements")):
            resistance_type = str(resistance.get("resistance_type", "")).strip()
            if resistance_type not in RESISTANCE_TYPES:
                issues.append(_issue("error", sample_id, "resistance_type", "resistance requires a valid resistance_type"))
            elif resistance_type == "unresolved":
                issues.append(_issue("review_required", sample_id, "resistance_type", "resistance attribution is unresolved"))
            expected_domain = "interface" if resistance_type == "electrode_interface_resistance" else "transport"
            if resistance_type != "unresolved" and resistance.get("measurement_domain") != expected_domain:
                issues.append(_issue("error", sample_id, "resistance.measurement_domain", f"{resistance_type} must use {expected_domain} domain"))
            if not _missing(resistance.get("value")):
                _check_evidence(issues, sample_id, "resistance.evidence", resistance)

        for measurement in _records(sample.get("interface_measurements")) + _records(sample.get("battery_measurements")):
            if _missing(measurement.get("sample_id")):
                issues.append(_issue("error", sample_id, "measurement.sample_id", "performance value lacks sample_id"))
            if not isinstance(measurement.get("test_conditions"), Mapping) or not measurement.get("test_conditions"):
                issues.append(_issue("warning", sample_id, "measurement.test_conditions", "battery/interface result lacks test conditions"))
            if not _missing(measurement.get("value")):
                _check_evidence(issues, sample_id, "measurement.evidence", measurement)

    counts = {severity: sum(item["severity"] == severity for item in issues) for severity in ("error", "warning", "review_required")}
    return {"valid": counts["error"] == 0, "issues": issues, "counts": counts}
