const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
import { getAccessToken } from './session'

function authHeaders(extra?: HeadersInit): HeadersInit {
  const token = getAccessToken()
  return { ...(extra ?? {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) }
}

async function apiFetch(path: string, init: RequestInit = {}) {
  return fetch(`${API_BASE}${path}`, { credentials: 'include', ...init, headers: authHeaders(init.headers) })
}

import type { Classroom, CreateClassroomInput } from '../types'

export type JeeTopic = { id: string; subject: 'physics' | 'chemistry' | 'mathematics'; name: string; slug: string; problem_count: number }
export type JeeProblem = { id: string; title: string; subject: string; chapter: string; statement: string; question_type: 'MCQ' | 'Numerical'; difficulty: 'Easy' | 'Medium' | 'Hard'; choices?: string[]; answer: string; explanation: string; hints: string[]; formula?: string; exam_relevance: string[]; estimated_minutes: number; topics: string[]; solved?: boolean; attempted?: boolean; attempts?: { correct: boolean; created_at: string }[] }

export type AuthUser = { id: string; email: string; name: string; role: 'student' | 'teacher'; unique_id?: string }

export async function getCurrentUser(): Promise<AuthUser | null> {
  const response = await apiFetch('/auth/me')
  if (!response.ok) return null
  const body = await response.json()
  return body.user
}

export function startGoogleLogin() {
  window.location.assign(`${API_BASE}/auth/google/start`)
}

export async function joinClassroom(code: string) {
  const response = await apiFetch('/classrooms/join', {
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
  const response = await apiFetch('/classrooms', {
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
  const response = await apiFetch('/classrooms')
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
  const response = await apiFetch('/auth/upgrade-teacher', {
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
  const response = await apiFetch(`/classrooms/${encodeURIComponent(slug)}`)
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load classroom')
  return body.classroom
}

export async function logout() {
  await apiFetch('/auth/logout', { method: 'POST' })
}

async function authRequest(path: string, payload: unknown) {
  const response = await fetch(`${API_BASE}${path}`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Authentication failed')
  return body as { user: AuthUser; access_token: string }
}

export const teacherLogin = (uniqueId: string, password: string) => authRequest('/auth/teacher/login', { unique_id: uniqueId, password })
export const teacherRegister = (name: string, uniqueId: string, password: string, teacherInviteCode: string) => authRequest('/auth/teacher/register', { name, unique_id: uniqueId, password, teacher_invite_code: teacherInviteCode })

export async function teacherClassrooms() {
  const response = await fetch(`${API_BASE}/teacher/classrooms`, { credentials: 'include' })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load teacher classrooms')
  return body.classrooms as Array<Record<string, string | number>>
}

export async function teacherStudents(slug: string) {
  const response = await fetch(`${API_BASE}/classrooms/${encodeURIComponent(slug)}/students`, { credentials: 'include' })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load students')
  return body.students as Array<Record<string, string | number>>
}

export async function createTeacherQuiz(payload: { classroom_slug: string; title: string; description: string; difficulty: string; time_limit_minutes: number; questions: Array<{ prompt: string; question_type: 'MCQ' | 'Numerical'; choices: string[]; answer: string; explanation: string; hints: string[] }> }) {
  const response = await fetch(`${API_BASE}/teacher/quizzes`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not publish quiz')
  return body
}

export async function studentQuizzes() {
  const response = await fetch(`${API_BASE}/teacher/student-quizzes`, { credentials: 'include' })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load classroom quizzes')
  return body.quizzes as Array<Record<string, string | number>>
}

export async function studentQuizDetail(id: string) {
  const response = await fetch(`${API_BASE}/teacher/student-quizzes/${encodeURIComponent(id)}`, { credentials: 'include' })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load quiz')
  return body.quiz as { id: string; title: string; difficulty: string; time_limit_minutes: number; questions: Array<{ id: string; prompt: string; choices: string[]; answer: string; explanation: string }> }
}

export async function listJeeTopics(subject?: string): Promise<JeeTopic[]> {
  const response = await apiFetch(`/content/topics${subject ? `?subject=${encodeURIComponent(subject)}` : ''}`)
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load topics')
  return body.topics
}

export async function listJeeProblems(topic?: string): Promise<JeeProblem[]> {
  const response = await apiFetch(`/content/problems${topic ? `?topic=${encodeURIComponent(topic)}` : ''}`)
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load problems')
  return body.problems
}

export async function getJeeProblem(id: string): Promise<JeeProblem> {
  const response = await apiFetch(`/content/problems/${encodeURIComponent(id)}`)
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not load problem')
  return body.problem
}

export async function submitJeeAttempt(id: string, payload: { answer: string; time_taken: number; hint_used: boolean }) {
  const response = await apiFetch(`/content/problems/${encodeURIComponent(id)}/attempt`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not save attempt')
  return body.attempt
}
