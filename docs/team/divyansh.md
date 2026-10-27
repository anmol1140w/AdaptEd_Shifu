# Divyansh — frontend

## Role

Own the React frontend for AdaptEd's learner and teacher experiences.

The frontend should make the adaptive loop visible to users: a learner sees why the next action was selected, and a teacher sees the subject-level summary, concept-level evidence and recommended intervention.

## Read before working

### Product and demo

- `README.md`
- `docs/product/Problem_statement.md`
- `docs/pitch/PS22_Hackathon_PPT_Blueprint.md`
- `docs/pitch/PS22_Pitch_Script_and_Rehearsal.md`
- `docs/architecture/PS22_Diagrams_and_Product_Assets.md`

### Frontend and integration

- `frontend/README.md`
- `frontend/src/README.md`
- `frontend/src/features/README.md`
- `frontend/src/features/learner/README.md`
- `frontend/src/features/teacher/README.md`
- `frontend/src/features/assessment/README.md`
- `frontend/src/features/mastery/README.md`
- `frontend/src/features/tutor/README.md`
- `frontend/src/services/README.md`
- `frontend/src/types/README.md`
- `frontend/tests/README.md`
- `contracts/README.md`
- `contracts/examples/README.md`
- `content/README.md`
- `content/seeds/README.md`

## Owned area

```text
frontend/
```

Divyansh integrates with backend behavior through `contracts/`. Backend routes, database models and AI internals should not be imported directly into the frontend.

## Main responsibilities

### Learner experience

- Build the learner home screen.
- Show the Mathematics subject-level summary.
- Allow drill-down into concept-level mastery.
- Build the adaptive diagnostic flow.
- Show question difficulty and progress.
- Show the “why this next?” explanation.
- Capture answers, hints and re-attempts.
- Show targeted practice recommendations.
- Show transfer and re-check questions.
- Display mastery trends and learning progress.
- Add tutor hint and explanation screens.
- Display source labels and teacher-review states.
- Show weak-area quiz recommendations.

### Teacher experience

- Build the teacher dashboard.
- Show class-level subject summaries.
- Show concept-level mastery and gap heatmaps.
- Show evidence count, confidence and trend.
- Show the intervention queue.
- Show affected learners or groups.
- Show recommended actions and reasons.
- Support approve, edit and override states.
- Show progress after re-assessment.

### Demo experience

The UI must support the documented demo sequence:

1. Open Riya's learner dashboard.
2. Start the diagnostic.
3. Submit a correct answer.
4. Submit a distributive-property error.
5. Show subject summary → concept map drill-down.
6. Show why the next item was selected.
7. Request a hint.
8. Submit a corrected attempt.
9. Complete targeted practice and a transfer item.
10. Switch to the teacher dashboard.
11. Show the intervention queue.
12. Approve or edit the recommendation.
13. Show the mastery trend after re-check.

## Integration requirements

- Use contract examples before live backend APIs are ready.
- Keep API access in frontend service boundaries.
- Do not duplicate mastery or recommendation calculations in the UI.
- Render subject summaries from backend-provided data.
- Preserve concept IDs, subject IDs and evidence references.
- Show clear loading, empty, error and fallback states.
- Support demo mode with seeded data and mocked tutor responses.

## Testing responsibilities

- Test learner assessment navigation.
- Test subject summary → concept detail drill-down.
- Test adaptive recommendation display.
- Test hint and explanation states.
- Test teacher intervention review states.
- Test loading, empty and AI-fallback states.
- Test the Riya and Arjun demo flows.
- Test accessibility basics such as keyboard navigation and readable status labels.

## Boundaries

Do not:

- Implement learning policy or mastery calculations in frontend components.
- Hard-code AI output as if it came from the backend.
- Depend on database models or backend internal imports.
- Hide uncertainty, confidence or teacher-review flags.
- Expand the MVP to multiple subjects before the Class 9 Mathematics flow works.

## Definition of done

Divyansh's work is complete when:

- Learner and teacher flows are usable with mock contract data.
- Subject summaries drill down to concept-level evidence.
- The adaptive learner journey is visible end to end.
- The teacher sees an actionable intervention queue.
- AI hints and explanations show source or fallback states.
- The frontend can switch from mock services to backend APIs without redesigning the screens.
- Tests cover the main learner and teacher workflows.
