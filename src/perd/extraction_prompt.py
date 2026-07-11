"""Prompt construction for evidence-aware paper extraction."""

from __future__ import annotations

import json
from typing import Any, Mapping


CRITICAL_EXTRACTION_FIELDS = {
    "composition": (
        "final_formula",
        "dopant_element",
        "dopant_site",
        "dopant_concentration",
    ),
    "processing": (
        "calcination_temperature",
        "sintering_temperature",
        "sintering_time",
        "atmosphere",
    ),
    "transport": (
        "total_conductivity",
        "bulk_conductivity",
        "grain_boundary_conductivity",
        "activation_energy",
    ),
    "interface": (
        "interfacial_resistance",
        "CCD",
        "Li_symmetric_lifetime",
    ),
    "battery": (
        "capacity_retention",
        "cycle_number",
    ),
}


def extraction_output_template(paper_metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return the required extraction response shape."""

    template: dict[str, Any] = {"paper_metadata": dict(paper_metadata or {})}
    for section, fields in CRITICAL_EXTRACTION_FIELDS.items():
        template[section] = [
            {
                "field": field,
                "value": "unknown",
                "normalized_value": None,
                "unit": None,
                "confidence": "unknown",
                "source_page": None,
                "source_section": None,
                "source_sentence": None,
                "extraction_method": "ai_extraction",
            }
            for field in fields
        ]
    return template


def build_extraction_prompt(
    document_text: str,
    paper_metadata: Mapping[str, Any] | None = None,
) -> str:
    """Build a model-neutral prompt for PDF-text or Markdown extraction."""

    if not document_text or not document_text.strip():
        raise ValueError("document_text must not be empty")

    template = json.dumps(extraction_output_template(paper_metadata), ensure_ascii=False, indent=2)
    return f"""You extract solid-electrolyte evidence for the PERD research database.

Return JSON only, using exactly the section names and critical fields in the template below.

Rules:
1. Extract only facts explicitly reported in the supplied document text.
2. Every critical field must appear exactly once. Use value \"unknown\" when it is not reported.
3. For a reported value, copy the supporting source sentence and page label exactly enough for human verification.
4. Preserve the raw source value in value. Put a converted machine-readable value in normalized_value and its unit in unit.
5. Do not infer a dopant site, formula, measurement condition, or performance value. If an inference is unavoidable, use extraction_method \"ai_inference\" and confidence no higher than low.
6. Use confidence high, medium, low, or unknown. A value without a source page cannot be high confidence.
7. Distinguish total, bulk, and grain-boundary conductivity. Preserve measurement temperature in source_sentence or source_section.
8. Do not treat predictions or calculations as experimental measurements. Use extraction_method \"prediction\" for model outputs.
9. Do not add the extraction to any database. Human review is mandatory.

JSON template:
{template}

DOCUMENT TEXT START
{document_text.strip()}
DOCUMENT TEXT END
"""
