"""Backfill Bloom Taxonomy levels for every stored question.

This uses the deterministic QuestionClassifier already used by the question-bank
workflow. It produces inspectable levels and reasons without sending question
content to an external model. Teachers can still override levels in the
learning-item workflow when a human review is needed.

Run from backend/:
    $env:PYTHONPATH='src'; .venv/Scripts/python.exe scripts/classify_bloom_levels.py
"""

from backend.app.domain.services.question_classifier import QuestionClassifier
from backend.app.domain.entities.question_bank import QuestionDraft
from backend.app.infrastructure.database.connection import connect


def normalized_type(value: str) -> str:
    value = value.casefold()
    return {"mcq": "mcq", "numerical": "numerical", "short_answer": "short_answer", "descriptive": "descriptive"}.get(value, "short_answer")


def classify(question: str, question_type: str, subject: str, topic: str) -> tuple[str, float, str]:
    result = QuestionClassifier().classify(QuestionDraft(
        question=question,
        question_type=normalized_type(question_type),
        subject=subject or "jee",
        topic=topic or "general",
        correct_answer="placeholder",
        fields={"option_a": "A", "option_b": "B"} if normalized_type(question_type) == "mcq" else {},
    ))
    return result.bloom_level.name.casefold(), result.bloom_confidence, result.bloom_reason


def main() -> None:
    connection = connect()
    counts: dict[str, int] = {}
    try:
        problems = connection.execute("SELECT id, subject, chapter, question_type, statement FROM jee_problems").fetchall()
        for row in problems:
            level, _, _ = classify(row["statement"], row["question_type"], row["subject"], row["chapter"])
            connection.execute("UPDATE jee_problems SET bloom_level = %s WHERE id = %s", (level, row["id"]))
            counts[level] = counts.get(level, 0) + 1

        quiz_questions = connection.execute(
            """SELECT qq.id, qq.prompt, qq.question_type, q.title
               FROM teacher_quiz_questions qq JOIN teacher_quizzes q ON q.id = qq.quiz_id"""
        ).fetchall()
        for row in quiz_questions:
            level, _, _ = classify(row["prompt"], row["question_type"], "jee", row["title"])
            connection.execute("UPDATE teacher_quiz_questions SET bloom_level = %s WHERE id = %s", (level, row["id"]))
            counts[level] = counts.get(level, 0) + 1

        learning_items = connection.execute("SELECT item_id, subject, chapter, item_type, question FROM learning_items").fetchall()
        for row in learning_items:
            level, _, _ = classify(row["question"], row["item_type"], row["subject"], row["chapter"])
            connection.execute("UPDATE learning_items SET bloom_level = %s WHERE item_id = %s", (level, row["item_id"]))
            counts[level] = counts.get(level, 0) + 1

        connection.commit()
    finally:
        connection.close()
    print(f"Classified {sum(counts.values())} questions: {counts}")


if __name__ == "__main__":
    main()
