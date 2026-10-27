# AdaptEd team work division

This directory defines the ownership boundaries for the four-person AdaptEd implementation team.

## Team ownership

| Person | Primary responsibility | Main area |
|---|---|---|
| Sharad | AI integration, learning intelligence and backend orchestration | `backend/app/domain/`, `backend/app/application/`, `backend/app/infrastructure/ai/`, `contracts/` |
| Kaustubh | Core backend platform and persistence | `backend/app/api/`, `backend/app/infrastructure/database/`, `backend/app/schemas/`, `backend/scripts/` |
| Divyansh | Learner and teacher frontend | `frontend/` |
| Anmol | AI, RAG, prompts and AI evaluation | `backend/app/infrastructure/ai/`, `content/lessons/`, `content/items/` |

## Shared rules

- Read the assigned documentation before implementing anything.
- Keep the MVP focused on Class 9 Mathematics: Algebra and Linear Equations.
- Preserve the subject-wise summary → concept-wise drill-down hierarchy.
- Use synthetic learners and demo data only.
- Integrate through `contracts/` instead of importing another person's internal modules.
- Add tests for every new behavior before calling the work complete.
- Support deterministic or mocked behavior before requiring live AI credentials.
- Do not commit secrets, real learner records or private classroom data.
- Coordinate changes that affect shared contracts before changing them.

## Integration order

1. Agree on shared entities and API response shapes.
2. Kaustubh establishes the backend and persistence boundaries.
3. Sharad establishes the learning-domain and orchestration boundaries.
4. Anmol supplies provider-neutral AI, retrieval and evaluation behavior.
5. Divyansh integrates the learner and teacher flows through the shared contracts.
6. The team runs the Riya and Arjun scenarios end to end.

Each member's detailed scope is documented in their own file in this directory.
