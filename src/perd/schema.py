"""Schema definitions for PERD data tables."""

from __future__ import annotations

CONFIDENCE_VALUES = ("high", "medium", "low", "unknown")

PAPER_FIELDS = (
    "paper_id",
    "title",
    "doi",
    "year",
    "journal",
    "material_family",
    "source_type",
    "notes",
)

COMPOSITION_FIELDS = (
    "sample_id",
    "paper_id",
    "base_formula",
    "final_formula",
    "material_family",
    "dopant_element_1",
    "dopant_site_1",
    "dopant_valence_1",
    "dopant_concentration_1",
    "dopant_element_2",
    "dopant_site_2",
    "dopant_valence_2",
    "dopant_concentration_2",
    "co_doping_flag",
    "li_content",
    "charge_compensation_type",
    "confidence",
    "formula_evidence",
    "dopant_evidence",
    "dopant_site_evidence",
    "concentration_evidence",
)

PROCESSING_FIELDS = (
    "sample_id",
    "synthesis_method",
    "calcination_temperature_c",
    "calcination_time_h",
    "sintering_temperature_c",
    "sintering_time_h",
    "atmosphere",
    "excess_lithium_source",
    "mother_powder",
    "relative_density_percent",
    "grain_size_um",
    "phase",
    "lattice_parameter_a",
    "secondary_phase",
    "confidence",
    "sintering_temperature_evidence",
    "sintering_time_evidence",
    "atmosphere_evidence",
)

TRANSPORT_FIELDS = (
    "sample_id",
    "total_conductivity_25c_s_cm",
    "bulk_conductivity_25c_s_cm",
    "gb_conductivity_25c_s_cm",
    "activation_energy_ev",
    "electronic_conductivity_s_cm",
    "eis_temperature_range",
    "drt_available",
    "confidence",
    "conductivity_evidence",
    "activation_energy_evidence",
    "bulk_conductivity_evidence",
    "grain_boundary_conductivity_evidence",
)

INTERFACE_FIELDS = (
    "sample_id",
    "li_contact_method",
    "interfacial_resistance_ohm_cm2",
    "critical_current_density_ma_cm2",
    "li_symmetric_current_density_ma_cm2",
    "li_symmetric_areal_capacity_mah_cm2",
    "li_symmetric_lifetime_h",
    "cycling_temperature_c",
    "stack_pressure_mpa",
    "confidence",
    "lifetime_evidence",
    "ccd_evidence",
    "interfacial_resistance_evidence",
)

BATTERY_FIELDS = (
    "sample_id",
    "cathode_type",
    "cathode_loading_mg_cm2",
    "liquid_electrolyte_amount_ul",
    "cycling_rate",
    "cycle_number",
    "capacity_mah_g",
    "capacity_retention_percent",
    "coulombic_efficiency_percent",
    "operating_temperature_c",
    "confidence",
    "cycle_number_evidence",
    "capacity_retention_evidence",
)

EVIDENCE_FIELD_MAP = {
    "composition": {
        "formula": {"value_fields": ("base_formula", "final_formula"), "evidence_field": "formula_evidence"},
        "dopant": {
            "value_fields": ("dopant_element_1", "dopant_element_2"),
            "evidence_field": "dopant_evidence",
        },
        "dopant_site": {
            "value_fields": ("dopant_site_1", "dopant_site_2"),
            "evidence_field": "dopant_site_evidence",
        },
        "concentration": {
            "value_fields": ("dopant_concentration_1", "dopant_concentration_2"),
            "evidence_field": "concentration_evidence",
        },
    },
    "processing": {
        "sintering_temperature": {
            "value_fields": ("sintering_temperature_c",),
            "evidence_field": "sintering_temperature_evidence",
        },
        "sintering_time": {
            "value_fields": ("sintering_time_h",),
            "evidence_field": "sintering_time_evidence",
        },
        "atmosphere": {"value_fields": ("atmosphere",), "evidence_field": "atmosphere_evidence"},
    },
    "transport": {
        "conductivity": {
            "value_fields": ("total_conductivity_25c_s_cm",),
            "evidence_field": "conductivity_evidence",
        },
        "activation_energy": {
            "value_fields": ("activation_energy_ev",),
            "evidence_field": "activation_energy_evidence",
        },
        "bulk_conductivity": {
            "value_fields": ("bulk_conductivity_25c_s_cm",),
            "evidence_field": "bulk_conductivity_evidence",
        },
        "grain_boundary_conductivity": {
            "value_fields": ("gb_conductivity_25c_s_cm",),
            "evidence_field": "grain_boundary_conductivity_evidence",
        },
    },
    "interface": {
        "lifetime": {
            "value_fields": ("li_symmetric_lifetime_h",),
            "evidence_field": "lifetime_evidence",
        },
        "CCD": {
            "value_fields": ("critical_current_density_ma_cm2",),
            "evidence_field": "ccd_evidence",
        },
        "interfacial_resistance": {
            "value_fields": ("interfacial_resistance_ohm_cm2",),
            "evidence_field": "interfacial_resistance_evidence",
        },
    },
    "battery": {
        "cycle_number": {"value_fields": ("cycle_number",), "evidence_field": "cycle_number_evidence"},
        "capacity_retention": {
            "value_fields": ("capacity_retention_percent",),
            "evidence_field": "capacity_retention_evidence",
        },
    },
}

MASTER_REQUIRED_FIELDS = (
    "sample_id",
    "paper_id",
    "year",
    "base_formula",
    "final_formula",
    "material_family",
)

_SCHEMAS = {
    "paper": PAPER_FIELDS,
    "composition": COMPOSITION_FIELDS,
    "processing": PROCESSING_FIELDS,
    "transport": TRANSPORT_FIELDS,
    "interface": INTERFACE_FIELDS,
    "battery": BATTERY_FIELDS,
    "master": MASTER_REQUIRED_FIELDS,
}


def get_required_fields(table_name: str) -> tuple[str, ...]:
    """Return required fields for a supported PERD table."""

    key = table_name.lower()
    if key not in _SCHEMAS:
        raise ValueError(f"Unsupported table_name: {table_name}")
    return _SCHEMAS[key]


def get_all_schema_fields() -> dict[str, tuple[str, ...]]:
    """Return all known table schemas."""

    return dict(_SCHEMAS)


def get_evidence_schema(table_name: str) -> dict[str, dict[str, tuple[str, ...] | str]]:
    """Return evidence-enabled concepts and their value/evidence columns."""

    key = table_name.lower()
    if key not in EVIDENCE_FIELD_MAP:
        raise ValueError(f"Unsupported evidence table_name: {table_name}")
    return dict(EVIDENCE_FIELD_MAP[key])
