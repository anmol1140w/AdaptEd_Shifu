"""Regression tests for mapping boolean attempt results into numeric evidence."""

from __future__ import annotations

import unittest
from pathlib import Path



class LearningProgressSqlTests(unittest.TestCase):
    def test_progress_and_teacher_analytics_do_not_cast_boolean_to_float(self) -> None:
        route_path = Path(__file__).resolve().parents[3] / "src/backend/app/api/v1/routes/learning.py"
        source = route_path.read_text(encoding="utf-8")

        self.assertEqual(source.count("CASE WHEN a.correct THEN 1.0::double precision"), 3)
        self.assertEqual(source.count("ELSE 0.0::double precision END AS score"), 3)
        self.assertNotIn("a.correct::float", source)


if __name__ == "__main__":
    unittest.main()
