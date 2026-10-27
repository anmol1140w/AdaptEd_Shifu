# Retrieval adapters

This directory contains mock and vector-backed retrieval adapters over learning
content.

`in_memory.py` currently matches approved sources by subject and concept and
returns a deterministic confidence value for local tests.

`qdrant_ncert.py` implements the application's `RetrievalPort` against the
active Qdrant Cloud collection alias. It requires `QDRANT_URL` and a
`QDRANT_READ_ONLY_API_KEY`. Corpus validation,
versioned ingestion, and alias activation are handled by
`content/datasets/ncert/qdrant_pipeline.py`; see
`content/datasets/ncert/README.md` for the ingestion commands.
