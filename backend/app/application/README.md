# Application use cases

This area coordinates complete user actions such as starting an assessment, submitting an attempt, requesting a tutor hint and building a teacher intervention queue.

Use cases should depend on stable ports and domain behavior rather than concrete external services.

The first implemented actions are:

- `use_cases/start_assessment.py` — `StartAssessment.execute()` validates the learner and subject, selects a deterministic baseline concept and approved item, and persists an active session.
- `use_cases/submit_attempt.py` — `SubmitAttempt.execute()` validates an active session and current concept, loads learner evidence through ports, invokes the provider-independent learning engine, persists the result, and advances the session to the next concept.
