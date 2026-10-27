const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'

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
  return body.classroom
}

export async function createClassroom(name: string, description?: string) {
  const response = await fetch(`${API_BASE}/classrooms`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
  })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Could not create classroom')
  return body.classroom
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
