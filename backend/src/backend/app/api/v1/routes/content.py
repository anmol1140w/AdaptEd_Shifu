import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.api.v1.dependencies import current_user
from backend.app.infrastructure.database.connection import connect

router = APIRouter(prefix="/content", tags=["jee-content"])


class AttemptRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=2000)
    time_taken: int = Field(default=0, ge=0, le=86400)
    hint_used: bool = False


@router.get("/topics")
def list_topics(subject: str | None = Query(default=None)):
    connection = connect()
    try:
        if subject:
            rows = connection.execute(
                """SELECT t.id, t.subject, t.name, t.slug, COUNT(pt.problem_id)::int AS problem_count
                   FROM jee_topics t LEFT JOIN problem_topics pt ON pt.topic_id = t.id
                   WHERE t.subject = %s GROUP BY t.id ORDER BY t.subject, t.name""", (subject,)
            ).fetchall()
        else:
            rows = connection.execute(
                """SELECT t.id, t.subject, t.name, t.slug, COUNT(pt.problem_id)::int AS problem_count
                   FROM jee_topics t LEFT JOIN problem_topics pt ON pt.topic_id = t.id
                   GROUP BY t.id ORDER BY t.subject, t.name"""
            ).fetchall()
        return {"topics": rows}
    finally:
        connection.close()


@router.get("/problems")
def list_problems(topic: str | None = Query(default=None), subject: str | None = Query(default=None), search: str | None = Query(default=None), user=Depends(current_user)):
    connection = connect()
    try:
        clauses: list[str] = []
        values: list[str] = []
        if topic:
            clauses.append("t.slug = %s")
            values.append(topic)
        if subject:
            clauses.append("p.subject = %s")
            values.append(subject)
        if search:
            clauses.append("(p.title ILIKE %s OR p.statement ILIKE %s)")
            values.extend([f"%{search}%", f"%{search}%"])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = connection.execute(
            f"""SELECT p.id, p.title, p.subject, p.chapter, p.question_type, p.difficulty,
                       p.estimated_minutes, p.exam_relevance,
                       COALESCE(bool_or(a.correct), FALSE) AS solved,
                       COALESCE(bool_or(a.id IS NOT NULL), FALSE) AS attempted,
                       COALESCE(array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL), '{{}}') AS topics
                FROM jee_problems p LEFT JOIN problem_topics pt ON pt.problem_id = p.id
                LEFT JOIN jee_topics t ON t.id = pt.topic_id
                LEFT JOIN problem_attempts a ON a.problem_id = p.id AND a.user_id = %s
                {where}
                GROUP BY p.id ORDER BY p.subject, p.chapter, p.id""", [user["id"], *values]
        ).fetchall()
        return {"problems": rows}
    finally:
        connection.close()


@router.get("/problems/{problem_id}")
def get_problem(problem_id: str, user=Depends(current_user)):
    connection = connect()
    try:
        row = connection.execute(
            """SELECT p.*, COALESCE(array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL), '{}') AS topics,
                      COALESCE((SELECT jsonb_agg(jsonb_build_object('correct', a.correct, 'created_at', a.created_at)
                        ORDER BY a.created_at DESC) FROM problem_attempts a WHERE a.problem_id = p.id AND a.user_id = %s), '[]') AS attempts
               FROM jee_problems p LEFT JOIN problem_topics pt ON pt.problem_id = p.id
               LEFT JOIN jee_topics t ON t.id = pt.topic_id WHERE p.id = %s GROUP BY p.id""",
            (user["id"], problem_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Problem not found")
        return {"problem": row}
    finally:
        connection.close()


@router.post("/problems/{problem_id}/attempt", status_code=status.HTTP_201_CREATED)
def submit_attempt(problem_id: str, payload: AttemptRequest, user=Depends(current_user)):
    connection = connect()
    try:
        problem = connection.execute("SELECT answer FROM jee_problems WHERE id = %s", (problem_id,)).fetchone()
        if problem is None:
            raise HTTPException(status_code=404, detail="Problem not found")
        correct = payload.answer.strip().casefold() == str(problem["answer"]).strip().casefold()
        row = connection.execute(
            """INSERT INTO problem_attempts (id, problem_id, user_id, answer, correct, time_taken, hint_used)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id, correct, created_at""",
            (str(uuid.uuid4()), problem_id, user["id"], payload.answer.strip(), correct, payload.time_taken, payload.hint_used),
        ).fetchone()
        connection.commit()
        return {"attempt": row}
    finally:
        connection.close()

