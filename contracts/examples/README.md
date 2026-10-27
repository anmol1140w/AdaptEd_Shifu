# Contract examples

The versioned examples show the assessment contracts with synthetic learners.
They are fixtures for frontend development and contract tests, not classroom
results.

## Files

- `v1/riya_assessment.json` demonstrates a foundation gap, repeated errors,
  high hint use, prerequisite support and teacher review.
- `v1/arjun_assessment.json` demonstrates stable independent mastery and a
  transfer-practice recommendation.
- The subject-summary v1 contracts expose the same learner evidence as a
  subject aggregate with concept-level drill-down.
- `v1/riya_subject_summary.json` demonstrates aggregate metrics, an unresolved
  foundation gap, prerequisite support, and an unassessed concept.
- `v1/riya_learning_support.json` demonstrates a grounded non-spoiler tutor hint
  and a source-linked weak-area quiz.

Assessment fixtures contain a start-assessment request/response pair and a
later submit-attempt request/response pair. Subject-summary and learning-support
fixtures contain the corresponding request/response pairs for those boundaries.
All examples are synthetic and intended for frontend development and contract
tests.
