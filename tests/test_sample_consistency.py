from copy import deepcopy
import json
from pathlib import Path

from perd.extraction_prompt import build_extraction_prompt, sample_extraction_output_template
from perd.pdf_extraction import SampleLevelPaperExtraction, paper_extraction_from_dict
from perd.sample_consistency import validate_sample_consistency


def _sample(sample_id: str = "P1-S1") -> dict:
    return {
        "sample_id": sample_id,
        "sample_label": "x=0.2",
        "nominal_formula": "Li6.2Ga0.2La3Zr1.8Nb0.2O12",
        "final_formula": "unknown",
        "measured_composition": "unknown",
        "composition_method": "nominal",
        "dopants": [{
            "element": "Ga", "site": "Li", "concentration_value": 0.2,
            "concentration_basis": "formula_coefficient", "site_assignment_basis": "explicitly_reported",
            "sample_id": sample_id, "evidence": {"source_page": 3, "source_sentence": "Ga occupies Li sites."},
        }],
        "processing": [], "phase_structure": [], "microstructure": [],
        "transport_measurements": [{
            "measurement_id": "M1", "sample_id": sample_id,
            "property_type": "total_ionic_conductivity", "value": "3.7e-4 S/cm",
            "normalized_value": 3.7e-4, "original_unit": "S cm-1", "normalized_unit": "S/cm",
            "temperature_value": "room temperature", "temperature_unit": "as reported",
            "evidence": {"source_page": 5, "source_sentence": "The conductivity is 3.7e-4 S cm-1."},
            "confidence": "high",
        }],
        "resistance_measurements": [], "interface_measurements": [], "battery_measurements": [],
        "evidence": [], "review_status": "pending",
    }


def test_multiple_samples_and_formula_series_remain_distinct() -> None:
    first = _sample("P1-S1")
    second = _sample("P1-S2")
    second["sample_label"] = "x=0.3"
    second["nominal_formula"] = "Li5.9Ga0.3La3Zr1.8Nb0.2O12"
    for record in second["dopants"] + second["transport_measurements"]:
        record["sample_id"] = "P1-S2"
    report = validate_sample_consistency({"sample_records": [first, second]})
    assert report["valid"]
    assert {first["nominal_formula"], second["nominal_formula"]} == {
        "Li6.2Ga0.2La3Zr1.8Nb0.2O12", "Li5.9Ga0.3La3Zr1.8Nb0.2O12"
    }


def test_nominal_is_not_measured_composition() -> None:
    sample = _sample()
    sample["measured_composition"] = sample["nominal_formula"]
    report = validate_sample_consistency({"sample_records": [sample]})
    assert any(issue["field"] == "measured_composition" for issue in report["issues"])


def test_transport_requires_sample_and_temperature_binding() -> None:
    sample = _sample()
    sample["transport_measurements"][0]["sample_id"] = ""
    sample["transport_measurements"][0]["temperature_value"] = None
    fields = {issue["field"] for issue in validate_sample_consistency({"sample_records": [sample]})["issues"]}
    assert {"transport.sample_id", "transport.temperature"}.issubset(fields)

    sample = _sample()
    sample["transport_measurements"][0]["temperature_value"] = "unknown"
    report = validate_sample_consistency({"sample_records": [sample]})
    assert any(issue["severity"] == "review_required" and issue["field"] == "transport.temperature" for issue in report["issues"])


def test_transport_types_do_not_accept_resistance_or_generic_conductivity() -> None:
    sample = _sample()
    sample["transport_measurements"][0]["property_type"] = "conductivity"
    report = validate_sample_consistency({"sample_records": [sample]})
    assert any(issue["field"] == "transport.property_type" for issue in report["issues"])


def test_grain_boundary_and_electrode_interface_resistance_are_distinct() -> None:
    sample = _sample()
    sample["resistance_measurements"] = [
        {"resistance_type": "grain_boundary_resistance", "measurement_domain": "transport", "sample_id": "P1-S1"},
        {"resistance_type": "electrode_interface_resistance", "measurement_domain": "interface", "sample_id": "P1-S1"},
    ]
    assert validate_sample_consistency({"sample_records": [sample]})["valid"]
    sample["resistance_measurements"][1]["resistance_type"] = "interface_resistance"
    assert not validate_sample_consistency({"sample_records": [sample]})["valid"]


def test_resistance_domain_cannot_mix_gb_and_electrode_interface() -> None:
    sample = _sample()
    sample["resistance_measurements"] = [{
        "resistance_type": "grain_boundary_resistance", "measurement_domain": "interface", "sample_id": "P1-S1"
    }]
    report = validate_sample_consistency({"sample_records": [sample]})
    assert any(issue["field"] == "resistance.measurement_domain" for issue in report["issues"])


def test_unresolved_binding_is_review_required_and_confidence_is_lowered() -> None:
    sample = _sample("unresolved")
    sample["dopants"][0]["sample_id"] = "unresolved"
    sample["transport_measurements"][0]["sample_id"] = "unresolved"
    extraction = SampleLevelPaperExtraction(sample_records=[sample])
    assert extraction.sample_records[0]["transport_measurements"][0]["confidence"] == "medium"
    assert extraction.validation_report()["consistency"]["counts"]["review_required"] >= 1


def test_explicit_site_requires_direct_evidence() -> None:
    sample = _sample()
    sample["dopants"][0]["evidence"] = {}
    report = validate_sample_consistency({"sample_records": [sample]})
    assert any(issue["field"] == "dopant.site" for issue in report["issues"])


def test_prompt_and_parser_use_sample_level_schema() -> None:
    prompt = build_extraction_prompt("[Page 1] text")
    for rule in ("Build a sample map", "room temperature", "Blocking-electrode EIS", "nominal_formula"):
        assert rule in prompt
    payload = sample_extraction_output_template({"paper_id": "P1"})
    parsed = paper_extraction_from_dict(payload)
    assert isinstance(parsed, SampleLevelPaperExtraction)
    assert parsed.to_dict()["schema_version"] == "2.0"


def test_validation_does_not_mutate_payload_or_master_dataset(tmp_path) -> None:
    payload = {"sample_records": [_sample()]}
    before = deepcopy(payload)
    master = tmp_path / "master_dataset.csv"
    master.write_text("sample_id\nS1\n", encoding="utf-8")
    master_before = master.read_bytes()
    validate_sample_consistency(payload)
    assert payload == before
    assert master.read_bytes() == master_before


def test_b01_v2_is_distinct_from_v1_and_meets_binding_rules() -> None:
    root = Path(__file__).resolve().parents[1]
    v1_path = root / "data/raw/extraction_json/B01-0072_extraction.json"
    v2_path = root / "data/raw/extraction_json/B01-0072_extraction_v2.json"
    if not (v1_path.exists() and v2_path.exists()):
        return
    v1 = json.loads(v1_path.read_text(encoding="utf-8"))
    v2 = json.loads(v2_path.read_text(encoding="utf-8"))
    assert "sample_records" not in v1
    assert len(v2["sample_records"]) == 4
    assert validate_sample_consistency(v2)["issues"] == []
    measurements = [m for sample in v2["sample_records"] for m in sample["transport_measurements"]]
    assert measurements
    assert all(m["sample_id"] != "unresolved" for m in measurements)
    assert all(m["temperature_value"] for m in measurements if "conductivity" in m["property_type"])
