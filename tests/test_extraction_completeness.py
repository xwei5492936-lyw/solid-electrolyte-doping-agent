import pandas as pd

from scripts.check_extraction_completeness import CORE_FIELDS, check_completeness


def complete_row(**overrides):
    row = {
        "sample_id": "sample-1",
        "final_formula": "synthetic formula",
        "dopant_element_1": "Ta",
        "dopant_site_1": "Zr",
        "sintering_temperature_c": 1150,
        "phase": "cubic",
        "total_conductivity_25c_s_cm": 1e-3,
        "activation_energy_ev": 0.3,
        "li_symmetric_lifetime_h": 800,
        "confidence": "high",
    }
    row.update(overrides)
    return row


def test_complete_sample_has_no_missing_fields() -> None:
    report = check_completeness(pd.DataFrame([complete_row()]))

    assert report["valid"]
    assert report["summary"]["complete_sample_count"] == 1
    assert report["samples"][0]["missing_fields"] == []


def test_missing_core_field_value_is_reported() -> None:
    report = check_completeness(pd.DataFrame([complete_row(phase="unknown")]))

    assert report["valid"]
    assert report["summary"]["incomplete_sample_count"] == 1
    assert report["samples"][0]["missing_fields"] == ["phase"]
    assert report["warnings"][0]["sample_id"] == "sample-1"


def test_missing_core_column_is_error() -> None:
    row = complete_row()
    row.pop("activation_energy_ev")
    report = check_completeness(pd.DataFrame([row]))

    assert not report["valid"]
    assert {"field": "activation_energy_ev", "message": "missing core completeness column"} in report["errors"]
    assert "activation_energy_ev" in report["samples"][0]["missing_fields"]


def test_core_fields_match_requested_list() -> None:
    assert CORE_FIELDS == (
        "final_formula",
        "dopant_element_1",
        "dopant_site_1",
        "sintering_temperature_c",
        "phase",
        "total_conductivity_25c_s_cm",
        "activation_energy_ev",
        "li_symmetric_lifetime_h",
        "confidence",
    )
