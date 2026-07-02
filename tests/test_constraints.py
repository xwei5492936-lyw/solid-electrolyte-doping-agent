from llzo_doping_agent.constraints import evaluate_candidate
from llzo_doping_agent.schema import CandidateScheme


def test_valid_aliovalent_zr_site_candidate_passes() -> None:
    candidate = CandidateScheme(
        material="LLZO",
        dopant="Ta",
        site="Zr",
        dopant_fraction=0.25,
        assumed_valence=5,
        host_valence=4,
    )

    result = evaluate_candidate(candidate)

    assert result.passed
    assert result.reasons == ()


def test_invalid_candidate_reports_all_reasons() -> None:
    candidate = CandidateScheme(
        material="LLZO",
        dopant="Mg",
        site="unknown",
        dopant_fraction=0,
        assumed_valence=2,
        host_valence=2,
    )

    result = evaluate_candidate(candidate)

    assert not result.passed
    assert "unsupported substitution site: unknown" in result.reasons
    assert "dopant fraction must be positive" in result.reasons
    assert "dopant valence should differ from host valence for charge compensation" in result.reasons
