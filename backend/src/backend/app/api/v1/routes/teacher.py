import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from psycopg.types.json import Json

from backend.app.api.v1.dependencies import current_user, teacher_only
from backend.app.infrastructure.database.connection import connect
from backend.app.infrastructure.database.rewards import award_teacher_quiz_completion, total_coins

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


class StudentQuizAttemptRequest(BaseModel):
    attempt_id: str = Field(min_length=1, max_length=80)
    answers: dict[str, str] = Field(default_factory=dict, max_length=100)


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
    questions = connection.execute("SELECT id, position, prompt, question_type, choices FROM teacher_quiz_questions WHERE quiz_id = %s ORDER BY position", (quiz_id,)).fetchall()
    connection.close()
    return {"quiz": {**quiz, "questions": questions}}


@router.post("/student-quizzes/{quiz_id}/attempt")
def submit_student_quiz_attempt(quiz_id: str, payload: StudentQuizAttemptRequest, user=Depends(current_user)):
    if user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can submit classroom quizzes")
    connection = connect()
    try:
        existing = connection.execute(
            "SELECT id,user_id,quiz_id,score,max_score,points_awarded FROM teacher_quiz_attempts WHERE id=%s",
            (payload.attempt_id,),
        ).fetchone()
        if existing:
            if existing["user_id"] != user["id"] or existing["quiz_id"] != quiz_id:
                raise HTTPException(status_code=409, detail="This attempt ID is already in use")
            result = {"attempt_id": existing["id"], "score": existing["score"], "max_score": existing["max_score"], "points_awarded": existing["points_awarded"], "coins": total_coins(connection, user["id"]), "already_submitted": True}
            connection.commit()
            return result
        quiz = connection.execute(
            """SELECT q.id FROM teacher_quizzes q JOIN classroom_memberships m ON m.classroom_id=q.classroom_id
               WHERE q.id=%s AND q.published=TRUE AND m.user_id=%s AND m.role='student'""",
            (quiz_id, user["id"]),
        ).fetchone()
        if quiz is None:
            raise HTTPException(status_code=404, detail="Quiz not found")
        questions = connection.execute(
            "SELECT id,answer FROM teacher_quiz_questions WHERE quiz_id=%s ORDER BY position",
            (quiz_id,),
        ).fetchall()
        if not questions:
            raise HTTPException(status_code=409, detail="This quiz has no questions")
        valid_ids = {question["id"] for question in questions}
        if set(payload.answers) - valid_ids:
            raise HTTPException(status_code=422, detail="Answers contain a question that is not part of this quiz")
        if set(payload.answers) != valid_ids or any(not answer.strip() for answer in payload.answers.values()):
            raise HTTPException(status_code=422, detail="Answer every question before submitting the quiz")
        normalize = lambda value: "".join(value.strip().casefold().split()).replace("−", "-").replace("–", "-")
        score = sum(
            normalize(payload.answers.get(question["id"], "")) == normalize(str(question["answer"]))
            for question in questions
        )
        coins_awarded = award_teacher_quiz_completion(connection, user["id"], quiz_id, payload.attempt_id)
        inserted = connection.execute(
            """INSERT INTO teacher_quiz_attempts
               (id,quiz_id,user_id,answers,score,max_score,points_awarded)
               VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s)
               ON CONFLICT (id) DO NOTHING
               RETURNING id""",
            (payload.attempt_id, quiz_id, user["id"], json.dumps(payload.answers), score, len(questions), coins_awarded),
        ).fetchone()
        if inserted is None:
            existing = connection.execute(
                "SELECT id,user_id,quiz_id,score,max_score,points_awarded FROM teacher_quiz_attempts WHERE id=%s",
                (payload.attempt_id,),
            ).fetchone()
            if not existing or existing["user_id"] != user["id"] or existing["quiz_id"] != quiz_id:
                raise HTTPException(status_code=409, detail="This attempt ID is already in use")
            result = {"attempt_id": existing["id"], "score": existing["score"], "max_score": existing["max_score"], "points_awarded": existing["points_awarded"], "coins": total_coins(connection, user["id"]), "already_submitted": True}
            connection.commit()
            return result
        result = {"attempt_id": payload.attempt_id, "score": score, "max_score": len(questions), "points_awarded": coins_awarded, "coins": total_coins(connection, user["id"]), "already_submitted": False}
        connection.commit()
        return result
    except HTTPException:
        connection.rollback()
        raise
    finally:
        connection.close()

