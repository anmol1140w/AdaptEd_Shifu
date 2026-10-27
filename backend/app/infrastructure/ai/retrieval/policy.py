"""Shared corpus identity and measured retrieval acceptance policy."""

EMBEDDING_MODEL = "sentence-transformers/all-minilm-l6-v2"
CORPUS_ID = "ncert_pcm_english_2026_27"
SOURCE_KIND = "official_ncert"
# Evaluated on 60 chapter-labeled queries: this cutoff preserved 90.38% chapter
# Recall@5/MRR and yielded no above-cutoff results for the six unanswerable probes.
MIN_RELEVANCE_SCORE = 0.6
OFFICIAL_ALIAS = "ncert_pcm_official_active"
