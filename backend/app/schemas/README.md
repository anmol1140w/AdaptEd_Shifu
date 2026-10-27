# Backend schemas

This area defines the validated shapes exchanged by the backend application
boundary. Schema design must remain aligned with `contracts/` so the frontend
can integrate without importing backend internals.

## Implemented v1 assessment boundary

`assessment_v1.py` contains the dependency-free mapper for the shared
assessment contracts:

- `parse_start_assessment_request()` validates a v1 payload and returns
  `StartAssessmentCommand`.
- `parse_submit_attempt_request()` validates a raw-answer payload and returns
  `SubmitAttemptRequest` without attempting to grade the answer.
- `to_attempt_evidence()` is the explicit grading boundary. A future grader
  supplies `is_correct`, difficulty and an optional misconception to create
  domain `AttemptEvidence`.
- `start_assessment_response()` maps `StartAssessmentResult` to a JSON-safe
  v1 response and omits the assessment-item answer.
- `submit_attempt_response()` maps `SubmitAttemptResult` plus loaded concept,
  item and evidence-reference context to the v1 response.
- `parse_subject_summary_request()` validates a learner subject-summary request
  and returns `BuildSubjectSummaryCommand`.
- `subject_summary_response()` maps `SubjectSummary` to a JSON-safe v1
  response containing aggregate metrics and concept-level evidence.

`learning_support_v1.py` contains the dependency-free tutor and weak-area quiz
contract mapper:

- `parse_tutor_request()` and `tutor_response()`;
- `parse_weak_area_quiz_request()` and `weak_area_quiz_response()`; and
- answer-safe response mapping that omits generated quiz answers.

The module does not call FastAPI, a database, a language model or a grading
provider.
