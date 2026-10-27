from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.core.settings import settings
from backend.main import app


def test_classroom_join_uses_separate_opaque_slug():
    settings.teacher_invite_code = "teacher-demo"
    client = TestClient(app)
    suffix = uuid4().hex[:10]

    teacher = client.post("/api/v1/auth/register", json={"email": f"teacher-{suffix}@example.com", "name": "Teacher", "password": "password123", "teacher_invite_code": "teacher-demo"})
    student = client.post("/api/v1/auth/register", json={"email": f"student-{suffix}@example.com", "name": "Student", "password": "password123"})
    assert teacher.status_code == 201
    assert student.status_code == 201

    teacher_headers = {"Authorization": f"Bearer {teacher.json()['access_token']}"}
    student_headers = {"Authorization": f"Bearer {student.json()['access_token']}"}
    created = client.post("/api/v1/classrooms", headers=teacher_headers, json={"name": "Algebra"})
    assert created.status_code == 201
    classroom = created.json()["classroom"]

    assert classroom["slug"] != classroom["join_code"]
    assert client.post("/api/v1/classrooms", headers=student_headers, json={"name": "Forbidden"}).status_code == 403
    assert client.post("/api/v1/classrooms/join", headers=student_headers, json={"code": classroom["join_code"]}).status_code == 200
    assert client.get(f"/api/v1/classrooms/{classroom['slug']}", headers=student_headers).status_code == 200
    assert client.post("/api/v1/classrooms/join", headers=student_headers, json={"code": "invalid-code"}).status_code == 404
