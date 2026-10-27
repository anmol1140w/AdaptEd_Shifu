# Backend API boundary

The API layer owns transport concerns and role-aware request context. It must
not contain mastery formulas, item-selection policy, grading policy or direct
database calls.

## Current implementation

`v1/routes/assessment.py` provides a framework-independent adapter:

- `AssessmentApi.start()` for the future start-assessment endpoint.
- `AssessmentApi.submit()` for the future submit-attempt endpoint.
- `LearnerRequestContext` as the trusted identity/role input supplied by an
  authentication layer.
- `AssessmentApiResponse` as an HTTP-like status/body/header result.

`v1/routes/learning_support.py` provides framework-independent tutor and quiz
adapters:

- `LearningSupportApi.tutor()` for tutor support requests;
- `LearningSupportApi.weak_area_quiz()` for weak-area quiz requests; and
- the same trusted `LearnerRequestContext` identity/role boundary.

The repository does not currently define an HTTP framework or server startup.
A future backend integration can wrap these adapters with FastAPI or another
transport without moving assessment orchestration into route functions.
