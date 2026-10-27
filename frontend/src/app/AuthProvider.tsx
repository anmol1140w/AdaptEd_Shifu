import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { AuthSession, Classroom, CreateClassroomInput, JoinClassroomInput, Role } from '../types'
import { clearSession, getSession, patchSession, subscribeSession } from '../services/session'
import {
  completeAuthCallback,
  googleAuthStatus,
  signInWithPassword,
  signUpWithPassword,
  type AuthResult,
} from '../features/auth/services/authService'
import {
  createClassroom,
  joinClassroom,
  membershipsFor,
} from '../features/onboarding/services/classroomService'

/**
 * One source of truth for the whole Phase 1 frontend: current user, auth status,
 * classroom membership and onboarding completion. Pages read this context and
 * never touch storage directly.
 */
interface AuthContextValue {
  session: AuthSession | null
  status: 'loading' | 'authenticated' | 'unauthenticated'
  classrooms: Classroom[]
  hasClassroom: boolean
  google: ReturnType<typeof googleAuthStatus>
  signIn: (input: { email: string; password: string }) => AuthResult<AuthSession>
  signUp: (input: { name: string; email: string; password: string; confirm: string }) => AuthResult<AuthSession>
  continueWithGoogle: () => AuthResult<AuthSession>
  finishCallback: () => AuthResult<AuthSession>
  signOut: () => void
  refreshClassrooms: () => void
  createClassroom: (input: CreateClassroomInput) => ReturnType<typeof createClassroom>
  joinClassroom: (input: JoinClassroomInput) => ReturnType<typeof joinClassroom>
  completeOnboarding: (role?: Role) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(() => getSession())
  const [ready, setReady] = useState(false)
  const [classrooms, setClassrooms] = useState<Classroom[]>([])

  useEffect(() => subscribeSession(setSession), [])

  useEffect(() => {
    // Hydration happens synchronously in the store; this tick settles the first paint.
    const timer = window.setTimeout(() => setReady(true), 0)
    return () => window.clearTimeout(timer)
  }, [])

  const refreshClassrooms = useCallback(() => {
    const current = getSession()
    setClassrooms(current ? membershipsFor(current.user.id) : [])
  }, [])

  useEffect(() => {
    refreshClassrooms()
  }, [refreshClassrooms, session?.user.id])

  const value = useMemo<AuthContextValue>(() => {
    const status: AuthContextValue['status'] = !ready
      ? 'loading'
      : session
        ? 'authenticated'
        : 'unauthenticated'

    return {
      session,
      status,
      classrooms,
      hasClassroom: classrooms.length > 0,
      google: googleAuthStatus(),
      signIn: (input) => {
        const result = signInWithPassword(input)
        if (result.ok) refreshClassrooms()
        return result
      },
      signUp: (input) => {
        const result = signUpWithPassword(input)
        if (result.ok) refreshClassrooms()
        return result
      },
      continueWithGoogle: () => ({ ok: false, message: googleAuthStatus().message, field: 'form' as const }),
      finishCallback: () => {
        const result = completeAuthCallback()
        if (result.ok) refreshClassrooms()
        return result
      },
      signOut: () => {
        clearSession()
        setClassrooms([])
      },
      refreshClassrooms,
      createClassroom: (input) => {
        const result = createClassroom(input)
        if (result.ok) refreshClassrooms()
        return result
      },
      joinClassroom: (input) => {
        const result = joinClassroom(input)
        if (result.ok) refreshClassrooms()
        return result
      },
      completeOnboarding: (role) => patchSession({ onboardingComplete: true, ...(role ? { role } : {}) }),
    }
  }, [classrooms, ready, refreshClassrooms, session])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
