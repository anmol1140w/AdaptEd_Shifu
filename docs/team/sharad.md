# Sharad — AI integration and learning-intelligence backend

## Role

Own the connection between AdaptEd's learning intelligence and the backend application. This is the AI plus focused backend responsibility.

Sharad owns the orchestration that turns learner evidence into mastery state, gap identification, recommendations and the next learning action. Anmol owns the quality and behavior of the AI/RAG components that Sharad integrates.

## Read before working

### Product and problem

- `README.md`
- `docs/product/Problem_statement.md`
- `docs/pitch/PS22_Hackathon_PPT_Blueprint.md`
- `docs/pitch/PS22_Pitch_Script_and_Rehearsal.md`

### Architecture and research

- `docs/architecture/PS22_Diagrams_and_Product_Assets.md`
- `docs/architecture/README.md`
- `docs/research/PS22_Research_and_Citations.md`
- `backend/app/domain/README.md`
- `backend/app/application/README.md`
- `backend/app/infrastructure/README.md`
- `backend/app/application/ports/README.md`
- `backend/app/application/use_cases/README.md`
- `backend/app/infrastructure/ai/README.md`
- `backend/app/infrastructure/ai/llm/README.md`
- `backend/app/infrastructure/ai/retrieval/README.md`
- `backend/app/infrastructure/ai/validators/README.md`
- `contracts/README.md`
- `content/README.md`

## Owned areas

Primary ownership:

```text
backend/app/domain/
backend/app/application/ports/
backend/app/application/use_cases/
contracts/
```

Shared coordination with Anmol:

```text
backend/app/infrastructure/ai/
```

Sharad may add only the backend wiring required to connect the learning intelligence to Kaustubh's APIs and persistence layer. The core API and database remain Kaustubh's responsibility.

## Main responsibilities

### Learning intelligence

- Define the flow from attempt evidence to updated mastery state.
- Implement concept-gap detection.
- Implement prerequisite-aware next-best-action orchestration.
- Implement adaptive item-selection orchestration.
- Aggregate concept states into subject-level summaries.
- Preserve the subject-wise summary → concept-wise drill-down relationship.
- Track confidence, evidence count, trend and likely misconception.
- Keep the learning policy deterministic and inspectable where possible.

### AI/backend integration

- Define provider-neutral ports for language models, retrieval and AI output validation.
- Connect Anmol's tutor and quiz-generation capabilities to application use cases.
- Add mock and fallback behavior when a live model or retriever is unavailable.
- Ensure tutor failures do not stop assessment, mastery or recommendation flows.
- Pass subject, concept, learner attempt and retrieved-source context through the correct boundaries.
- Coordinate model, source and decision audit information with the backend.

### Contracts

- Define and maintain request/response shapes for:
  - Assessment sessions
  - Attempts
  - Mastery states
  - Subject summaries
  - Concept gaps
  - Recommendations
  - Tutor responses
  - Weak-area quizzes
  - Teacher interventions
- Provide mock examples that Divyansh can use before the backend is complete.
- Coordinate breaking contract changes with Kaustubh and Divyansh before merging them.

## Required scenarios

### Riya — foundation gap

- Repeated distributive-property errors.
- High hint usage.
- Low or developing mastery.
- Receives prerequisite support, a grounded hint and scaffolded practice.
- Appears in the teacher intervention queue.

### Arjun — ready for transfer

- Stable mastery of the current concept.
- Low hint usage.
- Receives a harder or transfer item.
- Does not receive the same remediation path as Riya.

The key acceptance behavior is:

```text
Different evidence → different mastery state → different next action
```

## Testing responsibilities

- Unit-test mastery updates and state transitions.
- Unit-test prerequisite blocking and next-item policy decisions.
- Unit-test subject summary aggregation.
- Test confidence and evidence-count boundaries.
- Test recommendation reasons and evidence references.
- Test AI-provider failure and fallback behavior.
- Add scenario tests for Riya and Arjun.
- Add contract tests for every response consumed by the frontend.

## Boundaries

Do not:

- Build the complete database layer owned by Kaustubh.
- Change frontend components owned by Divyansh.
- Replace Anmol's prompt, retrieval or evaluation work without coordination.
- Make a live LLM mandatory for the basic assessment flow.
- Hide the evidence behind a single unexplained score.

## Definition of done

Sharad's work is complete when:

- The learning loop can run with mock data and no live credentials.
- Subject summaries can drill down to concept evidence.
- Riya and Arjun receive different next actions.
- AI failures fall back safely.
- Shared contracts are documented and testable.
- Kaustubh can connect the orchestration to the backend APIs.
- Divyansh can build the UI using the contract examples.
- Tests cover both normal behavior and important failure boundaries.
