from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from backend.app.core.settings import settings
from backend.app.infrastructure.database.granular_content_seed import seed_granular_content


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'teacher')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_subject TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS unique_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_unique_id ON users(unique_id) WHERE unique_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_subject ON users(google_subject) WHERE google_subject IS NOT NULL;
CREATE TABLE IF NOT EXISTS classrooms (
    id TEXT PRIMARY KEY,
    public_slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    owner_id TEXT NOT NULL REFERENCES users(id),
    join_code_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS classroom_memberships (
    classroom_id TEXT NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'student')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (classroom_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_classrooms_join_code_hash ON classrooms(join_code_hash);
CREATE TABLE IF NOT EXISTS jee_topics (
    id TEXT PRIMARY KEY,
    subject TEXT NOT NULL CHECK (subject IN ('physics', 'chemistry', 'mathematics')),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    syllabus_source TEXT NOT NULL DEFAULT 'JEE Main 2026 / JEE Advanced 2026',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS jee_problems (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    subject TEXT NOT NULL CHECK (subject IN ('physics', 'chemistry', 'mathematics')),
    chapter TEXT NOT NULL,
    statement TEXT NOT NULL,
    question_type TEXT NOT NULL CHECK (question_type IN ('MCQ', 'Numerical')),
    difficulty TEXT NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    choices JSONB,
    answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    formula TEXT,
    hints JSONB NOT NULL DEFAULT '[]'::jsonb,
    exam_relevance JSONB NOT NULL DEFAULT '["JEE Main"]'::jsonb,
    estimated_minutes INTEGER NOT NULL DEFAULT 5,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS problem_topics (
    problem_id TEXT NOT NULL REFERENCES jee_problems(id) ON DELETE CASCADE,
    topic_id TEXT NOT NULL REFERENCES jee_topics(id) ON DELETE CASCADE,
    PRIMARY KEY (problem_id, topic_id)
);
CREATE INDEX IF NOT EXISTS idx_jee_topics_subject ON jee_topics(subject);
CREATE INDEX IF NOT EXISTS idx_problem_topics_topic ON problem_topics(topic_id);
CREATE TABLE IF NOT EXISTS problem_attempts (
    id TEXT PRIMARY KEY,
    problem_id TEXT NOT NULL REFERENCES jee_problems(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    answer TEXT NOT NULL,
    correct BOOLEAN NOT NULL,
    time_taken INTEGER NOT NULL DEFAULT 0,
    hint_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_problem_attempts_user ON problem_attempts(user_id, problem_id);
CREATE TABLE IF NOT EXISTS content_seed_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS teacher_quizzes (
    id TEXT PRIMARY KEY,
    classroom_id TEXT NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    teacher_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    difficulty TEXT NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    time_limit_minutes INTEGER NOT NULL DEFAULT 30,
    published BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS teacher_quiz_questions (
    id TEXT PRIMARY KEY,
    quiz_id TEXT NOT NULL REFERENCES teacher_quizzes(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    prompt TEXT NOT NULL,
    question_type TEXT NOT NULL CHECK (question_type IN ('MCQ', 'Numerical')),
    choices JSONB NOT NULL DEFAULT '[]'::jsonb,
    answer TEXT NOT NULL,
    explanation TEXT NOT NULL DEFAULT '',
    hints JSONB NOT NULL DEFAULT '[]'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_teacher_quizzes_classroom ON teacher_quizzes(classroom_id, published);
"""


def connect() -> psycopg.Connection:
    connection = psycopg.connect(settings.database_url, password=settings.database_password, row_factory=dict_row)
    connection.execute(SCHEMA)
    seed_granular_content(connection)
    connection.commit()
    return connection


@contextmanager
def transaction() -> Iterator[psycopg.Connection]:
    connection = connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
