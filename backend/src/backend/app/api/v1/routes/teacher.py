import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from psycopg.types.json import Json

from backend.app.api.v1.dependencies import current_user, teacher_only
from backend.app.infrastructure.database.connection import connect

router = APIRouter(prefix="/teacher", tags=["teacher"])


class QuizQuestionRequest(BaseModel):
    prompt: str = Field(min_length=5, max_length=5000)
    question_type: str = Field(default="MCQ", pattern="^(MCQ|Numerical)$")
    choices: list[str] = Field(default_factory=list, max_length=6)
    answer: str = Field(min_length=1, max_length=2000)
    explanation: str = Field(default="", max_length=5000)
    hints: list[str] = Field(default_factory=list, max_length=5)


class QuizCreateRequest(BaseModel):
    classroom_slug: str
    title: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=2000)
    difficulty: str = Field(pattern="^(Easy|Medium|Hard)$")
    time_limit_minutes: int = Field(default=30, ge=1, le=300)
    questions: list[QuizQuestionRequest] = Field(min_length=1, max_length=100)


@router.get("/classrooms")
def teacher_classrooms(teacher=Depends(teacher_only)):
    connection = connect()
    rows = connection.execute(
        """SELECT c.*, COUNT(m.user_id) FILTER (WHERE m.role = 'student')::int AS student_count,
           COUNT(q.id)::int AS quiz_count
           FROM classrooms c LEFT JOIN classroom_memberships m ON m.classroom_id = c.id
           LEFT JOIN teacher_quizzes q ON q.classroom_id = c.id
           WHERE c.owner_id = %s GROUP BY c.id ORDER BY c.created_at DESC""",
        (teacher["id"],),
    ).fetchall()
    connection.close()
    return {"classrooms": rows}


@router.post("/quizzes", status_code=status.HTTP_201_CREATED)
def create_quiz(payload: QuizCreateRequest, teacher=Depends(teacher_only)):
    connection = connect()
    classroom = connection.execute("SELECT id FROM classrooms WHERE public_slug = %s AND owner_id = %s", (payload.classroom_slug, teacher["id"])).fetchone()
    if classroom is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Classroom not found")
    quiz_id = str(uuid.uuid4())
    try:
        connection.execute(
            "INSERT INTO teacher_quizzes (id, classroom_id, teacher_id, title, description, difficulty, time_limit_minutes) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (quiz_id, classroom["id"], teacher["id"], payload.title.strip(), payload.description.strip(), payload.difficulty, payload.time_limit_minutes),
        )
        for position, question in enumerate(payload.questions, start=1):
            connection.execute(
                """INSERT INTO teacher_quiz_questions (id, quiz_id, position, prompt, question_type, choices, answer, explanation, hints)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (str(uuid.uuid4()), quiz_id, position, question.prompt.strip(), question.question_type, Json(question.choices), question.answer.strip(), question.explanation.strip(), Json(question.hints)),
            )
        connection.commit()
    finally:
        connection.close()
    return {"quiz_id": quiz_id, "published": True}


@router.get("/classrooms/{slug}/quizzes")
def teacher_quizzes(slug: str, teacher=Depends(teacher_only)):
    connection = connect()
    rows = connection.execute(
        """SELECT q.id, q.title, q.description, q.difficulty, q.time_limit_minutes, q.created_at,
           COUNT(qq.id)::int AS question_count FROM teacher_quizzes q
           JOIN classrooms c ON c.id = q.classroom_id LEFT JOIN teacher_quiz_questions qq ON qq.quiz_id = q.id
           WHERE c.public_slug = %s AND c.owner_id = %s GROUP BY q.id ORDER BY q.created_at DESC""",
        (slug, teacher["id"]),
    ).fetchall()
    connection.close()
    return {"quizzes": rows}


@router.get("/student-quizzes")
def student_quizzes(user=Depends(current_user)):
    connection = connect()
    rows = connection.execute(
        """SELECT q.id, q.title, q.description, q.difficulty, q.time_limit_minutes, q.created_at,
           c.name AS classroom_name, COUNT(qq.id)::int AS question_count
           FROM teacher_quizzes q JOIN classrooms c ON c.id = q.classroom_id
           JOIN classroom_memberships m ON m.classroom_id = c.id LEFT JOIN teacher_quiz_questions qq ON qq.quiz_id = q.id
           WHERE m.user_id = %s AND q.published = TRUE GROUP BY q.id, c.name ORDER BY q.created_at DESC""",
        (user["id"],),
    ).fetchall()
    connection.close()
    return {"quizzes": rows}


@router.get("/student-quizzes/{quiz_id}")
def student_quiz_detail(quiz_id: str, user=Depends(current_user)):
    connection = connect()
    quiz = connection.execute(
        """SELECT q.*, c.name AS classroom_name FROM teacher_quizzes q JOIN classrooms c ON c.id = q.classroom_id
           JOIN classroom_memberships m ON m.classroom_id = c.id WHERE q.id = %s AND m.user_id = %s AND q.published = TRUE""",
        (quiz_id, user["id"]),
    ).fetchone()
    if quiz is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Quiz not found")
    questions = connection.execute("SELECT id, position, prompt, question_type, choices, answer, explanation, hints FROM teacher_quiz_questions WHERE quiz_id = %s ORDER BY position", (quiz_id,)).fetchall()
    connection.close()
    return {"quiz": {**quiz, "questions": questions}}

