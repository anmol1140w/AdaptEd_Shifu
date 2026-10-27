# AdaptEd Coding Handoff

**Handoff date:** 2026-10-25  
**Repository:** `/home/sharad/Projects/AdaptEd/AdaptEd`  
**Branch:** `sharad`  
**Base revision when checked:** `4bb4e44 first day work done`

The working tree contains the subsequent uncommitted implementation and
documentation changes described below. Do not reset or discard them.

## Goal

Continue building Sharad's provider-independent learning-intelligence backend for AdaptEd.

## Resume summary

The latest implementation is a dependency-free local runtime covering
assessment, subject summaries, and mock tutor/quiz support:

```text
AssessmentApi → AssessmentFacade → start / grade / submit / subject summary
LearningSupportApi → LearningSupportFacade → tutor / weak-area quiz
  → retrieval → mock generation → structural validation → fallback when needed
  → in-memory AI audit
Both paths → contract-shaped JSON responses
```

**Sharad's independent work is not finished, and he does not need to wait for
other teammates.** Next, implement adaptive next-item selection. Teacher
intervention orchestration/contracts, evidence-driven tutor/quiz integration,
and validation/fallback improvements can also proceed locally through ports.

The latest user clarification is to distinguish that independent work from
team-dependent integration. Earlier completion messages referred to local
prototype slices, not the full definition of done in `docs/team/sharad.md`.
Do not use an unsupported completion percentage or mark the whole charter done.

Do not install or assume an HTTP framework, authentication scheme or database.
Kaustubh owns the core API/auth/persistence platform; Sharad owns the necessary
integration wiring. Anmol owns AI/RAG behavior and evaluation; Sharad integrates
those components through the ports. Live providers are not required to finish
the independent orchestration and tests.

The working style for the next session is:

1. Read the relevant files before changing them.
2. Before each work item, explain the target files, purpose, and current plan.
3. Make focused changes inside Sharad's ownership boundaries.
4. Record meaningful decisions and tradeoffs in `decision.md`.
5. Update `Flow.md` with real entry points, callers, function order, ports, and fallback paths.
6. Add behavior tests and run the available checks before finishing.
7. Ignore unrelated configuration edits and do not modify them unless explicitly requested.

## Current state

Implemented with local tests (not production readiness or full charter completion):

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
- Versioned v1 assessment request/response schemas under `contracts/v1/`.
- Synthetic Riya and Arjun contract examples.
- Standard-library contract-shape tests for the v1 payloads.
- Backend v1 request parsing, grading-boundary conversion, and response mapping.
- Provider-neutral `AssessmentGraderPort` and `GradingResult`.
- `PrepareAttempt.execute()` item lookup, grading orchestration and evidence creation.
- Deterministic normalized-answer grading adapter with no network or credentials.
- Framework-independent `AssessmentFacade.start()` and `AssessmentFacade.submit()` orchestration.
- Framework-independent `BuildSubjectSummary.execute()` aggregation with concept evidence drill-down.
- Versioned v1 subject-summary request and response schemas with a synthetic Riya example.
- `AssessmentFacade.summary()` and `AssessmentApi.summary()` framework-independent summary path.
- Provider-neutral retrieval, tutor-generation, quiz-generation, validation and audit ports.
- Deterministic approved-source retrieval and mock tutor/quiz adapters with curated fallbacks.
- `ProvideTutorSupport.execute()` retrieval/generation/validation orchestration for hint, explanation and check-question modes using mock output.
- `GenerateWeakAreaQuiz.execute()` draft generation with subject/concept/difficulty field checks and expected-answer field redaction.
- Tutor and weak-area quiz v1 contracts with a synthetic Riya support example.
- Framework-independent `LearningSupportFacade` and `LearningSupportApi` adapters.
- End-to-end in-memory Riya and Arjun assessment flows.
- Framework-independent v1 `AssessmentApi` route adapter with learner context checks and stable error responses.
- Reusable in-memory catalog and persistence adapters for all current application ports.
- `build_in_memory_assessment_runtime()` composition root for assembled local execution.
- `scripts/run_assessment_demo.py` synthetic command for the assembled API flow.

Current application call paths are documented in `Flow.md`.

### Known prototype limitations — do not mistake these for completed features

- Only initial assessment-item selection exists. A recommendation or a changed
  session concept does not automatically select and serve the next approved item.
- Tutor/quiz use cases accept context from the caller; they do not yet load and
  bind stored learner attempts, mastery and misconceptions to support requests.
- Source IDs are checked, but that does not prove the generated text is grounded
  in source content. The mock generators use templates. The hint validator checks
  the `answer_revealed` flag, not whether the message actually leaks a solution.
- Quiz metadata alignment is not mathematical validation. Mock difficulty and
  transfer labels do not prove suitable difficulty or genuine transfer practice.
  The quiz fallback is placeholder practice, not a reviewed content bank.
- Quiz drafts are not persisted into the approved item catalog; generation alone
  is not a complete practice → submission → reassessment loop.
- Fallbacks cover the tested failures, not every failure boundary. Low-confidence
  retrieval, malformed provider output, fallback failure and audit failure need
  broader checks; verify assessment remains usable after support failure.
- AI audit events are process-local generation/fallback metadata, not a complete
  persisted model/version/source/learning-decision audit trail.
- The teacher-intervention queue and its contracts/examples are not implemented.

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
  - Assessment grading port and grading result.

- `backend/app/application/use_cases/prepare_attempt.py`
  - `PrepareAttempt.execute()` loads an approved item, calls the grader and creates `AttemptEvidence`.

- `backend/app/application/assessment_facade.py`
  - `AssessmentFacade.start()` parses and runs the start flow.
  - `AssessmentFacade.submit()` parses, grades, submits and maps the response.
  - `AssessmentFacade.summary()` aggregates and maps subject-level evidence.

- `backend/app/application/use_cases/build_subject_summary.py`
  - `BuildSubjectSummary.execute()` aggregates mastery, confidence, gaps and evidence for one subject.

- `backend/app/application/use_cases/provide_tutor_support.py`
  - `ProvideTutorSupport.execute()` retrieves approved content, validates tutor output and falls back safely.

- `backend/app/application/use_cases/generate_weak_area_quiz.py`
  - `GenerateWeakAreaQuiz.execute()` generates aligned quiz drafts, validates them and falls back safely.

- `backend/app/application/ports/ai.py`
  - Provider-neutral retrieval, generation, validation and audit contracts.

- `backend/app/application/learning_support_facade.py`
  - Framework-independent tutor and weak-area quiz orchestration.

- `backend/app/api/v1/routes/assessment.py`
  - `AssessmentApi.start()`, `AssessmentApi.submit()` and `AssessmentApi.summary()` route adapters.
  - `LearnerRequestContext` trusted identity/role boundary.
  - `AssessmentApiResponse` status/body/header result.

- `backend/app/api/v1/routes/learning_support.py`
  - `LearningSupportApi.tutor()` and `LearningSupportApi.weak_area_quiz()` route adapters.

- `backend/app/infrastructure/in_memory.py`
  - Reusable learner, concept, item, session, ID, attempt, mastery and recommendation adapters.

- `backend/app/bootstrap.py`
  - `build_in_memory_assessment_runtime()` assembles assessment, summary, tutor and quiz local runtime paths.

- `backend/app/infrastructure/ai/`
  - Mock retrieval, generation, curated fallback, validation and audit adapters.

- `scripts/run_assessment_demo.py`
  - Runs synthetic Riya and Arjun flows through `AssessmentApi`.
  - Prints contract-shaped JSON and persisted summaries.

- `backend/app/application/ports/learning.py`
  - Attempt persistence.
  - Mastery-state persistence.
  - Recommendation persistence.

### Contract boundary

- `contracts/v1/`
  - Versioned assessment, subject-summary, tutor and weak-area quiz schemas.
- `contracts/examples/v1/`
  - Synthetic Riya and Arjun assessment payloads, subject summary and learning-support payloads.
- `backend/app/schemas/assessment_v1.py`
  - Request parsing.
  - Raw-answer request representation.
  - Explicit grading-boundary conversion to `AttemptEvidence`.
  - JSON-safe start, submit and subject-summary response mapping.

- `backend/app/schemas/learning_support_v1.py`
  - Tutor and weak-area quiz request parsing and answer-safe response mapping.
- `backend/app/infrastructure/assessment/grading.py`
  - `DeterministicAssessmentGrader` for local/test answer grading.

### Tests

- `backend/tests/unit/domain/test_learning_engine.py`
- `backend/tests/unit/application/test_start_assessment.py`
- `backend/tests/unit/application/test_submit_attempt.py`
- `backend/tests/unit/contracts/test_assessment_contracts.py`
- `backend/tests/unit/schemas/test_assessment_v1.py`
- `backend/tests/unit/application/test_prepare_attempt.py`
- `backend/tests/unit/infrastructure/test_grading.py`
- `backend/tests/unit/application/test_assessment_facade.py`
- `backend/tests/unit/application/test_build_subject_summary.py`
- `backend/tests/unit/application/test_learning_support.py`
- `backend/tests/unit/api/test_assessment_api.py`
- `backend/tests/unit/api/test_learning_support.py`
- `backend/tests/unit/infrastructure/test_in_memory.py`
- `backend/tests/unit/infrastructure/test_ai.py`
- `backend/tests/unit/application/test_bootstrap.py`
- `backend/tests/unit/schemas/test_learning_support_v1.py`
- `backend/tests/unit/scripts/test_run_assessment_demo.py`

### Project tracking

- `decision.md` — latest meaningful decision is `D-029`, defining provider-neutral tutor/quiz support with safe fallbacks.
- `Flow.md` — latest flow includes assessment, subject summary, AI support, facades, API adapters, assembled runtime, demo command and session-transfer boundary.

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

The future transport path now has these implemented inner boundaries:

```text
v1 submit request payload
  → backend/app/schemas/assessment_v1.py
  → validated raw-answer request
  → AssessmentFacade.submit()
  → PrepareAttempt.execute()
  → AssessmentGraderPort
  → AttemptEvidence
  → SubmitAttempt.execute()
  → JSON-safe v1 response mapping
  → AssessmentApiResponse
   → future HTTP framework
```

Local composition path:

```text
build_in_memory_assessment_runtime()
  ├─ in-memory assessment ports + deterministic grader
  │    → assessment and subject-summary use cases
  │    → AssessmentFacade → AssessmentApi
  └─ in-memory retrieval + mock generators + fallback + validator + AI audit
       → ProvideTutorSupport / GenerateWeakAreaQuiz
       → LearningSupportFacade → LearningSupportApi
```

Synthetic command path:

```text
python scripts/run_assessment_demo.py
  → build_in_memory_assessment_runtime()
  → Riya and Arjun API calls
  → contract-shaped JSON output
```

## Decisions that affect the next task

- Domain logic remains independent of FastAPI, PostgreSQL, network access, and live AI providers.
- The MVP uses deterministic and inspectable learning rules before learned models.
- Application use cases depend on ports, not concrete repositories or SDKs.
- Assessment sessions begin at a deterministic root concept.
- Initial items must be approved and are selected deterministically.
- Attempts must be bound to both an active session and an approved item.
- Answer grading must remain separate from mastery and next-action policy.
- The deterministic grader is an MVP adapter, not a complete algebraic-equivalence engine.
- The facade is framework-independent; API authentication and transport remain outside it.
- The API adapter enforces trusted learner context but does not implement authentication or HTTP server startup.
- The in-memory runtime is process-local and does not provide production durability or transaction guarantees.
- The synthetic demo is local integration evidence, not classroom evidence or an HTTP smoke test.
- Persistence writes are currently sequential; database transactions, retries, idempotency, and concurrency controls are not implemented yet.
- Tutor and quiz support use deterministic local providers; live model/retrieval adapters and provider evaluation remain pending.
- Tutor/quiz fallbacks are explicit and audited in memory; audit persistence and source storage remain pending.

## Checks

Rechecked on 2026-10-25 against the current uncommitted working tree based on
`4bb4e44`. Passing tests demonstrate the covered local behavior, not completion
of the known limitations above. This handoff refresh changes only `HANDOFF.md`.

### Tests — passed

Command, run from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s backend/tests -p 'test_*.py' -v
```

Latest observed result:

```text
Ran 88 tests
OK
```

### Compilation — passed

```bash
PYTHONDONTWRITEBYTECODE=1 python -m compileall -q backend scripts
```

Exit status 0. This is a syntax compilation check, not a typecheck or build.

### Synthetic demo smoke — passed

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/run_assessment_demo.py
```

Observed result:

```text
Riya  → targeted_practice
Arjun → transfer_practice
Attempts persisted: 2 and 4
```

### Contract JSON parsing — passed

```bash
python -c 'import json; from pathlib import Path; paths = list(Path("contracts").rglob("*.json")); [json.loads(path.read_text()) for path in paths]; print(f"Parsed {len(paths)} JSON files")'
```

Observed result: fourteen JSON files parsed successfully.

### Diff hygiene — passed

```bash
git diff --check
```

### Missing or not run

- **Lint:** No project lint command configured; not run.
- **Typecheck:** No project typecheck command configured; not run.
- **Build/package:** No package/build configuration defined; not run.
- **HTTP/database/browser smoke:** Not available; no executable HTTP application
  or production persistence exists. Current API tests call Python adapters.
- **Live AI evaluation:** Not run; no live provider configured. Coordinate
  content quality, grounding and evaluation with Anmol.
- **JSON Schema conformance:** JSON parsing and standard-library shape tests
  pass; these are not full validation by a JSON Schema implementation.

## Working-tree note

The working tree contains many modified and untracked implementation, test,
contract and documentation files from the preceding work. They are not committed
or merged. Preserve all of them; do not reset, clean, commit or push unless asked.

`Flow.md` and `decision.md` exist locally but are ignored by `.gitignore`; they
will not automatically travel with a commit or fresh checkout. Their tracking
policy was not changed by this handoff refresh.

The earlier note about a modified `opencode.json` is stale: the latest
`git status --short` does not report that modification. Continue leaving
unrelated configuration untouched.

## Remaining independent work — no teammate dependency

1. **Adaptive next-item selection:** Turn mastery/recommendation results into
   selection of an actual approved item, including prerequisite remediation,
   harder transfer practice, deterministic ordering and no-suitable-item behavior.
2. **Teacher-intervention queue:** Build evidence-backed application orchestration,
   its request/response contracts, synthetic examples and tests. Riya should
   appear for the relevant foundation-gap scenario; Arjun should not receive the
   same remediation. Do not build Divyansh's dashboard or Kaustubh's database.
3. **Evidence-driven tutor/quiz integration:** Load learner evidence through ports,
   bind context to the correct learner/subject/concept, and connect support and
   scaffolded practice to the learning loop rather than only caller-supplied labels.
4. **Validation and fallback hardening:** Close the known prototype gaps, add
   malformed-output and failure-boundary tests, and preserve assessment/mastery
   availability when support fails. Coordinate AI-quality rules with Anmol.
5. **Complete scenario and contract coverage:** Exercise the full local Riya and
   Arjun journeys through support, actual item selection and reassessment; provide
   frontend-ready examples for newly implemented boundaries.

Mastery states, gap statuses and recommendations already have shapes within
assessment/summary contracts. Separate standalone files are not mandatory just
because they were listed as missing earlier; add them only if integration needs
a separate operation or richer gap/intervention payload.

## Team-dependent integration — coordinate, do not take over

- **With Anmol:** Connect evaluated tutor, quiz, retrieval and validation adapters
  through the existing ports. Preserve mock execution without live credentials.
- **With Kaustubh:** Wire the orchestration to his chosen HTTP/auth/persistence
  interfaces, map trusted identity to `LearnerRequestContext`, and agree model,
  source and learning-decision audit metadata and persistence behavior.
- **With Kaustubh:** Define transaction, retry, idempotency and concurrency
  guarantees and add HTTP/persistence smoke tests once his runtime is available.
- **With Divyansh and Kaustubh:** Coordinate shared contract changes and examples
  before merging. The frontend and complete backend platform are not Sharad's scope.

## Next recommended task: adaptive next-item selection

Begin with `backend/app/domain/services/learning_engine.py` and its tests to
inspect the existing initial-item policy. Then trace `SubmitAttempt.execute()`
and the facade/contract mapping before choosing the smallest additive next-item
use case. The next-item use case is **planned, not implemented**.

Acceptance targets:

- Select only approved items for the recommendation's subject/concept.
- Riya receives suitable prerequisite/scaffolded practice; Arjun receives a
  genuinely harder or transfer item rather than only a recommendation label.
- Keep selection deterministic, handle prior-item repetition and missing content
  explicitly, and do not leak catalog answers in the response.
- Add focused policy/application tests, then run the full suite above. No new
  framework, database or live AI dependency is required.

Start by reading:

- `docs/team/sharad.md`
- `backend/app/domain/services/learning_engine.py`
- `backend/app/domain/entities/learning.py`
- `backend/app/application/use_cases/start_assessment.py`
- `backend/app/application/use_cases/submit_attempt.py`
- `backend/app/application/ports/assessment.py`
- `backend/app/application/ports/learning.py`
- `backend/app/application/assessment_facade.py`
- `backend/app/schemas/assessment_v1.py`
- `backend/app/bootstrap.py`
- `backend/tests/unit/domain/test_learning_engine.py`
- `backend/tests/unit/application/test_start_assessment.py`
- `backend/tests/unit/application/test_submit_attempt.py`
- `Flow.md` and `decision.md` (local, Git-ignored)
