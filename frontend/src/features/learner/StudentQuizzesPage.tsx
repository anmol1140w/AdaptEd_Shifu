import { useMemo, useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowRight, CalendarClock, Search, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import type { JeeSubjectId } from '../../types'
import { SUBJECTS } from './services/problemCatalog'
import { recentlyUploadedQuizzes } from './services/teacherQuizCatalog'
import { StudentNav } from './ProblemsPage'
import './problems.css'
import './quizzes.css'

type QuizSubjectFilter = 'all' | JeeSubjectId
type QuizSort = 'newest' | 'oldest'

const subjectLabels: Record<JeeSubjectId, string> = {
  physics: 'Physics',
  chemistry: 'Chemistry',
  mathematics: 'Mathematics',
}

function uploadDateLabel(timestamp: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(timestamp))
}

export function StudentQuizzesPage() {
  const { session, status: authStatus } = useAuth()
  const [searchParams] = useSearchParams()
  const preview = searchParams.get('preview') === '1'
  const [subject, setSubject] = useState<QuizSubjectFilter>('all')
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<QuizSort>('newest')
  const navigate = useNavigate()

  const quizzes = useMemo(() => {
    const query = search.trim().toLocaleLowerCase()
    return recentlyUploadedQuizzes()
      .filter((quiz) => subject === 'all' || quiz.subject === subject)
      .filter((quiz) => !query || `${quiz.title} ${quiz.teacherName} ${subjectLabels[quiz.subject]} ${quiz.chapter}`.toLocaleLowerCase().includes(query))
      .sort((a, b) => sort === 'newest'
        ? Date.parse(b.uploadedAt) - Date.parse(a.uploadedAt)
        : Date.parse(a.uploadedAt) - Date.parse(b.uploadedAt))
  }, [search, sort, subject])

  if (authStatus === 'loading' && !preview) return <div className="phase-loading">Loading your workspace…</div>
  if (!session && !preview) return <Navigate to="/sign-in" replace />
  if (session && !preview && (!session.user.onboardingComplete || session.user.role !== 'student')) return <Navigate to="/classroom" replace />

  const clearFilters = () => { setSubject('all'); setSearch(''); setSort('newest') }

  return <div className="problems-app">
    <StudentNav preview={preview} />
    <main className="problems-main">
      <div className="problems-heading">
        <div>
          <span className="problems-kicker">{preview ? 'PUBLIC PREVIEW / QUIZZES' : 'STUDENT WORKSPACE / QUIZZES'}</span>
          <h1>Quizzes</h1>
          <p>Recently shared practice from your classroom.</p>
        </div>
        <div className="problem-count-box"><CalendarClock size={17} /><b>{quizzes.length}</b><span>{quizzes.length === 1 ? 'quiz available' : 'quizzes available'}</span></div>
      </div>

      {preview && <div className="preview-banner">Read-only preview · Sign in and join a classroom to save quiz attempts.</div>}

      <section className="recent-quizzes-panel" aria-label="Recently uploaded quizzes">
        <div className="recent-quizzes-toolbar">
          <label className="recent-quiz-search"><Search size={17} /><Input aria-label="Search quizzes" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search title, teacher, subject or chapter" /></label>
          <div className="recent-quiz-controls">
            <div className="recent-subject-filters" aria-label="Filter quizzes by subject">
              <button type="button" className={subject === 'all' ? 'recent-subject-active' : ''} aria-pressed={subject === 'all'} onClick={() => setSubject('all')}>All subjects</button>
              {SUBJECTS.map((item) => <button type="button" key={item.id} className={subject === item.id ? 'recent-subject-active' : ''} aria-pressed={subject === item.id} onClick={() => setSubject(item.id)}>{item.label}</button>)}
            </div>
            <label className="recent-quiz-sort"><span>Sort</span><select aria-label="Sort quizzes" value={sort} onChange={(event) => setSort(event.target.value as QuizSort)}><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select></label>
          </div>
        </div>

        {quizzes.length ? <div className="recent-quiz-list">{quizzes.map((quiz) => <article className="recent-quiz-card" key={quiz.id}>
          <div className="recent-quiz-main">
            <div className="recent-quiz-title-row"><h2>{quiz.title}</h2><span className="recent-quiz-mock-badge">MOCK UPLOAD</span></div>
            <p className="recent-quiz-teacher">Uploaded by <b>{quiz.teacherName}</b></p>
            <div className="recent-quiz-tags"><span className={`subject-label subject-text-${quiz.subject}`}>{subjectLabels[quiz.subject]}</span><span className="topic-tag">{quiz.chapter}</span>{quiz.difficulty && <span className={`difficulty-label difficulty-${quiz.difficulty.toLowerCase()}`}><i />{quiz.difficulty}</span>}</div>
          </div>
          <dl className="recent-quiz-meta">
            <div><dt>QUESTIONS</dt><dd>{quiz.questionCount}</dd></div>
            <div><dt>MAX MARKS</dt><dd>{quiz.maxMarks}</dd></div>
            <div><dt>TIME</dt><dd>{quiz.timeLimitMinutes} min</dd></div>
          </dl>
          <div className="recent-quiz-action"><time dateTime={quiz.uploadedAt}>{uploadDateLabel(quiz.uploadedAt)}</time><Button className="attempt-quiz-button" onClick={() => navigate(`/student/quizzes/${quiz.quizId}${preview ? '?preview=1' : ''}`)}>Attempt Now <ArrowRight size={14} /></Button></div>
        </article>)}</div> : <div className="problems-empty recent-quiz-empty"><span className="empty-filter-icon"><Sparkles size={20} /></span><h2>{recentlyUploadedQuizzes().length === 0 ? 'No quizzes have been shared yet.' : 'No quizzes match these filters.'}</h2><p>{recentlyUploadedQuizzes().length === 0 ? 'Teacher-uploaded quizzes will appear here when they become available.' : 'Try another subject or search term.'}</p>{(search || subject !== 'all' || sort !== 'newest') && <Button variant="neutral" onClick={clearFilters}>Clear filters</Button>}</div>}

        <div className="recent-quizzes-footer"><span>Teacher quiz uploads are not connected yet. Sample rows are labeled MOCK UPLOAD.</span><span>Sorted by upload time</span></div>
      </section>
      <p className="data-note">Quiz attempt results are stored in this browser only until an assessment API is available.</p>
    </main>
  </div>
}
