"""Prompt construction for evidence-aware, sample-level paper extraction."""

from __future__ import annotations

import json
from typing import Any, Mapping

from perd.schema import (
    COMPOSITION_METHOD_VALUES,
    CONCENTRATION_BASIS_VALUES,
    RESISTANCE_TYPES,
    SITE_ASSIGNMENT_BASIS_VALUES,
    TRANSPORT_PROPERTY_TYPES,
)

CRITICAL_EXTRACTION_FIELDS = {
    "composition": ("final_formula", "dopant_element", "dopant_site", "dopant_concentration"),
    "processing": ("calcination_temperature", "sintering_temperature", "sintering_time", "atmosphere"),
    "transport": ("total_conductivity", "bulk_conductivity", "grain_boundary_conductivity", "activation_energy"),
    "interface": ("interfacial_resistance", "critical_current_density", "li_symmetric_lifetime"),
    "battery": ("capacity_retention", "cycle_number"),
}


def extraction_output_template(paper_metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return the legacy v1 response shape for compatibility and migration tests."""

    template: dict[str, Any] = {"paper_metadata": dict(paper_metadata or {})}
    for section, fields in CRITICAL_EXTRACTION_FIELDS.items():
        template[section] = [
            {
                "field": field, "value": "unknown", "normalized_value": None, "unit": None,
                "confidence": "unknown", "source_page": None, "source_section": None,
                "source_sentence": None, "extraction_method": "ai_extraction",
            }
            for field in fields
        ]
    return template


def sample_extraction_output_template(paper_metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return the sample-level v2 extraction response shape."""

    return {
        "schema_version": "2.0",
        "paper_metadata": dict(paper_metadata or {}),
        "sample_records": [{
            "sample_id": "unresolved", "sample_label": "unknown",
            "nominal_formula": "unknown", "final_formula": "unknown",
            "measured_composition": "unknown", "composition_method": "unknown",
            "dopants": [{
                "element": "unknown", "site": "unknown", "concentration_value": "unknown",
                "concentration_basis": "unknown", "site_assignment_basis": "unknown",
                "sample_id": "unresolved", "evidence": {},
            }],
            "processing": [], "phase_structure": [], "microstructure": [],
            "transport_measurements": [{
                "measurement_id": "unknown", "sample_id": "unresolved", "property_type": "unknown",
                "value": "unknown", "normalized_value": None, "original_unit": None,
                "normalized_unit": None, "temperature_value": "unknown", "temperature_unit": None,
                "frequency_range": "unknown", "atmosphere": "unknown", "electrode_type": "unknown",
                "fitting_method": "unknown", "source_type": "unknown", "evidence": {}, "confidence": "unknown",
            }],
            "resistance_measurements": [], "interface_measurements": [], "battery_measurements": [],
            "evidence": [], "review_status": "pending",
        }],
    }


def build_extraction_prompt(document_text: str, paper_metadata: Mapping[str, Any] | None = None) -> str:
    """Build a model-neutral prompt that requires sample and condition binding."""

    if not document_text or not document_text.strip():
        raise ValueError("document_text must not be empty")
    template = json.dumps(sample_extraction_output_template(paper_metadata), ensure_ascii=False, indent=2)
    return f"""You extract solid-electrolyte evidence for the PERD research database.

Return JSON only using the sample-level template below.
Required concepts from the legacy schema must be represented when reported: {CRITICAL_EXTRACTION_FIELDS}.

Rules:
1. First identify all distinct samples and sample labels. Build a sample map before extracting property values.
2. Bind every extracted value to one sample_id. Never infer missing sample identity; use sample_id "unresolved", lower confidence, and require human review.
3. Do not merge values from different compositions, conditions, or cells. Do not bind a composition-series range to one optimal sample.
4. Distinguish composition series from selected samples. Keep nominal_formula, final_formula, and measured_composition separate.
5. Fill measured_composition only when a measurement method is reported. composition_method: {COMPOSITION_METHOD_VALUES}.
6. Every dopant needs element, site, concentration_value, concentration_basis, site_assignment_basis, sample_id, and evidence.
7. concentration_basis: {CONCENTRATION_BASIS_VALUES}. site_assignment_basis: {SITE_ASSIGNMENT_BASIS_VALUES}.
8. Never infer an experimentally confirmed site from valence or general knowledge. Explicit assignment requires direct evidence.
9. Preserve raw and normalized values separately, plus sample, units, temperature, and test conditions.
10. transport property_type: {TRANSPORT_PROPERTY_TYPES}. Never exchange total, bulk, and grain-boundary conductivity.
11. Conductivity requires temperature. Preserve "room temperature" as reported; never silently replace it with 25 C.
12. Activation energy must identify total, bulk, or grain-boundary transport and preserve its fitted temperature range.
13. Figure-read values require source_type "estimated_from_figure".
14. resistance_type: {RESISTANCE_TYPES}. Also record measurement_domain. Grain-boundary and total-cell resistance belong to transport; Li|electrolyte resistance belongs to interface.
15. Blocking-electrode EIS is not Li-metal interface resistance. Symmetric-cell EIS still requires explicit attribution.
16. If resistance attribution is ambiguous, use resistance_type "unresolved" and needs_human_review true.
17. Extract only explicit facts. Use "unknown" for unreported values; do not turn references or potential applications into results.
18. Human review is mandatory. Do not write extraction results into the database.

JSON template:
{template}

DOCUMENT TEXT START
{document_text.strip()}
DOCUMENT TEXT END
"""
