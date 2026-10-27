import { describe, expect, it } from 'vitest'
import { CHAPTER_QUIZZES, filterChapterQuizzes, type QuizAttempt } from '../src/features/learner/services/quizCatalog'
import { beginQuiz, quizScore, remainingQuizSeconds } from '../src/features/learner/services/quizAttempts'

const emptyAttempts: QuizAttempt[] = []
const baseFilters = {
  selectedSubjects: new Set<'physics' | 'chemistry' | 'mathematics'>(),
  selectedTopics: new Set<string>(),
  difficulty: 'All difficulties',
  status: 'All statuses',
  search: '',
  attempts: emptyAttempts,
}

describe('chapter quiz browser', () => {
  it('keeps quizzes across multiple selected subjects and topics (OR topic matching)', () => {
    const selectedTopics = new Set([
      'physics:Rotational Motion',
      'chemistry:Chemical Kinetics',
      'mathematics:Area Under the Curve',
    ])
    const result = filterChapterQuizzes(CHAPTER_QUIZZES, { ...baseFilters, selectedTopics })
    expect(new Set(result.map(({ subject, chapter }) => `${subject}:${chapter}`))).toEqual(new Set([
      'physics:Rotational Motion',
      'chemistry:Chemical Kinetics',
      'mathematics:Area Under the Curve',
    ]))
  })

  it('combines subject, difficulty, status and search filters', () => {
    const result = filterChapterQuizzes(CHAPTER_QUIZZES, {
      ...baseFilters,
      selectedSubjects: new Set(['physics']),
      selectedTopics: new Set(['physics:Rotational Motion']),
      difficulty: 'Hard',
      status: 'Unsolved',
      search: 'rotational',
    })
    expect(result.length).toBeGreaterThan(0)
    expect(result.every((quiz) => quiz.subject === 'physics' && quiz.chapter === 'Rotational Motion' && quiz.difficulty === 'Hard')).toBe(true)
  })

  it('filters quiz state and orders by status', () => {
    const firstQuiz = CHAPTER_QUIZZES[0]!
    const attempts: QuizAttempt[] = [{ quizId: firstQuiz.id, status: 'completed', startedAt: new Date().toISOString(), submittedAt: new Date().toISOString(), answers: {}, score: 0 }]
    const result = filterChapterQuizzes(CHAPTER_QUIZZES, { ...baseFilters, attempts, status: 'Solved', sort: 'Status' })
    expect(result.map((quiz) => quiz.id)).toContain(firstQuiz.id)
    expect(result).toHaveLength(1)
  })
})

describe('quiz attempt mechanics', () => {
  it('starts once and resumes an active attempt without resetting answers or timer', () => {
    const quizId = CHAPTER_QUIZZES[0]!.id
    const started = beginQuiz(quizId, [], new Date('2026-10-27T10:00:00.000Z'))
    const resumed = beginQuiz(quizId, [{ ...started, answers: { q1: 'A' } }], new Date('2026-10-27T10:05:00.000Z'))
    expect(resumed.startedAt).toBe('2026-10-27T10:00:00.000Z')
    expect(resumed.answers).toEqual({ q1: 'A' })
    expect(remainingQuizSeconds(5, started.startedAt, Date.parse('2026-10-27T10:00:30.000Z'))).toBe(270)
  })

  it('scores exact answer matches and treats whitespace and minus glyph variants consistently', () => {
    expect(quizScore([
      { id: 'a', prompt: '', answer: '−2', explanation: '' },
      { id: 'b', prompt: '', answer: 'Correct', explanation: '' },
    ], { a: '- 2', b: ' incorrect' })).toBe(4)
  })
})
