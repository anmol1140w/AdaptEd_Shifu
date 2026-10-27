# Application use cases

This area coordinates complete user actions such as starting an assessment, submitting an attempt, requesting a tutor hint and building a teacher intervention queue.

Use cases should depend on stable ports and domain behavior rather than concrete external services.

The first implemented actions are:

- `use_cases/start_assessment.py` — `StartAssessment.execute()` validates the learner and subject, selects a deterministic baseline concept and approved item, and persists an active session.
- `use_cases/prepare_attempt.py` — `PrepareAttempt.execute()` loads an approved item, calls `AssessmentGraderPort`, and creates `AttemptEvidence` without calculating mastery.
- `use_cases/submit_attempt.py` — `SubmitAttempt.execute()` validates an active session and current concept, loads learner evidence through ports, invokes the provider-independent learning engine, persists the result, and advances the session to the next concept.
- `use_cases/build_subject_summary.py` — `BuildSubjectSummary.execute()` aggregates concept mastery and evidence for one subject while preserving prerequisite-aware recommendations.
- `assessment_facade.py` — `AssessmentFacade.start()`, `AssessmentFacade.submit()` and `AssessmentFacade.summary()` coordinate the v1 request parser, application use cases and response mapper without requiring an HTTP framework.
- `use_cases/provide_tutor_support.py` — `ProvideTutorSupport.execute()` retrieves approved context, validates tutor output, and falls back safely when AI support is unavailable.
- `use_cases/generate_weak_area_quiz.py` — `GenerateWeakAreaQuiz.execute()` generates concept-aligned practice, validates it, redacts answers at the contract boundary, and falls back safely.
- `learning_support_facade.py` — `LearningSupportFacade.tutor()` and `LearningSupportFacade.weak_area_quiz()` coordinate the support contracts without an HTTP framework.
- `../bootstrap.py` — `build_in_memory_assessment_runtime()` composes the ports, use cases, facade and API adapter for local execution without a database or HTTP server.
