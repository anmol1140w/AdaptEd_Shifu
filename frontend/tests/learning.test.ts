import { describe, expect, it } from 'vitest'
import { ASSESSMENTS, PROBLEMS, STUDENT } from '../src/services/data'
import { calculateConceptMastery, generateTargetedQuiz, masteryStatus, selectAdaptiveQuestions } from '../src/services/learning'
import { activitySummary, calendarDates, loadState, recordActivity } from '../src/services/storage'
import type { DemoState, LearningActivity } from '../src/types'

function emptyState(): DemoState {
  const state = loadState()
  return { ...state, activity: [], problemAttempts: [], assessmentAttempts: [], masteryAdjustments: {} }
}

function localIso(daysAgo: number) {
  const date = new Date()
  date.setHours(12, 0, 0, 0)
  date.setDate(date.getDate() - daysAgo)
  return date.toISOString()
}

function activity(daysAgo: number, id: string): LearningActivity {
  return { id, studentId: STUDENT.id, type: 'question_attempted', timestamp: localIso(daysAgo), relatedId: id, contributionPoints: 1, isDemo: false }
}

describe('learning services', () => {
  it('uses the configured mastery thresholds', () => {
    expect(masteryStatus(39)).toBe('Weak')
    expect(masteryStatus(40)).toBe('Developing')
    expect(masteryStatus(60)).toBe('Proficient')
    expect(masteryStatus(80)).toBe('Mastered')
  })

  it('calculates mastery from the base concept and recorded evidence', () => {
    const state = emptyState()
    const before = calculateConceptMastery('phy-torque', state)
    const next = { ...state, problemAttempts: [{ id: 'attempt-1', problemId: 'PHY-001', studentId: STUDENT.id, answer: '1 N·m', correct: true, timeTaken: 20, hintUsed: false, createdAt: localIso(0) }] }
    expect(calculateConceptMastery('phy-torque', next)).toBeGreaterThan(before)
  })

  it('filters targeted quizzes by scope and keeps selection deterministic', () => {
    const state = emptyState()
    const filters = { subject: 'physics', chapter: 'Rotational Motion', difficulty: 'Easy', questionType: 'MCQ', count: 3 }
    const first = generateTargetedQuiz(filters, state)
    const second = generateTargetedQuiz(filters, state)
    expect(first.map((problem) => problem.id)).toEqual(second.map((problem) => problem.id))
    expect(first.every((problem) => problem.subject === 'physics' && problem.chapter === 'Rotational Motion' && problem.difficulty === 'Easy' && problem.questionType === 'MCQ')).toBe(true)
  })

  it('selects a bounded adaptive set from the assessment context', () => {
    const state = emptyState()
    const assessment = ASSESSMENTS.find((item) => item.id === 'assessment-diagnostic')!
    const selected = selectAdaptiveQuestions(assessment, state)
    expect(selected).toHaveLength(assessment.questionCount)
    expect(selected.every((problem) => problem.subject === assessment.subject && problem.chapter === assessment.chapter)).toBe(true)
  })
})

describe('activity ledger', () => {
  it('deduplicates repeated activity submissions by event key', () => {
    const state = emptyState()
    const input = { studentId: STUDENT.id, type: 'question_attempted' as const, timestamp: localIso(0), relatedId: 'PHY-001', conceptId: 'phy-torque', isDemo: false }
    const first = recordActivity(state, input)
    const second = recordActivity(first, input)
    expect(first.activity).toHaveLength(1)
    expect(second.activity).toHaveLength(1)
  })

  it('calculates a current streak through today and yesterday', () => {
    const summary = activitySummary([activity(1, 'yesterday'), activity(0, 'today')])
    expect(summary.currentStreak).toBe(2)
    expect(summary.longestStreak).toBe(2)
  })

  it('builds a Monday-aligned calendar with seven-day weeks', () => {
    const dates = calendarDates(30)
    expect(dates.length % 7).toBe(0)
    expect(dates[0].getDay()).toBe(1)
    expect(dates[dates.length - 1].getTime()).toBeGreaterThanOrEqual(new Date().setHours(12, 0, 0, 0))
  })
})

describe('demo question bank', () => {
  it('contains enough varied problems for the explorer and quiz builder', () => {
    expect(PROBLEMS.length).toBeGreaterThanOrEqual(30)
    expect(new Set(PROBLEMS.map((problem) => problem.subject)).size).toBeGreaterThanOrEqual(4)
    expect(new Set(PROBLEMS.map((problem) => problem.questionType)).size).toBe(2)
  })
})
