# Database Fields

This document defines the manually filled PERD data tables. All real values must be traceable to a paper, supplementary file, figure estimate, or verified experiment.

## Priority Labels

- `required`: needed for joins, provenance, validation, or core PERD/BPRS scoring.
- `recommended`: strongly useful for interpretation, baseline comparison, or experimental planning.
- `optional`: useful when available, but downstream scripts should tolerate absence.

## Literature Table

| Field | Meaning | Unit | Priority | Notes |
|---|---|---:|---|---|
| `paper_id` | Stable local paper identifier | none | required | Must link all sample rows to metadata. |
| `title` | Paper title | none | required | Do not abbreviate if avoidable. |
| `doi` | DOI | none | required | Use `unknown` only if no DOI exists. |
| `year` | Publication year | year | required | Used for temporal validation. |
| `journal` | Journal name | none | recommended | Keep raw journal name. |
| `material_family` | Electrolyte family | none | required | Example: garnet, NASICON, sulfide. |
| `source_type` | article, review, SI, thesis, synthetic_example | none | recommended | Synthetic examples are not real data. |
| `notes` | Provenance notes | none | optional | Mark estimates clearly. |

## Composition Table

| Field | Meaning | Unit | Priority | Notes |
|---|---|---:|---|---|
| `sample_id` | Stable local sample identifier | none | required | One row per distinct electrolyte sample. |
| `paper_id` | Linked source paper identifier | none | required | Must match literature table. |
| `base_formula` | Undoped or parent formula | none | recommended | Use `unknown` if absent. |
| `final_formula` | Reported final doped formula | none | required | Core completeness field. |
| `material_family` | Electrolyte family | none | required | LLZO/LLZTO, NASICON, sulfide, etc. |
| `dopant_element_1` | Primary dopant element | none | required | Core completeness field. |
| `dopant_site_1` | Primary substitution site | none | required | Core completeness field. |
| `dopant_valence_1` | Primary dopant valence | none | recommended | Mark inference in notes if not reported. |
| `dopant_concentration_1` | Primary dopant concentration | formula/site fraction | recommended | Preserve original basis in notes if needed. |
| `dopant_element_2` | Secondary dopant element | none | optional | Use `unknown` if none. |
| `dopant_site_2` | Secondary substitution site | none | optional | Use `unknown` if none. |
| `dopant_valence_2` | Secondary dopant valence | none | optional | Mark inference if needed. |
| `dopant_concentration_2` | Secondary dopant concentration | formula/site fraction | optional | Use 0 if no co-doping. |
| `co_doping_flag` | Whether co-doped | boolean | recommended | true/false preferred. |
| `li_content` | Lithium content in formula | formula units | recommended | Useful for charge balance. |
| `charge_compensation_type` | Charge compensation description | none | optional | Experimental or inferred. |
| `confidence` | Extraction confidence | none | required | high, medium, low, unknown. |

## Processing Table

| Field | Meaning | Unit | Priority | Notes |
|---|---|---:|---|---|
| `sample_id` | Linked sample identifier | none | required | Must match composition table. |
| `synthesis_method` | Synthesis route | none | recommended | Solid-state, sol-gel, mechanochemical, etc. |
| `calcination_temperature_c` | Calcination temperature | C | optional | Use `unknown` if absent. |
| `calcination_time_h` | Calcination time | h | optional | Use `unknown` if absent. |
| `sintering_temperature_c` | Sintering temperature | C | required | Core completeness field. |
| `sintering_time_h` | Sintering time | h | recommended | Processing context. |
| `atmosphere` | Processing atmosphere | none | recommended | air, O2, Ar, vacuum, etc. |
| `excess_lithium_source` | Lithium excess source | none | optional | Useful for LLZO. |
| `mother_powder` | Mother powder / packing powder | none | optional | Useful for Li loss control. |
| `relative_density_percent` | Relative density | % | recommended | Used by grain-boundary score. |
| `grain_size_um` | Grain size | um | optional | SEM-derived if available. |
| `phase` | Reported phase | none | required | Core completeness field. |
| `lattice_parameter_a` | Lattice parameter a | angstrom | optional | Family-dependent. |
| `secondary_phase` | Secondary phase | none | recommended | Use `none reported` if explicit. |
| `confidence` | Extraction confidence | none | required | high, medium, low, unknown. |

## Transport Table

| Field | Meaning | Unit | Priority | Notes |
|---|---|---:|---|---|
| `sample_id` | Linked sample identifier | none | required | Must match composition table. |
| `total_conductivity_25c_s_cm` | Total ionic conductivity at 25 C | S/cm | required | Core completeness field. |
| `bulk_conductivity_25c_s_cm` | Bulk conductivity at 25 C | S/cm | recommended | Keep separate from total. |
| `gb_conductivity_25c_s_cm` | Grain-boundary conductivity at 25 C | S/cm | recommended | Used by grain-boundary score. |
| `activation_energy_ev` | Activation energy | eV | required | Core completeness field. |
| `electronic_conductivity_s_cm` | Electronic conductivity | S/cm | optional | Important for stability if reported. |
| `eis_temperature_range` | EIS temperature range | C | recommended | Needed when conductivity is temperature-dependent. |
| `drt_available` | Whether DRT analysis is available | boolean | optional | true/false preferred. |
| `confidence` | Extraction confidence | none | required | high, medium, low, unknown. |

## Interface Table

| Field | Meaning | Unit | Priority | Notes |
|---|---|---:|---|---|
| `sample_id` | Linked sample identifier | none | required | Must match composition table. |
| `li_contact_method` | Li contact preparation | none | recommended | Polished pellet, molten Li, coating, etc. |
| `interfacial_resistance_ohm_cm2` | Li interface resistance | ohm cm2 | recommended | Used by interface score. |
| `critical_current_density_ma_cm2` | Critical current density | mA/cm2 | recommended | Used by interface score. |
| `li_symmetric_current_density_ma_cm2` | Li symmetric-cell current density | mA/cm2 | recommended | Required context for lifetime. |
| `li_symmetric_areal_capacity_mah_cm2` | Li symmetric-cell areal capacity | mAh/cm2 | recommended | Required context for lifetime. |
| `li_symmetric_lifetime_h` | Li symmetric-cell lifetime | h | required | Core completeness field. |
| `cycling_temperature_c` | Cycling temperature | C | recommended | Context for interface metrics. |
| `stack_pressure_mpa` | Stack pressure | MPa | recommended | Context for interface metrics. |
| `confidence` | Extraction confidence | none | required | high, medium, low, unknown. |

## Battery Table

| Field | Meaning | Unit | Priority | Notes |
|---|---|---:|---|---|
| `sample_id` | Linked sample identifier | none | required | Must match composition table. |
| `cathode_type` | Cathode chemistry | none | recommended | NCM, LFP, LCO, etc. |
| `cathode_loading_mg_cm2` | Cathode loading | mg/cm2 | recommended | Needed for practical comparison. |
| `liquid_electrolyte_amount_ul` | Added liquid electrolyte | uL | recommended | 0 for all-solid-state if reported. |
| `cycling_rate` | Cycling rate | C-rate or current | recommended | Keep original notation. |
| `cycle_number` | Reported cycle count | cycles | recommended | Context for retention. |
| `capacity_mah_g` | Specific capacity | mAh/g | recommended | Record basis in notes if different. |
| `capacity_retention_percent` | Capacity retention | % | recommended | Battery-performance target. |
| `coulombic_efficiency_percent` | Coulombic efficiency | % | optional | Useful if available. |
| `operating_temperature_c` | Cell operating temperature | C | recommended | Context for performance. |
| `confidence` | Extraction confidence | none | required | high, medium, low, unknown. |
