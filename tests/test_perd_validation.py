import pandas as pd

from perd.validation import validate_confidence_values, validate_dataset, validate_required_columns, validate_year_range


def test_missing_fields_are_detected() -> None:
    result = validate_required_columns(pd.DataFrame({"sample_id": ["s1"]}), ["sample_id", "paper_id"])
    assert not result["valid"]
    assert result["errors"][0]["field"] == "paper_id"


def test_invalid_confidence_is_detected() -> None:
    result = validate_confidence_values(pd.DataFrame({"confidence": ["certain"]}))
    assert not result["valid"]
    assert result["errors"][0]["field"] == "confidence"


def test_year_range_check_available() -> None:
    result = validate_year_range(pd.DataFrame({"year": [1980]}))
    assert result["valid"]
    assert result["warnings"][0]["field"] == "year"


def test_validate_dataset_combines_checks() -> None:
    result = validate_dataset(pd.DataFrame({"year": [1980], "confidence": ["bad"]}), ["sample_id"])
    assert not result["valid"]
    assert result["errors"]
    assert result["warnings"]
