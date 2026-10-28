# AdaptCoins and classroom leaderboards

AdaptCoins are stored as immutable rows in `learner_coin_events`. Event keys are unique per learner, so retries and repeat submissions cannot claim the same reward twice. Classroom quiz answers and scores are stored in `teacher_quiz_attempts`; the server grades submissions and does not send answer keys to students.

## Rewards

| Activity | Reward |
| --- | ---: |
| Student daily check-in | 1 per day |
| First successful AI tutor response | 1 per day |
| Correct database-backed practice problem | 10 per problem |
| Adaptive assessment completion | 10 per day |
| New classroom quiz completion | 10 per quiz |
| Quiz participation | 5 per week |
| Mock assessment completion | 5 per fortnight |
| Quiz and assessment in the same week | 35 bonus |
| Practice on 25 different days in a month | 25 bonus |
| Practice every day in a completed month | 25 additional bonus |

The final two milestones are evaluated in the `Asia/Kolkata` timezone. Activity and point history remain in the database if the student signs out or changes devices.

## Where to see it

- Students: **Leaderboard** in the student navigation. It shows their AdaptCoins, monthly challenge progress, coin history, and their classroom ranks for this month or all time.
- Teachers: **Class leaderboard** in the teacher workspace. A teacher can view only classrooms they own; students can view only classrooms they have joined.
- APIs: `GET /api/v1/rewards/summary`, `GET /api/v1/rewards/leaderboard`, and `POST /api/v1/rewards/check-in`.

Adaptive/mock assessments, published classroom quizzes, database-backed practice problems, connected quiz results, and successful tutor responses are eligible. The older sample Problems/Chapter quizzes are explicitly local demo content and are not included in the ledger; they must be moved to a server-graded question bank before they can safely earn persistent points.

The additive table definitions live in `backend/src/backend/app/infrastructure/database/connection.py` and are applied by the existing database connection bootstrap.
