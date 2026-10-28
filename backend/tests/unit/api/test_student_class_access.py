"""Student class access follows classroom membership, not a client supplied grade."""

from __future__ import annotations

import unittest
import ast
from pathlib import Path
from typing import Any

from fastapi import HTTPException


_route_path = Path(__file__).resolve().parents[3] / "src/backend/app/api/v1/routes/learning.py"
_tree = ast.parse(_route_path.read_text(encoding="utf-8"))
_helpers = [
    node for node in _tree.body
    if isinstance(node, ast.FunctionDef) and node.name in {"_student_class_levels", "_require_student_class"}
]
_module = ast.Module(
    body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *_helpers],
    type_ignores=[],
)
_namespace: dict[str, Any] = {"Any": Any, "HTTPException": HTTPException}
exec(compile(ast.fix_missing_locations(_module), str(_route_path), "exec"), _namespace)
_student_class_levels = _namespace["_student_class_levels"]
_require_student_class = _namespace["_require_student_class"]


class FakeConnection:
    def __init__(self, levels: list[int]) -> None:
        self.levels = levels
        self.queries: list[tuple[str, tuple[object, ...]]] = []

    def execute(self, query: str, params: tuple[object, ...]):
        self.queries.append((query, params))
        return self

    def fetchone(self) -> dict[str, int] | None:
        return {"class_level": self.levels[0]} if self.levels else None


class StudentClassAccessTests(unittest.TestCase):
    def test_class_levels_are_read_from_student_memberships(self) -> None:
        connection = FakeConnection([12, 11])

        self.assertEqual(_student_class_levels(connection, {"id": "student-1", "role": "student"}), [12])
        self.assertEqual(connection.queries[0][1], ("student-1",))
        self.assertIn("ORDER BY m.joined_at DESC", connection.queries[0][0])

    def test_student_cannot_request_a_class_without_membership(self) -> None:
        connection = FakeConnection([12])

        with self.assertRaises(HTTPException) as error:
            _require_student_class(connection, {"id": "student-1", "role": "student"}, 11)

        self.assertEqual(error.exception.status_code, 403)

    def test_student_can_request_an_enrolled_class(self) -> None:
        _require_student_class(FakeConnection([11]), {"id": "student-1", "role": "student"}, 11)

    def test_teacher_can_review_either_class(self) -> None:
        _require_student_class(FakeConnection([]), {"id": "teacher-1", "role": "teacher"}, 12)


if __name__ == "__main__":
    unittest.main()
