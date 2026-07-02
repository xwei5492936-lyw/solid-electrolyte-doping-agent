from perd.schema import COMPOSITION_FIELDS, CONFIDENCE_VALUES, get_all_schema_fields, get_required_fields


def test_schema_fields_exist() -> None:
    assert "sample_id" in COMPOSITION_FIELDS
    assert CONFIDENCE_VALUES == ("high", "medium", "low", "unknown")
    assert "battery" in get_all_schema_fields()


def test_get_required_fields_available() -> None:
    assert "paper_id" in get_required_fields("paper")
    assert "sample_id" in get_required_fields("master")
