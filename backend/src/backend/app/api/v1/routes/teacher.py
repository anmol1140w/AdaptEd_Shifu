import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from psycopg.types.json import Json

from backend.app.api.v1.dependencies import current_user, teacher_only
from backend.app.domain.entities.question_bank import QuestionDraft
from backend.app.domain.services.question_classifier import QuestionClassifier
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


def _classify_bloom_level(question: QuizQuestionRequest) -> str:
    question_type = question.question_type.casefold()
    fields = {f"option_{letter}": choice for letter, choice in zip("abcd", question.choices)}
    try:
        classification = QuestionClassifier().classify(QuestionDraft(
            question=question.prompt.strip(),
            question_type=question_type,
            subject="jee",
            topic="classroom quiz",
            correct_answer=question.answer.strip(),
            fields=fields,
        ))
        return classification.bloom_level.name.casefold()
    except ValueError:
        # Preserve quiz creation for incomplete MCQ option sets; the schema default
        # still gives the question a visible, reviewable Bloom level.
        return "understand"


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
                """INSERT INTO teacher_quiz_questions
                   (id, quiz_id, position, prompt, question_type, choices, answer, explanation, hints, bloom_level)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (str(uuid.uuid4()), quiz_id, position, question.prompt.strip(), question.question_type, Json(question.choices), question.answer.strip(), question.explanation.strip(), Json(question.hints), _classify_bloom_level(question)),
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


def _owned_student(connection, slug: str, student_id: str, teacher_id: str):
    return connection.execute(
        """SELECT u.id, u.name, u.email, m.joined_at, c.id AS classroom_id, c.name AS classroom_name
           FROM classrooms c JOIN classroom_memberships m ON m.classroom_id = c.id
           JOIN users u ON u.id = m.user_id
           WHERE c.public_slug = %s AND c.owner_id = %s AND u.id = %s AND m.role = 'student'""",
        (slug, teacher_id, student_id),
    ).fetchone()


@router.get("/classrooms/{slug}/students/{student_id}/profile")
def student_profile(slug: str, student_id: str, teacher=Depends(teacher_only)):
    connection = connect()
    try:
        student = _owned_student(connection, slug, student_id, teacher["id"])
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found in this classroom")
        summary = connection.execute(
            """SELECT COUNT(a.id)::int AS attempts,
                      COUNT(a.id) FILTER (WHERE a.correct)::int AS solved,
                      COUNT(DISTINCT a.problem_id)::int AS problems_attempted,
                      COUNT(DISTINCT a.created_at::date)::int AS active_days,
                      COALESCE(AVG(CASE WHEN a.id IS NOT NULL THEN (a.correct::int) END), 0)::float AS accuracy
               FROM users u LEFT JOIN problem_attempts a ON a.user_id = u.id
               WHERE u.id = %s GROUP BY u.id""",
            (student_id,),
        ).fetchone()
        topics = connection.execute(
            """SELECT t.name, COUNT(a.id)::int AS attempts,
                      COUNT(a.id) FILTER (WHERE a.correct)::int AS solved,
                      COALESCE(AVG(a.correct::int), 0)::float AS accuracy
               FROM problem_attempts a JOIN problem_topics pt ON pt.problem_id = a.problem_id
               JOIN jee_topics t ON t.id = pt.topic_id
               WHERE a.user_id = %s GROUP BY t.id, t.name ORDER BY accuracy ASC, attempts DESC, t.name LIMIT 12""",
            (student_id,),
        ).fetchall()
        recent = connection.execute(
            """SELECT p.title, p.subject, p.chapter, a.correct, a.created_at
               FROM problem_attempts a JOIN jee_problems p ON p.id = a.problem_id
               WHERE a.user_id = %s ORDER BY a.created_at DESC LIMIT 12""",
            (student_id,),
        ).fetchall()
        return {"student": student, "summary": summary, "topics": topics, "recent": recent}
    finally:
        connection.close()


@router.get("/classrooms/{slug}/analytics")
def classroom_analytics(slug: str, teacher=Depends(teacher_only)):
    connection = connect()
    try:
        classroom = connection.execute(
            "SELECT id, name FROM classrooms WHERE public_slug = %s AND owner_id = %s",
            (slug, teacher["id"]),
        ).fetchone()
        if classroom is None:
            raise HTTPException(status_code=404, detail="Classroom not found")
        overview = connection.execute(
            """WITH student_stats AS (
                 SELECT m.user_id, COUNT(a.id)::int AS attempts,
                        COUNT(a.id) FILTER (WHERE a.correct)::int AS solved,
                        COUNT(DISTINCT a.created_at::date)::int AS active_days,
                        COALESCE(AVG(a.correct::int), 0)::float AS accuracy
                 FROM classroom_memberships m LEFT JOIN problem_attempts a ON a.user_id = m.user_id
                 WHERE m.classroom_id = %s AND m.role = 'student'
                 GROUP BY m.user_id
               )
               SELECT COUNT(*)::int AS students,
                      COALESCE(SUM(attempts), 0)::int AS attempts,
                      COALESCE(SUM(solved), 0)::int AS solved,
                      COALESCE(SUM(active_days), 0)::int AS active_days,
                      COALESCE(AVG(accuracy), 0)::float AS accuracy,
                      COALESCE(AVG(attempts), 0)::float AS average_attempts,
                      COALESCE(AVG(solved), 0)::float AS average_solved
               FROM student_stats""",
            (classroom["id"],),
        ).fetchone()
        below_threshold = connection.execute(
            """SELECT COUNT(*)::int AS count FROM (
                 SELECT m.user_id, COALESCE(AVG(a.correct::int), 0) AS accuracy
                 FROM classroom_memberships m LEFT JOIN problem_attempts a ON a.user_id = m.user_id
                 WHERE m.classroom_id = %s AND m.role = 'student'
                 GROUP BY m.user_id
               ) student_scores WHERE accuracy < 0.5""",
            (classroom["id"],),
        ).fetchone()
        topics = connection.execute(
            """SELECT t.name, COUNT(a.id)::int AS attempts,
                      COUNT(a.id) FILTER (WHERE a.correct)::int AS solved,
                      COUNT(DISTINCT a.user_id)::int AS students,
                      COALESCE(AVG(a.correct::int), 0)::float AS accuracy
               FROM classroom_memberships m JOIN problem_attempts a ON a.user_id = m.user_id
               JOIN problem_topics pt ON pt.problem_id = a.problem_id
               JOIN jee_topics t ON t.id = pt.topic_id
               WHERE m.classroom_id = %s AND m.role = 'student'
               GROUP BY t.id, t.name ORDER BY accuracy ASC, attempts DESC, t.name LIMIT 12""",
            (classroom["id"],),
        ).fetchall()
        return {"classroom": classroom, "overview": {**overview, "below_threshold": below_threshold["count"]}, "topics": topics}
    finally:
        connection.close()


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
    questions = connection.execute("SELECT id, position, prompt, question_type, choices, answer, explanation, hints, bloom_level FROM teacher_quiz_questions WHERE quiz_id = %s ORDER BY position", (quiz_id,)).fetchall()
    connection.close()
    return {"quiz": {**quiz, "questions": questions}}

