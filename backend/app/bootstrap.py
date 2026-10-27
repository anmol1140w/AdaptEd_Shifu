"""Composition roots for local AdaptEd application runtimes."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from .api.v1.routes.assessment import AssessmentApi
from .api.v1.routes.learning_support import LearningSupportApi
from .application.assessment_facade import AssessmentFacade
from .application.learning_support_facade import LearningSupportFacade
from .application.ports.ai import RetrievedSource
from .application.ports.assessment import AssessmentGraderPort
from .application.use_cases.build_subject_summary import BuildSubjectSummary
from .application.use_cases.generate_weak_area_quiz import GenerateWeakAreaQuiz
from .application.use_cases.prepare_attempt import PrepareAttempt
from .application.use_cases.provide_tutor_support import ProvideTutorSupport
from .application.use_cases.start_assessment import StartAssessment
from .application.use_cases.submit_attempt import SubmitAttempt
from .domain.entities.learning import AssessmentItem, Concept
from .domain.services.learning_engine import LearningEngine
from .infrastructure.assessment.grading import DeterministicAssessmentGrader
from .infrastructure.ai.audit import InMemoryAIAudit
from .infrastructure.ai.llm import (
    CuratedQuizFallback,
    CuratedTutorFallback,
    DeterministicQuizGenerator,
    DeterministicTutorGenerator,
)
from .infrastructure.ai.retrieval import InMemoryLearningRetriever
from .infrastructure.ai.validators import StructuredLearningOutputValidator
from .infrastructure.in_memory import (
    InMemoryAssessmentSessions,
    InMemoryAttempts,
    InMemoryConceptCatalog,
    InMemoryItemCatalog,
    InMemoryLearners,
    InMemoryMasteryStates,
    InMemoryRecommendations,
    InMemorySessionIds,
)


@dataclass(slots=True)
class InMemoryAssessmentRuntime:
    """Assembled local runtime plus its inspectable in-memory adapters."""

    api: AssessmentApi
    facade: AssessmentFacade
    learners: InMemoryLearners
    concepts: InMemoryConceptCatalog
    items: InMemoryItemCatalog
    sessions: InMemoryAssessmentSessions
    session_ids: InMemorySessionIds
    attempts: InMemoryAttempts
    mastery_states: InMemoryMasteryStates
    recommendations: InMemoryRecommendations
    support_api: LearningSupportApi
    support_facade: LearningSupportFacade
    ai_audit: InMemoryAIAudit


def build_in_memory_assessment_runtime(
    *,
    learner_ids: Iterable[str],
    concepts: Iterable[Concept],
    items: Iterable[AssessmentItem],
    subject_names: Mapping[str, str],
    session_id_prefix: str = "session",
    grader: AssessmentGraderPort | None = None,
    sources: Iterable[RetrievedSource] = (),
) -> InMemoryAssessmentRuntime:
    """Build a complete assessment runtime without a database or HTTP server."""

    concept_list = tuple(concepts)
    subject_name_map = dict(subject_names)
    if not subject_name_map:
        raise ValueError("at least one subject name is required")
    if any(not subject_id.strip() or not name.strip() for subject_id, name in subject_name_map.items()):
        raise ValueError("subject IDs and names must not be empty")
    missing_subject_names = {
        concept.subject_id
        for concept in concept_list
        if concept.subject_id not in subject_name_map
    }
    if missing_subject_names:
        raise ValueError(
            "missing subject names: " + ", ".join(sorted(missing_subject_names))
        )

    concept_catalog = InMemoryConceptCatalog(concept_list)
    item_catalog = InMemoryItemCatalog(items)
    learners = InMemoryLearners(learner_ids)
    sessions = InMemoryAssessmentSessions()
    session_ids = InMemorySessionIds(prefix=session_id_prefix)
    attempts = InMemoryAttempts()
    mastery_states = InMemoryMasteryStates()
    recommendations = InMemoryRecommendations()
    ai_audit = InMemoryAIAudit()
    retriever = InMemoryLearningRetriever(sources)
    validator = StructuredLearningOutputValidator()
    learning_engine = LearningEngine(concept_list)
    start_assessment = StartAssessment(
        learners=learners,
        concepts=concept_catalog,
        items=item_catalog,
        sessions=sessions,
        session_ids=session_ids,
    )
    prepare_attempt = PrepareAttempt(
        items=item_catalog,
        grader=grader or DeterministicAssessmentGrader(),
    )
    submit_attempt = SubmitAttempt(
        learning_engine=learning_engine,
        sessions=sessions,
        items=item_catalog,
        attempts=attempts,
        mastery_states=mastery_states,
        recommendations=recommendations,
    )
    build_subject_summary = BuildSubjectSummary(
        concepts=concept_catalog,
        attempts=attempts,
        mastery_states=mastery_states,
    )
    provide_tutor_support = ProvideTutorSupport(
        concepts=concept_catalog,
        retriever=retriever,
        generator=DeterministicTutorGenerator(),
        fallback_generator=CuratedTutorFallback(),
        validator=validator,
        audit=ai_audit,
    )
    generate_weak_area_quiz = GenerateWeakAreaQuiz(
        concepts=concept_catalog,
        retriever=retriever,
        generator=DeterministicQuizGenerator(),
        fallback_generator=CuratedQuizFallback(),
        validator=validator,
        audit=ai_audit,
    )
    facade = AssessmentFacade(
        start_assessment=start_assessment,
        prepare_attempt=prepare_attempt,
        submit_attempt=submit_attempt,
        concepts=concept_catalog,
        items=item_catalog,
        attempts=attempts,
        subject_names=subject_name_map,
        build_subject_summary=build_subject_summary,
    )
    api = AssessmentApi(facade=facade)
    support_facade = LearningSupportFacade(
        provide_tutor_support=provide_tutor_support,
        generate_weak_area_quiz=generate_weak_area_quiz,
    )
    support_api = LearningSupportApi(facade=support_facade)
    return InMemoryAssessmentRuntime(
        api=api,
        facade=facade,
        learners=learners,
        concepts=concept_catalog,
        items=item_catalog,
        sessions=sessions,
        session_ids=session_ids,
        attempts=attempts,
        mastery_states=mastery_states,
        recommendations=recommendations,
        support_api=support_api,
        support_facade=support_facade,
        ai_audit=ai_audit,
    )
