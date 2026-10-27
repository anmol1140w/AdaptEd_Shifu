export type Role = 'student' | 'teacher'
export type SubjectId = 'physics' | 'chemistry' | 'mathematics' | 'biology'
export type Difficulty = 'Easy' | 'Medium' | 'Hard'
export type QuestionType = 'MCQ' | 'Numerical'
export type ActivityType = 'question_attempted' | 'lesson_completed' | 'assessment_completed' | 'mistake_reviewed' | 'targeted_practice'
export type MasteryStatus = 'Weak' | 'Developing' | 'Proficient' | 'Mastered'

export interface User {
  id: string
  name: string
  role: Role
  avatar: string
}

export interface StudentProfile extends User {
  role: 'student'
  className: string
  exam: string
  subjects: SubjectId[]
  weeklyGoal: number
  streak: number
}

export interface TeacherProfile extends User {
  role: 'teacher'
  subject: string
  classes: string[]
}

export interface Concept {
  id: string
  name: string
  subject: SubjectId
  chapter: string
  description: string
  prerequisites: string[]
  mastery: number
  recentAccuracy: number
  attempts: number
  lastPracticed: string
}

export interface Problem {
  id: string
  title: string
  subject: SubjectId
  className: string
  chapter: string
  conceptIds: string[]
  tags: string[]
  difficulty: Difficulty
  questionType: QuestionType
  examRelevance: string[]
  estimatedMinutes: number
  statement: string
  choices?: string[]
  answer: string
  explanation: string
  formula?: string
  hints?: string[]
  prerequisiteConcepts?: string[]
}

export interface ProblemAttempt {
  id: string
  problemId: string
  studentId: string
  answer: string
  correct: boolean
  timeTaken: number
  hintUsed: boolean
  createdAt: string
}

export interface Assessment {
  id: string
  title: string
  type: string
  subject: SubjectId
  chapter: string
  questionIds: string[]
  questionCount: number
  duration: number
  difficulty: Difficulty
  examRelevance: string
  adaptive: boolean
  description: string
}

export interface AssessmentAttempt {
  id: string
  assessmentId: string
  studentId: string
  answers: Record<string, string>
  score: number
  accuracy: number
  timeTaken: number
  completedAt: string
  questionResults?: Record<string, boolean>
}

export interface LearningActivity {
  id: string
  studentId: string
  type: ActivityType
  timestamp: string
  relatedId?: string
  conceptId?: string
  contributionPoints: number
  isDemo: boolean
  dedupeKey?: string
  metadata?: { label?: string; duration?: number }
}

export interface LearningRecommendation {
  id: string
  title: string
  description: string
  reason: string
  actionLabel: string
  actionPath: string
  type: 'practice' | 'lesson' | 'assessment' | 'review'
  conceptId?: string
}

export interface LearningPathItem {
  id: string
  conceptId: string
  title: string
  objective: string
  duration: string
  difficulty: Difficulty
  activityType: 'Learn' | 'Practice' | 'Assess' | 'Revise'
  prerequisites: string[]
  completed: boolean
  locked: boolean
}

export interface TutorMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sourceLabel?: string
}

export interface TeacherStudent {
  id: string
  name: string
  className: string
  section: string
  overallMastery: number
  latestAssessment: number
  recentActivity: string
  weakestConcept: string
  interventionStatus: 'On Track' | 'Needs Attention' | 'Intervention Suggested'
  trend: number[]
  subjectScores: Record<string, number>
  conceptScores: Record<string, number>
  mistakes: string[]
}

export interface TeacherIntervention {
  id: string
  conceptId: string
  conceptName: string
  affectedStudents: string[]
  severity: 'High' | 'Medium' | 'Low'
  reason: string
  recommendation: string
  status: 'Open' | 'Reviewed' | 'Completed'
  createdAt: string
}

// --- Phase 1: authentication, onboarding and classrooms (frontend-only UI state) ---

/** Subjects AdaptEd supports. Phase 1 is restricted to PCM. */
export type JeeSubjectId = 'physics' | 'chemistry' | 'mathematics'
export type ClassLevel = 'Class 11' | 'Class 12'
export type ExamTarget = 'JEE Main' | 'JEE Advanced' | 'JEE Main + Advanced'
export type StudentClassLevel = 'Class 11' | 'Class 12' | 'Dropper' | 'Other'
export type StudentJeeGoal = 'JEE Main' | 'JEE Advanced' | 'Both'
export type StudentStrengthSubject = JeeSubjectId | 'all'
export type StudentImprovementSubject = JeeSubjectId | 'not-sure'
export type StudentLearningStyle = 'concepts-first' | 'questions-first' | 'worked-examples' | 'mix'
export type ClassroomRole = 'teacher' | 'student'
export type AuthProvider = 'password' | 'google'

export interface StudentOnboardingProfile {
  displayName: string
  currentClass: StudentClassLevel
  jeeGoal: StudentJeeGoal
  strongestSubject: StudentStrengthSubject
  improvementSubject: StudentImprovementSubject
  learningStyle: StudentLearningStyle
  completedAt: string
}

export interface AuthUser {
  id: string
  name: string
  email: string
  role: Role
  onboardingComplete: boolean
  /** Student preference onboarding is separate from classroom membership onboarding. */
  studentOnboardingComplete?: boolean
  studentOnboarding?: StudentOnboardingProfile
}

export interface AuthSession {
  user: AuthUser
  provider: AuthProvider
  issuedAt: string
  /** True while authentication is served by the local UI-only demo service. */
  isDemo: boolean
}

export interface ClassroomMember {
  userId: string
  name: string
  role: ClassroomRole
  joinedAt: string
}

export interface Classroom {
  id: string
  name: string
  code: string
  classLevel: ClassLevel
  academicYear: string
  examTarget: ExamTarget
  subjects: JeeSubjectId[]
  creatorId: string
  creatorName: string
  members: ClassroomMember[]
  createdAt: string
  /** True while classrooms are served by the local UI-only demo service. */
  isDemo: boolean
}

export interface CreateClassroomInput {
  name: string
  teacherName: string
  classLevel: ClassLevel
  academicYear: string
  examTarget: ExamTarget
  subjects: JeeSubjectId[]
}

export interface JoinClassroomInput {
  code: string
}

export interface DemoState {
  selectedRole: Role | null
  activity: LearningActivity[]
  problemAttempts: ProblemAttempt[]
  assessmentAttempts: AssessmentAttempt[]
  completedPlanTasks: string[]
  completedPathItems: string[]
  bookmarks: string[]
  masteryAdjustments: Record<string, number>
  tutorMessages: TutorMessage[]
  interventions: TeacherIntervention[]
}
