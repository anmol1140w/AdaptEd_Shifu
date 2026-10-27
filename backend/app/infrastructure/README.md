# Infrastructure adapters

This area contains replaceable adapters for persistence, retrieval, generation,
configuration, and audit storage.

The first implementation should support deterministic or mocked adapters so the platform can be tested without credentials or network access.

The implemented assessment adapter is:

- `assessment/grading.py` — `DeterministicAssessmentGrader` compares a
  normalized learner answer with the approved catalog answer and returns only
  correctness plus optional misconception metadata.

The reusable local integration adapters are:

- `in_memory.py` — catalog, learner, session, attempt, mastery,
  recommendation and session-ID adapters that satisfy the application ports.
- `backend/app/bootstrap.py` — composition root that assembles those adapters
  with the application use cases, facade and framework-independent API adapter.

The AI adapters are:

- `ai/retrieval/in_memory.py` — approved source retrieval by subject and concept.
- `ai/retrieval/qdrant_ncert.py` — semantic NCERT source retrieval from the active Qdrant Cloud collection.
- `ai/llm/mock.py` — deterministic tutor and quiz generators plus curated fallbacks.
- `ai/validators/structured.py` — source, concept, mode, spoiler and item-alignment validation.
- `ai/settings.py` — shared Qdrant configuration loaded from process environment or `backend/.env`.
- `ai/audit.py` — process-local model/source/fallback audit storage.

The assessment composition root remains an in-memory local runtime. Qdrant is
available through the same retrieval port, but must be explicitly injected into
a runtime configured with matching class 11/12 concepts. Live text generation
is not configured; Qdrant inference only embeds retrieval queries.
