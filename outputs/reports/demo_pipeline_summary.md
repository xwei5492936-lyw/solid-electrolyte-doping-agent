# Demo PERD Pipeline Summary

This report summarizes a full PERD demonstration run on a fully synthetic/fictitious dataset. The data are for software demonstration only and are not real literature or experimental records.

## Dataset

- Samples: 30
- Material families:
  - LLZO: 10
  - LLZTO: 10
  - NASICON: 5
  - sulfide: 5
- Synthetic BPRS classes:
  - high: 10
  - medium: 10
  - low: 10
- Validation status: True
- Extraction completeness: complete=24, incomplete=6

## BPRS Top 5 Candidates

| rank | sample_id | material_family | synthetic_class | bprs_score |
|---:|---|---|---|---:|
| 1 | synthetic-sample-004 | LLZO | high | 0.973833 |
| 2 | synthetic-sample-008 | LLZO | high | 0.969167 |
| 3 | synthetic-sample-007 | LLZO | high | 0.966500 |
| 4 | synthetic-sample-003 | LLZO | high | 0.965500 |
| 5 | synthetic-sample-010 | LLZO | high | 0.962833 |

## Baseline Model Results

- conductivity_only_ranking top_k_hit_rate: 1.000
- composition_only: accuracy=0.889, precision=0.800, recall=1.000, f1=0.889, roc_auc=0.900
- descriptor_only: accuracy=0.889, precision=0.800, recall=1.000, f1=0.889, roc_auc=1.000
- processing_aware: accuracy=1.000, precision=1.000, recall=1.000, f1=1.000, roc_auc=1.000
- full_perd: accuracy=1.000, precision=1.000, recall=1.000, f1=1.000, roc_auc=1.000

## Temporal Validation Results

- composition_only: accuracy=0.917, precision=1.000, recall=0.800, f1=0.889, roc_auc=1.000, top_k_hit_rate=1.000
- processing_aware: accuracy=1.000, precision=1.000, recall=1.000, f1=1.000, roc_auc=1.000, top_k_hit_rate=1.000
- transport_aware: accuracy=0.917, precision=1.000, recall=0.800, f1=0.889, roc_auc=0.971, top_k_hit_rate=1.000
- full_perd: accuracy=0.917, precision=1.000, recall=0.800, f1=0.889, roc_auc=1.000, top_k_hit_rate=1.000

## Generated Reports

- `outputs/reports/baseline_metrics.json`
- `outputs/reports/extraction_completeness_report.json`
- `outputs/reports/figure_generation_report.json`
- `outputs/reports/temporal_validation_results.json`
- `outputs/reports/validation_report.json`

## Generated Tables

- `outputs/tables/ranked_candidates.csv`

## Generated Figures

- `outputs/figures/bprs_vs_conductivity.png`
- `outputs/figures/candidate_map.png`
- `outputs/figures/conductivity_distribution.png`
- `outputs/figures/conductivity_vs_lifetime.png`
- `outputs/figures/dopant_distribution.png`

## No-Overclaim Statement

This synthetic dataset cannot be used for scientific conclusions. The apparent model performance and BPRS ranking behavior are consequences of deliberately constructed fictitious demonstration data. Claims that PERD/BPRS outperforms existing methods require a real curated literature database, baseline comparisons, temporal validation on real records, and external experimental validation.
