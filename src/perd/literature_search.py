"""Public-metadata literature discovery helpers for PERD.

The module intentionally stores only bibliographic metadata returned by public
APIs. It does not scrape Google Scholar and does not download PDFs.
"""

from __future__ import annotations

import csv
import json
import re
import time
from dataclasses import dataclass
from datetime import date
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BATCH_QUERIES: dict[int, list[str]] = {
    1: [
        "LLZO doped ionic conductivity",
        "LLZTO garnet electrolyte doping",
        "Ta doped LLZO conductivity",
        "Nb doped LLZO solid electrolyte",
        "Ga doped LLZO",
        "Al doped LLZO",
        "Ca doped LLZO",
        "Sr doped LLZO",
        "co-doped LLZO garnet solid electrolyte",
        "garnet solid electrolyte lithium symmetric cell",
    ]
}

CANDIDATE_FIELDS = [
    "candidate_id",
    "batch_id",
    "title",
    "normalized_title",
    "doi",
    "year",
    "journal",
    "authors",
    "abstract",
    "keywords",
    "material_family_guess",
    "topic_tags",
    "query_used",
    "source_api",
    "source_url",
    "openalex_id",
    "semantic_scholar_id",
    "crossref_id",
    "arxiv_id",
    "citation_count",
    "is_open_access",
    "retrieved_date",
    "screening_status",
    "screening_decision",
    "screening_reason",
    "notes",
]


@dataclass(frozen=True)
class SearchResult:
    """A batch search result and the files created by that search."""

    records: list[dict[str, str]]
    output_path: Path
    report_path: Path
    status: str
    error: str = ""


def normalize_title(title: str) -> str:
    """Normalize titles for fallback deduplication when DOI is missing."""

    text = unescape(str(title or "")).lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_doi(doi: str) -> str:
    """Normalize DOI strings from API variants."""

    value = str(doi or "").strip().lower()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    value = value.removeprefix("doi:")
    return value.strip()


def reconstruct_openalex_abstract(index: dict[str, list[int]] | None) -> str:
    """Rebuild an OpenAlex inverted-index abstract."""

    if not index:
        return ""
    positioned: list[tuple[int, str]] = []
    for word, positions in index.items():
        for position in positions:
            positioned.append((position, word))
    return " ".join(word for _, word in sorted(positioned))


def infer_material_family(text: str) -> str:
    """Guess material family from title, abstract, and keywords."""

    lowered = text.lower()
    if "llzto" in lowered or "ta-doped llzo" in lowered or "ta doped llzo" in lowered:
        return "LLZTO"
    if "llzo" in lowered or "li7la3zr2o12" in lowered or "li 7 la 3 zr 2 o 12" in lowered:
        return "LLZO"
    if "garnet" in lowered:
        return "garnet"
    if "nasicon" in lowered or "latp" in lowered or "lagp" in lowered:
        return "NASICON"
    if "sulfide" in lowered or "argyrodite" in lowered or "lgps" in lowered:
        return "sulfide"
    return "unknown"


def infer_topic_tags(text: str) -> str:
    """Infer simple searchable tags for screening and summaries."""

    lowered = text.lower()
    tag_rules = {
        "llzo": ["llzo", "li7la3zr2o12"],
        "llzto": ["llzto", "ta-doped llzo", "ta doped llzo"],
        "garnet": ["garnet"],
        "doping": ["dop", "substitut"],
        "ionic_conductivity": ["ionic conductivity", "conductivity"],
        "activation_energy": ["activation energy"],
        "interface": ["interface", "interfacial"],
        "li_symmetric_cell": ["symmetric cell", "li symmetric", "lithium symmetric"],
        "critical_current_density": ["critical current density", "ccd"],
        "battery_performance": ["full cell", "battery performance", "capacity retention"],
    }
    tags = [tag for tag, needles in tag_rules.items() if any(needle in lowered for needle in needles)]
    return ";".join(tags)


def candidate_from_openalex_work(work: dict, batch_id: int, query: str, retrieved: str) -> dict[str, str]:
    """Convert an OpenAlex work object to the PERD candidate schema."""

    title = work.get("title") or ""
    doi = normalize_doi(work.get("doi") or work.get("ids", {}).get("doi", ""))
    authors = "; ".join(
        authorship.get("author", {}).get("display_name", "")
        for authorship in work.get("authorships", [])
        if authorship.get("author", {}).get("display_name")
    )
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    abstract = reconstruct_openalex_abstract(work.get("abstract_inverted_index"))
    keyword_items = work.get("keywords") or []
    concept_items = work.get("concepts") or []
    keywords = "; ".join(
        item.get("display_name") or item.get("keyword") or ""
        for item in [*keyword_items, *concept_items]
        if item.get("display_name") or item.get("keyword")
    )
    text_blob = " ".join([title, abstract, keywords])
    ids = work.get("ids") or {}
    record = {
        "candidate_id": "",
        "batch_id": str(batch_id),
        "title": title,
        "normalized_title": normalize_title(title),
        "doi": doi,
        "year": str(work.get("publication_year") or ""),
        "journal": source.get("display_name") or "",
        "authors": authors,
        "abstract": abstract,
        "keywords": keywords,
        "material_family_guess": infer_material_family(text_blob),
        "topic_tags": infer_topic_tags(text_blob),
        "query_used": query,
        "source_api": "OpenAlex",
        "source_url": primary_location.get("landing_page_url") or work.get("id") or "",
        "openalex_id": work.get("id") or "",
        "semantic_scholar_id": "",
        "crossref_id": ids.get("doi", ""),
        "arxiv_id": ids.get("arxiv", ""),
        "citation_count": str(work.get("cited_by_count") or 0),
        "is_open_access": str(bool((work.get("open_access") or {}).get("is_oa"))).lower(),
        "retrieved_date": retrieved,
        "screening_status": "unreviewed",
        "screening_decision": "",
        "screening_reason": "",
        "notes": "Synthetic-free public metadata record; no PDF downloaded.",
    }
    return {field: str(record.get(field, "")) for field in CANDIDATE_FIELDS}


def _strip_markup(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", str(text or ""))
    return re.sub(r"\s+", " ", unescape(cleaned)).strip()


def _crossref_date(item: dict) -> str:
    for key in ["published-print", "published-online", "published", "created"]:
        parts = (item.get(key) or {}).get("date-parts") or []
        if parts and parts[0]:
            return str(parts[0][0])
    return ""


def candidate_from_crossref_item(item: dict, batch_id: int, query: str, retrieved: str) -> dict[str, str]:
    """Convert a Crossref work object to the PERD candidate schema."""

    title = " ".join(item.get("title") or []).strip()
    doi = normalize_doi(item.get("DOI", ""))
    authors = "; ".join(
        " ".join(part for part in [author.get("given", ""), author.get("family", "")] if part).strip()
        for author in item.get("author", [])
        if author.get("given") or author.get("family")
    )
    abstract = _strip_markup(item.get("abstract", ""))
    keywords = "; ".join(item.get("subject") or [])
    text_blob = " ".join([title, abstract, keywords])
    source_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
    record = {
        "candidate_id": "",
        "batch_id": str(batch_id),
        "title": title,
        "normalized_title": normalize_title(title),
        "doi": doi,
        "year": _crossref_date(item),
        "journal": " ".join(item.get("container-title") or []),
        "authors": authors,
        "abstract": abstract,
        "keywords": keywords,
        "material_family_guess": infer_material_family(text_blob),
        "topic_tags": infer_topic_tags(text_blob),
        "query_used": query,
        "source_api": "Crossref",
        "source_url": source_url,
        "openalex_id": "",
        "semantic_scholar_id": "",
        "crossref_id": doi,
        "arxiv_id": "",
        "citation_count": str(item.get("is-referenced-by-count") or 0),
        "is_open_access": "",
        "retrieved_date": retrieved,
        "screening_status": "unreviewed",
        "screening_decision": "",
        "screening_reason": "",
        "notes": "Synthetic-free public metadata record; no PDF downloaded.",
    }
    return {field: str(record.get(field, "")) for field in CANDIDATE_FIELDS}


def fetch_openalex(query: str, per_page: int = 25, mailto: str | None = None) -> list[dict]:
    """Fetch works from OpenAlex for one query."""

    params = {
        "search": query,
        "per-page": str(per_page),
        "page": "1",
        "sort": "relevance_score:desc",
    }
    if mailto:
        params["mailto"] = mailto
    url = f"https://api.openalex.org/works?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "PERD-literature-discovery/0.1 (public metadata only)"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("results", [])


def fetch_crossref(query: str, rows: int = 25, mailto: str | None = None) -> list[dict]:
    """Fetch works from Crossref for one query."""

    params = {
        "query.bibliographic": query,
        "rows": str(rows),
        "select": ",".join(
            [
                "DOI",
                "URL",
                "title",
                "container-title",
                "published-print",
                "published-online",
                "published",
                "created",
                "author",
                "abstract",
                "subject",
                "is-referenced-by-count",
            ]
        ),
    }
    if mailto:
        params["mailto"] = mailto
    url = f"https://api.crossref.org/works?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "PERD-literature-discovery/0.1 (mailto optional)"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return (payload.get("message") or {}).get("items", [])


def assign_candidate_ids(records: list[dict[str, str]], batch_id: int) -> list[dict[str, str]]:
    """Assign stable batch-local candidate identifiers."""

    for index, record in enumerate(records, start=1):
        record["candidate_id"] = f"B{batch_id:02d}-{index:04d}"
    return records


def write_candidate_csv(path: str | Path, records: Iterable[dict[str, str]]) -> Path:
    """Write candidate records using the required field order."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in CANDIDATE_FIELDS})
    return output


def read_candidate_csv(path: str | Path) -> list[dict[str, str]]:
    """Read candidate CSV records."""

    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def dedup_key(record: dict[str, str]) -> str:
    """Return DOI-first, normalized-title-second deduplication key."""

    doi = normalize_doi(record.get("doi", ""))
    if doi:
        return f"doi:{doi}"
    return f"title:{normalize_title(record.get('normalized_title') or record.get('title', ''))}"


def deduplicate_candidates(records: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """Deduplicate records by DOI, falling back to normalized title."""

    merged: dict[str, dict[str, str]] = {}
    for record in records:
        key = dedup_key(record)
        if key not in merged:
            merged[key] = {field: record.get(field, "") for field in CANDIDATE_FIELDS}
            continue
        existing = merged[key]
        for field in ["query_used", "source_api"]:
            values = [v for v in [existing.get(field, ""), record.get(field, "")] if v]
            existing[field] = "; ".join(dict.fromkeys(part.strip() for value in values for part in value.split(";") if part.strip()))
        for field in CANDIDATE_FIELDS:
            if not existing.get(field) and record.get(field):
                existing[field] = record[field]
    return list(merged.values())


def search_batch(
    batch_id: int,
    target: int,
    output_path: str | Path,
    report_path: str | Path,
    per_query: int | None = None,
    mailto: str | None = None,
    delay_s: float = 0.2,
) -> SearchResult:
    """Run an OpenAlex-backed search batch and write raw candidate metadata."""

    if batch_id not in BATCH_QUERIES:
        raise ValueError(f"Unsupported batch {batch_id}; available batches: {sorted(BATCH_QUERIES)}")
    retrieved = date.today().isoformat()
    queries = BATCH_QUERIES[batch_id]
    per_query = per_query or max(10, min(50, (target // len(queries)) + 8))
    records: list[dict[str, str]] = []
    errors: list[str] = []
    for query in queries:
        if len(records) >= target:
            break
        try:
            works = fetch_openalex(query, per_page=per_query, mailto=mailto)
            records.extend(candidate_from_openalex_work(work, batch_id, query, retrieved) for work in works)
            time.sleep(delay_s)
        except Exception as exc:  # noqa: BLE001 - CLI reports API/network failures explicitly.
            errors.append(f"{query} via OpenAlex: {exc}")
            try:
                items = fetch_crossref(query, rows=per_query, mailto=mailto)
                records.extend(candidate_from_crossref_item(item, batch_id, query, retrieved) for item in items)
                time.sleep(delay_s)
            except Exception as fallback_exc:  # noqa: BLE001 - CLI reports API/network failures explicitly.
                errors.append(f"{query} via Crossref: {fallback_exc}")
    records = assign_candidate_ids(records[:target], batch_id)
    output = write_candidate_csv(output_path, records)
    report = {
        "status": "ok" if records else "network_or_api_failure",
        "batch_id": batch_id,
        "target": target,
        "fetched_candidate_count": len(records),
        "queries": queries,
        "output_path": str(output),
        "errors": errors,
    }
    report_output = Path(report_path)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return SearchResult(records, output, report_output, report["status"], "\n".join(errors))


def summarize_candidates(records: list[dict[str, str]]) -> dict:
    """Summarize a deduplicated literature candidate pool."""

    total = len(records)
    material_counts: dict[str, int] = {}
    llzo_like = 0
    doi_count = 0
    abstract_count = 0
    for record in records:
        material = record.get("material_family_guess") or "unknown"
        material_counts[material] = material_counts.get(material, 0) + 1
        tags = record.get("topic_tags", "").lower()
        if material in {"LLZO", "LLZTO", "garnet"} or any(tag in tags for tag in ["llzo", "llzto", "garnet"]):
            llzo_like += 1
        if normalize_doi(record.get("doi", "")):
            doi_count += 1
        if record.get("abstract", "").strip():
            abstract_count += 1
    return {
        "candidate_count": total,
        "llzo_llzto_garnet_ratio": round(llzo_like / total, 4) if total else 0,
        "doi_coverage": round(doi_count / total, 4) if total else 0,
        "abstract_coverage": round(abstract_count / total, 4) if total else 0,
        "material_family_distribution": dict(sorted(material_counts.items())),
    }
