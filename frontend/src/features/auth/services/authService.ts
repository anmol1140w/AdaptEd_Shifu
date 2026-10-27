import type { AuthProvider, AuthSession, AuthUser } from '../../../types'
import { getSession, setSession } from '../../../services/session'
import { membershipsFor } from '../../onboarding/services/classroomService'

/**
 * Phase 1 authentication service.
 *
 * This repository contains no authentication provider: the backend exposes only
 * a health route, and no OAuth client id is configured anywhere. So this service
 * performs client-side validation and keeps a local, clearly-flagged demo session
 * (`isDemo: true`). It never stores passwords and never fabricates a provider
 * callback — `googleAuth()` reports that the provider is not configured instead.
 */

export type AuthResult<T> =
  | { ok: true; data: T }
  | { ok: false; message: string; field?: 'name' | 'email' | 'password' | 'confirm' | 'form' }

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
const MIN_PASSWORD_LENGTH = 8
const SESSION_HOURS = 12

export interface GoogleAuthStatus {
  configured: false
  message: string
  requiredEnv: string[]
}

/** Reports whether a real Google OAuth provider is wired up. */
export function googleAuthStatus(): GoogleAuthStatus {
  return {
    configured: false,
    message:
      'Google sign-in is not configured for this build yet. Add a Google OAuth client id and its authorized redirect URI to continue with email and password for now.',
    requiredEnv: [
      'VITE_GOOGLE_CLIENT_ID (Google OAuth web client id)',
      'VITE_GOOGLE_REDIRECT_URI (must match /auth/callback on this origin)',
    ],
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
    role: 'teacher',
    onboardingComplete: false,
  }
  return {
    user,
    provider,
    issuedAt: new Date(Date.now() + SESSION_HOURS * 60 * 60 * 1000).toISOString(),
    isDemo: true,
  }
}

export function signInWithPassword(input: { email: string; password: string }): AuthResult<AuthSession> {
  const emailError = validateEmail(input.email)
  if (emailError) return { ok: false, message: emailError, field: 'email' }
  const passwordError = validatePassword(input.password, 'sign-in')
  if (passwordError) return { ok: false, message: passwordError, field: 'password' }

  const existing = getSession()
  const normalizedEmail = input.email.trim().toLowerCase()
  const returning = existing?.user.email === normalizedEmail ? existing : null
  const session = createSession(returning?.user.name ?? localNameFromEmail(input.email), input.email, 'password')
  if (returning) {
    session.user.onboardingComplete = returning.user.onboardingComplete
    session.user.role = returning.user.role
  }
  const memberRecord = membershipsFor(session.user.id)
    .flatMap((classroom) => classroom.members)
    .find((member) => member.userId === session.user.id)
  if (memberRecord) {
    session.user.role = memberRecord.role
    session.user.onboardingComplete = true
  }
  setSession(session)
  return { ok: true, data: session }
}

export function signUpWithPassword(input: {
  name: string
  email: string
  password: string
  confirm: string
}): AuthResult<AuthSession> {
  if (!input.name.trim()) return { ok: false, message: 'Enter your full name.', field: 'name' }
  if (input.name.trim().length < 2) return { ok: false, message: 'That name looks too short.', field: 'name' }

  const emailError = validateEmail(input.email)
  if (emailError) return { ok: false, message: emailError, field: 'email' }

  const passwordError = validatePassword(input.password, 'sign-up')
  if (passwordError) return { ok: false, message: passwordError, field: 'password' }

  if (input.password !== input.confirm) {
    return { ok: false, message: 'Both passwords must match.', field: 'confirm' }
  }

  const session = createSession(input.name, input.email, 'password')
  setSession(session)
  return { ok: true, data: session }
}

/** Complete the password/Google sign-in round trip started at /sign-in. */
export function completeAuthCallback(): AuthResult<AuthSession> {
  const session = getSession()
  if (!session) {
    return { ok: false, message: 'This sign-in link expired. Please sign in again.', field: 'form' }
  }
  return { ok: true, data: session }
}

function localNameFromEmail(email: string): string {
  const local = email.trim().split('@')[0] ?? 'learner'
  return local
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ') || 'Learner'
}
