from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row
from pathlib import Path
import json

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
ALTER TABLE classrooms ADD COLUMN IF NOT EXISTS class_level INTEGER NOT NULL DEFAULT 12 CHECK (class_level IN (11, 12));
UPDATE classrooms SET class_level = CASE WHEN description ~* '^class[[:space:]]+11' THEN 11 ELSE 12 END
WHERE description ~* '^class[[:space:]]+1[12]' AND class_level = 12;
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
CREATE TABLE IF NOT EXISTS learner_coin_events (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_key TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    points INTEGER NOT NULL CHECK (points >= 0),
    description TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_learner_coin_events_user_time
    ON learner_coin_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_learner_coin_events_activity_date
    ON learner_coin_events(user_id, event_type, (metadata->>'activity_date'));
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
CREATE TABLE IF NOT EXISTS teacher_quiz_attempts (
    id TEXT PRIMARY KEY,
    quiz_id TEXT NOT NULL REFERENCES teacher_quizzes(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    answers JSONB NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0),
    max_score INTEGER NOT NULL CHECK (max_score > 0 AND score <= max_score),
    points_awarded INTEGER NOT NULL DEFAULT 0 CHECK (points_awarded >= 0),
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_teacher_quiz_attempts_user
    ON teacher_quiz_attempts(user_id, completed_at DESC);
CREATE TABLE IF NOT EXISTS learning_concepts (
    concept_id TEXT PRIMARY KEY,
    subject TEXT NOT NULL CHECK (subject IN ('physics', 'chemistry', 'mathematics')),
    class_level INTEGER NOT NULL CHECK (class_level IN (11, 12)),
    chapter TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    prerequisite_ids JSONB NOT NULL DEFAULT '[]'::jsonb
);
CREATE TABLE IF NOT EXISTS learning_items (
    item_id TEXT PRIMARY KEY,
    concept_id TEXT NOT NULL REFERENCES learning_concepts(concept_id) ON DELETE CASCADE,
    subject TEXT NOT NULL CHECK (subject IN ('physics', 'chemistry', 'mathematics')),
    class_level INTEGER NOT NULL CHECK (class_level IN (11, 12)),
    chapter TEXT NOT NULL,
    item_type TEXT NOT NULL,
    bloom_level TEXT NOT NULL,
    bloom_source TEXT NOT NULL DEFAULT 'unverified_seed',
    bloom_teacher_verified BOOLEAN NOT NULL DEFAULT FALSE,
    difficulty TEXT NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    difficulty_source TEXT NOT NULL DEFAULT 'unverified_seed',
    difficulty_teacher_verified BOOLEAN NOT NULL DEFAULT FALSE,
    question TEXT NOT NULL,
    answer_guide TEXT NOT NULL,
    explanation TEXT NOT NULL,
    options JSONB NOT NULL DEFAULT '[]'::jsonb,
    marks DOUBLE PRECISION,
    time_seconds INTEGER,
    source_reference_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    supporting_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    citation_status TEXT NOT NULL DEFAULT 'teacher_review_required',
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    created_by TEXT REFERENCES users(id) ON DELETE SET NULL,
    reviewed_by TEXT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE learning_items ADD COLUMN IF NOT EXISTS bloom_source TEXT NOT NULL DEFAULT 'unverified_seed';
ALTER TABLE learning_items ADD COLUMN IF NOT EXISTS bloom_teacher_verified BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE learning_items ADD COLUMN IF NOT EXISTS difficulty_source TEXT NOT NULL DEFAULT 'unverified_seed';
ALTER TABLE learning_items ADD COLUMN IF NOT EXISTS difficulty_teacher_verified BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE learning_items ADD COLUMN IF NOT EXISTS options JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE learning_items ADD COLUMN IF NOT EXISTS marks DOUBLE PRECISION;
ALTER TABLE learning_items ADD COLUMN IF NOT EXISTS time_seconds INTEGER;
CREATE INDEX IF NOT EXISTS idx_learning_items_lookup ON learning_items(subject, class_level, concept_id, approved, difficulty);
CREATE TABLE IF NOT EXISTS learning_assessments (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    class_level INTEGER NOT NULL,
    assessment_type TEXT NOT NULL DEFAULT 'adaptive' CHECK (assessment_type IN ('adaptive', 'mock')),
    item_ids JSONB NOT NULL,
    current_index INTEGER NOT NULL DEFAULT 0,
    target_count INTEGER NOT NULL DEFAULT 5,
    status TEXT NOT NULL CHECK (status IN ('in_progress', 'completed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);
ALTER TABLE learning_assessments ADD COLUMN IF NOT EXISTS target_count INTEGER NOT NULL DEFAULT 5;
ALTER TABLE learning_assessments ADD COLUMN IF NOT EXISTS assessment_type TEXT NOT NULL DEFAULT 'adaptive'
    CHECK (assessment_type IN ('adaptive', 'mock'));
CREATE TABLE IF NOT EXISTS learning_attempts (
    id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL REFERENCES learning_assessments(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL REFERENCES learning_items(item_id) ON DELETE CASCADE,
    answer TEXT NOT NULL,
    correct BOOLEAN NOT NULL,
    time_taken INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_learning_attempts_user ON learning_attempts(user_id, item_id, created_at DESC);
CREATE TABLE IF NOT EXISTS learning_external_evidence (
    id TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    learner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quiz_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    subject TEXT NOT NULL CHECK (subject IN ('physics', 'chemistry', 'mathematics')),
    class_level INTEGER NOT NULL CHECK (class_level IN (11, 12)),
    concept_id TEXT NOT NULL REFERENCES learning_concepts(concept_id) ON DELETE CASCADE,
    chapter TEXT NOT NULL,
    question_text TEXT NOT NULL,
    response TEXT NOT NULL DEFAULT '',
    score DOUBLE PRECISION NOT NULL CHECK (score >= 0),
    max_score DOUBLE PRECISION NOT NULL CHECK (max_score > 0 AND score <= max_score),
    difficulty TEXT NOT NULL DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
    time_taken INTEGER NOT NULL DEFAULT 0 CHECK (time_taken >= 0),
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_system, source_event_id, question_id)
);
CREATE INDEX IF NOT EXISTS idx_learning_external_evidence_learner
    ON learning_external_evidence(learner_id, subject, class_level, concept_id, attempted_at DESC);
CREATE TABLE IF NOT EXISTS generated_learning_content (
    id TEXT PRIMARY KEY,
    creator_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    class_level INTEGER NOT NULL,
    concept_id TEXT NOT NULL REFERENCES learning_concepts(concept_id) ON DELETE CASCADE,
    content_type TEXT NOT NULL CHECK (content_type IN ('tutor', 'quiz')),
    payload JSONB NOT NULL,
    source_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending_review' CHECK (status IN ('pending_review', 'approved', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE generated_learning_content ADD COLUMN IF NOT EXISTS sources JSONB NOT NULL DEFAULT '[]'::jsonb;
CREATE TABLE IF NOT EXISTS ai_request_audit (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_type TEXT NOT NULL CHECK (request_type IN ('tutor','weak_area_quiz','recommendations')),
    subject TEXT NOT NULL,
    class_level INTEGER NOT NULL,
    concept_id TEXT NOT NULL REFERENCES learning_concepts(concept_id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    source_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS ai_tutor_memory (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject TEXT NOT NULL CHECK (subject IN ('physics', 'chemistry', 'mathematics')),
    class_level INTEGER NOT NULL CHECK (class_level IN (11, 12)),
    concept_id TEXT NOT NULL REFERENCES learning_concepts(concept_id) ON DELETE CASCADE,
    mode TEXT NOT NULL CHECK (mode IN ('hint', 'explanation', 'check_question')),
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    check_question TEXT NOT NULL,
    source_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE ai_tutor_memory ADD COLUMN IF NOT EXISTS sources JSONB NOT NULL DEFAULT '[]'::jsonb;
CREATE INDEX IF NOT EXISTS idx_ai_tutor_memory_context
    ON ai_tutor_memory(user_id, subject, class_level, concept_id, created_at DESC);
CREATE TABLE IF NOT EXISTS user_learning_preferences (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    subject TEXT NOT NULL DEFAULT 'physics' CHECK (subject IN ('physics', 'chemistry', 'mathematics')),
    class_level INTEGER NOT NULL DEFAULT 11 CHECK (class_level IN (11, 12)),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO user_learning_preferences (user_id, subject, class_level)
SELECT DISTINCT ON (membership.user_id) membership.user_id, 'physics', classroom.class_level
FROM classroom_memberships membership
JOIN classrooms classroom ON classroom.id = membership.classroom_id
ORDER BY membership.user_id, membership.joined_at DESC
ON CONFLICT (user_id) DO NOTHING;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ai_request_audit_request_type_check'
          AND pg_get_constraintdef(oid) LIKE '%recommendations%'
    ) THEN
        ALTER TABLE ai_request_audit DROP CONSTRAINT IF EXISTS ai_request_audit_request_type_check;
        ALTER TABLE ai_request_audit ADD CONSTRAINT ai_request_audit_request_type_check
            CHECK (request_type IN ('tutor','weak_area_quiz','recommendations'));
    END IF;
END $$;
"""


def seed_pcm_learning_content(connection: psycopg.Connection) -> None:
    """Idempotently load authored PCM concepts and question drafts for review."""
    root = Path(__file__).resolve().parents[6]
    marker = connection.execute("SELECT value FROM content_seed_meta WHERE key = 'pcm_learning_content'").fetchone()
    manifest = []
    for folder, key in (("concepts", "concepts"), ("items", "items")):
        for path in sorted((root / "content" / folder).glob("*_class_*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            manifest.append((path, data, key))
    fingerprint = str(sum(path.stat().st_mtime_ns for path, _, _ in manifest))
    if marker and marker["value"] == fingerprint:
        return

    for path, data, key in manifest:
        subject = str(data["subject"]).lower()
        grade = int(data["class"])
        if key == "concepts":
            for concept in data.get("concepts", []):
                connection.execute(
                    """INSERT INTO learning_concepts
                       (concept_id, subject, class_level, chapter, name, description, prerequisite_ids)
                       VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
                       ON CONFLICT (concept_id) DO UPDATE SET subject=EXCLUDED.subject,
                         class_level=EXCLUDED.class_level, chapter=EXCLUDED.chapter, name=EXCLUDED.name,
                         description=EXCLUDED.description, prerequisite_ids=EXCLUDED.prerequisite_ids""",
                    (concept["concept_id"], subject, grade, concept.get("chapter", ""), concept["name"],
                     concept.get("description", ""), json.dumps(concept.get("prerequisite_ids", []))),
                )
        else:
            for item in data.get("items", []):
                connection.execute(
                    """INSERT INTO learning_items
                       (item_id, concept_id, subject, class_level, chapter, item_type, bloom_level,
                        difficulty, question, answer_guide, explanation, source_reference_ids,
                        supporting_chunk_ids, citation_status, options, marks, time_seconds, approved)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s::jsonb,%s,%s,%s)
                       ON CONFLICT (item_id) DO UPDATE SET concept_id=EXCLUDED.concept_id,
                         subject=EXCLUDED.subject, class_level=EXCLUDED.class_level, chapter=EXCLUDED.chapter,
                         item_type=EXCLUDED.item_type, bloom_level=EXCLUDED.bloom_level,
                         difficulty=EXCLUDED.difficulty, question=EXCLUDED.question,
                         answer_guide=EXCLUDED.answer_guide, explanation=EXCLUDED.explanation,
                         source_reference_ids=EXCLUDED.source_reference_ids,
                         supporting_chunk_ids=EXCLUDED.supporting_chunk_ids,
                         citation_status=EXCLUDED.citation_status, options=EXCLUDED.options,
                         marks=EXCLUDED.marks, time_seconds=EXCLUDED.time_seconds""",
                    (item["item_id"], item["concept_id"], subject, grade, item.get("chapter", ""),
                     item.get("item_type", "short_answer"), item.get("bloom_level", "understand"),
                     str(item.get("difficulty", "easy")).lower(), item["question"], item.get("answer_guide", ""),
                     item.get("explanation", ""), json.dumps(item.get("source_reference_ids", [])),
                     json.dumps(item.get("supporting_chunk_ids", [])), item.get("citation_status", "teacher_review_required"),
                     json.dumps(item.get("options", [])), item.get("marks"), item.get("time_seconds"),
                     bool(item.get("teacher_approved", False))),
                )
    connection.execute(
        """INSERT INTO content_seed_meta (key, value) VALUES ('pcm_learning_content', %s)
           ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value, updated_at=CURRENT_TIMESTAMP""",
        (fingerprint,),
    )


def connect() -> psycopg.Connection:
    connection = psycopg.connect(settings.database_url, password=settings.database_password, row_factory=dict_row)
    try:
        connection.execute(SCHEMA)
        seed_granular_content(connection)
        seed_pcm_learning_content(connection)
        connection.commit()
        return connection
    except Exception:
        connection.rollback()
        connection.close()
        raise


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
