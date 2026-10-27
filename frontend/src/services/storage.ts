import type { DemoState, LearningActivity, ProblemAttempt, TutorMessage, TeacherIntervention } from '../types'
import { BASE_INTERVENTIONS, CONCEPTS, PROBLEMS, STUDENT } from './data'

const STORAGE_KEY = 'adapted-demo-state-v1'

function dateAtOffset(daysAgo: number, hour = 12) {
  const date = new Date()
  date.setHours(hour, 0, 0, 0)
  date.setDate(date.getDate() - daysAgo)
  return date.toISOString()
}

function seededActivity(): LearningActivity[] {
  const events: LearningActivity[] = []
  let id = 0
  for (let daysAgo = 0; daysAgo < 365; daysAgo += 1) {
    const signal = (daysAgo * 17 + 11) % 29
    const active = signal < 8 || daysAgo % 41 === 0 || daysAgo === 1
    if (!active) continue
    const count = signal % 5 === 0 ? 3 : signal % 3 === 0 ? 2 : 1
    for (let item = 0; item < count; item += 1) {
      const type = item === 2 ? 'mistake_reviewed' : item === 1 ? 'lesson_completed' : 'question_attempted'
      events.push({
        id: `demo-activity-${id += 1}`,
        studentId: STUDENT.id,
        type,
        timestamp: dateAtOffset(daysAgo, 9 + ((signal + item) % 9)),
        relatedId: PROBLEMS[(daysAgo + item) % PROBLEMS.length].id,
        conceptId: CONCEPTS[(daysAgo + item) % CONCEPTS.length].id,
        contributionPoints: type === 'lesson_completed' ? 2 : 1,
        isDemo: true,
        metadata: { label: type === 'lesson_completed' ? 'Completed a lesson' : type === 'mistake_reviewed' ? 'Reviewed an incorrect answer' : 'Attempted a question' },
      })
    }
  }
  return events
}

const initialState: DemoState = {
  selectedRole: 'student',
  activity: seededActivity(),
  problemAttempts: [
    { id: 'attempt-demo-1', problemId: 'PHY-001', studentId: STUDENT.id, answer: '0.5 N·m', correct: false, timeTaken: 38, hintUsed: false, createdAt: dateAtOffset(1, 17) },
    { id: 'attempt-demo-2', problemId: 'CHEM-001', studentId: STUDENT.id, answer: '1.04', correct: false, timeTaken: 74, hintUsed: true, createdAt: dateAtOffset(2, 18) },
  ],
  assessmentAttempts: [],
  completedPlanTasks: ['plan-review'],
  completedPathItems: ['path-1'],
  bookmarks: ['PHY-002', 'MATH-005'],
  masteryAdjustments: {},
  tutorMessages: [
    { id: 'tutor-welcome', role: 'assistant', content: 'Hi Aarav. I can help you reason through a concept, review a mistake, or build a focused practice set. What would you like to work on?', timestamp: dateAtOffset(0, 8), sourceLabel: 'Demo tutor · teacher-reviewed content' },
  ],
  interventions: BASE_INTERVENTIONS,
}

function safeParse(raw: string | null): DemoState | null {
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as Partial<DemoState>
    if (!Array.isArray(parsed.activity) || !Array.isArray(parsed.problemAttempts)) return null
    const isRecord = (value: unknown): value is Record<string, unknown> => Boolean(value) && typeof value === 'object' && !Array.isArray(value)
    return {
      ...initialState,
      selectedRole: parsed.selectedRole === 'teacher' || parsed.selectedRole === 'student' ? parsed.selectedRole : initialState.selectedRole,
      activity: parsed.activity,
      problemAttempts: parsed.problemAttempts,
      assessmentAttempts: Array.isArray(parsed.assessmentAttempts) ? parsed.assessmentAttempts : initialState.assessmentAttempts,
      completedPlanTasks: Array.isArray(parsed.completedPlanTasks) ? parsed.completedPlanTasks : initialState.completedPlanTasks,
      completedPathItems: Array.isArray(parsed.completedPathItems) ? parsed.completedPathItems : initialState.completedPathItems,
      bookmarks: Array.isArray(parsed.bookmarks) ? parsed.bookmarks : initialState.bookmarks,
      masteryAdjustments: isRecord(parsed.masteryAdjustments) ? parsed.masteryAdjustments as Record<string, number> : initialState.masteryAdjustments,
      tutorMessages: Array.isArray(parsed.tutorMessages) ? parsed.tutorMessages : initialState.tutorMessages,
      interventions: Array.isArray(parsed.interventions) ? parsed.interventions : BASE_INTERVENTIONS,
    }
  } catch {
    return null
  }
}

export function loadState(): DemoState {
  if (typeof window === 'undefined') return initialState
  return safeParse(window.localStorage.getItem(STORAGE_KEY)) ?? initialState
}

export function saveState(state: DemoState) {
  if (typeof window !== 'undefined') window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

export function resetState() {
  if (typeof window !== 'undefined') window.localStorage.removeItem(STORAGE_KEY)
  return initialState
}

export function activityWeight(type: LearningActivity['type']) {
  return type === 'lesson_completed' ? 2 : type === 'assessment_completed' ? 3 : 1
}

export function recordActivity(state: DemoState, input: Omit<LearningActivity, 'id' | 'contributionPoints'> & { dedupeKey?: string }): DemoState {
  const dedupeKey = input.dedupeKey ?? `${input.studentId}:${input.type}:${input.relatedId ?? ''}:${input.timestamp.slice(0, 10)}`
  const exists = state.activity.some((event) => (event.dedupeKey ?? `${event.studentId}:${event.type}:${event.relatedId ?? ''}:${event.timestamp.slice(0, 10)}`) === dedupeKey)
  if (exists) return state
  const nextActivity: LearningActivity = { ...input, id: `activity-${Date.now()}`, contributionPoints: activityWeight(input.type), isDemo: false, dedupeKey }
  const next = { ...state, activity: [...state.activity, nextActivity] }
  saveState(next)
  return next
}

export function recordProblemAttempt(state: DemoState, attempt: Omit<ProblemAttempt, 'id'>) {
  const next = { ...state, problemAttempts: [...state.problemAttempts, { ...attempt, id: `attempt-${Date.now()}` }] }
  saveState(next)
  return next
}

export function addTutorMessage(state: DemoState, message: Omit<TutorMessage, 'id' | 'timestamp'>) {
  const nextMessage: TutorMessage = { ...message, id: `tutor-${Date.now()}`, timestamp: new Date().toISOString() }
  const next = { ...state, tutorMessages: [...state.tutorMessages, nextMessage] }
  saveState(next)
  return next
}

export function updateIntervention(state: DemoState, intervention: TeacherIntervention) {
  const next = { ...state, interventions: state.interventions.map((item) => item.id === intervention.id ? intervention : item) }
  saveState(next)
  return next
}

export function getDateKey(date: Date | string) {
  const parsed = typeof date === 'string' ? new Date(date) : date
  return `${parsed.getFullYear()}-${String(parsed.getMonth() + 1).padStart(2, '0')}-${String(parsed.getDate()).padStart(2, '0')}`
}

export function calendarDates(days: number) {
  const today = new Date()
  today.setHours(12, 0, 0, 0)
  const end = new Date(today)
  const start = new Date(today)
  start.setDate(start.getDate() - days + 1)
  const mondayOffset = (start.getDay() + 6) % 7
  start.setDate(start.getDate() - mondayOffset)
  const dates: Date[] = []
  for (const cursor = new Date(start); cursor <= end; cursor.setDate(cursor.getDate() + 1)) dates.push(new Date(cursor))
  return dates
}

export function activitySummary(activity: LearningActivity[], days?: number) {
  const scopedActivity = days === undefined
    ? activity
    : activity.filter((event) => Date.now() - new Date(event.timestamp).getTime() <= days * 86400000)
  const byDate = new Map<string, LearningActivity[]>()
  scopedActivity.forEach((event) => {
    const key = getDateKey(event.timestamp)
    byDate.set(key, [...(byDate.get(key) ?? []), event])
  })
  const activeKeys = [...byDate.keys()].sort()
  const today = new Date()
  const todayKey = getDateKey(today)
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const yesterdayKey = getDateKey(yesterday)
  let currentStreak = 0
  let cursor = byDate.has(todayKey) ? today : byDate.has(yesterdayKey) ? yesterday : null
  while (cursor && byDate.has(getDateKey(cursor))) {
    currentStreak += 1
    cursor = new Date(cursor)
    cursor.setDate(cursor.getDate() - 1)
  }
  let longestStreak = 0
  let run = 0
  activeKeys.forEach((key, index) => {
    const previous = index === 0 ? null : new Date(`${activeKeys[index - 1]}T12:00:00`)
    const current = new Date(`${key}T12:00:00`)
    if (previous && (current.getTime() - previous.getTime()) / 86400000 === 1) run += 1
    else run = 1
    longestStreak = Math.max(longestStreak, run)
  })
  const last7 = scopedActivity.filter((event) => Date.now() - new Date(event.timestamp).getTime() <= 7 * 86400000)
  const last30 = scopedActivity.filter((event) => Date.now() - new Date(event.timestamp).getTime() <= 30 * 86400000)
  return { byDate, activeDays: activeKeys.length, totalQuestions: scopedActivity.filter((event) => event.type === 'question_attempted').length, totalActivities: scopedActivity.length, currentStreak, longestStreak, last7: last7.length, last30: last30.length }
}

export function activityLabel(type: LearningActivity['type']) {
  return type.split('_').join(' ')
}
