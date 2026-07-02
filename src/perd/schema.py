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
)

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
