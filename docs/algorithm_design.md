# Algorithm Design

## Why Conductivity Alone Is Not Enough

Ionic conductivity is important, but practical battery behavior also depends on phase stability, processing density, grain-boundary transport, interface impedance, Li symmetric-cell stability, cathode compatibility, and evidence quality.

## PERD Data Chain

PERD uses a composition-processing-transport-interface-battery chain:

```text
composition -> processing -> structure/transport -> interface -> battery performance
```

This chain allows the project to ask which dopant rules transfer from electrolyte properties to cell-level outcomes.

## BPRS Definition

BPRS is the first rule-based scoring algorithm:

```text
BPRS =
0.20 * phase_score
+ 0.20 * transport_score
+ 0.20 * grain_boundary_score
+ 0.20 * interface_score
+ 0.10 * processing_score
+ 0.10 * evidence_score
```

All sub-scores are constrained to 0-1.

## Predictive and Analysis Feature Modes

PERD separates predictive feature sets from full-chain analysis features.

Predictive feature sets are used for supervised models:

- `composition_only`
- `descriptor_only`
- `processing_aware`
- `structure_transport_aware`
- `perd_predictive`

These modes must not use battery outcome fields that are only known after cell testing, including `li_symmetric_lifetime_h`, `critical_current_density_ma_cm2`, `capacity_retention_percent`, `capacity_mah_g`, and `coulombic_efficiency_percent`. If the label is derived from one of these outcomes, feeding that same outcome back as an input would create data leakage and overstate model performance.

`full_chain_analysis` is reserved for correlation analysis, visualization, and rule discovery across composition, processing, transport, interface, and battery performance. It is not used to train supervised models for labels that are directly derived from the same downstream outcome fields.

## Baseline Comparison

Baselines include conductivity-only ranking, composition-only models, descriptor-only models, processing-aware models, structure/transport-aware models, and PERD predictive models.

## Temporal Validation

Temporal validation trains on earlier literature and tests on later literature. This checks whether rules have extrapolative value rather than only fitting historical records.
