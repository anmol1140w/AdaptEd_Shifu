# Versioned API routes

This directory contains framework-independent route adapters. They accept
validated-by-contract payload dictionaries and trusted request context, then
return HTTP-like status/body responses that a future FastAPI or other transport
adapter can expose.

## Implemented assessment adapter

`assessment.py` provides:

- `AssessmentApi.start()` — future `POST /api/v1/assessments/start`, returning
  `201` on success.
- `AssessmentApi.submit()` — future `POST /api/v1/assessments/attempts`,
  returning `200` on success.
- `AssessmentApi.summary()` — future subject-summary operation at
  `/api/v1/assessments/summary`, returning `200` on success and preserving
  subject-to-concept-to-evidence drill-down.
- `LearningSupportApi.tutor()` — future `POST /api/v1/tutor/responses`,
  returning grounded tutor content or a safe fallback.
- `LearningSupportApi.weak_area_quiz()` — future
  `POST /api/v1/quizzes/weak-area`, returning validated concept-aligned items
  without exposing generated answers.
- `LearnerRequestContext` — trusted identity/role input supplied by the future
  authentication layer.
- `AssessmentApiResponse` — status code, JSON body and content-type headers.

The adapter does not implement authentication, persistence or HTTP server
startup. It enforces the learner identity/role boundary and delegates the
assessment flow to `AssessmentFacade`.
