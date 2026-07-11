# PDF Extraction Pilot 3 Report

This report covers only priorities 1-3 from `pdf_extraction_pilot10.csv`. Extraction artifacts remain pending human review and are not included in `master_dataset.csv`.

## Summary

- Selected papers: **3**
- Processed papers (valid extraction JSON present): **1**
- Accessible papers (authorized local PDF present): **1**
- Inaccessible or access-pending papers: **2**
- Extracted non-missing fields: **9**
- Automatic database inclusion: **disabled**

## Paper Status

| Priority | Paper ID | Access status | Local PDF | Extraction JSON |
|---:|---|---|---|---|
| 1 | B01-0032 | access_pending | no | no |
| 2 | B01-0034 | access_pending | no | no |
| 3 | B01-0072 | official_oa_pdf_acquired | yes | yes |

## Extracted And Missing Fields

### B01-0032

Extraction not run; all critical fields remain pending.

### B01-0034

Extraction not run; all critical fields remain pending.

### B01-0072

- Extracted fields (9): composition.final_formula, composition.dopant_element, composition.dopant_site, composition.dopant_concentration, processing.calcination_temperature, processing.sintering_temperature, processing.sintering_time, processing.atmosphere, transport.total_conductivity
- Missing fields (8): transport.bulk_conductivity, transport.grain_boundary_conductivity, transport.activation_energy, interface.interfacial_resistance, interface.critical_current_density, interface.li_symmetric_lifetime, battery.capacity_retention, battery.cycle_number
- Evidence validation: valid

## Confidence Distribution

- All critical records in processed JSON: high: 8, medium: 1, unknown: 8

## Potential Extraction Errors

- B01-0032: OpenAlex reports closed access; no authorized local PDF was present.
- B01-0034: Publisher and OpenAlex identify gold OA/CC BY but the official PDF endpoint returned HTTP 403 in this environment.
- B01-0072: Internal PDF Title metadata is incorrect; rendered title and DOI were visually verified.

## Review Gate

No extraction has been written to the master dataset. Every non-missing value must be checked against its PDF page and source sentence using `data/review/human_validation_template.csv`.
