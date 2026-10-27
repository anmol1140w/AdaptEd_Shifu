# AdaptEd Coding Handoff

**Handoff date:** 2026-10-25  
**Repository:** `/home/sharad/Projects/AdaptEd/AdaptEd`  
**Branch:** `sharad`  
**Base revision when checked:** `c492d7b work is assigned`

## Goal

Continue building Sharad's provider-independent learning-intelligence backend for AdaptEd.

The working style for the next session is:

1. Read the relevant files before changing them.
2. Before each work item, explain the target files, purpose, and current plan.
3. Make focused changes inside Sharad's ownership boundaries.
4. Record meaningful decisions and tradeoffs in `decision.md`.
5. Update `Flow.md` with real entry points, callers, function order, ports, and fallback paths.
6. Add behavior tests and run the available checks before finishing.
7. Ignore unrelated configuration edits and do not modify them unless explicitly requested.

## Current state

Implemented and tested:

- Provider-independent learning entities and deterministic learning policy.
- Mastery score, confidence, evidence count, trend, misconception, gap status, and recommendation calculation.
- Riya foundation-gap behavior and Arjun transfer-practice behavior.
- `StartAssessment.execute()` application use case.
- Deterministic root-concept selection.
- Approved initial assessment-item selection, preferring medium difficulty.
- `SubmitAttempt.execute()` application use case.
- Active assessment-session validation.
- Session ownership and current-concept validation.
- Assessment-item identity, approval, subject, concept, and difficulty validation.
- Session advancement to the recommendation target after successful evaluation.
- Provider-neutral ports with in-memory test doubles.

Current application call paths are documented in `Flow.md`.

## Important files

### Domain

- `backend/app/domain/entities/learning.py`
  - `Concept`
  - `AssessmentItem`
  - `AssessmentSession`
  - `AttemptEvidence`
  - `MasteryState`
  - `Recommendation`
  - `LearningOutcome`

- `backend/app/domain/services/learning_engine.py`
  - `LearningEngine.evaluate()`
  - `LearningEngine.select_initial_concept()`
  - `LearningEngine.select_initial_item()`

### Application

- `backend/app/application/use_cases/start_assessment.py`
  - `StartAssessment.execute()`

- `backend/app/application/use_cases/submit_attempt.py`
  - `SubmitAttempt.execute()`

- `backend/app/application/ports/assessment.py`
  - Learner lookup.
  - Concept and item catalog access.
  - Assessment-session lookup, creation, and update.
  - Session ID generation.

- `backend/app/application/ports/learning.py`
  - Attempt persistence.
  - Mastery-state persistence.
  - Recommendation persistence.

### Tests

- `backend/tests/unit/domain/test_learning_engine.py`
- `backend/tests/unit/application/test_start_assessment.py`
- `backend/tests/unit/application/test_submit_attempt.py`

### Project tracking

- `decision.md` — latest meaningful decision is `D-019`, requiring every attempt to reference an approved catalog item.
- `Flow.md` — latest flow includes session validation and item validation before `LearningEngine.evaluate()`.

## Latest execution flow

```text
SubmitAttempt.execute(command)
  → load assessment session
  → validate active status, learner ownership, and current concept
  → load item by item_id
  → validate approval, subject, concept, and difficulty
  → load attempt history and mastery states
  → call LearningEngine.evaluate()
  → persist attempt
  → persist mastery state
  → persist recommendation
  → advance session to recommendation target
  → return result
```

## Decisions that affect the next task

- Domain logic remains independent of FastAPI, PostgreSQL, network access, and live AI providers.
- The MVP uses deterministic and inspectable learning rules before learned models.
- Application use cases depend on ports, not concrete repositories or SDKs.
- Assessment sessions begin at a deterministic root concept.
- Initial items must be approved and are selected deterministically.
- Attempts must be bound to both an active session and an approved item.
- Persistence writes are currently sequential; database transactions, retries, idempotency, and concurrency controls are not implemented yet.

## Checks

### Tests — passed

Command, run from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s backend/tests -p 'test_*.py' -v
```

Observed result:

```text
Ran 21 tests
OK
```

### Compilation — passed

```bash
PYTHONDONTWRITEBYTECODE=1 python -m compileall -q backend
```

### Diff hygiene — passed

```bash
git diff --check
```

### Not available or not run

- No project package configuration, lint command, typecheck command, or build command is currently defined in the scaffold.
- No API, database, or browser smoke test exists yet.

## Working-tree note

The working tree contains the implementation changes described above. An unrelated `opencode.json` modification is also present; it was not part of the implementation and should not be changed as part of the next coding task.

## Next recommended task

Implement the first shared assessment contract boundary under `contracts/`.

Recommended scope:

1. Define versioned request/response shapes for starting an assessment and submitting an attempt.
2. Include subject, session, concept, item, evidence, mastery, recommendation, and evidence-reference fields.
3. Add synthetic JSON examples for Riya and Arjun.
4. Add contract-shape tests without adding a third-party dependency unless the project adopts one explicitly.
5. Update `Flow.md` so the future API route maps to these contracts.

Start by reading:

- `contracts/README.md`
- `contracts/examples/README.md`
- `Flow.md`
- `decision.md`
- `backend/app/application/use_cases/start_assessment.py`
- `backend/app/application/use_cases/submit_attempt.py`
