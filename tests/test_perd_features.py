import pandas as pd

from perd.features import build_feature_matrix, create_high_conductivity_label, log_transform_conductivity, safe_log10


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
