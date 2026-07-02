from scripts.init_database import build_seed_records


def test_seed_records_are_experimental_facts() -> None:
    records = build_seed_records()

    assert len(records) >= 2
    assert {record.evidence_type for record in records} == {"experimental_fact"}
    assert all(record.source_id for record in records)
