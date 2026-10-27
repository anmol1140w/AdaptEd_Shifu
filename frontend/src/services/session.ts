import type { AuthSession } from '../types'

/**
 * Session store for Phase 1.
 *
 * No authentication provider is configured in this repository yet, so the session
 * lives in the browser and is clearly flagged with `isDemo: true`. When a real
 * provider is added, only this module and `authService` need to change — every
 * consumer reads through the same subscribe/get/set/clear API.
 */
const SESSION_KEY = 'adapted-local-session-v1'

type Listener = (session: AuthSession | null) => void

let memorySession: AuthSession | null = null
let hydrated = false
const listeners = new Set<Listener>()

function readPersisted(): AuthSession | null {
  try {
    const raw = window.localStorage.getItem(SESSION_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as AuthSession
    if (!parsed || !parsed.user || typeof parsed.user.id !== 'string') return null
    return parsed
  } catch {
    return null
  }
}

function hydrate() {
  if (hydrated) return
  hydrated = true
  memorySession = readPersisted()
}

export function getSession(): AuthSession | null {
  hydrate()
  return memorySession
}

export function setSession(session: AuthSession): void {
  hydrate()
  memorySession = session
  if (session.isDemo) {
    try {
      window.localStorage.setItem(SESSION_KEY, JSON.stringify(session))
    } catch {
      /* storage unavailable: keep the in-memory session only */
    }
  }
  emit()
}

export function patchSession(patch: Partial<AuthSession['user']>): void {
  hydrate()
  if (!memorySession) return
  memorySession = { ...memorySession, user: { ...memorySession.user, ...patch } }
  if (memorySession.isDemo) {
    try {
      window.localStorage.setItem(SESSION_KEY, JSON.stringify(memorySession))
    } catch {
      /* ignore */
    }
  }
  emit()
}

export function clearSession(): void {
  hydrate()
  memorySession = null
  try {
    window.localStorage.removeItem(SESSION_KEY)
  } catch {
    /* ignore */
  }
  emit()
}

export function subscribeSession(listener: Listener): () => void {
  hydrate()
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function emit() {
  listeners.forEach((listener) => listener(memorySession))
}
