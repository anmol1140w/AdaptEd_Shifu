# AI infrastructure

The application-facing AI contracts live in `backend/app/application/ports/ai.py`.
The use cases own retrieval, fallback, validation, answer redaction, and audit
decisions. This directory contains the replaceable adapters:

- `retrieval/in_memory.py` supplies deterministic local sources.
- `retrieval/qdrant_ncert.py` searches the dedicated official corpus through
  `ncert_pcm_official_active` and applies corpus and source-kind filters.
  It reads `QDRANT_URL` plus `QDRANT_READ_ONLY_API_KEY` from process
  environment or `backend/.env`.
- `llm/ollama_cloud.py` generates tutor support and weak-area quizzes through
  Ollama Cloud. `OLLAMA_API_KEY` and `OLLAMA_MODEL` configure it. Its JSON is
  parsed and validated locally before it reaches the application validator.
- `llm/mock.py` supplies deterministic local generators and curated fallbacks.
- `validators/structured.py` checks source approval, concept alignment,
  non-spoiler hints, and quiz alignment.
- `audit.py` records local provider, source, and fallback decisions.
- `settings.py` centralizes AI adapter configuration.

Qdrant Cloud Inference embeds retrieval queries; Ollama Cloud generates tutor
explanations and quizzes from retrieved source text. Ollama Cloud does not
currently enforce JSON schemas, so its JSON output is parsed against the
expected shape and passed through the application validator.

The in-memory composition root accepts a `RetrievalPort` through `retriever`,
and generation ports through `tutor_generator` and `quiz_generator`. Set
`use_ollama_cloud=True` to use the configured Ollama model for both tutor and
quiz generation. The runtime defaults to offline adapters; Qdrant must be
explicitly supplied with a class 11/12 concept catalog compatible with the
indexed concept IDs.
