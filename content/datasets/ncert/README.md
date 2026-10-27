# NCERT retrieval datasets

This folder contains the derived corpora created from the official English NCERT textbooks. Raw source archives and chapter PDFs stay under [`../../books/ncert/`](../../books/ncert/README.md); this directory contains only derived retrieval data and its loader.

## Chunk corpora

[`chunks/`](chunks/) stores three JSONL datasets using LangChain's `page_content` and `metadata` shape:

- `page/`: one non-empty PDF page per chunk, preserving page boundaries.
- `heading_aware_650_words/`: chunks grouped around section headings, with a soft 650-word target. Detected worked examples stay intact and can exceed that size.
- `fixed_450_words_overlap_75/`: 450-word windows with 75-word overlap, which can cross page boundaries.

Records include stable chunk IDs, class, subject, book part, chapter code and title, strategy, PDF page span, source path, and citation label. Metadata values are flat strings, numbers, and booleans for vector-store compatibility. Worked examples, formulas, chemical equations, figure references, and table references are flagged. Page content is extracted text; diagrams are not embedded and equations or tables may lose their two-dimensional layout. Each record points to the original source PDF and page span for visual verification. Keep each strategy in its own vector-store collection when comparing chunking approaches.

The extractor repairs a common shifted-font encoding and selected unambiguous equation symbols. It flags private-use glyphs that could not be mapped. Match these sources to the platform's authored concepts separately; the records do not claim topic-level alignment.

## Loading LangChain documents

`langchain_loader.py` converts any corpus JSONL into `langchain_core.documents.Document` objects when `langchain-core` is installed:

```python
from content.datasets.ncert.langchain_loader import load_documents

documents = load_documents(
    "content/datasets/ncert/chunks/heading_aware_650_words/keph1/keph101.jsonl"
)
```

## Rebuild

Run `python3 content/books/ncert/process_ncert_corpus.py` from the repository root. The builder reads retained archives, uses Poppler's `pdftotext` at `/usr/bin/pdftotext`, and regenerates this folder's chunk JSONL files along with the source catalog and references. See [`../../books/ncert/README.md`](../../books/ncert/README.md) for source details.

## Qdrant Cloud ingestion and retrieval

The production ingestion command validates citation PDFs and chapter-to-concept mappings, creates a versioned collection, writes idempotent points, verifies the final count and six filtered queries, then atomically moves the dedicated `ncert_pcm_official_active` alias. It does not move or overwrite the pre-existing `ncert_pcm_active` alias. Embedding segments are capped at 64 whitespace-delimited words with overlap; payloads retain source book/edition, source and chapter identity, page range, citation, parent chunk ID, extraction/chunk strategies, corpus/source kind, stable content fingerprint, and ingest batch. The project uses Qdrant Cloud Inference with `sentence-transformers/all-minilm-l6-v2` (384 dimensions); no model training or separate embedding server is needed.

Install the backend dependencies and configure the cluster endpoint and API keys in `backend/.env` (copy the variable names from `backend/.env.example`). Use a write-capable cluster key for ingestion and a separate read-only database key for the application. Never put either key in frontend code or commit a populated `.env` file. The client requests Qdrant Cloud Inference with the same model for document and query embeddings.

```bash
uv run --project backend python -m content.datasets.ncert.qdrant_pipeline validate --strategy heading_aware_650_words
uv run --project backend python -m content.datasets.ncert.qdrant_pipeline ingest --strategy heading_aware_650_words
uv run --project backend python -m content.datasets.ncert.qdrant_pipeline search \
  "How does impulse relate to change in momentum?" \
  --subject Physics --grade 11 --concept-id phy-11-impulse-momentum
```

Use `--strategy page` or `--strategy fixed_450_words_overlap_75` to compare the other prepared corpora. Each completed run gets a new collection fingerprint and switches the serving alias only after validation and count verification.

The packaged FastAPI tutor, recommendation, and weak-area quiz routes read `ncert_pcm_official_active` with a read-only key and require `corpus_id`, `source_kind`, subject, class, and concept filters. The separate in-memory architecture can use `QdrantNcertRetriever()` through `build_in_memory_assessment_runtime(...)`; it applies the same corpus boundary. Only chapters mapped to an authored AdaptEd concept are placed in either student-facing collection. The validator distinguishes intentional answer-key, preliminaries, appendix, and supplementary exclusions from curricular chapters that still need authored concept mappings.

Qdrant point IDs are deterministic UUIDs, so retrying ingestion does not create duplicates. The pipeline validates all chunk rows against retained source PDFs before connecting, uses bounded batches and retries for upserts, indexes filter fields, verifies the exact expected point count, tests six class/subject-filtered retrievals, and uses an atomic alias switch for re-ingestion. The separate official alias targets one strategy at a time; use non-activated collections for retrieval experiments. Before changing runtime routing away from a legacy collection, export its point IDs and full payloads and verify the count and checksum; the checked-in `.gitignore` excludes local corpus backups.

The 71-query evaluation set and results are in [`evaluation/`](evaluation/). `evaluate_strategies.py` compares the three local chunk layouts with lexical BM25; `evaluate_qdrant.py` measures the active semantic collection and the effect of the relevance cutoff. See [`quality_report.md`](quality_report.md) for measured results and extraction limitations.

The PDFs and extracted text are for the project's local educational RAG experiments. Attribute textbook content to NCERT and consult NCERT's current reuse terms before redistributing extracted text.
