import pandas as pd

from perd.scoring import evidence_score, interface_score, phase_score, rank_candidates, transport_score


def test_cubic_phase_scores_higher_than_tetragonal() -> None:
    assert phase_score({"phase": "cubic"}) > phase_score({"phase": "tetragonal"})


def test_higher_conductivity_gives_higher_transport_score() -> None:
    low = transport_score({"total_conductivity_25c_s_cm": 1e-6, "activation_energy_ev": 0.4})
    high = transport_score({"total_conductivity_25c_s_cm": 1e-3, "activation_energy_ev": 0.4})
    assert high > low


def test_longer_li_symmetric_lifetime_gives_higher_interface_score() -> None:
    short = interface_score({"li_symmetric_lifetime_h": 10, "critical_current_density_ma_cm2": 0.1})
    long = interface_score({"li_symmetric_lifetime_h": 1000, "critical_current_density_ma_cm2": 0.1})
    assert long > short


def test_complete_data_gets_higher_evidence_score() -> None:
    incomplete = evidence_score({"confidence": "unknown"})
    complete = evidence_score(
        {
            "confidence": "high",
            "phase": "cubic",
            "total_conductivity_25c_s_cm": 1e-3,
            "relative_density_percent": 95,
            "li_symmetric_lifetime_h": 1000,
            "critical_current_density_ma_cm2": 1.0,
        }
    )
    assert complete > incomplete


def test_rank_candidates_sorts_by_bprs() -> None:
    df = pd.DataFrame(
        [
            {"sample_id": "bad", "phase": "tetragonal", "total_conductivity_25c_s_cm": 1e-6, "confidence": "low"},
            {
                "sample_id": "good",
                "phase": "cubic",
                "total_conductivity_25c_s_cm": 1e-3,
                "relative_density_percent": 95,
                "li_symmetric_lifetime_h": 1000,
                "critical_current_density_ma_cm2": 1.0,
                "confidence": "high",
            },
        ]
    )
    ranked = rank_candidates(df)
    assert ranked["sample_id"].iloc[0] == "good"
