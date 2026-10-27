# AI infrastructure

The application-facing AI contracts live in `backend/app/application/ports/ai.py`.
The use cases own retrieval, fallback, validation, answer redaction, and audit
decisions. This directory contains the replaceable adapters:

- `retrieval/in_memory.py` supplies deterministic local sources.
- `retrieval/qdrant_ncert.py` searches the active `ncert_pcm_active` Qdrant
  collection and reads `QDRANT_URL` plus `QDRANT_READ_ONLY_API_KEY` from
  process environment or `backend/.env`.
- `llm/grok.py` uses xAI's Responses API and strict JSON Schema output for
  primary tutor and quiz generation. `GROK_API_KEY` and `GROK_MODEL` configure it.
- `llm/ollama_cloud.py` is the Ollama Cloud backup. `OLLAMA_API_KEY` and
  `OLLAMA_MODEL` configure it; its output is parsed and validated locally.
- `llm/primary_fallback.py` validates Grok results and switches to Ollama when
  Grok fails generation, JSON parsing, or learning-contract validation.
- `llm/mock.py` supplies deterministic local generators and curated fallbacks.
- `validators/structured.py` checks source approval, concept alignment,
  non-spoiler hints, and quiz alignment.
- `audit.py` records local provider, source, and fallback decisions.
- `settings.py` centralizes AI adapter configuration.

Qdrant Cloud Inference embeds retrieval queries; Grok generates tutor
explanations and quizzes from retrieved source text, with Ollama Cloud as the
backup. xAI schema-constrained JSON is checked locally as well. Ollama Cloud
does not currently enforce JSON schemas, so its JSON output is parsed against
the same schema and passed through the application validator.

The in-memory composition root accepts a `RetrievalPort` through `retriever`,
and generation ports through `tutor_generator` and `quiz_generator`. Set
`use_grok=True` to use Grok as primary and the configured Ollama model as
backup for both tutor and quiz generation. The runtime defaults to offline
adapters; Qdrant must be explicitly supplied with a class 11/12 concept catalog
compatible with the indexed concept IDs. The previous
`use_ollama_cloud=True` flag remains a compatible alias for this provider chain.
