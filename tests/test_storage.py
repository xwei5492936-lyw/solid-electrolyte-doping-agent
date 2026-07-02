from llzo_doping_agent.schema import DopantCase
from llzo_doping_agent.storage import load_jsonl, write_jsonl


def test_write_and_load_jsonl_round_trip(tmp_path) -> None:
    record = DopantCase(
        material="LLZTO",
        dopant="Ta",
        site="Zr",
        dopant_fraction=0.4,
        evidence_type="experimental_fact",
        source_id="doi:example",
        conductivity_s_cm=1.0e-3,
    )
    output_path = tmp_path / "records.jsonl"

    write_jsonl(output_path, [record.to_dict()])

    rows = load_jsonl(output_path)
    assert rows == [record.to_dict()]
