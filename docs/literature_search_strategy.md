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

`candidate_id, batch_id, title, normalized_title, doi, year, journal, authors, abstract, keywords, material_family_guess, topic_tags, query_used, source_api, source_url, openalex_id, semantic_scholar_id, crossref_id, arxiv_id, citation_count, is_open_access, retrieved_date, screening_status, screening_decision, screening_reason, notes`

`screening_status` starts as `unreviewed`. Reviewers later fill `screening_decision`, `screening_reason`, and `notes`.

## Batch 1 Scope

Batch 1 targets LLZO/LLZTO garnet electrolyte doping and battery-performance-linked studies. The initial queries are:

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

Run:

```bash
python scripts/search_literature_batch.py --batch 1 --target 100
python scripts/deduplicate_literature.py
python scripts/summarize_literature_pool.py
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

Generated candidate pools are reproducible metadata outputs and should be reviewed before any scientific interpretation.
