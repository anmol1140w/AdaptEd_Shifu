from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from backend.app.infrastructure.database.rewards import (
    activity_context,
    award_event,
    award_external_quiz_completion,
    award_teacher_quiz_completion,
)


class FakeCursor:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.calls = []

    def execute(self, query, params):
        self.calls.append((query, params))
        return FakeCursor(self.row)


class RewardTests(unittest.TestCase):
    def test_activity_date_uses_india_local_date(self):
        now = datetime(2026, 10, 27, 20, 0, tzinfo=timezone.utc)

        self.assertEqual(
            activity_context(now),
            {"activity_date": "2026-10-28", "activity_week": "2026-W44", "activity_fortnight": "2026-F22"},
        )

    def test_event_is_namespaced_and_existing_event_awards_zero(self):
        connection = FakeConnection({"points": 10})

        awarded = award_event(connection, "student-1", "problem:first", "problem_solved", 10, "Solved")

        self.assertEqual(awarded, 10)
        self.assertEqual(connection.calls[0][1][2], "student-1:problem:first")
        connection.row = None
        self.assertEqual(award_event(connection, "student-1", "problem:first", "problem_solved", 10, "Solved"), 0)

    def test_negative_coin_award_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "negative points"):
            award_event(FakeConnection(None), "student-1", "bad", "bad", -1, "Bad")

    def test_teacher_and_connected_quizzes_share_one_weekly_reward_key(self):
        connection = FakeConnection({"quizzes": 1, "assessments": 0})
        event_keys = []

        def record(_connection, _user_id, event_key, *_args, **_kwargs):
            event_keys.append(event_key)
            return 5 if event_key.startswith("quiz_week:") else 0

        with patch("backend.app.infrastructure.database.rewards.award_event", side_effect=record), patch("backend.app.infrastructure.database.rewards.settle_monthly_bonus"):
            award_teacher_quiz_completion(connection, "student-1", "quiz-1", "attempt-1")
            award_external_quiz_completion(connection, "student-1", "quiz-app", "event-1", "quiz-2")

        weekly_keys = [key for key in event_keys if key.startswith("quiz_week:")]
        self.assertEqual(len(weekly_keys), 2)
        self.assertEqual(weekly_keys[0], weekly_keys[1])


if __name__ == "__main__":
    unittest.main()
