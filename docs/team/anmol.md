# Anmol — AI, RAG and AI evaluation

## Role

Own the AI behavior for AdaptEd: retrieval-grounded tutoring, prompt design, weak-area quiz generation, structured output validation and AI evaluation.

Anmol provides provider-neutral AI capabilities. Sharad integrates those capabilities into the learning loop and backend application, while Kaustubh owns the API and persistence foundation.

## Read before working

### Product and responsible AI

- `README.md`
- `docs/product/Problem_statement.md`
- `docs/pitch/PS22_Hackathon_PPT_Blueprint.md`
- `docs/pitch/PS22_Pitch_Script_and_Rehearsal.md`
- `docs/research/PS22_Research_and_Citations.md`

### AI and architecture

- `docs/architecture/PS22_Diagrams_and_Product_Assets.md`
- `docs/architecture/README.md`
- `backend/app/infrastructure/README.md`
- `backend/app/infrastructure/ai/README.md`
- `backend/app/infrastructure/ai/llm/README.md`
- `backend/app/infrastructure/ai/retrieval/README.md`
- `backend/app/infrastructure/ai/prompts/README.md`
- `backend/app/infrastructure/ai/validators/README.md`
- `backend/app/application/ports/README.md`
- `contracts/README.md`
- `content/README.md`
- `content/concepts/README.md`
- `content/items/README.md`
- `content/lessons/README.md`

## Owned areas

Primary ownership:

```text
backend/app/infrastructure/ai/llm/
backend/app/infrastructure/ai/retrieval/
backend/app/infrastructure/ai/prompts/
backend/app/infrastructure/ai/validators/
content/lessons/
content/items/
```

Shared coordination with Sharad:

```text
backend/app/infrastructure/ai/
backend/app/application/ports/
contracts/
```

## Main responsibilities

### Grounded tutor

- Design the tutor input and output behavior.
- Support hint mode, explanation mode and check-question mode.
- Use only approved retrieved content for factual explanations.
- Include source IDs or lesson references.
- Match the learner's grade, subject, concept and requested language.
- Prefer a leading hint before revealing a complete solution.
- Avoid shame, comparison and permanent labels.
- Return a teacher-review flag when sources are missing, weak or contradictory.

### Weak-area quiz generation

- Generate quiz drafts tied to a specific subject and concept.
- Use the learner's identified misconception and difficulty state.
- Produce structured items with controlled answer types.
- Vary representation where appropriate: symbolic, verbal, visual or story.
- Include transfer questions rather than only repeating the original item.
- Ensure generated items can be validated before they reach the learner.

### Retrieval and approved content

- Prepare approved lesson chunks and worked examples.
- Associate content with subject IDs, concept IDs and source IDs.
- Define retrieval expectations for the distributive-property demo.
- Provide a mock retriever for local tests.
- Define low-confidence and no-source behavior.

### Validation and evaluation

- Validate structured tutor responses.
- Validate source IDs against retrieved or approved content.
- Detect answer dumping in hint mode.
- Detect missing check questions.
- Record safety flags and teacher-review requirements.
- Create an evaluation set covering:
  - Mathematical correctness
  - Grounding
  - Age-appropriate language
  - Hint-first behavior
  - Actionable next step
  - Source traceability
  - Robustness to missing retrieval

## Required demo behavior

For Riya's distributive-property misconception, the AI should be able to produce a grounded hint such as:

```text
The negative multiplier applies to every term inside the bracket.
Which term has not received the multiplier yet?
```

It should also return:

- A check question.
- The approved source ID.
- A confidence value.
- A teacher-review flag when appropriate.
- No unsupported full answer before the learner attempts the next step.

For Arjun, the AI should support a harder transfer question or explanation without forcing the foundation remediation path used for Riya.

## Integration requirements

- Expose AI capabilities through provider-neutral ports.
- Provide mock responses with the same application-level shape as live responses.
- Do not make a specific LLM vendor mandatory for tests.
- Coordinate response schema changes with Sharad.
- Keep generated-content audit fields available to Kaustubh's persistence layer.
- Keep lesson and item identifiers stable for frontend source labels.

## Testing responsibilities

- Test tutor output schema validation.
- Test missing and low-confidence retrieval.
- Test hint-first behavior.
- Test source references and unsupported-source rejection.
- Test weak-area quiz schema and concept alignment.
- Test prompt behavior against the evaluation set.
- Test mock provider behavior without network access or credentials.
- Document known model limitations and fallback behavior.

## Boundaries

Do not:

- Let the LLM decide the entire curriculum path.
- Put database access inside prompts or AI adapters.
- Make generated content automatically high-stakes or teacher-independent.
- Replace deterministic assessment or mastery logic with a chat response.
- Change frontend screens directly.

## Definition of done

Anmol's work is complete when:

- Tutor and quiz-generation interfaces are documented and provider-neutral.
- Mock AI behavior works without credentials.
- Retrieved responses include approved sources.
- Hint mode is non-spoiler and includes a check question.
- Low-confidence retrieval falls back safely.
- Generated quiz items pass structural validation.
- Evaluation results and limitations are documented.
- Sharad can integrate the AI behavior into the backend learning loop.
