import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, ChevronDown, ClipboardList } from 'lucide-react'
import type { JeeSubjectId } from '../../types'
import { CHAPTERS_BY_SUBJECT, CHAPTER_QUIZZES, filterChapterQuizzes, type QuizAttempt } from './services/quizCatalog'
import { SUBJECTS } from './services/problemCatalog'

type Props = {
  selectedSubjects: Set<JeeSubjectId>
  selectedTopics: Set<string>
  difficulty: string
  status: string
  search: string
  attempts: QuizAttempt[]
  sort: string
}

function attemptLabel(quiz: (typeof CHAPTER_QUIZZES)[number], attempts: QuizAttempt[]) {
  const attempt = attempts.find((item) => item.quizId === quiz.id)
  if (attempt?.status === 'completed') return 'Completed'
  if (attempt?.status === 'in_progress') return 'In Progress'
  return 'Not Attempted'
}

export function ChapterQuizBrowser({ selectedSubjects, selectedTopics, difficulty, status, search, attempts, sort }: Props) {
  const navigate = useNavigate()
  const allFiltered = useMemo(() => filterChapterQuizzes(CHAPTER_QUIZZES, { selectedSubjects, selectedTopics, difficulty, status, search, attempts, sort }), [attempts, difficulty, search, selectedSubjects, selectedTopics, sort, status])
  const visibleSubjects = SUBJECTS.filter(({ id }) => !selectedSubjects.size || selectedSubjects.has(id))
  const quizzesForChapter = (subject: JeeSubjectId, chapter: string) => allFiltered.filter((quiz) => quiz.subject === subject && quiz.chapter === chapter)

  return <section className="chapter-browser" aria-label="Chapter quiz browser"><div className="chapter-browser-heading"><div><span className="problems-kicker">BROWSE BY SUBJECT AND CHAPTER</span><h2>Chapter quizzes</h2><p>Open a subject, expand a chapter, then choose a quiz.</p></div><div className="chapter-quiz-count"><ClipboardList size={16} /><b>{allFiltered.length}</b><span>quizzes match</span></div></div>{allFiltered.length === 0 ? <div className="problems-empty chapter-empty"><span className="empty-filter-icon"><ClipboardList size={20} /></span><h2>No chapter quizzes match these filters.</h2><p>Try another topic, difficulty, status, or search term.</p></div> : <div className="subject-accordion-list">{visibleSubjects.map((subject) => {
    const subjectQuizzes = allFiltered.filter((quiz) => quiz.subject === subject.id)
    if (!subjectQuizzes.length) return null
    return <details className={`subject-accordion subject-accordion-${subject.id}`} key={subject.id}><summary><span className={`subject-dot subject-${subject.id}`} /><b>{subject.label}</b><span className="subject-quiz-total">{subjectQuizzes.length} quizzes</span><ChevronDown size={16} className="accordion-chevron" /></summary><div className="chapter-accordion-list">{CHAPTERS_BY_SUBJECT[subject.id].map((chapter) => {
      const quizzes = quizzesForChapter(subject.id, chapter)
      if (!quizzes.length) return null
      return <details className="chapter-accordion" key={chapter}><summary><span className="chapter-title">{chapter}</span><span className="chapter-quiz-total">{quizzes.length} {quizzes.length === 1 ? 'quiz' : 'quizzes'}</span><ChevronDown size={14} className="accordion-chevron" /></summary><div className="chapter-quiz-table-wrap"><table className="chapter-quiz-table"><thead><tr><th>Quiz</th><th>Questions</th><th>Max marks</th><th>Time</th><th>Difficulty</th><th>Status</th><th><span className="sr-only">Action</span></th></tr></thead><tbody>{quizzes.map((quiz) => {
        const quizStatus = attemptLabel(quiz, attempts)
        return <tr key={quiz.id}><td><span className="chapter-quiz-name">{quiz.name}</span><span className="quiz-data-badge">{quiz.source === 'mock' ? 'MOCK' : 'DEMO BANK'}</span></td><td>{quiz.questionCount}</td><td>{quiz.maxMarks}</td><td>{quiz.timeLimitMinutes} min</td><td><span className={`difficulty-label difficulty-${quiz.difficulty.toLowerCase()}`}><i />{quiz.difficulty}</span></td><td><span className={`quiz-status quiz-status-${quizStatus.toLowerCase().replace(' ', '-')}`}>{quizStatus}</span></td><td><button className="attempt-quiz-button" onClick={() => navigate(`/student/quizzes/${quiz.id}`)}>{quizStatus === 'In Progress' ? 'Resume' : quizStatus === 'Completed' ? 'Retake' : 'Attempt Now'} <ArrowRight size={13} /></button></td></tr>
      })}</tbody></table></div></details>
    })}</div></details>
  })}</div>}<div className="chapter-browser-footer">Quiz prompts marked <b>MOCK</b> are sample UI content; DEMO BANK questions come from AdaptEd’s existing local question bank. No quiz API is connected.</div></section>
}
