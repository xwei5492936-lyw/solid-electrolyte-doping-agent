"""Human-grounded quality evaluation for PERD paper extraction."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from perd.extraction_prompt import CRITICAL_EXTRACTION_FIELDS


CATEGORIES = ("composition", "processing", "transport", "interface", "battery")
GOLD_STANDARD_FIELDS = (
    "paper_id",
    "field_name",
    "ai_value",
    "human_value",
    "match",
    "reviewer_comment",
)
TRUE_MATCH_VALUES = {"true", "1", "yes", "y", "match", "correct"}
FALSE_MATCH_VALUES = {"false", "0", "no", "n", "mismatch", "incorrect"}

FIELD_CATEGORY = {
    field_name: category
    for category, field_names in CRITICAL_EXTRACTION_FIELDS.items()
    for field_name in field_names
}


def _normalize_text(value: Any, case_sensitive: bool) -> str:
    text = unicodedata.normalize("NFKC", str(value)).strip()
    text = re.sub(r"\s+", " ", text)
    return text if case_sensitive else text.casefold()


def _parse_structured_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        try:
            return float(text)
        except ValueError:
            return value


def _values_equal(
    ai_value: Any,
    human_value: Any,
    *,
    case_sensitive: bool,
    relative_tolerance: float,
    absolute_tolerance: float,
) -> bool:
    ai_value = _parse_structured_value(ai_value)
    human_value = _parse_structured_value(human_value)

    if isinstance(ai_value, bool) or isinstance(human_value, bool):
        return ai_value is human_value
    if isinstance(ai_value, (int, float)) and isinstance(human_value, (int, float)):
        return math.isclose(
            float(ai_value),
            float(human_value),
            rel_tol=relative_tolerance,
            abs_tol=absolute_tolerance,
        )
    if isinstance(ai_value, Mapping) and isinstance(human_value, Mapping):
        if set(ai_value) != set(human_value):
            return False
        return all(
            _values_equal(
                ai_value[key],
                human_value[key],
                case_sensitive=case_sensitive,
                relative_tolerance=relative_tolerance,
                absolute_tolerance=absolute_tolerance,
            )
            for key in ai_value
        )
    if (
        isinstance(ai_value, Sequence)
        and isinstance(human_value, Sequence)
        and not isinstance(ai_value, (str, bytes))
        and not isinstance(human_value, (str, bytes))
    ):
        if len(ai_value) != len(human_value):
            return False
        return all(
            _values_equal(
                ai_item,
                human_item,
                case_sensitive=case_sensitive,
                relative_tolerance=relative_tolerance,
                absolute_tolerance=absolute_tolerance,
            )
            for ai_item, human_item in zip(ai_value, human_value)
        )
    return _normalize_text(ai_value, case_sensitive) == _normalize_text(human_value, case_sensitive)


def compare_ai_human_values(
    ai_value: Any,
    human_value: Any,
    field_name: str | None = None,
    *,
    relative_tolerance: float = 1e-6,
    absolute_tolerance: float = 1e-12,
) -> bool:
    """Compare AI and human values conservatively across text, numbers, and JSON."""

    bare_field = (field_name or "").split(".")[-1]
    case_sensitive = bare_field in {"final_formula", "dopant_element"}
    return _values_equal(
        ai_value,
        human_value,
        case_sensitive=case_sensitive,
        relative_tolerance=relative_tolerance,
        absolute_tolerance=absolute_tolerance,
    )


def _parse_match(value: Any) -> bool | None:
    normalized = str(value or "").strip().casefold()
    if normalized in TRUE_MATCH_VALUES:
        return True
    if normalized in FALSE_MATCH_VALUES:
        return False
    return None


def _has_value(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _reviewed_match(row: Mapping[str, Any]) -> bool | None:
    explicit = _parse_match(row.get("match"))
    if explicit is not None:
        return explicit
    if not (_has_value(row.get("ai_value")) and _has_value(row.get("human_value"))):
        return None
    return compare_ai_human_values(row["ai_value"], row["human_value"], str(row.get("field_name", "")))


def _field_category(field_name: str) -> str | None:
    if "." in field_name:
        prefix, bare_field = field_name.split(".", 1)
        if prefix in CATEGORIES and bare_field in CRITICAL_EXTRACTION_FIELDS[prefix]:
            return prefix
    return FIELD_CATEGORY.get(field_name)


def calculate_field_accuracy(
    rows: Iterable[Mapping[str, Any]],
    field_name: str | None = None,
) -> dict[str, Any]:
    """Calculate reviewed accuracy for one field or an arbitrary row subset."""

    reviewed: list[bool] = []
    for row in rows:
        current_field = str(row.get("field_name", "")).strip()
        if field_name is not None and current_field != field_name:
            continue
        match = _reviewed_match(row)
        if match is not None:
            reviewed.append(match)

    correct = sum(reviewed)
    total = len(reviewed)
    return {
        "field_name": field_name,
        "total_reviewed_fields": total,
        "correct_fields": correct,
        "incorrect_fields": total - correct,
        "accuracy": correct / total if total else None,
    }


def calculate_extraction_accuracy(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Calculate overall and category-level extraction accuracy."""

    records = [row for row in rows if _field_category(str(row.get("field_name", ""))) in CATEGORIES]
    overall = calculate_field_accuracy(records)
    by_category: dict[str, dict[str, Any]] = {}
    for category in CATEGORIES:
        category_rows = [row for row in records if _field_category(str(row.get("field_name", ""))) == category]
        by_category[category] = calculate_field_accuracy(category_rows)
        by_category[category]["category"] = category
    return {**overall, "accuracy_by_category": by_category}


def generate_extraction_quality_report(
    rows: Iterable[Mapping[str, Any]],
    output_path: str | Path | None = None,
) -> str:
    """Generate a Markdown quality report based only on human-reviewed fields."""

    metrics = calculate_extraction_accuracy(rows)
    accuracy = metrics["accuracy"]
    overall_display = "N/A" if accuracy is None else f"{accuracy:.1%}"
    lines = [
        "# Extraction Quality Report",
        "",
        "This report evaluates AI extraction only against human-reviewed gold-standard fields. Unreviewed rows are excluded from accuracy calculations.",
        "",
        "## Overall",
        "",
        f"- Total reviewed fields: **{metrics['total_reviewed_fields']}**",
        f"- Correct fields: **{metrics['correct_fields']}**",
        f"- Incorrect fields: **{metrics['incorrect_fields']}**",
        f"- Overall accuracy: **{overall_display}**",
        "",
        "## Accuracy By Category",
        "",
        "| Category | Reviewed | Correct | Incorrect | Accuracy |",
        "|---|---:|---:|---:|---:|",
    ]
    for category in CATEGORIES:
        result = metrics["accuracy_by_category"][category]
        category_accuracy = result["accuracy"]
        display = "N/A" if category_accuracy is None else f"{category_accuracy:.1%}"
        lines.append(
            f"| {category} | {result['total_reviewed_fields']} | {result['correct_fields']} | "
            f"{result['incorrect_fields']} | {display} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "No scientific or prompt-quality conclusion should be drawn until human-reviewed gold-standard rows are available." if metrics["total_reviewed_fields"] == 0 else "These metrics describe the reviewed subset only and may not generalize to unreviewed papers or fields.",
            "",
        ]
    )
    report = "\n".join(lines)
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
    return report


def load_gold_standard(path: str | Path) -> list[dict[str, str]]:
    """Load the extraction gold standard without inferring missing reviews."""

    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(GOLD_STANDARD_FIELDS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"gold standard is missing columns: {sorted(missing)}")
        return list(reader)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PERD extraction quality metrics.")
    parser.add_argument("--gold-standard", default="data/review/extraction_gold_standard.csv")
    parser.add_argument("--output", default="outputs/reports/extraction_quality_report.md")
    args = parser.parse_args()

    rows = load_gold_standard(args.gold_standard)
    generate_extraction_quality_report(rows, args.output)
    metrics = calculate_extraction_accuracy(rows)
    print(
        "Extraction quality: reviewed={total_reviewed_fields}, correct={correct_fields}, incorrect={incorrect_fields}".format(
            **metrics
        )
    )


if __name__ == "__main__":
    main()
