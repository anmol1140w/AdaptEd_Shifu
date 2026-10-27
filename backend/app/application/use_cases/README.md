# Application use cases

This directory contains complete AdaptEd actions coordinated by the backend application layer.

The current use cases are:

- `start_assessment.py` — provides `StartAssessment`, its command input, and its result type, including the first approved item.
- `submit_attempt.py` — provides `SubmitAttempt`, its command input, and its result type.
- `build_subject_summary.py` — provides `BuildSubjectSummary`, which aggregates mastery metrics while retaining concept-level evidence and recommendations.
- `provide_tutor_support.py` — provides grounded tutor hints, explanations and check questions with retrieval, validation, fallback and audit behavior.
- `generate_weak_area_quiz.py` — provides concept-aligned weak-area quiz generation with structured validation, answer redaction and fallback behavior.

All are deliberately callable without an API server so the application flow can be tested with in-memory adapters first.
