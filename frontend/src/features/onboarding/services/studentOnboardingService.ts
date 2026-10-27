import type { StudentOnboardingProfile } from '../../../types'

/**
 * Development-only persistence for the student preference flow.
 *
 * No profile/onboarding write endpoint is exposed by the current frontend API
 * contract, so answers are kept locally and keyed by the authenticated user.
 * Replace this boundary with the supported API when one is available.
 */
const STORAGE_KEY = 'adapted-student-onboarding-v1'
const memoryProfiles = new Map<string, StudentOnboardingProfile>()

type ProfileStore = Record<string, StudentOnboardingProfile>

function readStore(): ProfileStore {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as unknown
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? parsed as ProfileStore
      : {}
  } catch {
    return {}
  }
}

export function getStudentOnboarding(userId: string): StudentOnboardingProfile | null {
  const memory = memoryProfiles.get(userId)
  if (memory) return memory
  const stored = readStore()[userId]
  if (stored) memoryProfiles.set(userId, stored)
  return stored ?? null
}

export function saveStudentOnboarding(userId: string, profile: StudentOnboardingProfile): { ok: true; persistence: 'localStorage' | 'memory' } {
  memoryProfiles.set(userId, profile)
  try {
    const next = { ...readStore(), [userId]: profile }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    return { ok: true, persistence: 'localStorage' }
  } catch {
    // Keep the active flow usable, but let the UI explain that this is session-only.
    return { ok: true, persistence: 'memory' }
  }
}
