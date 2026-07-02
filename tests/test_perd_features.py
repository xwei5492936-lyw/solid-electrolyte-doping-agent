import pandas as pd
import pytest

from perd.features import (
    BATTERY_OUTCOME_FIELDS,
    build_feature_matrix,
    create_high_conductivity_label,
    log_transform_conductivity,
    safe_log10,
)


def test_conductivity_log_transform_available() -> None:
    df = log_transform_conductivity(pd.DataFrame({"total_conductivity_25c_s_cm": [1e-3]}))
    assert df["log10_total_conductivity_25c_s_cm"].iloc[0] == safe_log10(1e-3)


def test_high_conductivity_label_available() -> None:
    df = create_high_conductivity_label(pd.DataFrame({"total_conductivity_25c_s_cm": [1e-3, 1e-6]}))
    assert df["high_conductivity"].tolist() == [1, 0]


def test_build_feature_matrix_available() -> None:
    df = pd.DataFrame(
        {
            "material_family": ["garnet"],
            "dopant_element_1": ["Ta"],
            "dopant_site_1": ["Zr"],
            "dopant_concentration_1": [0.5],
            "li_content": [6.5],
        }
    )
    X, feature_names = build_feature_matrix(df, "composition_only")
    assert len(X) == 1
    assert feature_names


def test_perd_predictive_excludes_battery_outcome_fields() -> None:
    df = pd.DataFrame(
        {
            "material_family": ["LLZO"],
            "dopant_element_1": ["Ta"],
            "dopant_site_1": ["Zr"],
            "dopant_concentration_1": [0.5],
            "li_content": [6.5],
            "li_symmetric_lifetime_h": [1000],
            "critical_current_density_ma_cm2": [0.8],
            "capacity_retention_percent": [90],
            "capacity_mah_g": [150],
            "coulombic_efficiency_percent": [99.5],
        }
    )
    _, feature_names = build_feature_matrix(df, "perd_predictive", label_column="long_lifetime")
    assert not (set(feature_names) & BATTERY_OUTCOME_FIELDS)


def test_full_chain_analysis_is_blocked_for_long_lifetime_prediction() -> None:
    df = pd.DataFrame(
        {
            "material_family": ["LLZO"],
            "dopant_element_1": ["Ta"],
            "dopant_site_1": ["Zr"],
            "dopant_concentration_1": [0.5],
            "li_content": [6.5],
            "li_symmetric_lifetime_h": [1000],
        }
    )
    with pytest.raises(ValueError, match="rule discovery only"):
        build_feature_matrix(df, "full_chain_analysis", label_column="exploratory_label")


def test_direct_lifetime_feature_is_blocked_for_long_lifetime_prediction() -> None:
    df = pd.DataFrame({"li_symmetric_lifetime_h": [1000], "dopant_concentration_1": [0.5]})
    with pytest.raises(ValueError, match="long_lifetime"):
        build_feature_matrix(df, "full_chain_analysis", label_column="long_lifetime")
