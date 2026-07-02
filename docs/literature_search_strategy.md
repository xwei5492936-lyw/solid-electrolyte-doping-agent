# Literature Search Strategy

This workflow builds a public-metadata candidate pool for PERD literature curation. It is designed for batch discovery, manual screening, and later extraction into the structured PERD database.

## Guardrails

- Use public metadata APIs such as OpenAlex, Crossref, Semantic Scholar, or arXiv.
- Do not scrape Google Scholar.
- Do not download or commit publisher PDFs.
- Do not store API keys in the repository.
- Treat every result as a candidate until a human reviewer screens it.

## Candidate Fields

Each candidate record uses the following schema:

`candidate_id, batch_id, title, normalized_title, doi, year, journal, authors, abstract, keywords, relevance_score, exclusion_hint, material_family_guess, topic_tags, query_used, source_api, source_url, openalex_id, semantic_scholar_id, crossref_id, arxiv_id, citation_count, is_open_access, retrieved_date, screening_status, screening_decision, screening_reason, notes`

`screening_status` starts as `unreviewed`. Reviewers later fill `screening_decision`, `screening_reason`, and `notes`.

`relevance_score` is a 0-1 metadata-only heuristic. It rewards LLZO/LLZTO/garnet/Li7La3Zr2O12 mentions, doping language, conductivity/activation-energy terms, cell-performance terms, and solid-electrolyte wording. `exclusion_hint` flags likely non-target records such as `polymer_only`, `liquid_electrolyte_only`, `electrode_only`, or `review_only`; reviewers should treat it as a triage hint rather than an automatic exclusion.

## Batch Scope

### Batch 1: LLZO/LLZTO Pilot Discovery

Target: 100 raw candidates.

Batch 1 targets LLZO/LLZTO garnet electrolyte doping and battery-performance-linked studies. The queries are:

- LLZO doped ionic conductivity
- LLZTO garnet electrolyte doping
- Ta doped LLZO conductivity
- Nb doped LLZO solid electrolyte
- Ga doped LLZO
- Al doped LLZO
- Ca doped LLZO
- Sr doped LLZO
- co-doped LLZO garnet solid electrolyte
- garnet solid electrolyte lithium symmetric cell

### Batch 2: Garnet Expansion

Target: 400 raw candidates.

Batch 2 expands within garnet-type solid electrolytes across composition, processing, transport, interface, and battery-performance topics. The queries are:

- garnet-type solid electrolyte dopant
- Li7La3Zr2O12 doping
- garnet electrolyte co-doping
- LLZO grain boundary conductivity dopant
- LLZO activation energy doped
- LLZO critical current density doped
- LLZO lithium metal interface doped
- LLZO full cell doped solid electrolyte
- garnet solid electrolyte processing density conductivity
- garnet electrolyte sintering dopant conductivity

### Batch 3: External Validation Families

Target: 500 raw candidates.

Batch 3 expands beyond garnet materials to NASICON, sulfide, halide, and broader data-driven solid electrolyte discovery. This batch is intended for external validation and transferability checks. The queries are:

- NASICON solid electrolyte doping ionic conductivity
- LATP doping solid electrolyte conductivity
- LAGP doping solid electrolyte conductivity
- sulfide solid electrolyte doping lithium conductivity
- argyrodite solid electrolyte doping
- halide solid electrolyte doping lithium battery
- solid electrolyte dopant battery performance
- solid electrolyte ionic conductivity lithium symmetric cell
- solid electrolyte critical current density doping
- data driven solid electrolyte discovery doping

## Running Batches

Batch 1 has been used as the initial demonstration run. Batch 2 and Batch 3 are configured but should be run later when the reviewer is ready to screen larger candidate pools.

Run:

```bash
python scripts/search_literature_batch.py --batch 1 --target 100
python scripts/deduplicate_literature.py
python scripts/summarize_literature_pool.py
```

Default targets are also available:

```bash
python scripts/search_literature_batch.py --batch 1
python scripts/search_literature_batch.py --batch 2
python scripts/search_literature_batch.py --batch 3
```

## Deduplication

Deduplication uses DOI first. If DOI is absent, it falls back to `normalized_title`, which lowercases the title and removes punctuation. When duplicates are merged, the first record is retained and query/source fields are combined.

## Screening Handoff

The candidate pool is not the curated database. After deduplication:

1. Screen candidates for LLZO/LLZTO relevance.
2. Exclude reviews from sample-level extraction unless they lead to original papers.
3. Record screening decisions in `data/templates/literature_screening_log.csv` or a reviewed copy.
4. Extract accepted papers into composition, processing, transport, interface, and battery tables.

## Output Files

- Raw batch candidates: `data/interim/literature_candidates_batch_1_raw.csv`
- Deduplicated pool: `data/processed/literature_candidates_dedup.csv`
- Summary JSON: `outputs/reports/literature_pool_summary.json`
- Summary Markdown: `outputs/reports/literature_pool_summary.md`

Summaries include high, medium, low, and likely irrelevant relevance counts to help prioritize manual screening.

Generated candidate pools are reproducible metadata outputs and should be reviewed before any scientific interpretation.
