import type { AuthProvider, AuthSession, AuthUser } from '../../../types'
import { getSession, setAccessToken, setSession } from '../../../services/session'

/**
 * Phase 1 authentication service.
 *
 * Password accounts use the FastAPI auth API. Local validation runs first so the
 * form can show useful errors without making a request.
 */

export type AuthResult<T> =
  | { ok: true; data: T }
  | { ok: false; message: string; field?: 'name' | 'email' | 'password' | 'confirm' | 'form' }

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
const MIN_PASSWORD_LENGTH = 8
const SESSION_HOURS = 12

export interface GoogleAuthStatus {
  configured: boolean
  message: string
  requiredEnv: string[]
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

/** Reports whether the frontend has a real backend OAuth flow wired up. */
export function googleAuthStatus(): GoogleAuthStatus {
  const configured = import.meta.env.VITE_GOOGLE_OAUTH_ENABLED === 'true'
  return {
    configured,
    message: configured ? '' : 'Google OAuth requires backend client credentials and redirect settings.',
    requiredEnv: ['ADAPTED_GOOGLE_CLIENT_ID', 'ADAPTED_GOOGLE_CLIENT_SECRET'],
  }
}

export function startGoogleOAuth(): void {
  window.location.assign(`${API_BASE}/auth/google/start`)
}

export async function completeGoogleCallback(): Promise<AuthResult<AuthSession>> {
  try {
    const response = await fetch(`${API_BASE}/auth/me`, { credentials: 'include' })
    if (!response.ok) return { ok: false, message: 'Google sign-in could not be completed. Please try again.', field: 'form' }
    const body = await response.json() as { user: { id: string; name: string; email: string; role: 'student' | 'teacher' } }
    const session: AuthSession = {
      user: { ...body.user, onboardingComplete: false },
      provider: 'google',
      issuedAt: new Date().toISOString(),
      isDemo: false,
    }
    setSession(session)
    return { ok: true, data: session }
  } catch {
    return { ok: false, message: 'Could not reach the AdaptEd authentication server.', field: 'form' }
  }
}

export function validateEmail(email: string): string | null {
  const value = email.trim()
  if (!value) return 'Enter your email address.'
  if (!EMAIL_PATTERN.test(value)) return 'Enter a valid email address, for example you@school.edu.'
  return null
}

export function validatePassword(password: string, action: 'sign-in' | 'sign-up'): string | null {
  if (!password) return action === 'sign-in' ? 'Enter your password.' : 'Create a password.'
  if (action === 'sign-up' && password.length < MIN_PASSWORD_LENGTH) {
    return `Use at least ${MIN_PASSWORD_LENGTH} characters.`
  }
  return null
}

function createSession(name: string, email: string, provider: AuthProvider): AuthSession {
  const user: AuthUser = {
    id: `local-${email.trim().toLowerCase()}`,
    name: name.trim(),
    email: email.trim().toLowerCase(),
    role: 'student',
    onboardingComplete: false,
  }
  return {
    user,
    provider,
    issuedAt: new Date(Date.now() + SESSION_HOURS * 60 * 60 * 1000).toISOString(),
    isDemo: false,
  }
}

export async function signInWithPassword(input: { email: string; password: string }): Promise<AuthResult<AuthSession>> {
  const emailError = validateEmail(input.email)
  if (emailError) return { ok: false, message: emailError, field: 'email' }
  const passwordError = validatePassword(input.password, 'sign-in')
  if (passwordError) return { ok: false, message: passwordError, field: 'password' }

  try {
    const response = await fetch(`${API_BASE}/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: input.email.trim(), password: input.password }) })
    const body = await response.json()
    if (!response.ok) return { ok: false, message: body.detail ?? 'Could not sign in.', field: 'form' }
    const session = createSession(body.user.name, body.user.email, 'password')
    session.user = { ...body.user, onboardingComplete: false }
    setAccessToken(body.access_token)
    setSession(session)
    return { ok: true, data: session }
  } catch { return { ok: false, message: 'Could not reach the AdaptEd authentication server.', field: 'form' } }
}

export async function signUpWithPassword(input: {
  name: string
  email: string
  password: string
  confirm: string
  teacherInviteCode?: string
}): Promise<AuthResult<AuthSession>> {
  if (!input.name.trim()) return { ok: false, message: 'Enter your full name.', field: 'name' }
  if (input.name.trim().length < 2) return { ok: false, message: 'That name looks too short.', field: 'name' }

  const emailError = validateEmail(input.email)
  if (emailError) return { ok: false, message: emailError, field: 'email' }

  const passwordError = validatePassword(input.password, 'sign-up')
  if (passwordError) return { ok: false, message: passwordError, field: 'password' }

  if (input.password !== input.confirm) {
    return { ok: false, message: 'Both passwords must match.', field: 'confirm' }
  }

  try {
    const response = await fetch(`${API_BASE}/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: input.name.trim(), email: input.email.trim(), password: input.password, ...(input.teacherInviteCode?.trim() ? { teacher_invite_code: input.teacherInviteCode.trim() } : {}) }) })
    const body = await response.json()
    if (!response.ok) return { ok: false, message: body.detail ?? 'Could not create the account.', field: 'form' }
    const session = createSession(body.user.name, body.user.email, 'password')
    session.user = { ...body.user, onboardingComplete: false }
    setAccessToken(body.access_token)
    setSession(session)
    return { ok: true, data: session }
  } catch { return { ok: false, message: 'Could not reach the AdaptEd authentication server.', field: 'form' } }
}

/** Complete the password/Google sign-in round trip started at /sign-in. */
export function completeAuthCallback(): AuthResult<AuthSession> {
  const session = getSession()
  if (!session) {
    return { ok: false, message: 'This sign-in link expired. Please sign in again.', field: 'form' }
  }
  return { ok: true, data: session }
}
