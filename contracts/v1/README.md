# AdaptEd contracts — v1

These files define the shared transport boundary for assessment and learning
support flows.
They are versioned independently from the domain entities so the API and
frontend can coordinate without importing backend Python classes.

## Contract files

| File | Purpose |
|---|---|
| `start_assessment_request.schema.json` | Learner and subject context sent when starting an assessment. |
| `start_assessment_response.schema.json` | The new session, selected concept, subject and first item. |
| `submit_attempt_request.schema.json` | Raw learner answer and interaction signals for one item. |
| `submit_attempt_response.schema.json` | Evaluated evidence, updated mastery, gap status and next recommendation. |
| `subject_summary_request.schema.json` | Learner and subject context for a subject summary. |
| `subject_summary_response.schema.json` | Subject aggregate with concept and evidence drill-down. |
| `tutor_request.schema.json` | Learner context, tutor mode and misconception context. |
| `tutor_response.schema.json` | Grounded tutor message, check question, sources and fallback metadata. |
| `weak_area_quiz_request.schema.json` | Concept, difficulty, misconception and quiz-size context. |
| `weak_area_quiz_response.schema.json` | Validated quiz items without exposing generated answers. |

## Boundary rules

- Every payload carries `contract_version: "v1"`.
- Subject and concept identifiers remain explicit in every relevant object.
- Assessment-item responses contain the question and source reference, but not
  the answer. The answer is request-only content.
- `is_correct` belongs to evaluated evidence in the response. The current
  application use case receives an already-graded `AttemptEvidence`; a future
  API adapter will map the submitted answer to that evidence.
- Recommendation evidence references use stable attempt IDs so a client can
  explain why the next action was selected.
- Tutor responses include approved source IDs, a check question and an explicit
  answer-revealed flag; hint mode must remain non-spoiler.
- Weak-area quiz responses include concept-aligned questions and source IDs, but
  generated answer values remain internal to the application boundary.
- Examples are synthetic and must not be presented as classroom outcomes.

The JSON files use JSON Schema 2020-12 vocabulary. The repository currently
tests the important contract shape with the Python standard library and does
not require a third-party schema validator.
