"""Validation and reporting helpers for independent machine secondary review."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


MATCH_STATUSES = {
    "correct",
    "minor_difference",
    "incorrect",
    "missing",
    "unresolved",
    "conflict",
}
VERIFICATION_METHODS = {
    "body_text",
    "table",
    "figure_caption",
    "estimated_from_figure",
    "supplementary",
    "not_found",
}
REVIEW_CONFIDENCES = {"high", "medium", "low"}
QUEUE_STATUSES = {"incorrect", "missing", "unresolved", "conflict"}
CATEGORIES = ("composition", "processing", "transport", "interface", "battery")

MACHINE_REVIEW_FIELDS = (
    "paper_id",
    "category",
    "field_name",
    "ai_value",
    "machine_verified_value",
    "match_status",
    "review_comment",
    "evidence_page",
    "evidence_location",
    "evidence_sentence",
    "verification_method",
    "review_confidence",
    "needs_human_review",
)


def _is_true(value: Any) -> bool:
    return str(value).strip().casefold() == "true"


def validate_machine_reviews(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Validate review enums and evidence requirements without changing source data."""

    records = [dict(row) for row in rows]
    for index, row in enumerate(records, start=2):
        missing = [field for field in MACHINE_REVIEW_FIELDS if field not in row]
        if missing:
            raise ValueError(f"row {index} is missing columns: {missing}")
        if row["category"] not in CATEGORIES:
            raise ValueError(f"row {index} has invalid category: {row['category']}")
        if row["match_status"] not in MATCH_STATUSES:
            raise ValueError(f"row {index} has invalid match_status: {row['match_status']}")
        if row["verification_method"] not in VERIFICATION_METHODS:
            raise ValueError(f"row {index} has invalid verification_method: {row['verification_method']}")
        if row["review_confidence"] not in REVIEW_CONFIDENCES:
            raise ValueError(f"row {index} has invalid review_confidence: {row['review_confidence']}")
        if str(row["needs_human_review"]).strip().casefold() not in {"true", "false"}:
            raise ValueError(f"row {index} has invalid needs_human_review")
        if row["match_status"] != "unresolved" and not str(row["evidence_page"]).strip():
            raise ValueError(f"row {index} requires an evidence_page")
    return records


def requires_human_review(row: Mapping[str, Any]) -> bool:
    """Return whether a secondary-review result belongs in the human queue."""

    return (
        row.get("match_status") in QUEUE_STATUSES
        or row.get("review_confidence") == "low"
        or _is_true(row.get("needs_human_review"))
    )


def build_human_review_queue(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    """Build a compact queue containing only decisions that require a human."""

    queue = []
    for row in validate_machine_reviews(rows):
        if not requires_human_review(row):
            continue
        queue.append(
            {
                "paper_id": str(row["paper_id"]),
                "field_name": str(row["field_name"]),
                "ai_value": str(row["ai_value"]),
                "machine_verified_value": str(row["machine_verified_value"]),
                "issue_type": str(row["match_status"]),
                "evidence_page": str(row["evidence_page"]),
                "evidence_sentence": str(row["evidence_sentence"]),
                "question_for_human": str(row.get("question_for_human", "")),
            }
        )
    return queue


def summarize_machine_reviews(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Calculate provisional machine agreement metrics and category counts."""

    records = validate_machine_reviews(rows)
    statuses = Counter(row["match_status"] for row in records)
    confidences = Counter(row["review_confidence"] for row in records)
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    for row in records:
        by_category[row["category"]][row["match_status"]] += 1
    total = len(records)
    correct = statuses["correct"]
    tolerant = correct + statuses["minor_difference"]
    return {
        "total": total,
        "statuses": statuses,
        "confidences": confidences,
        "human_review_count": sum(requires_human_review(row) for row in records),
        "by_category": {category: by_category[category] for category in CATEGORIES},
        "strict_agreement": correct / total if total else None,
        "tolerant_agreement": tolerant / total if total else None,
    }


def load_machine_review(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return validate_machine_reviews(rows)


def generate_machine_review_report(
    rows: Iterable[Mapping[str, Any]], output_path: str | Path | None = None
) -> str:
    """Generate a report that explicitly remains separate from human validation."""

    metrics = summarize_machine_reviews(rows)
    statuses = metrics["statuses"]
    confidences = metrics["confidences"]
    lines = [
        "# B01-0072 Machine Secondary Review",
        "",
        "> **该结果是 machine secondary review，不是 human gold standard，不能作为最终人工准确率。**",
        "",
        "本报告仅描述机器独立二审的一致性。下列 agreement 不得称为 human-validated accuracy。",
        "",
        "## Review Summary",
        "",
        f"- Reviewed fields: **{metrics['total']}**",
        f"- Correct: **{statuses['correct']}**",
        f"- Minor difference: **{statuses['minor_difference']}**",
        f"- Incorrect: **{statuses['incorrect']}**",
        f"- Missing: **{statuses['missing']}**",
        f"- Unresolved: **{statuses['unresolved']}**",
        f"- Conflict: **{statuses['conflict']}**",
        f"- Confidence: high **{confidences['high']}**, medium **{confidences['medium']}**, low **{confidences['low']}**",
        f"- Needs human confirmation: **{metrics['human_review_count']}**",
        f"- Provisional strict agreement (correct only): **{metrics['strict_agreement']:.1%}**",
        f"- Provisional tolerant agreement (correct + minor difference): **{metrics['tolerant_agreement']:.1%}**",
        "",
        "## Category Results",
        "",
        "| Category | Fields | Correct | Minor | Incorrect | Missing | Unresolved | Conflict |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for category in CATEGORIES:
        counts = metrics["by_category"][category]
        category_total = sum(counts.values())
        lines.append(
            f"| {category} | {category_total} | {counts['correct']} | {counts['minor_difference']} | "
            f"{counts['incorrect']} | {counts['missing']} | {counts['unresolved']} | {counts['conflict']} |"
        )
    lines.extend(
        [
            "",
            "## Typical Issues",
            "",
            "- `final_formula` represents a nominal composition series, not a measured final composition for one sample.",
            "- Dopant concentration extraction omits the optimized `x = 0.2` sample context.",
            "- The scalar conductivity value is numerically correct but does not itself preserve sample identity, room-temperature condition, and total-conductivity type.",
            "- Activation energy was not located in the six-page article and remains unresolved pending human confirmation.",
            "- The phrase `grain interface resistance` refers to grain/grain-boundary impedance, not an electrode/electrolyte interface metric.",
            "- No values were estimated from figures, and no body/table/figure conflicts were found.",
            "",
            "## Prompt Refinement Recommendations",
            "",
            "- Require `composition_status` to distinguish nominal series, nominal sample formula, and measured composition.",
            "- Emit one sample-scoped record per composition instead of collapsing a concentration series into one field.",
            "- Require transport records to bind value, original and normalized units, temperature, sample formula or `x`, and total/bulk/grain-boundary type.",
            "- Distinguish grain-boundary resistance from electrode/electrolyte interfacial resistance using the cell configuration and equivalent-circuit context.",
            "- Record an explicit full-text `not_reported` audit for absent activation-energy, interface, and battery fields.",
            "",
            "## Guardrails",
            "",
            "The extraction JSON and `master_dataset.csv` were not modified. Human confirmation is required before any Gold Standard decision or database inclusion.",
            "",
        ]
    )
    report = "\n".join(lines)
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
    return report
