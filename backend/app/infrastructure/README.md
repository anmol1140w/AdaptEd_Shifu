# Infrastructure adapters

This area will contain replaceable adapters for persistence, retrieval, language-model providers, configuration and audit storage.

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

The implemented mock AI adapters are:

- `ai/retrieval/in_memory.py` — approved source retrieval by subject and concept.
- `ai/llm/mock.py` — deterministic tutor and quiz generators plus curated fallbacks.
- `ai/validators/structured.py` — source, concept, mode, spoiler and item-alignment validation.
- `ai/audit.py` — process-local model/source/fallback audit storage.

These adapters are for local demos and tests. They do not provide production
durability, transactions, retries, idempotency or concurrency control.
