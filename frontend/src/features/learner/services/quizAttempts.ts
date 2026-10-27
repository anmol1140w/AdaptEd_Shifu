import type { QuizAttempt, QuizQuestion } from './quizCatalog'

const STORAGE_KEY = 'adapted-demo-quiz-attempts-v1'

export function loadQuizAttempts(): QuizAttempt[] {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? '[]') as QuizAttempt[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function persistQuizAttempt(attempt: QuizAttempt): QuizAttempt[] {
  const attempts = loadQuizAttempts().filter((item) => item.quizId !== attempt.quizId)
  const next = [...attempts, attempt]
  try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next)) } catch { /* keep the active in-memory flow usable */ }
  return next
}

export function beginQuiz(quizId: string, existing: QuizAttempt[], now = new Date()): QuizAttempt {
  const current = existing.find((attempt) => attempt.quizId === quizId)
  if (current?.status === 'in_progress') return current
  return { quizId, status: 'in_progress', startedAt: now.toISOString(), answers: {} }
}

export function remainingQuizSeconds(timeLimitMinutes: number, startedAt: string, now = Date.now()): number {
  const elapsedSeconds = Math.floor((now - new Date(startedAt).getTime()) / 1000)
  return Math.max(0, timeLimitMinutes * 60 - Math.max(0, elapsedSeconds))
}

export function quizScore(questions: QuizQuestion[], answers: Record<string, string>, marksPerQuestion = 4): number {
  const normalize = (value: string) => value.trim().toLocaleLowerCase().replace(/\s+/g, '').replace(/[−–]/g, '-')
  return questions.reduce((score, question) => score + (normalize(answers[question.id] ?? '') === normalize(question.answer) ? marksPerQuestion : 0), 0)
}
