# B01-0072 Machine Secondary Review

> **该结果是 machine secondary review，不是 human gold standard，不能作为最终人工准确率。**

本报告仅描述机器独立二审的一致性。下列 agreement 不得称为 human-validated accuracy。

## Review Summary

- Reviewed fields: **17**
- Correct: **13**
- Minor difference: **3**
- Incorrect: **0**
- Missing: **0**
- Unresolved: **1**
- Conflict: **0**
- Confidence: high **11**, medium **5**, low **1**
- Needs human confirmation: **5**
- Provisional strict agreement (correct only): **76.5%**
- Provisional tolerant agreement (correct + minor difference): **94.1%**

## Category Results

| Category | Fields | Correct | Minor | Incorrect | Missing | Unresolved | Conflict |
|---|---:|---:|---:|---:|---:|---:|---:|
| composition | 4 | 2 | 2 | 0 | 0 | 0 | 0 |
| processing | 4 | 4 | 0 | 0 | 0 | 0 | 0 |
| transport | 4 | 2 | 1 | 0 | 0 | 1 | 0 |
| interface | 3 | 3 | 0 | 0 | 0 | 0 | 0 |
| battery | 2 | 2 | 0 | 0 | 0 | 0 | 0 |

## Typical Issues

- `final_formula` represents a nominal composition series, not a measured final composition for one sample.
- Dopant concentration extraction omits the optimized `x = 0.2` sample context.
- The scalar conductivity value is numerically correct but does not itself preserve sample identity, room-temperature condition, and total-conductivity type.
- Activation energy was not located in the six-page article and remains unresolved pending human confirmation.
- The phrase `grain interface resistance` refers to grain/grain-boundary impedance, not an electrode/electrolyte interface metric.
- No values were estimated from figures, and no body/table/figure conflicts were found.

## Prompt Refinement Recommendations

- Require `composition_status` to distinguish nominal series, nominal sample formula, and measured composition.
- Emit one sample-scoped record per composition instead of collapsing a concentration series into one field.
- Require transport records to bind value, original and normalized units, temperature, sample formula or `x`, and total/bulk/grain-boundary type.
- Distinguish grain-boundary resistance from electrode/electrolyte interfacial resistance using the cell configuration and equivalent-circuit context.
- Record an explicit full-text `not_reported` audit for absent activation-energy, interface, and battery fields.

## Guardrails

The extraction JSON and `master_dataset.csv` were not modified. Human confirmation is required before any Gold Standard decision or database inclusion.
