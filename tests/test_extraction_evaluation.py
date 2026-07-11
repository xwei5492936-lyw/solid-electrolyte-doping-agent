from perd.extraction_evaluation import (
    CATEGORIES,
    calculate_extraction_accuracy,
    calculate_field_accuracy,
    compare_ai_human_values,
    generate_extraction_quality_report,
)


def test_compare_ai_human_values_handles_numbers_and_json() -> None:
    assert compare_ai_human_values("3.7e-4", 0.00037, "total_conductivity")
    assert compare_ai_human_values('{"Ga": "Li", "Nb": "Zr"}', {"Ga": "Li", "Nb": "Zr"}, "dopant_site")
    assert not compare_ai_human_values("Li6.5La3Zr1.5Ta0.5O12", "Li6.4La3Zr1.6Ta0.4O12", "final_formula")


def test_formula_and_element_comparison_is_case_sensitive() -> None:
    assert not compare_ai_human_values("Co", "CO", "dopant_element")
    assert compare_ai_human_values(" air ", "AIR", "atmosphere")


def test_calculate_field_accuracy_excludes_unreviewed_rows() -> None:
    rows = [
        {"field_name": "transport.total_conductivity", "ai_value": "0.001", "human_value": "0.001", "match": ""},
        {"field_name": "transport.total_conductivity", "ai_value": "0.002", "human_value": "0.001", "match": "false"},
        {"field_name": "transport.total_conductivity", "ai_value": "0.003", "human_value": "", "match": ""},
    ]

    result = calculate_field_accuracy(rows, "transport.total_conductivity")

    assert result["total_reviewed_fields"] == 2
    assert result["correct_fields"] == 1
    assert result["incorrect_fields"] == 1
    assert result["accuracy"] == 0.5


def test_calculate_extraction_accuracy_reports_all_categories() -> None:
    rows = [
        {"field_name": "composition.final_formula", "ai_value": "A", "human_value": "A", "match": "true"},
        {"field_name": "processing.sintering_time", "ai_value": "8", "human_value": "10", "match": "false"},
        {"field_name": "transport.activation_energy", "ai_value": "0.3", "human_value": "0.3", "match": "true"},
        {"field_name": "unsupported_field", "ai_value": "x", "human_value": "x", "match": "true"},
    ]

    result = calculate_extraction_accuracy(rows)

    assert result["total_reviewed_fields"] == 3
    assert result["correct_fields"] == 2
    assert result["accuracy"] == 2 / 3
    assert tuple(result["accuracy_by_category"]) == CATEGORIES
    assert result["accuracy_by_category"]["interface"]["accuracy"] is None


def test_empty_gold_standard_report_does_not_claim_accuracy(tmp_path) -> None:
    output = tmp_path / "quality.md"

    report = generate_extraction_quality_report([], output)

    assert "Total reviewed fields: **0**" in report
    assert "Overall accuracy: **N/A**" in report
    assert "No scientific or prompt-quality conclusion" in report
    assert output.read_text(encoding="utf-8") == report
