const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

import type { Classroom, CreateClassroomInput } from '../types'

export type JeeTopic = { id: string; subject: 'physics' | 'chemistry' | 'mathematics'; name: string; slug: string; problem_count: number }
export type JeeProblem = { id: string; title: string; subject: string; chapter: string; statement: string; question_type: 'MCQ' | 'Numerical'; difficulty: 'Easy' | 'Medium' | 'Hard'; choices?: string[]; answer: string; explanation: string; hints: string[]; formula?: string; exam_relevance: string[]; estimated_minutes: number; topics: string[]; solved?: boolean; attempted?: boolean; attempts?: { correct: boolean; created_at: string }[] }

export type AuthUser = { id: string; email: string; name: string; role: 'student' | 'teacher' }

export async function getCurrentUser(): Promise<AuthUser | null> {
  const response = await fetch(`${API_BASE}/auth/me`, { credentials: 'include' })
  if (!response.ok) return null
  const body = await response.json()
  return body.user
}

export function startGoogleLogin() {
  window.location.assign(`${API_BASE}/auth/google/start`)
}

export async function joinClassroom(code: string) {
  const response = await fetch(`${API_BASE}/classrooms/join`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not join classroom')
  return toFrontendClassroom(body.classroom, code)
}

export async function createClassroom(input: CreateClassroomInput) {
  const response = await fetch(`${API_BASE}/classrooms`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: input.name, description: `${input.classLevel} · ${input.examTarget}` }),
  })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not create classroom')
  return toFrontendClassroom(body.classroom, body.classroom.join_code)
}

export async function listClassrooms(): Promise<Classroom[]> {
  const response = await fetch(`${API_BASE}/classrooms`, { credentials: 'include' })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load classrooms')
  return body.classrooms.map((classroom: Record<string, string>) => toFrontendClassroom(classroom))
}

function toFrontendClassroom(row: Record<string, string>, code = ''): Classroom {
  return {
    id: row.id,
    name: row.name,
    code: code || 'Invite code hidden',
    classLevel: 'Class 12',
    academicYear: '2026–27',
    examTarget: 'JEE Main + Advanced',
    subjects: ['physics', 'chemistry', 'mathematics'],
    creatorId: row.owner_id,
    creatorName: '',
    members: [],
    createdAt: row.created_at,
    isDemo: false,
  }
}

export async function upgradeToTeacher(inviteCode: string) {
  const response = await fetch(`${API_BASE}/auth/upgrade-teacher`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ invite_code: inviteCode }),
  })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Teacher invite code is invalid')
  return body.user as AuthUser
}

export async function getClassroom(slug: string) {
  const response = await fetch(`${API_BASE}/classrooms/${encodeURIComponent(slug)}`, { credentials: 'include' })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load classroom')
  return body.classroom
}

export async function logout() {
  await fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'include' })
}

export async function listJeeTopics(subject?: string): Promise<JeeTopic[]> {
  const response = await fetch(`${API_BASE}/content/topics${subject ? `?subject=${encodeURIComponent(subject)}` : ''}`, { credentials: 'include' })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load topics')
  return body.topics
}

export async function listJeeProblems(topic?: string): Promise<JeeProblem[]> {
  const response = await fetch(`${API_BASE}/content/problems${topic ? `?topic=${encodeURIComponent(topic)}` : ''}`, { credentials: 'include' })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load problems')
  return body.problems
}

export async function getJeeProblem(id: string): Promise<JeeProblem> {
  const response = await fetch(`${API_BASE}/content/problems/${encodeURIComponent(id)}`, { credentials: 'include' })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load problem')
  return body.problem
}

export async function submitJeeAttempt(id: string, payload: { answer: string; time_taken: number; hint_used: boolean }) {
  const response = await fetch(`${API_BASE}/content/problems/${encodeURIComponent(id)}/attempt`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not save attempt')
  return body.attempt
}
