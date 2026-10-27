const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init.headers,
    },
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail ?? 'The learning service could not complete this request.')
  return body as T
}

export type AdaptiveConcept = {
  concept_id: string; subject: string; class_level: number; chapter: string; name: string
  description: string; prerequisite_ids: string[]; approved_items?: number; starter_items?: number; available_items?: number; pending_review_items?: number
  attempts?: number; correct?: number; accuracy?: number; mastery_status?: string
  recommendation?: string; last_practiced?: string | null
  learners?: number; intervention?: string
}
export type AdaptiveQuestion = {
  item_id: string; concept_id: string; subject: string; class_level: number
  chapter: string; item_type: string; bloom_level: string; difficulty: string; question: string
}
export type LearningPathStep = { concept_id: string; name: string; chapter: string; mastery_status: string; action: string; reason: string }
export type LearnerSummary = { learner_id: string; name: string; attempts: number; accuracy: number; weak_concepts: string[]; intervention: string }
export type AILearningRecommendation = { concept_id: string; concept_name: string; chapter: string; action: string; reason: string; source_ids: string[] }
export type LearningCitation = {
  source_id: string
  citation: string
  text: string
  score: number
  source_kind?: string
  source_book_id?: string
  corpus_id?: string
  chapter_code?: string
  page_start?: number | null
  page_end?: number | null
  concept_ids?: string[]
}
export type GeneratedWeakQuiz = { id: string; status: string; question_count: number; citations: LearningCitation[] }
export type TutorMemory = { id: string; mode: 'hint' | 'explanation' | 'check_question'; question: string; message: string; check_question: string; source_ids: string[]; sources: LearningCitation[]; created_at: string }
export type LearningPreferences = { subject: string; class_level: number; updated_at: string | null }
export type TopicScore = { topic: string; attempts: number; correct: number; accuracy: number; mastery_score: number; confidence: number; trend: 'insufficient_evidence' | 'improving' | 'stable' | 'declining' }
export type TopicScores = Record<string, TopicScore>
export type AssessmentSummary = { attempts: number; correct: number; accuracy: number; topic_scores: TopicScores }

export function getConcepts(subject: string, classLevel: number) {
  return request<{ concepts: AdaptiveConcept[] }>(`/learning/concepts?subject=${subject}&class_level=${classLevel}`)
}
export function getProgress(subject: string, classLevel: number) {
  return request<{ subject: string; class_level: number; concepts: AdaptiveConcept[]; learning_path: LearningPathStep[] }>(`/learning/progress?subject=${subject}&class_level=${classLevel}`)
}
export function getLearningPreferences() {
  return request<{ preferences: LearningPreferences }>('/learning/preferences')
}
export function saveLearningPreferences(subject: string, classLevel: number) {
  return request<{ preferences: LearningPreferences }>('/learning/preferences', {
    method: 'PUT', body: JSON.stringify({ subject, class_level: classLevel }),
  })
}
export function startAdaptiveAssessment(subject: string, classLevel: number, conceptId?: string, assessmentType: 'adaptive' | 'mock' = 'adaptive') {
  return request<{ assessment_id: string; status: string; assessment_type: 'adaptive' | 'mock'; question_count: number; index: number; question: AdaptiveQuestion }>('/assessments/start', {
    method: 'POST', body: JSON.stringify({ subject, class_level: classLevel, question_count: assessmentType === 'mock' ? 10 : 5, assessment_type: assessmentType, ...(conceptId ? { concept_id: conceptId } : {}) }),
  })
}
export function resumeAdaptiveAssessment(assessmentId: string) {
  return request<{ assessment_id: string; status: string; assessment_type: 'adaptive' | 'mock'; question_count: number; index: number; question?: AdaptiveQuestion }>(`/assessments/${encodeURIComponent(assessmentId)}`)
}
export function submitAdaptiveAttempt(assessmentId: string, itemId: string, answer: string, timeTaken: number) {
  return request<{ correct: boolean; answer_guide: string; explanation: string; grading: { correct: boolean; score: number; method: 'ollama' | 'exact' | 'similarity'; feedback: string }; completed: boolean; index: number; adaptation?: string; adaptation_reason?: string; question?: AdaptiveQuestion; summary?: AssessmentSummary }>(`/assessments/${assessmentId}/attempt`, {
    method: 'POST', body: JSON.stringify({ item_id: itemId, answer, time_taken: timeTaken }),
  })
}
export function askTutor(input: { subject: string; class_level: number; concept_id: string; question: string; mode: 'hint' | 'explanation' | 'check_question'; topic_scores?: Record<string, TopicScore> }) {
  return request<{ id: string; message: string; check_question: string; citations: LearningCitation[]; provider: string }>('/ai/tutor', {
    method: 'POST', body: JSON.stringify(input),
  })
}
export function askAdaptiveTutor(input: { subject: string; class_level: number; concept_id: string; question: string; topic_scores: TopicScores }) {
  return askTutor({ ...input, mode: 'explanation' })
}
export function getTutorHistory(subject: string, classLevel: number, conceptId: string) {
  const params = new URLSearchParams({ subject, class_level: String(classLevel), concept_id: conceptId })
  return request<{ items: TutorMemory[] }>(`/ai/tutor-history?${params.toString()}`)
}
export function getAILearningRecommendations(subject: string, classLevel: number) {
  return request<{ recommendations: AILearningRecommendation[]; citations: LearningCitation[]; provider: string }>('/ai/learning-recommendations', {
    method: 'POST', body: JSON.stringify({ subject, class_level: classLevel }),
  })
}
export function generateWeakQuiz(input: { subject: string; class_level: number; concept_id: string; item_count?: number }) {
  return request<GeneratedWeakQuiz>('/ai/weak-area-quiz', {
    method: 'POST', body: JSON.stringify(input),
  })
}
export function getTeacherAnalytics(subject: string, classLevel: number) {
  return request<{ subject: string; class_level: number; attempts: number; concepts: AdaptiveConcept[]; learners: LearnerSummary[] }>(`/teacher/analytics?subject=${subject}&class_level=${classLevel}`)
}
export function getTeacherQuestionBank(status: 'pending' | 'approved' | 'all' = 'pending', subject?: string, classLevel?: number) {
  return request<{ items: (AdaptiveQuestion & { answer_guide: string; explanation: string; approved: boolean; citation_status: string; bloom_source: string; bloom_teacher_verified: boolean; difficulty_teacher_verified: boolean; source_reference_ids: string[]; supporting_chunk_ids: string[] })[] }>(`/teacher/question-bank?status=${status}${subject ? `&subject=${subject}` : ''}${classLevel ? `&class_level=${classLevel}` : ''}`)
}
export function reviewQuestion(itemId: string, approved: boolean) {
  return request<{ item: { item_id: string; approved: boolean } }>(`/teacher/question-bank/${encodeURIComponent(itemId)}/review?approved=${approved}`, { method: 'PATCH' })
}
export function importTeacherQuestion(input: { subject: string; class_level: number; chapter: string; concept_id: string; question: string; answer_guide: string; explanation: string; difficulty: string; bloom_level?: string }) {
  return request<{ item_id: string; bloom_level: string; approved: boolean; message: string }>('/teacher/question-bank/import', { method: 'POST', body: JSON.stringify(input) })
}
export function importTeacherQuestionBatch(questions: { subject: string; class_level: number; chapter: string; concept_id: string; question: string; answer_guide: string; explanation?: string; difficulty?: string; bloom_level?: string; source_reference_ids?: string[]; supporting_chunk_ids?: string[] }[]) {
  return request<{ items: { item_id: string; concept_id: string; bloom_level: string; bloom_teacher_verified: boolean }[]; message: string }>('/teacher/question-bank/import-batch', { method: 'POST', body: JSON.stringify({ questions }) })
}
export function getTeacherGeneratedContent() {
  return request<{ items: { id: string; subject: string; class_level: number; concept_id: string; payload: { question: string; answer_guide: string; explanation: string; bloom_level: string }[]; source_ids: string[]; sources: { source_id: string; citation: string; text: string; score: number }[] }[] }>('/teacher/generated-content')
}
export function reviewGeneratedContent(id: string, approved: boolean) {
  return request<{ content: { id: string; status: string } }>(`/teacher/generated-content/${encodeURIComponent(id)}/review?approved=${approved}`, { method: 'PATCH' })
}
