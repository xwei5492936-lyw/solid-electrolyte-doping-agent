import csv
import json
from pathlib import Path

from perd.evidence import EvidenceRecord
from perd.schema import get_evidence_schema


def test_evidence_record_can_be_created() -> None:
    record = EvidenceRecord(
        field_name="total_conductivity_25c_s_cm",
        extracted_value="1.2 x 10^-3 S cm^-1",
        normalized_value=1.2e-3,
        unit="S/cm",
        source_page=6,
        source_section="Electrochemical characterization",
        source_sentence="The total ionic conductivity reached 1.2 x 10^-3 S cm^-1 at 25 C.",
        extraction_method="ai_extraction",
        confidence="high",
    )

    assert record.field_name == "total_conductivity_25c_s_cm"
    assert record.normalized_value == 1.2e-3
    assert record.confidence == "high"


def test_missing_source_page_lowers_confidence() -> None:
    record = EvidenceRecord(
        field_name="activation_energy_ev",
        extracted_value="0.28 eV",
        normalized_value=0.28,
        unit="eV",
        source_sentence="The activation energy is 0.28 eV.",
        extraction_method="ai_extraction",
        confidence="high",
    )

    assert record.source_page is None
    assert record.confidence == "medium"


def test_json_serialization_round_trip() -> None:
    record = EvidenceRecord(
        field_name="sintering_temperature_c",
        extracted_value="1150 C",
        normalized_value=1150,
        unit="C",
        source_page="S3",
        source_section="Experimental",
        source_sentence="Pellets were sintered at 1150 C for 12 h.",
        extraction_method="manual",
        confidence="high",
    )

    payload = record.to_json()
    restored = EvidenceRecord.from_dict(json.loads(payload))

    assert restored.to_dict() == record.to_dict()


def test_key_extraction_fields_have_evidence_columns() -> None:
    expected = {
        "composition": {"formula", "dopant", "dopant_site", "concentration"},
        "processing": {"sintering_temperature", "sintering_time", "atmosphere"},
        "transport": {"conductivity", "activation_energy", "bulk_conductivity", "grain_boundary_conductivity"},
        "interface": {"lifetime", "CCD", "interfacial_resistance"},
        "battery": {"cycle_number", "capacity_retention"},
    }

    for table_name, concepts in expected.items():
        schema = get_evidence_schema(table_name)
        assert set(schema) == concepts
        assert all(item["evidence_field"].endswith("_evidence") for item in schema.values())


def test_extraction_templates_include_evidence_columns() -> None:
    root = Path(__file__).resolve().parents[1]
    for table_name in ("composition", "processing", "transport", "interface", "battery"):
        template = root / "data" / "templates" / f"{table_name}_table_template.csv"
        with template.open(encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle))
        expected = {item["evidence_field"] for item in get_evidence_schema(table_name).values()}
        assert expected.issubset(header)
