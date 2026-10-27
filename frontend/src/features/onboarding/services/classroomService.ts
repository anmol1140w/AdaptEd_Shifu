import type {
  Classroom,
  ClassroomRole,
  CreateClassroomInput,
  JeeSubjectId,
  JoinClassroomInput,
} from '../../../types'
import { getSession } from '../../../services/session'

/**
 * Phase 1 classroom service.
 *
 * The repository has no classroom API (the backend only serves /api/v1/health),
 * so classrooms are stored in this browser and every record is flagged
 * `isDemo: true`. The public surface — create / lookup / join / memberships —
 * matches the shape a REST client would return, so the local implementation can
 * be swapped for `VITE_API_BASE_URL` calls without touching any page component.
 */
export type ClassroomResult<T> = { ok: true; data: T } | { ok: false; message: string }

const STORAGE_KEY = 'adapted-local-classrooms-v1'
const CODE_PATTERN = /^[A-Z0-9]{4,8}$/

const SUBJECT_LABELS: Record<JeeSubjectId, string> = {
  physics: 'Physics',
  chemistry: 'Chemistry',
  mathematics: 'Mathematics',
}

export const JEE_SUBJECTS: JeeSubjectId[] = ['physics', 'chemistry', 'mathematics']
export const CLASS_LEVELS = ['Class 11', 'Class 12'] as const
export const EXAM_TARGETS = ['JEE Main', 'JEE Advanced', 'JEE Main + Advanced'] as const
export const ACADEMIC_YEARS = ['2025–26', '2026–27', '2027–28'] as const

function readStore(): Classroom[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as Classroom[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function writeStore(classrooms: Classroom[]): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(classrooms))
  } catch {
    /* storage unavailable */
  }
}

function seedStore(): Classroom[] {
  const demo: Classroom = {
    id: 'demo-classroom-pcm',
    name: 'JEE PCM Foundation',
    code: 'PCM2027',
    classLevel: 'Class 12',
    academicYear: '2026–27',
    examTarget: 'JEE Main + Advanced',
    subjects: ['physics', 'chemistry', 'mathematics'],
    creatorId: 'local-demo-teacher',
    creatorName: 'Demo Teacher',
    members: [],
    createdAt: new Date().toISOString(),
    isDemo: true,
  }
  writeStore([demo])
  return [demo]
}

function allClassrooms(): Classroom[] {
  const stored = readStore()
  if (stored.length === 0) return seedStore()
  return stored
}

function save(classrooms: Classroom[]): void {
  writeStore(classrooms)
}

function randomCode(taken: Set<string>): string {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  for (let attempt = 0; attempt < 50; attempt += 1) {
    let code = ''
    for (let index = 0; index < 6; index += 1) {
      code += alphabet[Math.floor(Math.random() * alphabet.length)]
    }
    if (!taken.has(code)) return code
  }
  return `C${Date.now().toString(36).toUpperCase().slice(-6)}`
}

export function subjectLabel(subject: JeeSubjectId): string {
  return SUBJECT_LABELS[subject]
}

export function createClassroom(input: CreateClassroomInput): ClassroomResult<Classroom> {
  const session = getSession()
  if (!session) return { ok: false, message: 'Sign in before creating a classroom.' }

  const name = input.name.trim()
  if (!name) return { ok: false, message: 'Classroom name is required.' }
  if (name.length < 3) return { ok: false, message: 'Use at least 3 characters for the classroom name.' }
  if (name.length > 60) return { ok: false, message: 'Keep the classroom name under 60 characters.' }

  const teacherName = input.teacherName.trim()
  if (!teacherName) return { ok: false, message: 'Enter the teacher or display name.' }

  if (input.subjects.length === 0) {
    return { ok: false, message: 'Select at least one subject: Physics, Chemistry or Mathematics.' }
  }
  const invalidSubject = input.subjects.find((subject) => !JEE_SUBJECTS.includes(subject))
  if (invalidSubject) return { ok: false, message: 'AdaptEd supports Physics, Chemistry and Mathematics only.' }

  const classrooms = allClassrooms()
  const duplicate = classrooms.some(
    (classroom) =>
      classroom.creatorId === session.user.id &&
      classroom.name.toLowerCase() === name.toLowerCase(),
  )
  if (duplicate) return { ok: false, message: 'You already created a classroom with this name.' }

  const code = randomCode(new Set(classrooms.map((classroom) => classroom.code)))
  const now = new Date().toISOString()
  const classroom: Classroom = {
    id: `classroom-${Date.now().toString(36)}`,
    name,
    code,
    classLevel: input.classLevel,
    academicYear: input.academicYear,
    examTarget: input.examTarget,
    subjects: input.subjects,
    creatorId: session.user.id,
    creatorName: teacherName,
    members: [
      { userId: session.user.id, name: teacherName, role: 'teacher', joinedAt: now },
    ],
    createdAt: now,
    isDemo: true,
  }

  save([...classrooms, classroom])
  return { ok: true, data: classroom }
}

export function lookupClassroomByCode(code: string): ClassroomResult<Classroom> {
  const normalized = code.trim().toUpperCase()
  if (!normalized) return { ok: false, message: 'Enter a classroom code.' }
  if (!CODE_PATTERN.test(normalized)) {
    return { ok: false, message: 'A classroom code is 4–8 letters or numbers, for example PCM2027.' }
  }
  const classroom = allClassrooms().find((item) => item.code === normalized)
  if (!classroom) return { ok: false, message: 'We could not find a classroom with that code.' }
  return { ok: true, data: classroom }
}

export function joinClassroom(input: JoinClassroomInput): ClassroomResult<Classroom> {
  const session = getSession()
  if (!session) return { ok: false, message: 'Sign in before joining a classroom.' }

  const lookup = lookupClassroomByCode(input.code)
  if (!lookup.ok) return lookup

  const classrooms = allClassrooms()
  const index = classrooms.findIndex((item) => item.id === lookup.data.id)
  const classroom = classrooms[index]
  if (!classroom) return { ok: false, message: 'We could not find a classroom with that code.' }

  const existing = classroom.members.find((member) => member.userId === session.user.id)
  if (existing) {
    return { ok: false, message: `You are already in ${classroom.name} as ${existing.role}.` }
  }

  const role: ClassroomRole = classroom.creatorId === session.user.id ? 'teacher' : 'student'
  const updated: Classroom = {
    ...classroom,
    members: [
      ...classroom.members,
      { userId: session.user.id, name: session.user.name, role, joinedAt: new Date().toISOString() },
    ],
  }
  classrooms[index] = updated
  save(classrooms)
  return { ok: true, data: updated }
}

/** Classrooms the current user belongs to. */
export function membershipsFor(userId: string): Classroom[] {
  return allClassrooms().filter((classroom) =>
    classroom.members.some((member) => member.userId === userId),
  )
}

export function membershipRole(classroom: Classroom, userId: string): ClassroomRole | null {
  return classroom.members.find((member) => member.userId === userId)?.role ?? null
}
