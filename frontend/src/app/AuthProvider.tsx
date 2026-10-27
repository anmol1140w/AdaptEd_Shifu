import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { AuthSession, Classroom, CreateClassroomInput, JoinClassroomInput, Role } from '../types'
import { clearSession, getSession, patchSession, setSession, subscribeSession } from '../services/session'
import {
  completeAuthCallback,
  completeGoogleCallback,
  googleAuthStatus,
  signInWithPassword,
  signUpWithPassword,
  type AuthResult,
} from '../features/auth/services/authService'
import { createClassroom as createRemoteClassroom, getCurrentUser, joinClassroom as joinRemoteClassroom, listClassrooms, teacherLogin as teacherLoginRemote, teacherRegister as teacherRegisterRemote, upgradeToTeacher as upgradeRemoteToTeacher } from '../services/api'

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
  teacherLogin: (input: { uniqueId: string; password: string }) => Promise<AuthResult<AuthSession>>
  teacherRegister: (input: { name: string; uniqueId: string; password: string }) => Promise<AuthResult<AuthSession>>
  continueWithGoogle: () => AuthResult<AuthSession>
  finishCallback: () => Promise<AuthResult<AuthSession>>
  signOut: () => void
  refreshClassrooms: () => void
  createClassroom: (input: CreateClassroomInput) => Promise<{ ok: true; data: Classroom } | { ok: false; message: string }>
  joinClassroom: (input: JoinClassroomInput) => Promise<{ ok: true; data: Classroom } | { ok: false; message: string }>
  upgradeToTeacher: (inviteCode: string) => Promise<{ ok: true } | { ok: false; message: string }>
  completeOnboarding: (role?: Role) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(() => getSession())
  const [ready, setReady] = useState(false)
  const [classrooms, setClassrooms] = useState<Classroom[]>([])

  useEffect(() => subscribeSession(setSession), [])

  useEffect(() => {
    let active = true
    const hydrate = async () => {
      if (!getSession()) {
        const user = await getCurrentUser()
        if (active && user) setSession({ user: { ...user, onboardingComplete: false }, provider: 'google', issuedAt: new Date().toISOString(), isDemo: false })
      }
      if (active) setReady(true)
    }
    void hydrate()
    return () => { active = false }
  }, [])

  const refreshClassrooms = useCallback(async () => {
    if (!getSession()) { setClassrooms([]); return }
    try { setClassrooms(await listClassrooms()) } catch { setClassrooms([]) }
  }, [])

  useEffect(() => {
    void refreshClassrooms()
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
        if (result.ok) void refreshClassrooms()
        return result
      },
      signUp: (input) => {
        const result = signUpWithPassword(input)
        if (result.ok) void refreshClassrooms()
        return result
      },
      teacherLogin: async (input) => { try { const result = await teacherLoginRemote(input.uniqueId, input.password); const next = { user: { ...result.user, avatar: '', onboardingComplete: true }, provider: 'password' as const, issuedAt: new Date().toISOString(), isDemo: false }; setSession(next); return { ok: true, data: next } } catch (error) { return { ok: false, message: error instanceof Error ? error.message : 'Teacher login failed', field: 'form' as const } } },
      teacherRegister: async (input) => { try { const result = await teacherRegisterRemote(input.name, input.uniqueId, input.password); const next = { user: { ...result.user, avatar: '', onboardingComplete: true }, provider: 'password' as const, issuedAt: new Date().toISOString(), isDemo: false }; setSession(next); return { ok: true, data: next } } catch (error) { return { ok: false, message: error instanceof Error ? error.message : 'Teacher registration failed', field: 'form' as const } } },
      continueWithGoogle: () => { window.location.assign(`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'}/auth/google/start`); return { ok: false, message: '', field: 'form' as const } },
      finishCallback: async () => {
        const result = await completeGoogleCallback()
        if (result.ok) refreshClassrooms()
        return result
      },
      signOut: () => {
        clearSession()
        setClassrooms([])
      },
      refreshClassrooms,
      createClassroom: async (input) => { try { const result = await createRemoteClassroom(input); await refreshClassrooms(); return { ok: true, data: result } } catch (error) { return { ok: false, message: error instanceof Error ? error.message : 'Could not create classroom' } } },
      joinClassroom: async (input) => { try { const result = await joinRemoteClassroom(input.code); await refreshClassrooms(); return { ok: true, data: result } } catch (error) { return { ok: false, message: error instanceof Error ? error.message : 'Could not join classroom' } } },
      upgradeToTeacher: async (inviteCode) => { try { await upgradeRemoteToTeacher(inviteCode); patchSession({ role: 'teacher' }); return { ok: true } } catch (error) { return { ok: false, message: error instanceof Error ? error.message : 'Invalid teacher invite code' } } },
      completeOnboarding: (role) => {
        const userPatch = { onboardingComplete: true, ...(role ? { role } : {}) }
        patchSession(userPatch)
        if (session) setSession({ ...session, user: { ...session.user, ...userPatch } })
      },
    }
  }, [classrooms, ready, refreshClassrooms, session])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
