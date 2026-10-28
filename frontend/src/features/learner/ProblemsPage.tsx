import { useMemo, useState, type FormEvent, type ReactNode } from 'react'
import { Link, Navigate, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, BookOpen, Check, ChevronDown, Filter, LogOut, Search, SlidersHorizontal, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { loadState, recordProblemAttempt } from '../../services/storage'
import { subjectLabel } from '../../services/data'
import type { JeeSubjectId, Problem, ProblemAttempt } from '../../types'
import { SUBJECTS, STUDENT_PROBLEMS, TOPICS_BY_SUBJECT, type ListedProblem } from './services/problemCatalog'
import { filterChapterQuizzes, CHAPTER_QUIZZES } from './services/quizCatalog'
import { loadQuizAttempts } from './services/quizAttempts'
import type { QuizAttempt } from './services/quizCatalog'
import { ChapterQuizBrowser } from './ChapterQuizBrowser'
import './problems.css'
import './quizzes.css'

type ProblemStatus = 'Solved' | 'Attempted' | 'Unsolved'
type StatusFilter = 'All statuses' | ProblemStatus
type DifficultyFilter = 'All difficulties' | Problem['difficulty']
type SortMode = 'Title A–Z' | 'Difficulty: Easy first' | 'Status'

function topicKey(subject: JeeSubjectId, topic: string) { return `${subject}:${topic}` }

function getProblemStatus(problemId: string, attempts: ProblemAttempt[]): ProblemStatus {
  const related = attempts.filter((attempt) => attempt.problemId === problemId)
  if (!related.length) return 'Unsolved'
  return related.some((attempt) => attempt.correct) ? 'Solved' : 'Attempted'
}

export function StudentNav({ preview = false }: { preview?: boolean }) {
  const { session, signOut } = useAuth()
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const [profileOpen, setProfileOpen] = useState(false)
  if (!session && !preview) return null
  const previewSuffix = preview ? '?preview=1' : ''
  const onProblems = pathname.startsWith('/student/problems')
  const onQuizzes = pathname.startsWith('/student/quizzes')
  const onProfile = pathname.startsWith('/student/profile')
  const onLearning = pathname.startsWith('/student/learn')
  const initials = session ? session.user.name.split(/\s+/).map((part) => part[0]).join('').slice(0, 2).toUpperCase() : 'DE'
  return <header className="student-nav"><Link to={`/student/learn${previewSuffix}`} className="student-brand" aria-label="AdaptEd learning home"><img className="student-brand-mark" src="/adapted-icon.svg" alt="" /><span>Adapt<span>Ed</span></span></Link><nav className="student-links" aria-label="Student navigation"><Link className={`student-nav-link ${onLearning ? 'nav-current' : ''}`} to={`/student/learn${previewSuffix}`} aria-current={onLearning ? 'page' : undefined}>My learning</Link><Link className={`student-nav-link ${onProblems ? 'nav-current' : ''}`} to={`/student/problems${previewSuffix}`} aria-current={onProblems ? 'page' : undefined}>Problems</Link><Link className={`student-nav-link ${onQuizzes ? 'nav-current' : ''}`} to={`/student/quizzes${previewSuffix}`} aria-current={onQuizzes ? 'page' : undefined}>Quizzes</Link>{session?.user.role === 'teacher' && <Link className={`student-nav-link ${pathname.startsWith('/teacher') ? 'nav-current' : ''}`} to="/teacher">Teacher view</Link>}</nav><div className="student-profile-wrap">{session && <Link className={`student-avatar-link ${onProfile ? 'profile-open' : ''}`} to="/student/profile" aria-label="Open your student profile"><span className="student-avatar">{initials}</span></Link>}<button className={`student-profile-trigger ${profileOpen ? 'profile-open' : ''}`} aria-expanded={profileOpen} aria-haspopup="menu" onClick={() => setProfileOpen((open) => !open)}><span className="profile-name">Profile</span><ChevronDown size={15} /></button>{profileOpen && <div className="student-profile-menu" role="menu">{session ? <><div className="profile-menu-identity"><b>{session.user.name}</b><small>{session.user.email}</small></div><Link role="menuitem" to="/student/profile" onClick={() => setProfileOpen(false)}>View profile</Link><button role="menuitem" onClick={() => { signOut(); navigate('/', { replace: true }) }}><LogOut size={15} /> Sign out</button></> : <><div className="profile-menu-identity"><b>Preview mode</b><small>Browse sample problems without an account.</small></div><Link role="menuitem" to="/sign-in">Sign in</Link></>}</div>}</div></header>
}

function FilterChip({ children, onRemove }: { children: ReactNode; onRemove: () => void }) {
  return <button className="active-filter-chip" onClick={onRemove} aria-label={`Remove ${typeof children === 'string' ? children : 'search'} filter`}>{children}<X size={12} /></button>
}

function TopicPicker({ selected, onToggle, onClear }: { selected: Set<string>; onToggle: (key: string) => void; onClear: () => void }) {
  const [open, setOpen] = useState(false)
  const selectedCount = selected.size
  return <div className="topic-picker"><button type="button" className={`filter-control topic-trigger ${selectedCount ? 'filter-selected' : ''}`} aria-expanded={open} aria-haspopup="dialog" onClick={() => setOpen((value) => !value)}><Filter size={15} /> Topics {selectedCount > 0 && <span className="topic-count">{selectedCount}</span>}<ChevronDown size={14} /></button>{open && <div className="topic-popover" role="dialog" aria-label="Filter by topic"><div className="topic-popover-head"><div><b>Choose topics</b><small>Matches any selected topic</small></div><button type="button" className="icon-clear" onClick={() => { onClear(); setOpen(false) }} disabled={!selectedCount}>Clear</button></div><div className="topic-options-scroll">{SUBJECTS.map((subject) => <fieldset className="topic-subject-group" key={subject.id}><legend><span className={`subject-dot subject-${subject.id}`} />{subject.label}</legend>{TOPICS_BY_SUBJECT[subject.id].map((topic) => {
    const key = topicKey(subject.id, topic)
    const checked = selected.has(key)
    return <label className={`topic-option ${checked ? 'topic-option-selected' : ''}`} key={key}><input type="checkbox" checked={checked} onChange={() => onToggle(key)} /><span className="brutal-checkbox">{checked && <Check size={12} />}</span><span>{topic}</span></label>
  })}</fieldset>)}</div><button className="topic-done" onClick={() => setOpen(false)}>Done <Check size={14} /></button></div>}</div>
}

function ProblemRow({ entry, status, preview }: { entry: ListedProblem; status: ProblemStatus; preview: boolean }) {
  const problem = entry.problem
  const path = `/student/problems/${problem.id}${preview ? '?preview=1' : ''}`
  return <tr><td className="problem-title-cell"><div className="problem-name-line"><span className="problem-id">{problem.id}</span>{entry.isMock && <span className="demo-pill">DEMO</span>}</div><Link className="problem-title-link" to={path}>{problem.title}</Link></td><td><span className={`subject-label subject-text-${problem.subject}`}>{subjectLabel(problem.subject)}</span></td><td><span className="topic-tag">{entry.topic}</span></td><td><span className={`difficulty-label difficulty-${problem.difficulty.toLowerCase()}`}><i />{problem.difficulty}</span></td><td><span className={`status-label status-${status.toLowerCase()}`}><i />{status}</span></td><td><Link className="open-problem" to={path}>Open <ArrowRight size={14} /></Link></td></tr>
}

export function ProblemsPage() {
  const { session, status: authStatus } = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const preview = searchParams.get('preview') === '1'
  const activeView = searchParams.get('view') === 'quizzes' ? 'quizzes' : 'problems'
  const topicParam = searchParams.get('topic')
  const [search, setSearch] = useState('')
  const [selectedSubjects, setSelectedSubjects] = useState<Set<JeeSubjectId>>(new Set())
  const [selectedTopics, setSelectedTopics] = useState<Set<string>>(new Set())
  const [difficulty, setDifficulty] = useState<DifficultyFilter>('All difficulties')
  const [status, setStatus] = useState<StatusFilter>('All statuses')
  const [sort, setSort] = useState<SortMode>('Title A–Z')
  const [attempts, setAttempts] = useState<ProblemAttempt[]>(() => preview ? [] : loadState().problemAttempts)
  const [quizAttempts] = useState<QuizAttempt[]>(() => preview ? [] : loadQuizAttempts())

  const selectedTopicLabels = [...selectedTopics].map((key) => ({ key, label: key.split(':').slice(1).join(':') }))
  const toggleSubject = (subject: JeeSubjectId) => setSelectedSubjects((current) => {
    const next = new Set(current)
    if (next.has(subject)) next.delete(subject); else next.add(subject)
    return next
  })
  const toggleTopic = (key: string) => setSelectedTopics((current) => {
    const next = new Set(current)
    if (next.has(key)) next.delete(key); else next.add(key)
    return next
  })
  const clearAll = () => { setSearch(''); setSelectedSubjects(new Set()); setSelectedTopics(new Set()); setDifficulty('All difficulties'); setStatus('All statuses'); setSort('Title A–Z') }

  const filtered = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()
    const rows = STUDENT_PROBLEMS.filter(({ problem, topic }) => {
      if (topicParam && `${problem.subject}:${topic}` !== topicParam) return false
      if (selectedSubjects.size && !selectedSubjects.has(problem.subject as JeeSubjectId)) return false
      if (selectedTopics.size && !selectedTopics.has(topicKey(problem.subject as JeeSubjectId, topic))) return false
      if (difficulty !== 'All difficulties' && problem.difficulty !== difficulty) return false
      if (status !== 'All statuses' && getProblemStatus(problem.id, attempts) !== status) return false
      if (normalizedSearch && !`${problem.title} ${topic} ${problem.tags.join(' ')}`.toLowerCase().includes(normalizedSearch)) return false
      return true
    })
    const difficultyOrder: Record<Problem['difficulty'], number> = { Easy: 0, Medium: 1, Hard: 2 }
    const statusOrder: Record<ProblemStatus, number> = { Solved: 0, Attempted: 1, Unsolved: 2 }
    return rows.sort((a, b) => {
      if (sort === 'Difficulty: Easy first') return difficultyOrder[a.problem.difficulty] - difficultyOrder[b.problem.difficulty] || a.problem.title.localeCompare(b.problem.title)
      if (sort === 'Status') return statusOrder[getProblemStatus(a.problem.id, attempts)] - statusOrder[getProblemStatus(b.problem.id, attempts)] || a.problem.title.localeCompare(b.problem.title)
      return a.problem.title.localeCompare(b.problem.title)
    })
  }, [attempts, difficulty, search, selectedSubjects, selectedTopics, sort, status, topicParam])
  const filteredQuizzes = useMemo(() => filterChapterQuizzes(CHAPTER_QUIZZES, { selectedSubjects, selectedTopics, difficulty, status, search, attempts: quizAttempts, sort }), [difficulty, quizAttempts, search, selectedSubjects, selectedTopics, sort, status])

  if (authStatus === 'loading' && !preview) return <div className="phase-loading">Loading your workspace…</div>
  if (!session && !preview) return <Navigate to="/sign-in" replace />
  if (session && !preview && (!session.user.onboardingComplete || session.user.role !== 'student')) return <Navigate to="/classroom" replace />

  const activeFilterCount = selectedSubjects.size + selectedTopics.size + (difficulty !== 'All difficulties' ? 1 : 0) + (status !== 'All statuses' ? 1 : 0)
  const switchView = (view: 'problems' | 'quizzes') => {
    const params = new URLSearchParams(searchParams)
    if (view === 'problems') params.delete('view')
    else params.set('view', view)
    setSearchParams(params)
  }
  return <div className="problems-app"><StudentNav preview={preview} /><main className="problems-main"><div className="problems-heading"><div><span className="problems-kicker">{preview ? 'PUBLIC PREVIEW / PROBLEMS' : 'STUDENT WORKSPACE / PROBLEMS'}</span><h1>Problems</h1><p>Choose a topic, find a challenge, and keep your practice moving.</p></div><div className="problem-count-box"><BookOpen size={17} /><b>{activeView === 'problems' ? filtered.length : filteredQuizzes.length}</b><span>{activeView === 'problems' ? `of ${STUDENT_PROBLEMS.length} demo problems` : 'matching quizzes'}</span></div></div>{preview && <div className="preview-banner">Read-only preview · Sign in and join a classroom to save attempts.</div>}<section className="topic-explorer" aria-label="JEE topics"><div className="topic-explorer-head"><span className="problems-kicker">TOPIC-WISE PROBLEMS</span>{topicParam && <button className="clear-all-button" onClick={() => { const params = new URLSearchParams(searchParams); params.delete('topic'); setSearchParams(params) }}>Show all topics</button>}</div><div className="topic-card-grid">{SUBJECTS.map((subject) => <div className="topic-subject-card" key={subject.id}><div className="topic-subject-title"><span className={`subject-dot subject-${subject.id}`} /><b>{subject.label}</b><small>{TOPICS_BY_SUBJECT[subject.id].length} topics</small></div><div className="topic-card-list">{TOPICS_BY_SUBJECT[subject.id].map((topic) => { const key = `${subject.id}:${topic}`; const count = STUDENT_PROBLEMS.filter((item) => item.problem.subject === subject.id && item.topic === topic).length; return <button key={topic} className={`topic-card-link ${topicParam === key ? 'topic-card-active' : ''}`} onClick={() => navigate(`/student/topics/${subject.id}/${topic.toLowerCase().replace(/[^a-z0-9'-]+/g, '-')}`)}><span>{topic}</span><small>{count} questions</small><ArrowRight size={13} /></button> })}</div></div>)}</div></section><div className="problem-view-tabs" role="tablist" aria-label="Browse problems or chapter quizzes"><button role="tab" aria-selected={activeView === 'problems'} className={activeView === 'problems' ? 'view-tab-active' : ''} onClick={() => switchView('problems')}>Problems</button><button role="tab" aria-selected={activeView === 'quizzes'} className={activeView === 'quizzes' ? 'view-tab-active' : ''} onClick={() => switchView('quizzes')}>Chapter quizzes</button></div><section className="problems-panel" aria-label="Problem browser"><div className="problem-toolbar"><label className="problem-search"><Search size={17} /><Input aria-label={activeView === 'problems' ? 'Search problems' : 'Search problems and chapters'} value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by problem or topic" /><kbd>/</kbd></label><div className="problem-filter-controls"><div className="subject-filter-group" aria-label="Filter by subject">{SUBJECTS.map((subject) => <button type="button" key={subject.id} className={`subject-filter ${selectedSubjects.has(subject.id) ? `selected subject-selected-${subject.id}` : ''}`} aria-pressed={selectedSubjects.has(subject.id)} onClick={() => toggleSubject(subject.id)}><span className={`subject-dot subject-${subject.id}`} />{subject.label}</button>)}</div><TopicPicker selected={selectedTopics} onToggle={toggleTopic} onClear={() => setSelectedTopics(new Set())} /><label className="select-filter"><span className="sr-only">Filter by difficulty</span><select value={difficulty} onChange={(event) => setDifficulty(event.target.value as DifficultyFilter)}><option>All difficulties</option><option>Easy</option><option>Medium</option><option>Hard</option></select><ChevronDown size={13} /></label><label className="select-filter"><span className="sr-only">Filter by status</span><select value={status} onChange={(event) => setStatus(event.target.value as StatusFilter)}><option>All statuses</option><option>Solved</option><option>Attempted</option><option>Unsolved</option></select><ChevronDown size={13} /></label><label className="select-filter select-sort"><span className="sr-only">Sort problems</span><SlidersHorizontal size={14} /><select value={sort} onChange={(event) => setSort(event.target.value as SortMode)}><option>Title A–Z</option><option>Difficulty: Easy first</option><option>Status</option></select><ChevronDown size={13} /></label></div></div>{(activeFilterCount > 0 || search) && <div className="active-filters"><span className="active-filter-label">FILTERS</span>{[...selectedSubjects].map((id) => <FilterChip key={`subject-${id}`} onRemove={() => toggleSubject(id)}>{SUBJECTS.find((subject) => subject.id === id)?.label ?? id}</FilterChip>)}{selectedTopicLabels.map(({ key, label }) => <FilterChip key={key} onRemove={() => toggleTopic(key)}>{label}</FilterChip>)}{difficulty !== 'All difficulties' && <FilterChip onRemove={() => setDifficulty('All difficulties')}>{difficulty}</FilterChip>}{status !== 'All statuses' && <FilterChip onRemove={() => setStatus('All statuses')}>{status}</FilterChip>}{search && <FilterChip onRemove={() => setSearch('')}>Search: {search}</FilterChip>}<button className="clear-all-button" onClick={clearAll}>Clear all</button></div>}{activeView === 'problems' ? <><div className="table-scroll"><table className="problems-table"><thead><tr><th scope="col">Problem</th><th scope="col">Subject</th><th scope="col">Topic</th><th scope="col">Difficulty</th><th scope="col">Status</th><th scope="col"><span className="sr-only">Open problem</span></th></tr></thead><tbody>{filtered.map((entry) => <ProblemRow key={entry.problem.id} entry={entry} status={getProblemStatus(entry.problem.id, attempts)} preview={preview} />)}</tbody></table>{filtered.length === 0 && <div className="problems-empty"><span className="empty-filter-icon"><Search size={20} /></span><h2>No problems match those filters.</h2><p>Try clearing a topic or changing the difficulty and status.</p><Button variant="neutral" onClick={clearAll}>Clear filters</Button></div>}</div><div className="problems-panel-footer"><span>{preview ? 'Read-only demo question bank' : 'Demo question bank · progress is saved in this browser'}</span><span>{filtered.length} {filtered.length === 1 ? 'problem' : 'problems'} shown</span></div></> : <ChapterQuizBrowser selectedSubjects={selectedSubjects} selectedTopics={selectedTopics} difficulty={difficulty} status={status} search={search} attempts={quizAttempts} sort={sort} />}</section><p className="data-note">Questions and quiz listings are local demo content. More teacher-reviewed material will appear as the question bank grows.</p></main></div>
}

function normalizeAnswer(value: string) { return value.trim().toLowerCase().replace(/\s+/g, '').replace(/[−–]/g, '-') }

export function StudentProblemDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { session } = useAuth()
  const [searchParams] = useSearchParams()
  const preview = searchParams.get('preview') === '1'
  const problemEntry = STUDENT_PROBLEMS.find(({ problem }) => problem.id === id)
  const [answer, setAnswer] = useState('')
  const [outcome, setOutcome] = useState<boolean | null>(null)
  const [attempts, setAttempts] = useState<ProblemAttempt[]>(() => preview ? [] : loadState().problemAttempts)
  if (!session && !preview) return <Navigate to="/sign-in" replace />
  if (session && !preview && (!session.user.onboardingComplete || session.user.role !== 'student')) return <Navigate to="/classroom" replace />
  if (!problemEntry) return <Navigate to="/student/problems" replace />
  const problem = problemEntry.problem
  const status = getProblemStatus(problem.id, attempts)
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!answer.trim()) return
    const correct = normalizeAnswer(answer) === normalizeAnswer(problem.answer)
    if (!session || preview) return
    const next = recordProblemAttempt(loadState(), { problemId: problem.id, studentId: session.user.id, answer, correct, timeTaken: 0, hintUsed: false, createdAt: new Date().toISOString() })
    setAttempts(next.problemAttempts)
    setOutcome(correct)
  }
  return <div className="problems-app"><StudentNav preview={preview} /><main className="problem-detail-main"><Link className="back-to-problems" to={`/student/problems${preview ? '?preview=1' : ''}`}><ArrowLeft size={15} /> Back to Problems</Link><article className="problem-detail-card"><div className="detail-meta"><span>{problem.id}</span><span>{subjectLabel(problem.subject)}</span><span>{problemEntry.topic}</span><span className={`difficulty-label difficulty-${problem.difficulty.toLowerCase()}`}><i />{problem.difficulty}</span><span className={`status-label status-${status.toLowerCase()}`}><i />{status}</span>{problemEntry.isMock && <span className="demo-pill">DEMO</span>}</div><h1>{problem.title}</h1><p className="detail-subtitle">{problem.className} · {problem.estimatedMinutes} min</p><div className="question-statement"><span className="problems-kicker">QUESTION</span><p>{problem.statement}</p></div>{preview ? <div className="preview-banner">Read-only preview · Sign in and join a classroom to submit answers.</div> : <><form className="answer-form" onSubmit={submit}><label className="answer-label" htmlFor="problem-answer">Your answer</label>{problem.choices ? <div className="problem-choice-list">{problem.choices.map((choice) => <label className={`problem-choice ${answer === choice ? 'choice-picked' : ''}`} key={choice}><input type="radio" name="problem-answer" value={choice} checked={answer === choice} onChange={() => { setAnswer(choice); setOutcome(null) }} /><span className="choice-radio" />{choice}</label>)}</div> : <Input id="problem-answer" value={answer} onChange={(event) => { setAnswer(event.target.value); setOutcome(null) }} placeholder="Type your answer" autoComplete="off" />}{outcome !== null && <div className={`answer-feedback ${outcome ? 'answer-correct' : 'answer-incorrect'}`} role="status"><b>{outcome ? 'Correct — nice work.' : 'Not quite yet.'}</b><p>{problem.explanation}</p>{!outcome && <p>Review the explanation, then try again.</p>}</div>}<Button className="check-answer-button" type="submit" disabled={!answer.trim()}>{outcome === true ? 'Try again' : 'Check answer'} <Check size={16} /></Button></form>{outcome === false && <div className="answer-reveal">Answer: <b>{problem.answer}</b></div>}</>}</article><aside className="detail-side-note"><BookOpen size={17} /><p>{preview ? 'This is a read-only view of demo practice content.' : 'This is demo practice content. Your attempt updates the status on the Problems list in this browser.'}</p></aside></main></div>
}
