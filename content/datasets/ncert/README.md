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

The production ingestion command validates citation PDFs and chapter-to-concept mappings, creates a versioned collection, writes idempotent points, verifies the final count, then atomically moves the `ncert_pcm_active` alias to the new complete collection. Existing collections are retained for rollback. Embedding segments are capped at 64 whitespace-delimited words with overlap; their payload retains source chapter, page range, and parent chunk ID. The project uses Qdrant Cloud Inference with `sentence-transformers/all-minilm-l6-v2` (384 dimensions); no model training or separate embedding server is needed.

Install the backend dependencies and configure the cluster endpoint and API keys in `backend/.env` (copy the variable names from `backend/.env.example`). Use a write-capable cluster key for ingestion and a separate read-only database key for the application. Never put either key in frontend code or commit a populated `.env` file. The client requests Qdrant Cloud Inference with the same model for document and query embeddings.

```bash
uv run --project backend python -m content.datasets.ncert.qdrant_pipeline validate --strategy heading_aware_650_words
uv run --project backend python -m content.datasets.ncert.qdrant_pipeline ingest --strategy heading_aware_650_words
uv run --project backend python -m content.datasets.ncert.qdrant_pipeline search \
  "How does impulse relate to change in momentum?" \
  --subject Physics --grade 11 --concept-id phy-11-impulse-momentum
```

Use `--strategy page` or `--strategy fixed_450_words_overlap_75` to compare the other prepared corpora. Each completed run gets a new collection fingerprint and switches the serving alias only after validation and count verification.

In the backend composition root, pass `QdrantNcertRetriever()` as the `retriever` argument to `build_in_memory_assessment_runtime(...)`. It searches the active alias with subject, class, and concept filters and returns source text and NCERT citation metadata through the existing `RetrievalPort`. Only chapters mapped to an authored AdaptEd concept are placed in the student-facing collection. Unmapped chapters—including answer keys, preliminaries, and supplementary material—remain in the source/chunk corpus but are excluded from student retrieval until explicitly mapped and reviewed.

Qdrant point IDs are deterministic UUIDs, so retrying ingestion does not create duplicates. The pipeline validates all chunk rows against retained source PDFs before connecting, uses bounded batches and retries for upserts, indexes filter fields, verifies the exact expected point count, and uses an atomic alias switch for re-ingestion. The alias targets one strategy at a time; use non-activated collections for retrieval experiments.

The PDFs and extracted text are for the project's local educational RAG experiments. Attribute textbook content to NCERT and consult NCERT's current reuse terms before redistributing extracted text.
