from perd.literature_search import (
    BATCH_QUERIES,
    BATCH_TARGETS,
    CANDIDATE_FIELDS,
    calculate_relevance_score,
    candidate_from_crossref_item,
    candidate_from_openalex_work,
    deduplicate_candidates,
    infer_exclusion_hint,
    infer_material_family,
    infer_topic_tags,
    normalize_doi,
    normalize_title,
    reconstruct_openalex_abstract,
    summarize_candidates,
)


def test_batch_queries_support_batches_1_2_3():
    assert sorted(BATCH_QUERIES) == [1, 2, 3]
    assert BATCH_TARGETS == {1: 100, 2: 400, 3: 500}
    assert all(len(BATCH_QUERIES[batch]) == 10 for batch in [1, 2, 3])
    assert "garnet-type solid electrolyte dopant" in BATCH_QUERIES[2]
    assert "NASICON solid electrolyte doping ionic conductivity" in BATCH_QUERIES[3]


def test_normalize_title_removes_case_and_punctuation():
    assert normalize_title("Ta-Doped LLZO: Ionic Conductivity!") == "ta doped llzo ionic conductivity"


def test_normalize_doi_handles_url_prefix():
    assert normalize_doi("https://doi.org/10.1000/ABC") == "10.1000/abc"


def test_reconstruct_openalex_abstract_orders_words():
    index = {"solid": [0], "electrolyte": [1], "works": [2]}
    assert reconstruct_openalex_abstract(index) == "solid electrolyte works"


def test_candidate_from_openalex_work_has_required_fields_and_status():
    work = {
        "title": "Ta doped LLZO garnet electrolyte",
        "doi": "https://doi.org/10.1234/example",
        "publication_year": 2024,
        "primary_location": {
            "source": {"display_name": "Journal of Synthetic Metadata"},
            "landing_page_url": "https://example.test/paper",
        },
        "authorships": [{"author": {"display_name": "A. Researcher"}}],
        "abstract_inverted_index": {"LLZO": [0], "conductivity": [1]},
        "keywords": [{"display_name": "garnet electrolyte"}],
        "ids": {"doi": "https://doi.org/10.1234/example"},
        "cited_by_count": 7,
        "open_access": {"is_oa": True},
        "id": "https://openalex.org/W123",
    }
    record = candidate_from_openalex_work(work, batch_id=1, query="LLZO doped ionic conductivity", retrieved="2026-07-02")
    assert set(CANDIDATE_FIELDS) == set(record)
    assert record["screening_status"] == "unreviewed"
    assert record["relevance_score"]
    assert "exclusion_hint" in record
    assert record["material_family_guess"] in {"LLZO", "LLZTO"}
    assert "ionic_conductivity" in record["topic_tags"]


def test_candidate_from_crossref_item_has_required_fields_and_status():
    item = {
        "title": ["Ga doped LLZO electrolyte"],
        "DOI": "10.5678/example",
        "published-print": {"date-parts": [[2021, 1, 1]]},
        "container-title": ["Solid State Ionics"],
        "author": [{"given": "B.", "family": "Scientist"}],
        "abstract": "<jats:p>LLZO garnet conductivity.</jats:p>",
        "subject": ["Materials Chemistry"],
        "URL": "https://doi.org/10.5678/example",
        "is-referenced-by-count": 4,
    }
    record = candidate_from_crossref_item(item, batch_id=1, query="Ga doped LLZO", retrieved="2026-07-02")
    assert set(CANDIDATE_FIELDS) == set(record)
    assert record["source_api"] == "Crossref"
    assert record["screening_status"] == "unreviewed"
    assert record["abstract"] == "LLZO garnet conductivity."
    assert float(record["relevance_score"]) > 0


def test_relevance_score_rewards_llzo_doping_and_cell_metrics():
    record = {
        "title": "Co-doped LLZO garnet solid electrolyte for lithium symmetric cell",
        "abstract": "Li7La3Zr2O12 shows high ionic conductivity, low activation energy, and improved critical current density in a full cell.",
        "keywords": "doping; solid electrolyte",
    }
    assert calculate_relevance_score(record) >= 0.75


def test_exclusion_hint_marks_low_relevance_records():
    polymer_record = {
        "title": "Polymer-only liquid electrolyte for cathode cycling",
        "abstract": "This liquid electrolyte study discusses cathode behavior without solid electrolyte materials.",
        "keywords": "polymer electrolyte",
    }
    assert calculate_relevance_score(polymer_record) < 0.2
    assert "polymer_only" in infer_exclusion_hint(polymer_record)


def test_deduplicate_candidates_prefers_doi_then_title():
    records = [
        {"candidate_id": "A", "doi": "10.1/X", "title": "First", "normalized_title": "first", "query_used": "q1"},
        {"candidate_id": "B", "doi": "https://doi.org/10.1/x", "title": "First duplicate", "normalized_title": "first duplicate", "query_used": "q2"},
        {"candidate_id": "C", "doi": "", "title": "Same Title!", "normalized_title": normalize_title("Same Title!")},
        {"candidate_id": "D", "doi": "", "title": "same title", "normalized_title": normalize_title("same title")},
    ]
    deduped = deduplicate_candidates(records)
    assert len(deduped) == 2
    assert deduped[0]["query_used"] == "q1; q2"


def test_inference_and_summary_for_llzo_like_pool():
    text = "LLZTO garnet lithium symmetric cell critical current density"
    assert infer_material_family(text) == "LLZTO"
    tags = infer_topic_tags(text)
    assert "li_symmetric_cell" in tags
    assert "critical_current_density" in tags
    summary = summarize_candidates(
        [
            {
                "material_family_guess": "LLZTO",
                "topic_tags": tags,
                "doi": "10.1/a",
                "abstract": "metadata abstract",
                "relevance_score": "0.8",
                "exclusion_hint": "",
            },
            {
                "material_family_guess": "sulfide",
                "topic_tags": "",
                "doi": "",
                "abstract": "",
                "relevance_score": "0.1",
                "exclusion_hint": "liquid_electrolyte_only",
            },
        ]
    )
    assert summary["candidate_count"] == 2
    assert summary["llzo_llzto_garnet_ratio"] == 0.5
    assert summary["doi_coverage"] == 0.5
    assert summary["abstract_coverage"] == 0.5
    assert summary["high_relevance_count"] == 1
    assert summary["likely_irrelevant_count"] == 1
