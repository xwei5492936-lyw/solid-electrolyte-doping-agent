# Evidence-Aware PDF Extraction Workflow

## Scope

The PERD PDF extraction pipeline converts text or Markdown derived from a legally acquired paper PDF into a review-gated `paper_extraction.json`. It does not download PDFs, bypass access controls, or write extracted values to `master_dataset.csv`.

## Workflow

```text
PDF acquisition
      |
      v
Text / Markdown extraction
      |
      v
Evidence-aware field extraction
      |
      v
Evidence validation
      |
      v
Human review
      |
      v
Separate database inclusion decision
```

### 1. PDF Acquisition

Acquire a paper through an open-access source or an authorized personal/institutional route. Keep the PDF local and outside version control. PDF acquisition is separate from PERD extraction.

### 2. PDF, Text, or Markdown Input

The pipeline accepts a local PDF path, direct extracted text/Markdown, or a local `.md`, `.markdown`, or `.txt` path. Local PDF input is parsed with `pypdf` and converted into page-marked text such as `[Page 5]`. The module never downloads a PDF. Scanned PDFs with no extractable text are rejected with an OCR-required error instead of producing unsupported evidence.

For externally prepared Markdown, preserve page markers such as `[Page 5]` or `<!-- page: 5 -->`. Tables and figure captions should remain close to their page marker. OCR output must be labeled through `extraction_method` when it supplies evidence.

### 3. Extraction

`build_extraction_prompt()` creates a model-neutral prompt containing every critical field. An external extractor is injected into `extract_document_text()` or `run_pdf_extraction_pipeline()`; the PERD package does not require a specific model provider.

Every critical field is represented by an `EvidenceRecord`. If the paper does not report a field, the pipeline retains an `unknown` record instead of inventing a value. Reported values preserve the raw value, normalized value, unit, page, section, source sentence, extraction method, and confidence.

Example integration:

```python
from perd.pdf_extraction import run_pdf_extraction_pipeline

extraction, report = run_pdf_extraction_pipeline(
    document_input="data/raw/pdf/paper-001.pdf",
    extractor=my_model_adapter,
    output_path="outputs/extractions/paper_extraction.json",
    paper_metadata={"paper_id": "paper-001", "doi": "10.xxxx/example"},
)
```

Direct Markdown is also accepted:

```python
extraction, report = run_pdf_extraction_pipeline(
    document_input=pdf_markdown,
    input_format="markdown",
    extractor=my_model_adapter,
    output_path="outputs/extractions/paper_extraction.json",
)
```

The extractor callback receives a prompt and must return either a JSON string or a dictionary matching the requested extraction schema.

### 4. Evidence Validation

Validation checks:

- all sections and critical fields are present;
- each field has the required evidence keys;
- confidence uses `high`, `medium`, `low`, or `unknown`;
- known values include a source sentence;
- missing page locators produce a warning and lower confidence;
- output remains marked `database_inclusion_status: not_included`.

Structural or evidence errors prevent `paper_extraction.json` from being written. Warnings remain visible for human review.

### 5. Human Review

Every output begins with:

```json
{
  "paper_metadata": {
    "review_status": "pending",
    "database_inclusion_status": "not_included"
  }
}
```

A human reviewer must verify the PDF page, sentence, sample identity, units, normalization, experimental conditions, and whether each record is an experimental fact, AI inference, or prediction. Approval inside an extraction artifact still does not update the database automatically.

### 6. Database Inclusion

Database inclusion is a separate, explicit curation step. Only reviewed records may be transformed into composition, processing, transport, interface, and battery tables. This module intentionally has no function that writes to `data/processed/master_dataset.csv`.

## Critical Fields

- Composition: final formula, dopant element, dopant site, dopant concentration.
- Processing: calcination temperature, sintering temperature, sintering time, atmosphere.
- Transport: total, bulk, and grain-boundary conductivity; activation energy.
- Interface: interfacial resistance, critical current density, and Li symmetric-cell lifetime.
- Battery: capacity retention and cycle number.

## Three-Paper Pilot

Phase 2 is prepared with `python scripts/prepare_pdf_extraction_pilot.py`. The script selects only priorities 1-3 from `outputs/tables/pdf_extraction_pilot10.csv`, joins the verified access registry, checks local PDF and extraction JSON files, and writes the pilot table and report.

PDF files under `data/raw/pdf/`, extraction JSON under `data/raw/extraction_json/`, and completed human review files under `data/review/human_validation/` are ignored by Git. The access registry and blank review template contain no extracted scientific claims and remain tracked for reproducibility.
