import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowRight, CalendarClock, Search, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { studentQuizzes } from '../../services/api'
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
  const [classroomQuizzes, setClassroomQuizzes] = useState<Array<Record<string, string | number>>>([])
  const navigate = useNavigate()
  useEffect(() => { if (session) studentQuizzes().then(setClassroomQuizzes).catch(() => setClassroomQuizzes([])) }, [session])

  const quizzes = useMemo(() => {
    const query = search.trim().toLocaleLowerCase()
    return (preview ? recentlyUploadedQuizzes() : [])
      .filter((quiz) => subject === 'all' || quiz.subject === subject)
      .filter((quiz) => !query || `${quiz.title} ${quiz.teacherName} ${subjectLabels[quiz.subject]} ${quiz.chapter}`.toLocaleLowerCase().includes(query))
      .sort((a, b) => sort === 'newest'
        ? Date.parse(b.uploadedAt) - Date.parse(a.uploadedAt)
        : Date.parse(a.uploadedAt) - Date.parse(b.uploadedAt))
  }, [preview, search, sort, subject])

  const visibleClassroomQuizzes = useMemo(() => {
    const query = search.trim().toLocaleLowerCase()
    return classroomQuizzes
      .filter((quiz) => !query || `${quiz.title ?? ''} ${quiz.classroom_name ?? ''} ${quiz.difficulty ?? ''}`.toLocaleLowerCase().includes(query))
      .sort((a, b) => sort === 'newest'
        ? Date.parse(String(b.created_at ?? '')) - Date.parse(String(a.created_at ?? ''))
        : Date.parse(String(a.created_at ?? '')) - Date.parse(String(b.created_at ?? '')))
  }, [classroomQuizzes, search, sort])

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
        <div className="problem-count-box"><CalendarClock size={17} /><b>{preview ? quizzes.length : classroomQuizzes.length}</b><span>{(preview ? quizzes.length : classroomQuizzes.length) === 1 ? 'quiz available' : 'quizzes available'}</span></div>
      </div>

      {preview && <div className="preview-banner">Read-only preview · Sign in and join a classroom to save quiz attempts.</div>}

      {!preview && <section className="recent-quizzes-panel classroom-quiz-panel" aria-label="Classroom quizzes"><div className="recent-quizzes-toolbar"><h2 className="section-kicker">PUBLISHED BY YOUR TEACHERS</h2><label className="recent-quiz-search"><Search size={17} /><Input aria-label="Search classroom quizzes" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search quiz or classroom" /></label><label className="recent-quiz-sort"><span>Sort</span><select aria-label="Sort quizzes" value={sort} onChange={(event) => setSort(event.target.value as QuizSort)}><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select></label></div>{visibleClassroomQuizzes.length ? <div className="recent-quiz-list">{visibleClassroomQuizzes.map((quiz) => <article className="recent-quiz-card" key={String(quiz.id)}><div className="recent-quiz-main"><div className="recent-quiz-title-row"><h2>{String(quiz.title)}</h2><span className="recent-quiz-mock-badge">CLASSROOM</span></div><p className="recent-quiz-teacher">{String(quiz.classroom_name)}</p><div className="recent-quiz-tags"><span className="topic-tag">{String(quiz.question_count)} questions</span><span className={`difficulty-label difficulty-${String(quiz.difficulty).toLowerCase()}`}><i />{String(quiz.difficulty)}</span></div></div><div className="recent-quiz-action"><span>{String(quiz.time_limit_minutes)} min</span><Button className="attempt-quiz-button" onClick={() => navigate(`/student/quizzes/${String(quiz.id)}`)}>Attempt Now <ArrowRight size={14} /></Button></div></article>)}</div> : <div className="problems-empty recent-quiz-empty"><span className="empty-filter-icon"><Sparkles size={20} /></span><h2>{search ? 'No classroom quizzes match this search.' : 'No classroom quizzes yet.'}</h2><p>{search ? 'Try a different quiz or classroom name.' : 'Quizzes published by your teachers will appear here and save your results to your account.'}</p></div>}<div className="recent-quizzes-footer"><span>Completed classroom quizzes are saved to AdaptEd and earn AdaptCoins.</span><span>{visibleClassroomQuizzes.length} shown</span></div></section>}

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
      {preview && <p className="data-note">Preview quizzes are sample content; signed-in classroom quizzes save results to your account.</p>}
    </main>
  </div>
}
