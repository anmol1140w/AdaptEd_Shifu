import type { Difficulty } from '../../../types'
import { listJeeProblems, type JeeProblem } from '../../../services/api'
import { loadState } from '../../../services/storage'
import { STUDENT_PROBLEMS } from '../../learner/services/problemCatalog'

export type ProfileDataSource = 'api' | 'browser' | 'empty'

export interface ProfileSubmission {
  id: string
  timestamp: string
  difficulty: Difficulty
  correct: boolean
  label: string
}

export interface StudentProfileData {
  submissions: ProfileSubmission[]
  solvedByDifficulty: Record<Difficulty, number>
  trackedQuestionCount: number
  source: ProfileDataSource
  sourceLabel: string
  limitation?: string
}

const emptySolved = (): Record<Difficulty, number> => ({ Easy: 0, Medium: 0, Hard: 0 })

function isDifficulty(value: string): value is Difficulty {
  return value === 'Easy' || value === 'Medium' || value === 'Hard'
}

function fromApi(problems: JeeProblem[]): StudentProfileData {
  const submissions = problems.flatMap((problem) => {
    const difficulty = isDifficulty(problem.difficulty) ? problem.difficulty : 'Medium'
    return (problem.attempts ?? []).flatMap((attempt, index) => {
      if (!attempt.created_at || Number.isNaN(new Date(attempt.created_at).getTime())) return []
      return [{
        id: `${problem.id}-${attempt.created_at}-${index}`,
        timestamp: attempt.created_at,
        difficulty,
        correct: Boolean(attempt.correct),
        label: problem.title,
      }]
    })
  })
  const solvedByDifficulty = emptySolved()
  problems.forEach((problem) => {
    const difficulty = isDifficulty(problem.difficulty) ? problem.difficulty : 'Medium'
    const solvedFromAttempts = (problem.attempts ?? []).some((attempt) => attempt.correct)
    if (problem.solved ?? solvedFromAttempts) solvedByDifficulty[difficulty] += 1
  })
  return {
    submissions,
    solvedByDifficulty,
    trackedQuestionCount: problems.length,
    source: 'api',
    sourceLabel: 'Live question history',
    limitation: submissions.length === 0 && Object.values(solvedByDifficulty).every((value) => value === 0)
      ? 'The question service returned no submission history for this account yet.'
      : undefined,
  }
}

function fromBrowser(studentId: string): StudentProfileData {
  const localById = new Map(STUDENT_PROBLEMS.map((entry) => [entry.problem.id, entry.problem]))
  const attempts = loadState().problemAttempts.filter((attempt) => attempt.studentId === studentId)
  const submissions = attempts.map((attempt) => ({
    id: attempt.id,
    timestamp: attempt.createdAt,
    difficulty: localById.get(attempt.problemId)?.difficulty ?? 'Medium',
    correct: attempt.correct,
    label: localById.get(attempt.problemId)?.title ?? attempt.problemId,
  }))
  const solvedByDifficulty = emptySolved()
  const solvedProblemIds = new Set(attempts.filter((attempt) => attempt.correct).map((attempt) => attempt.problemId))
  solvedProblemIds.forEach((problemId) => {
    const difficulty = localById.get(problemId)?.difficulty
    if (difficulty) solvedByDifficulty[difficulty] += 1
  })
  return {
    submissions,
    solvedByDifficulty,
    trackedQuestionCount: STUDENT_PROBLEMS.length,
    source: submissions.length ? 'browser' : 'empty',
    sourceLabel: submissions.length ? 'Development-only browser attempts' : 'No submission history',
    limitation: submissions.length ? 'These records come from this browser because the current backend has no profile history endpoint.' : undefined,
  }
}

/**
 * Uses the existing authenticated question service first. The browser fallback
 * is deliberately limited to attempts belonging to the current session user.
 */
export async function loadStudentProfileData(studentId: string): Promise<StudentProfileData> {
  try {
    const problems = await listJeeProblems()
    return fromApi(problems)
  } catch {
    return fromBrowser(studentId)
  }
}

