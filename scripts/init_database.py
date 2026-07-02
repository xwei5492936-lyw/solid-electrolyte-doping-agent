"""Create a small starter LLZO dopant database."""

from __future__ import annotations

from pathlib import Path

from llzo_doping_agent.schema import DopantCase
from llzo_doping_agent.storage import write_jsonl


def build_seed_records() -> list[DopantCase]:
    """Return minimal seed records for schema validation and examples."""

    return [
        DopantCase(
            material="LLZO",
            dopant="Al",
            site="Li",
            dopant_fraction=0.2,
            evidence_type="experimental_fact",
            source_id="seed-al-llzo",
            synthesis_route="solid-state",
            notes="Placeholder seed record; replace with verified literature metadata.",
        ),
        DopantCase(
            material="LLZTO",
            dopant="Ta",
            site="Zr",
            dopant_fraction=0.4,
            evidence_type="experimental_fact",
            source_id="seed-ta-llzto",
            synthesis_route="solid-state",
            notes="Placeholder seed record; replace with verified literature metadata.",
        ),
    ]


def main() -> None:
    output_path = Path("data/processed/llzo_dopant_cases.jsonl")
    write_jsonl(output_path, (record.to_dict() for record in build_seed_records()))
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
