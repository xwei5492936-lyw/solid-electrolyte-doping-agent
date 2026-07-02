# Extraction Rules

## Core Rules

- Extract only values explicitly reported by the paper, supplementary information, or figure/table data.
- Mark figure-estimated values as estimated in `notes`.
- Write `unknown` for missing values.
- Do not infer unreported values.
- Record DOI, title, and year for every paper.
- Distinguish experimental fact, literature-derived inference, model prediction, and hypothesis in notes or downstream metadata.

## Conductivity Rules

- Keep total conductivity, bulk conductivity, and grain-boundary conductivity separate.
- Record temperature whenever conductivity is not reported at 25 C.
- Do not convert activation energy units unless the conversion is recorded.

## Li Symmetric-Cell Rules

- Always record current density and areal capacity with Li symmetric lifetime.
- Do not compare lifetimes without checking current density, areal capacity, temperature, and stack pressure.

## Confidence Rules

- `high`: directly reported and internally consistent.
- `medium`: reported but with minor ambiguity.
- `low`: estimated from figure or missing context.
- `unknown`: not enough information for confidence assignment.
