import { CONCEPTS, PROBLEMS, getConcept, getProblem, subjectLabel } from './data'
import type { Assessment, DemoState, LearningRecommendation, MasteryStatus, Problem } from '../types'

export function masteryStatus(value: number): MasteryStatus {
  if (value < 40) return 'Weak'
  if (value < 60) return 'Developing'
  if (value < 80) return 'Proficient'
  return 'Mastered'
}

export function adjustedMastery(conceptId: string, state: DemoState) {
  const concept = getConcept(conceptId)
  return Math.max(0, Math.min(100, (concept?.mastery ?? 0) + (state.masteryAdjustments[conceptId] ?? 0)))
}

export function calculateConceptMastery(conceptId: string, state: DemoState) {
  const concept = getConcept(conceptId)
  if (!concept) return 0
  const attempts = state.problemAttempts.filter((attempt) => PROBLEMS.find((problem) => problem.id === attempt.problemId)?.conceptIds.includes(conceptId))
  if (!attempts.length) return adjustedMastery(conceptId, state)
  const recentAccuracy = attempts.reduce((total, attempt) => total + (attempt.correct ? 1 : 0), 0) / attempts.length
  const evidenceBoost = Math.round((recentAccuracy - concept.recentAccuracy / 100) * 12)
  return Math.max(0, Math.min(100, adjustedMastery(conceptId, state) + evidenceBoost))
}

export function generateRecommendations(state: DemoState): LearningRecommendation[] {
  const weakest = [...CONCEPTS].sort((a, b) => calculateConceptMastery(a.id, state) - calculateConceptMastery(b.id, state)).slice(0, 4)
  return weakest.map((concept, index) => {
    const mastery = calculateConceptMastery(concept.id, state)
    const hasRepeatedErrors = state.problemAttempts.filter((attempt) => !attempt.correct && PROBLEMS.find((problem) => problem.id === attempt.problemId)?.conceptIds.includes(concept.id)).length >= 2
    const type = hasRepeatedErrors ? 'review' : mastery < 40 ? 'lesson' : index === 0 ? 'practice' : 'assessment'
    return {
      id: `recommendation-${concept.id}`,
      title: type === 'lesson' ? `Review ${concept.name}` : type === 'review' ? `Review mistakes in ${concept.name}` : `Practice ${concept.name}`,
      description: type === 'lesson' ? `Rebuild the prerequisite idea before adding more difficulty.` : `A focused activity using your most recent evidence.`,
      reason: hasRepeatedErrors ? `You have repeated errors on ${concept.name}.` : `Your recent accuracy in ${concept.name} is ${concept.recentAccuracy}%.`,
      actionLabel: type === 'lesson' ? 'Open lesson' : type === 'review' ? 'Review now' : 'Start practice',
      actionPath: type === 'lesson' ? `/student/learning-path?concept=${concept.id}` : `/student/problems?concept=${concept.id}`,
      type,
      conceptId: concept.id,
    }
  })
}

export function generateTargetedQuiz(filters: { subject?: string; chapter?: string; conceptIds?: string[]; difficulty?: string; exam?: string; questionType?: string; count?: number; weakOnly?: boolean }, state: DemoState): Problem[] {
  const count = filters.count ?? 5
  const selected = PROBLEMS.filter((problem) => {
    if (filters.subject && problem.subject !== filters.subject) return false
    if (filters.chapter && problem.chapter !== filters.chapter) return false
    if (filters.conceptIds?.length && !problem.conceptIds.some((id) => filters.conceptIds?.includes(id))) return false
    if (filters.difficulty && problem.difficulty !== filters.difficulty) return false
    if (filters.exam && !problem.examRelevance.includes(filters.exam)) return false
    if (filters.questionType && problem.questionType !== filters.questionType) return false
    if (filters.weakOnly && !problem.conceptIds.some((id) => calculateConceptMastery(id, state) < 60)) return false
    return true
  })
  return selected.sort((a, b) => {
    const aMastery = Math.min(...a.conceptIds.map((id) => calculateConceptMastery(id, state)))
    const bMastery = Math.min(...b.conceptIds.map((id) => calculateConceptMastery(id, state)))
    return aMastery - bMastery
  }).slice(0, count)
}

export function selectAdaptiveQuestions(assessment: Assessment, state: DemoState): Problem[] {
  const candidates = PROBLEMS.filter((problem) => problem.subject === assessment.subject && problem.chapter === assessment.chapter)
  const configured = assessment.questionIds.map((id) => getProblem(id)).filter((problem): problem is Problem => Boolean(problem))
  const pool = [...new Map([...candidates, ...configured].map((problem) => [problem.id, problem])).values()]
  const difficultyRank: Record<Problem['difficulty'], number> = { Easy: 1, Medium: 2, Hard: 3 }

  return pool.sort((a, b) => {
    const aMastery = Math.min(...a.conceptIds.map((id) => calculateConceptMastery(id, state)))
    const bMastery = Math.min(...b.conceptIds.map((id) => calculateConceptMastery(id, state)))
    const aAttempts = state.problemAttempts.filter((attempt) => attempt.problemId === a.id)
    const bAttempts = state.problemAttempts.filter((attempt) => attempt.problemId === b.id)
    const aAccuracy = aAttempts.length ? aAttempts.filter((attempt) => attempt.correct).length / aAttempts.length : 0.5
    const bAccuracy = bAttempts.length ? bAttempts.filter((attempt) => attempt.correct).length / bAttempts.length : 0.5
    const aTarget = aMastery < 45 ? 1 : aMastery < 70 ? 2 : 3
    const bTarget = bMastery < 45 ? 1 : bMastery < 70 ? 2 : 3
    return aMastery - bMastery
      || aAccuracy - bAccuracy
      || Math.abs(difficultyRank[a.difficulty] - aTarget) - Math.abs(difficultyRank[b.difficulty] - bTarget)
      || a.id.localeCompare(b.id)
  }).slice(0, assessment.questionCount)
}

export function recommendationReason(conceptId: string, state: DemoState) {
  const concept = getConcept(conceptId)
  if (!concept) return 'Selected from your learning history.'
  const mastery = calculateConceptMastery(conceptId, state)
  return `${subjectLabel(concept.subject)} · ${concept.chapter} · ${mastery}% estimated mastery from ${concept.attempts + state.problemAttempts.filter((attempt) => PROBLEMS.find((problem) => problem.id === attempt.problemId)?.conceptIds.includes(conceptId)).length} recorded attempts.`
}
