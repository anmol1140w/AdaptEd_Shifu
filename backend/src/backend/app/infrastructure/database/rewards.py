"""Idempotent AdaptCoins awards and activity milestones."""

from __future__ import annotations

import calendar
import json
import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo


APP_TIMEZONE = ZoneInfo("Asia/Kolkata")
CHALLENGE_EVENT_TYPES = ("problem_activity", "assessment_completed", "teacher_quiz_activity", "external_quiz_activity")


def activity_context(now: datetime | None = None) -> dict[str, str]:
    local = (now or datetime.now(APP_TIMEZONE)).astimezone(APP_TIMEZONE)
    iso = local.isocalendar()
    return {
        "activity_date": local.date().isoformat(),
        "activity_week": f"{iso.year}-W{iso.week:02d}",
        "activity_fortnight": f"{iso.year}-F{(iso.week - 1) // 2 + 1:02d}",
    }


def award_event(
    connection,
    user_id: str,
    event_key: str,
    event_type: str,
    points: int,
    description: str,
    metadata: dict | None = None,
) -> int:
    """Insert one stable event; return zero when the event was already recorded."""
    if points < 0:
        raise ValueError("Coin events cannot have negative points")
    row = connection.execute(
        """INSERT INTO learner_coin_events
           (id,user_id,event_key,event_type,points,description,metadata)
           VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
           ON CONFLICT (event_key) DO NOTHING RETURNING points""",
        (str(uuid.uuid4()), user_id, f"{user_id}:{event_key}", event_type, points,
         description, json.dumps(metadata or {})),
    ).fetchone()
    return int(row["points"]) if row else 0


def total_coins(connection, user_id: str) -> int:
    row = connection.execute(
        "SELECT COALESCE(SUM(points),0)::int AS points FROM learner_coin_events WHERE user_id=%s",
        (user_id,),
    ).fetchone()
    return int(row["points"] or 0)


def award_check_in(connection, user_id: str) -> int:
    context = activity_context()
    return award_event(
        connection, user_id, f"daily_check_in:{context['activity_date']}", "daily_check_in", 1,
        "Daily check-in", context,
    )


def award_ai_tutor(connection, user_id: str) -> int:
    context = activity_context()
    return award_event(
        connection, user_id, f"ai_tutor_daily:{context['activity_date']}", "ai_tutor_daily", 1,
        "First successful AI tutor question today", context,
    )


def award_problem_solve(connection, user_id: str, problem_id: str, attempt_id: str) -> int:
    context = activity_context()
    award_event(
        connection, user_id, f"problem_activity:{attempt_id}", "problem_activity", 0,
        "Correct problem attempt", {**context, "problem_id": problem_id},
    )
    coins = award_event(
        connection, user_id, f"problem_solved:{problem_id}", "problem_solved", 10,
        "Solved a practice problem", {**context, "problem_id": problem_id},
    )
    settle_monthly_bonus(connection, user_id, date.fromisoformat(context["activity_date"]))
    return coins


def award_assessment_completion(connection, user_id: str, assessment_id: str, assessment_type: str) -> int:
    context = activity_context()
    award_event(
        connection, user_id, f"assessment_activity:{assessment_id}", "assessment_completed", 0,
        "Completed an adaptive assessment" if assessment_type == "adaptive" else "Completed a mock assessment",
        {**context, "assessment_id": assessment_id, "assessment_type": assessment_type},
    )
    coins = award_event(
        connection, user_id, f"assessment_daily:{context['activity_date']}", "assessment_daily_reward", 10,
        "Completed a quiz or assessment", {**context, "assessment_id": assessment_id},
    )
    period_coins = 0
    if assessment_type == "mock":
        period_coins = award_event(
            connection, user_id, f"mock_assessment_fortnight:{context['activity_fortnight']}",
            "mock_assessment_fortnight", 5, "Completed a mock assessment this fortnight", context,
        )
    combo = _award_quiz_assessment_combo(connection, user_id, context)
    settle_monthly_bonus(connection, user_id, date.fromisoformat(context["activity_date"]))
    return coins + period_coins + combo


def award_teacher_quiz_completion(connection, user_id: str, quiz_id: str, attempt_id: str) -> int:
    context = activity_context()
    award_event(
        connection, user_id, f"teacher_quiz_activity:{quiz_id}:{context['activity_date']}", "teacher_quiz_activity", 0,
        "Completed a teacher quiz", {**context, "quiz_id": quiz_id, "attempt_id": attempt_id},
    )
    first_quiz = award_event(
        connection, user_id, f"teacher_quiz_first:{quiz_id}", "teacher_quiz_first", 10,
        "Completed a new teacher quiz", {**context, "quiz_id": quiz_id},
    )
    weekly = award_event(
        connection, user_id, f"quiz_week:{context['activity_week']}",
        "teacher_quiz_week", 5, "Joined a quiz this week", context,
    )
    combo = _award_quiz_assessment_combo(connection, user_id, context)
    settle_monthly_bonus(connection, user_id, date.fromisoformat(context["activity_date"]))
    return first_quiz + weekly + combo


def award_external_quiz_completion(connection, user_id: str, source_system: str, source_event_id: str, quiz_id: str) -> int:
    context = activity_context()
    event_identity = f"{source_system}:{source_event_id}"
    award_event(
        connection, user_id, f"external_quiz_activity:{event_identity}", "external_quiz_activity", 0,
        "Completed a connected quiz", {**context, "quiz_id": quiz_id, "source_system": source_system, "source_event_id": source_event_id},
    )
    earned = award_event(
        connection, user_id, f"external_quiz:{event_identity}", "external_quiz", 10,
        "Completed a connected quiz", {**context, "quiz_id": quiz_id},
    )
    weekly = award_event(
        connection, user_id, f"quiz_week:{context['activity_week']}",
        "external_quiz_week", 5, "Joined a quiz this week", context,
    )
    combo = _award_quiz_assessment_combo(connection, user_id, context)
    settle_monthly_bonus(connection, user_id, date.fromisoformat(context["activity_date"]))
    return earned + weekly + combo


def _award_quiz_assessment_combo(connection, user_id: str, context: dict[str, str]) -> int:
    row = connection.execute(
        """SELECT COUNT(*) FILTER (WHERE event_type IN ('teacher_quiz_activity','external_quiz_activity'))::int AS quizzes,
                  COUNT(*) FILTER (WHERE event_type='assessment_completed')::int AS assessments
           FROM learner_coin_events
           WHERE user_id=%s AND metadata->>'activity_week'=%s""",
        (user_id, context["activity_week"]),
    ).fetchone()
    if not row or not row["quizzes"] or not row["assessments"]:
        return 0
    return award_event(
        connection, user_id, f"quiz_assessment_combo:{context['activity_week']}",
        "quiz_assessment_combo", 35, "Completed a quiz and an assessment in the same week", context,
    )


def settle_monthly_bonus(connection, user_id: str, current_date: date | None = None) -> None:
    """Award 25 for 25 active challenge days and 25 more for a full finished month."""
    today = current_date or datetime.now(APP_TIMEZONE).date()
    current_month = date(today.year, today.month, 1)
    recorded_months = connection.execute(
        """SELECT DISTINCT substring(metadata->>'activity_date' from 1 for 7) AS month_key
           FROM learner_coin_events WHERE user_id=%s AND event_type=ANY(%s)
             AND metadata->>'activity_date'<%s""",
        (user_id, list(CHALLENGE_EVENT_TYPES), current_month.isoformat()),
    ).fetchall()
    months = {(today.year, today.month)}
    for row in recorded_months:
        year_text, month_text = row["month_key"].split("-")
        months.add((int(year_text), int(month_text)))
    for year, month in sorted(months):
        month_key = f"{year:04d}-{month:02d}"
        first = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        rows = connection.execute(
            """SELECT DISTINCT metadata->>'activity_date' AS activity_date
               FROM learner_coin_events
               WHERE user_id=%s AND event_type=ANY(%s)
                 AND metadata->>'activity_date'>=%s AND metadata->>'activity_date'<=%s""",
            (user_id, list(CHALLENGE_EVENT_TYPES), first.isoformat(), date(year, month, last_day).isoformat()),
        ).fetchall()
        active_days = len(rows)
        bonus_context = {
            "month": month_key,
            "active_days": active_days,
            "activity_date": today.isoformat()
            if (year, month) == (today.year, today.month)
            else date(year, month, last_day).isoformat(),
        }
        if active_days >= 25:
            award_event(
                connection, user_id, f"monthly_25_days:{month_key}", "monthly_25_days", 25,
                "Reached 25 active challenge days this month", bonus_context,
            )
        if (year, month) < (today.year, today.month) and active_days == last_day:
            award_event(
                connection, user_id, f"monthly_full:{month_key}", "monthly_full", 25,
                "Completed every daily challenge this month", bonus_context,
            )

