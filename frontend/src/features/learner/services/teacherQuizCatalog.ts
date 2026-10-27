import { TEACHER } from '../../../services/data'
import type { Difficulty, JeeSubjectId } from '../../../types'
import { CHAPTER_QUIZZES } from './quizCatalog'

export interface TeacherQuizUpload {
  id: string
  quizId: string
  title: string
  teacherName: string
  uploadedAt: string
}

export interface RecentlyUploadedQuiz {
  id: string
  quizId: string
  title: string
  teacherName: string
  subject: JeeSubjectId
  chapter: string
  questionCount: number
  maxMarks: number
  timeLimitMinutes: number
  difficulty?: Difficulty
  uploadedAt: string
  source: 'mock'
}

/**
 * Teacher quiz upload is not available in the current API or teacher UI.
 * These local fixtures reuse existing quiz IDs so Attempt Now enters the
 * existing attempt flow. Replace this fixture list with the upload API once
 * it exposes quiz metadata, questions, and an upload timestamp.
 */
const mockTeacherUploads: TeacherQuizUpload[] = [
  { id: 'upload-demo-01', quizId: 'mock-mathematics-area-under-the-curve-quiz-1', title: 'Area Under the Curve: Quick Check', teacherName: TEACHER.name, uploadedAt: '2026-10-27T09:30:00+05:30' },
  { id: 'upload-demo-02', quizId: 'local-chemistry-electrochemistry-quiz-1', title: 'Electrochemistry: Cell Potential', teacherName: TEACHER.name, uploadedAt: '2026-10-26T15:15:00+05:30' },
  { id: 'upload-demo-03', quizId: 'local-physics-rotation-quiz-3', title: 'Rotational Motion: Challenge Set', teacherName: TEACHER.name, uploadedAt: '2026-10-25T11:40:00+05:30' },
  { id: 'upload-demo-04', quizId: 'mock-chemistry-chemical-kinetics-quiz-1', title: 'Chemical Kinetics: First Principles', teacherName: TEACHER.name, uploadedAt: '2026-10-23T14:00:00+05:30' },
  { id: 'upload-demo-05', quizId: 'local-mathematics-definite-integration-quiz-1', title: 'Definite Integration: Practice Set', teacherName: TEACHER.name, uploadedAt: '2026-10-21T09:15:00+05:30' },
  { id: 'upload-demo-06', quizId: 'local-physics-newton-s-laws-of-motion-nlm-quiz-1', title: 'Newton’s Laws: Classroom Quiz', teacherName: TEACHER.name, uploadedAt: '2026-10-18T16:45:00+05:30' },
]

export function recentlyUploadedQuizzes(): RecentlyUploadedQuiz[] {
  return mockTeacherUploads.flatMap((upload) => {
    const quiz = CHAPTER_QUIZZES.find((item) => item.id === upload.quizId)
    if (!quiz) return []
    return [{
      id: upload.id,
      quizId: quiz.id,
      title: upload.title,
      teacherName: upload.teacherName,
      subject: quiz.subject,
      chapter: quiz.chapter,
      questionCount: quiz.questionCount,
      maxMarks: quiz.maxMarks,
      timeLimitMinutes: quiz.timeLimitMinutes,
      difficulty: quiz.difficulty,
      uploadedAt: upload.uploadedAt,
      source: 'mock' as const,
    }]
  }).sort((a, b) => Date.parse(b.uploadedAt) - Date.parse(a.uploadedAt))
}
