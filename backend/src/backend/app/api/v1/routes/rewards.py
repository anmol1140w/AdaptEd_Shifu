"""Persistent student coins and classroom leaderboards."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.api.v1.dependencies import current_user
from backend.app.infrastructure.database.connection import connect
from backend.app.infrastructure.database.rewards import (
    APP_TIMEZONE,
    award_check_in,
    settle_monthly_bonus,
    total_coins,
)


router = APIRouter(prefix="/rewards", tags=["rewards"])


def _classrooms(connection, user: dict) -> list[dict]:
    if user["role"] == "teacher":
        rows = connection.execute(
            "SELECT id,name,class_level FROM classrooms WHERE owner_id=%s ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()
    else:
        rows = connection.execute(
            """SELECT c.id,c.name,c.class_level FROM classrooms c
               JOIN classroom_memberships m ON m.classroom_id=c.id
               WHERE m.user_id=%s AND m.role='student'
               ORDER BY m.joined_at DESC""",
            (user["id"],),
        ).fetchall()
    return [dict(row) for row in rows]


@router.post("/check-in")
def daily_check_in(user=Depends(current_user)):
    if user["role"] != "student":
        raise HTTPException(status_code=403, detail="Daily check-in is available to students")
    connection = connect()
    try:
        earned = award_check_in(connection, user["id"])
        balance = total_coins(connection, user["id"])
        connection.commit()
        return {"points_awarded": earned, "coins": balance, "already_checked_in": earned == 0}
    finally:
        connection.close()


@router.get("/summary")
def reward_summary(user=Depends(current_user)):
    connection = connect()
    try:
        today = datetime.now(APP_TIMEZONE).date()
        settle_monthly_bonus(connection, user["id"], today)
        month_key = today.strftime("%Y-%m")
        totals = connection.execute(
            """SELECT COALESCE(SUM(points),0)::int AS all_time,
                      COALESCE(SUM(points) FILTER (WHERE COALESCE(metadata->>'month',substring(metadata->>'activity_date' from 1 for 7))=%s),0)::int AS this_month,
                      COALESCE(SUM(points) FILTER (WHERE metadata->>'activity_date'=%s),0)::int AS today
               FROM learner_coin_events WHERE user_id=%s""",
            (month_key, today.isoformat(), user["id"]),
        ).fetchone()
        active = connection.execute(
            """SELECT COUNT(DISTINCT metadata->>'activity_date')::int AS days
               FROM learner_coin_events WHERE user_id=%s AND event_type=ANY(%s)
                 AND metadata->>'activity_date'>=%s""",
            (user["id"], ["problem_activity", "assessment_completed", "teacher_quiz_activity", "external_quiz_activity"], today.replace(day=1).isoformat()),
        ).fetchone()
        events = connection.execute(
            """SELECT event_type,points,description,metadata,created_at
               FROM learner_coin_events WHERE user_id=%s AND points>0
               ORDER BY created_at DESC,id DESC LIMIT 12""",
            (user["id"],),
        ).fetchall()
        connection.commit()
        return {
            "coins": int(totals["all_time"] or 0),
            "month_coins": int(totals["this_month"] or 0),
            "today_coins": int(totals["today"] or 0),
            "challenge_days_this_month": int(active["days"] or 0),
            "challenge_days_goal": 25,
            "events": [dict(row) for row in events],
        }
    finally:
        connection.close()


@router.get("/leaderboard")
def classroom_leaderboard(
    classroom_id: str | None = Query(default=None),
    period: str = Query(default="month", pattern="^(month|all_time)$"),
    user=Depends(current_user),
):
    connection = connect()
    try:
        classrooms = _classrooms(connection, user)
        available_ids = {row["id"] for row in classrooms}
        selected_id = classroom_id or (classrooms[0]["id"] if classrooms else None)
        if selected_id and selected_id not in available_ids:
            raise HTTPException(status_code=403, detail="You do not have access to this classroom leaderboard")
        if not selected_id:
            return {"classrooms": classrooms, "classroom": None, "period": period, "leaderboard": [], "my_rank": None}
        selected = next(row for row in classrooms if row["id"] == selected_id)
        period_month = None
        if period == "month":
            today = datetime.now(APP_TIMEZONE).date()
            period_month = today.strftime("%Y-%m")
        rows = connection.execute(
            """WITH scores AS (
                   SELECT u.id AS student_id,u.name,
                          COALESCE(SUM(e.points),0)::int AS coins
                   FROM classroom_memberships m
                   JOIN users u ON u.id=m.user_id AND u.role='student'
                   LEFT JOIN learner_coin_events e ON e.user_id=u.id
                     AND (%s::text IS NULL OR COALESCE(e.metadata->>'month',substring(e.metadata->>'activity_date' from 1 for 7))=%s)
                   WHERE m.classroom_id=%s AND m.role='student'
                   GROUP BY u.id,u.name
               ), ranked AS (
                   SELECT student_id,name,coins,
                          ROW_NUMBER() OVER (ORDER BY coins DESC,lower(name),student_id)::int AS rank
                   FROM scores
               )
               SELECT student_id,name,coins,rank FROM ranked
               WHERE rank<=50 OR student_id=%s ORDER BY rank""",
            (period_month, period_month, selected_id, user["id"]),
        ).fetchall()
        rows = [dict(row) for row in rows]
        my_rank = next((row["rank"] for row in rows if row["student_id"] == user["id"]), None)
        leaderboard = [row for row in rows if row["rank"] <= 50]
        return {
            "classrooms": classrooms,
            "classroom": selected,
            "period": period,
            "leaderboard": leaderboard,
            "my_rank": my_rank,
        }
    finally:
        connection.close()
