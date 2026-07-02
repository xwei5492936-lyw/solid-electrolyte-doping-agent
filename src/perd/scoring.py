"""Rule-based PERD/BPRS candidate scoring."""

from __future__ import annotations

import pandas as pd

CONFIDENCE_WEIGHTS = {"high": 1.0, "medium": 0.7, "low": 0.4, "unknown": 0.2}


def _num(row, field: str, default: float | None = None) -> float | None:
    try:
        value = row.get(field, default)
    except AttributeError:
        value = row[field] if field in row else default
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clip(value: float) -> float:
    return max(0.0, min(1.0, value))


def phase_score(row) -> float:
    phase = str(row.get("phase", "unknown")).strip().lower()
    if "cubic" in phase:
        return 1.0
    if "mixed" in phase:
        return 0.6
    if "tetragonal" in phase:
        return 0.3
    return 0.2


def transport_score(row) -> float:
    total = _num(row, "total_conductivity_25c_s_cm", 0.0) or 0.0
    activation = _num(row, "activation_energy_ev", None)
    conductivity_component = _clip(total / 1e-3)
    activation_component = 0.5 if activation is None else _clip((0.6 - activation) / 0.4)
    return round(0.7 * conductivity_component + 0.3 * activation_component, 6)


def grain_boundary_score(row) -> float:
    density = _num(row, "relative_density_percent", None)
    gb = _num(row, "gb_conductivity_25c_s_cm", 0.0) or 0.0
    density_component = 0.3 if density is None else _clip((density - 70.0) / 25.0)
    gb_component = _clip(gb / 5e-4)
    return round(0.5 * density_component + 0.5 * gb_component, 6)


def interface_score(row) -> float:
    lifetime = _num(row, "li_symmetric_lifetime_h", 0.0) or 0.0
    ccd = _num(row, "critical_current_density_ma_cm2", 0.0) or 0.0
    resistance = _num(row, "interfacial_resistance_ohm_cm2", None)
    lifetime_component = _clip(lifetime / 1000.0)
    ccd_component = _clip(ccd / 1.0)
    resistance_component = 0.3 if resistance is None else _clip((200.0 - resistance) / 200.0)
    return round((lifetime_component + ccd_component + resistance_component) / 3.0, 6)


def processing_score(row) -> float:
    density = _num(row, "relative_density_percent", None)
    phase = phase_score(row)
    density_component = 0.3 if density is None else _clip((density - 70.0) / 25.0)
    return round(0.6 * density_component + 0.4 * phase, 6)


def evidence_score(row) -> float:
    confidence = str(row.get("confidence", "unknown")).strip().lower()
    base = CONFIDENCE_WEIGHTS.get(confidence, 0.0)
    key_fields = [
        "phase",
        "total_conductivity_25c_s_cm",
        "relative_density_percent",
        "li_symmetric_lifetime_h",
        "critical_current_density_ma_cm2",
        "confidence",
    ]
    present = sum(1 for field in key_fields if row.get(field, None) not in [None, "", "unknown"])
    completeness = present / len(key_fields)
    return round(0.6 * base + 0.4 * completeness, 6)


def calculate_bprs(row) -> dict:
    scores = {
        "phase_score": phase_score(row),
        "transport_score": transport_score(row),
        "grain_boundary_score": grain_boundary_score(row),
        "interface_score": interface_score(row),
        "processing_score": processing_score(row),
        "evidence_score": evidence_score(row),
    }
    bprs = (
        0.20 * scores["phase_score"]
        + 0.20 * scores["transport_score"]
        + 0.20 * scores["grain_boundary_score"]
        + 0.20 * scores["interface_score"]
        + 0.10 * scores["processing_score"]
        + 0.10 * scores["evidence_score"]
    )
    missing = [field for field in ["total_conductivity_25c_s_cm", "li_symmetric_lifetime_h", "confidence"] if row.get(field, None) in [None, "", "unknown"]]
    notes = "complete key scoring fields" if not missing else "missing key fields: " + ", ".join(missing)
    return {**scores, "bprs_score": round(bprs, 6), "score_notes": notes}


def add_bprs_scores(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    if output.empty:
        return output.assign(bprs_score=pd.Series(dtype=float), score_notes=pd.Series(dtype=str))
    score_rows = output.apply(lambda row: pd.Series(calculate_bprs(row)), axis=1)
    return pd.concat([output.reset_index(drop=True), score_rows.reset_index(drop=True)], axis=1)


def rank_candidates(df: pd.DataFrame) -> pd.DataFrame:
    scored = add_bprs_scores(df)
    if "bprs_score" not in scored.columns:
        return scored
    return scored.sort_values("bprs_score", ascending=False).reset_index(drop=True)
