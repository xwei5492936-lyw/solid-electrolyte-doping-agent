# Database Fields

This document defines the manually filled PERD data tables. All real values must be traceable to a paper, supplementary file, figure estimate, or verified experiment.

## Literature Table

| Field | Meaning | Unit | Required | Notes |
|---|---|---:|---|---|
| `paper_id` | Stable local paper identifier | none | yes | Must link all sample rows to metadata. |
| `title` | Paper title | none | yes | Do not abbreviate if avoidable. |
| `doi` | DOI | none | yes | Use `unknown` only if no DOI exists. |
| `year` | Publication year | year | yes | Used for temporal validation. |
| `journal` | Journal name | none | yes | Keep raw journal name. |
| `material_family` | Electrolyte family | none | yes | Example: garnet, NASICON, sulfide. |
| `source_type` | article, review, SI, thesis, synthetic_example | none | yes | Synthetic examples are not real data. |
| `notes` | Provenance notes | none | no | Mark estimates clearly. |

## Composition Table

Required identifiers are `sample_id` and `paper_id`. Dopant fields record element, site, valence, and concentration. `confidence` must be `high`, `medium`, `low`, or `unknown`.

## Processing Table

Processing fields capture synthesis method, calcination, sintering, atmosphere, excess lithium source, density, grain size, phase, lattice parameter, and secondary phase.

## Transport Table

Transport fields separate total conductivity, bulk conductivity, grain-boundary conductivity, activation energy, electronic conductivity, EIS temperature range, and DRT availability.

## Interface Table

Interface fields capture Li contact method, interfacial resistance, critical current density, Li symmetric-cell current density, areal capacity, lifetime, temperature, and stack pressure.

## Battery Table

Battery fields capture cathode type, loading, liquid electrolyte amount, rate, cycle number, capacity, capacity retention, Coulombic efficiency, and operating temperature.
