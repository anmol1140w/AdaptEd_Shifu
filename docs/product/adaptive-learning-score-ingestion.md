# Adaptive learning score integration

The student adaptive-assessment API persists attempts in PostgreSQL. An assessment can be started as `adaptive` (next questions respond to stored evidence) or `mock` (a fixed, balanced snapshot of teacher-approved questions). Only `learning_items.approved = true` items are served.

## Import results from a teammate quiz module

`POST /api/v1/teacher/learning-evidence/import` accepts a teacher-authenticated request. The student must belong to a classroom owned by that teacher at the supplied class level. `concept_id` values must match the server's authored concept map for the subject and class. A single quiz submission is one event; each question contributes an independently scored evidence row.

```json
{
  "source_system": "adapted-quiz-module",
  "source_event_id": "quiz-attempt-unique-id",
  "student_id": "student-account-id",
  "quiz_id": "quiz-id",
  "subject": "physics",
  "class_level": 11,
  "attempted_at": "2026-10-28T10:30:00Z",
  "questions": [
    {
      "question_id": "question-id",
      "concept_id": "authored-concept-id",
      "question": "Question text",
      "response": "Student response",
      "score": 1.5,
      "max_score": 2,
      "difficulty": "medium",
      "time_taken": 72
    }
  ]
}
```

`question_id` may be omitted; the API derives one from normalized question text. `(source_system, source_event_id, question_id)` is the idempotency key. Repeating the same data is reported as already imported; reusing that key with different learner, quiz, concept, score, or response data returns `409`. The caller should retain and retry the same event ID when delivery is uncertain.

Imported marks are retained as raw `score`/`max_score` evidence. For the adaptive mastery policy, a normalized result of at least `0.7` counts as correct. Progress, adaptive selection, and personalized recommendations incorporate both these records and app-native attempts. At assessment completion, the response includes `summary.topic_scores`, keyed by concept ID, with accuracy for this assessment and mastery/confidence/trend from the learner's combined saved evidence.

The learner result page links to `/student/ai-tutoring`, which displays the per-topic summary and sends it as personalization context. Those scores guide topic selection only; academic claims still must use retrieved NCERT passages. Quiz-generation drafts continue to require teacher review.
