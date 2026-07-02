"""Feature engineering utilities for PERD."""

from __future__ import annotations

import math
import warnings

import pandas as pd


def safe_log10(value) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric <= 0 or math.isnan(numeric):
        return None
    return math.log10(numeric)


def log_transform_conductivity(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    for column in [c for c in output.columns if "conductivity" in c]:
        output[f"log10_{column}"] = output[column].map(safe_log10)
    return output


def _label(df: pd.DataFrame, column: str, threshold: float, label_name: str) -> pd.DataFrame:
    output = df.copy()
    if column not in output.columns:
        warnings.warn(f"Missing column for label creation: {column}", stacklevel=2)
        output[label_name] = 0
        return output
    output[label_name] = (pd.to_numeric(output[column], errors="coerce").fillna(float("-inf")) >= threshold).astype(int)
    return output


def create_high_conductivity_label(df: pd.DataFrame, threshold: float = 1e-4) -> pd.DataFrame:
    return _label(df, "total_conductivity_25c_s_cm", threshold, "high_conductivity")


def create_very_high_conductivity_label(df: pd.DataFrame, threshold: float = 1e-3) -> pd.DataFrame:
    return _label(df, "total_conductivity_25c_s_cm", threshold, "very_high_conductivity")


def create_long_lifetime_label(df: pd.DataFrame, threshold: float = 500) -> pd.DataFrame:
    return _label(df, "li_symmetric_lifetime_h", threshold, "long_lifetime")


def create_high_ccd_label(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    return _label(df, "critical_current_density_ma_cm2", threshold, "high_ccd")


def create_co_doping_flag(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    if "co_doping_flag" in output.columns:
        output["co_doping_flag_numeric"] = output["co_doping_flag"].astype(str).str.lower().isin(["true", "1", "yes"]).astype(int)
    elif "dopant_element_2" in output.columns:
        output["co_doping_flag_numeric"] = (~output["dopant_element_2"].fillna("").astype(str).str.lower().isin(["", "unknown", "nan"])).astype(int)
    else:
        warnings.warn("Missing co-doping columns; using 0 for co_doping_flag_numeric", stacklevel=2)
        output["co_doping_flag_numeric"] = 0
    return output


def estimate_valence_difference(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    if {"dopant_valence_1", "dopant_site_1"}.issubset(output.columns):
        dopant_valence = pd.to_numeric(output["dopant_valence_1"], errors="coerce")
        site_valence = output["dopant_site_1"].map({"Li": 1, "La": 3, "Zr": 4, "O": -2})
        output["estimated_valence_difference"] = (dopant_valence - site_valence).fillna(0)
    else:
        warnings.warn("Missing valence/site columns; using 0 for estimated_valence_difference", stacklevel=2)
        output["estimated_valence_difference"] = 0
    return output


def build_feature_matrix(df: pd.DataFrame, feature_set: str):
    """Build feature matrix for a named PERD feature set."""

    output = log_transform_conductivity(create_co_doping_flag(estimate_valence_difference(df.copy())))
    numeric_by_set = {
        "composition_only": ["dopant_concentration_1", "dopant_concentration_2", "li_content", "co_doping_flag_numeric", "estimated_valence_difference"],
        "descriptor_only": ["dopant_concentration_1", "dopant_concentration_2", "li_content", "estimated_valence_difference"],
        "processing_aware": ["dopant_concentration_1", "dopant_concentration_2", "li_content", "relative_density_percent", "sintering_temperature_c", "sintering_time_h"],
        "transport_aware": ["dopant_concentration_1", "log10_total_conductivity_25c_s_cm", "log10_gb_conductivity_25c_s_cm", "activation_energy_ev"],
        "full_perd": [
            "dopant_concentration_1",
            "dopant_concentration_2",
            "li_content",
            "co_doping_flag_numeric",
            "estimated_valence_difference",
            "relative_density_percent",
            "sintering_temperature_c",
            "sintering_time_h",
            "log10_total_conductivity_25c_s_cm",
            "log10_gb_conductivity_25c_s_cm",
            "activation_energy_ev",
            "interfacial_resistance_ohm_cm2",
            "critical_current_density_ma_cm2",
            "li_symmetric_lifetime_h",
            "capacity_retention_percent",
        ],
    }
    categorical_by_set = {
        "composition_only": ["material_family", "dopant_element_1", "dopant_site_1"],
        "descriptor_only": ["material_family", "dopant_element_1", "dopant_site_1", "charge_compensation_type"],
        "processing_aware": ["material_family", "dopant_element_1", "synthesis_method", "atmosphere", "phase"],
        "transport_aware": ["material_family", "dopant_element_1", "phase"],
        "full_perd": ["material_family", "dopant_element_1", "dopant_site_1", "synthesis_method", "atmosphere", "phase", "cathode_type"],
    }
    if feature_set not in numeric_by_set:
        raise ValueError(f"Unsupported feature_set: {feature_set}")

    feature_parts: list[pd.DataFrame] = []
    for column in numeric_by_set[feature_set]:
        if column not in output.columns:
            warnings.warn(f"Missing numeric feature: {column}; filling with 0", stacklevel=2)
            output[column] = 0
        feature_parts.append(pd.to_numeric(output[column], errors="coerce").fillna(0).to_frame(column))

    for column in categorical_by_set[feature_set]:
        if column not in output.columns:
            warnings.warn(f"Missing categorical feature: {column}; filling with unknown", stacklevel=2)
            output[column] = "unknown"
        encoded = pd.get_dummies(output[column].fillna("unknown").astype(str), prefix=column, dtype=float)
        feature_parts.append(encoded)

    X = pd.concat(feature_parts, axis=1) if feature_parts else pd.DataFrame(index=output.index)
    return X, list(X.columns)
