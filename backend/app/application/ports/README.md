# Application ports

This directory contains provider-neutral boundaries used by application use cases.

The current ports are split by action:

- `learning.py` — attempt evidence, mastery-state, and recommendation persistence.
- `assessment.py` — learner lookup, subject concept and item loading/lookup, session lookup/update, session creation, and session-ID generation.
- `ai.py` — provider-neutral retrieval, tutor generation, quiz generation,
  structured-output validation and audit boundaries.

Concrete repositories can implement these protocols without changing the use cases or domain policy.
