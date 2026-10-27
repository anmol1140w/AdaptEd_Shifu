# Application use cases

This directory contains complete AdaptEd actions coordinated by the backend application layer.

The current use cases are:

- `start_assessment.py` — provides `StartAssessment`, its command input, and its result type, including the first approved item.
- `submit_attempt.py` — provides `SubmitAttempt`, its command input, and its result type.

Both are deliberately callable without an API server so the application flow can be tested with in-memory adapters first.
