# Kaustubh — core backend and persistence

## Role

Own the backend platform foundation for AdaptEd: FastAPI application structure, persistence, authentication, role-aware access and the APIs consumed by the frontend and learning-intelligence layers.

## Read before working

### Product and problem

- `README.md`
- `docs/product/Problem_statement.md`
- `docs/pitch/PS22_Hackathon_PPT_Blueprint.md`
- `docs/pitch/PS22_Pitch_Script_and_Rehearsal.md`

### Architecture and data model

- `docs/architecture/PS22_Diagrams_and_Product_Assets.md`
- `docs/architecture/README.md`
- `backend/README.md`
- `backend/app/README.md`
- `backend/app/domain/README.md`
- `backend/app/application/README.md`
- `backend/app/infrastructure/README.md`
- `backend/app/schemas/README.md`
- `backend/tests/README.md`
- `contracts/README.md`
- `content/README.md`
- `content/seeds/README.md`

## Owned areas

```text
backend/app/api/
backend/app/infrastructure/database/
backend/app/schemas/
backend/scripts/
backend/tests/integration/
```

Kaustubh owns the platform foundation. Sharad owns the learning-intelligence orchestration, and Anmol owns the AI/RAG behavior.

## Main responsibilities

### Backend application

- Establish the FastAPI application boundary.
- Organize versioned API routes under `/api/v1`.
- Add role-aware access for learner and teacher workflows.
- Implement assessment-session endpoints.
- Implement attempt-submission endpoints.
- Implement learner mastery and recommendation endpoints.
- Implement teacher summary and intervention endpoints.
- Implement tutor and weak-area quiz endpoints that call stable application ports.

### Persistence

- Translate the agreed data model into PostgreSQL persistence structures.
- Add models and migrations for:
  - Users
  - Subjects
  - Concepts
  - Concept edges
  - Items
  - Attempts
  - Mastery states
  - Recommendations
  - Content chunks
  - Interventions
  - Audit events
- Preserve both `subject_id` and `concept_id` so subject summaries can drill down into concept evidence.
- Add repositories that keep database details outside the learning domain.

### Demo and operations

- Add repeatable synthetic-data seeding.
- Support Riya, Arjun and the teacher dashboard scenarios.
- Keep credentials in environment configuration rather than source files; configuration belongs at the backend infrastructure boundary.
- Provide a local development path that works with mocked AI services.

## API responsibilities

Kaustubh should expose stable versioned endpoints for at least:

```text
POST /api/v1/assessment-sessions
POST /api/v1/attempts
GET  /api/v1/learners/{learner_id}/mastery
GET  /api/v1/learners/{learner_id}/gaps
GET  /api/v1/learners/{learner_id}/recommendations
POST /api/v1/tutor/hint
POST /api/v1/tutor/explanation
POST /api/v1/quizzes/weak-area
GET  /api/v1/teacher/classes/{class_id}/summary
GET  /api/v1/teacher/classes/{class_id}/interventions
POST /api/v1/teacher/interventions/{intervention_id}/review
```

The exact request and response shapes must be maintained in `contracts/` with Sharad and Divyansh.

## Testing responsibilities

- Test API validation and role restrictions.
- Test repository behavior against the agreed data model.
- Test migrations from a clean database.
- Test assessment and attempt persistence.
- Test subject summary and concept-detail retrieval.
- Test teacher intervention review behavior.
- Test seeded demo data and reset behavior.
- Add integration tests that run with mock AI adapters.

## Boundaries

Do not:

- Put mastery policy decisions directly into route handlers.
- Couple the backend to one LLM provider.
- Change the frontend implementation owned by Divyansh.
- Replace Sharad's domain orchestration with database-specific logic.
- Require live AI credentials for API tests.

## Definition of done

Kaustubh's work is complete when:

- The backend can start with documented local configuration.
- The database schema supports subject and concept reporting.
- Learner and teacher APIs expose the agreed contracts.
- Role-aware access is enforced.
- Synthetic demo data can be loaded repeatably.
- Mock AI adapters allow the core API flow to work offline.
- Integration tests cover the main assessment and teacher workflows.
