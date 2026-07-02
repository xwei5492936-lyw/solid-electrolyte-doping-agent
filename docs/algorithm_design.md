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

## Baseline Comparison

Baselines include conductivity-only ranking, composition-only models, descriptor-only models, processing-aware models, and full PERD models.

## Temporal Validation

Temporal validation trains on earlier literature and tests on later literature. This checks whether rules have extrapolative value rather than only fitting historical records.
