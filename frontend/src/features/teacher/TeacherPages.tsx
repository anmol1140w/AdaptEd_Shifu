import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { ArrowRight, BarChart3, BookOpen, LogOut, Plus, Upload, Users } from 'lucide-react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { createTeacherQuiz, teacherClassrooms, teacherStudents } from '../../services/api'
import './teacher.css'

export function TeacherFrame({ children }: { children: ReactNode }) {
  const { session, signOut } = useAuth()
  const navigate = useNavigate()
  if (!session || session.user.role !== 'teacher') return <Navigate to="/teacher-login" replace />
  return <div className="teacher-shell"><header className="teacher-nav"><Link to="/" className="teacher-brand"><span className="teacher-brand-mark">A</span><span>AdaptEd</span></Link><span className="teacher-nav-label">TEACHER WORKSPACE</span><Link className="teacher-learning-link" to="/teacher/learning">Adaptive PCM insights</Link><Link className="teacher-learning-link" to="/leaderboard">Class leaderboard</Link><div className="teacher-user">{session.user.name}<button onClick={() => { signOut(); navigate('/') }}><LogOut size={14} /> Sign out</button></div></header>{children}</div>
}

export function TeacherLoginPage() {
  const { teacherLogin, teacherRegister } = useAuth()
  const navigate = useNavigate()
  const [registering, setRegistering] = useState(false)
  const [form, setForm] = useState({ name: '', uniqueId: '', password: '', teacherInviteCode: '' })
  const [error, setError] = useState('')
  const submit = async (event: FormEvent) => { event.preventDefault(); setError(''); const result = registering ? await teacherRegister(form) : await teacherLogin({ uniqueId: form.uniqueId, password: form.password }); if (!result.ok) { setError(result.message); return }; navigate('/teacher', { replace: true }) }
  return <div className="teacher-auth"><div className="teacher-auth-card"><Link to="/" className="teacher-brand"><img className="teacher-brand-mark" src="/adapted-icon.svg" alt="" /><span>AdaptEd</span></Link><span className="teacher-kicker">TEACHER ACCESS</span><h1>{registering ? 'Create teacher account.' : 'Welcome, teacher.'}</h1><p>{registering ? 'Create your unique teacher ID to manage classrooms.' : 'Use your unique ID and password to continue.'}</p><form onSubmit={submit}>{registering && <label>Name<Input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Your name" /></label>}<label>Unique teacher ID<Input required value={form.uniqueId} onChange={(event) => setForm({ ...form, uniqueId: event.target.value })} placeholder="e.g. physics_mentor" /></label>{registering && <label>Teacher invite code<Input required minLength={8} type="password" value={form.teacherInviteCode} onChange={(event) => setForm({ ...form, teacherInviteCode: event.target.value })} placeholder="Provided by your project admin" /></label>}<label>Password<Input required minLength={8} type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} placeholder="At least 8 characters" /></label>{error && <p className="teacher-error">{error}</p>}<Button type="submit" className="teacher-submit">{registering ? 'Create teacher account' : 'Teacher login'} <ArrowRight size={16} /></Button></form><button className="teacher-switch" onClick={() => { setRegistering(!registering); setError('') }}>{registering ? 'Already a teacher? Log in' : 'Not registered? Create teacher ID'}</button></div></div>
}

export function TeacherDashboardPage() {
  const [classrooms, setClassrooms] = useState<Array<Record<string, string | number>>>([])
  const [selected, setSelected] = useState<Record<string, string | number> | null>(null)
  const [view, setView] = useState<'students' | 'quiz'>('students')
  useEffect(() => { teacherClassrooms().then((rows) => { setClassrooms(rows); setSelected(rows[0] ?? null) }).catch(() => setClassrooms([])) }, [])
  const openAnalytics = () => { if (selected) window.open(`/teacher/classrooms/${encodeURIComponent(String(selected.public_slug))}/analytics`, '_blank', 'noopener,noreferrer') }
  return <TeacherFrame><main className="teacher-main"><div className="teacher-heading"><div><span className="teacher-kicker">TEACHER DASHBOARD</span><h1>Your classrooms.</h1><p>Create classrooms, publish quizzes, and follow student progress.</p></div><Button className="teacher-primary" onClick={() => window.location.assign('/classroom/create')}><Plus size={16} /> Create classroom</Button></div><div className="teacher-layout"><aside className="teacher-classrooms"><h2>CLASSROOMS</h2>{classrooms.map((classroom) => <button className={selected?.public_slug === classroom.public_slug ? 'teacher-class-active' : ''} key={String(classroom.id)} onClick={() => setSelected(classroom)}><b>{String(classroom.name)}</b><small>{classroom.student_count} students · {classroom.quiz_count} quizzes</small></button>)}{!classrooms.length && <p className="teacher-muted">No classrooms yet.</p>}</aside>{selected ? <section className="teacher-workspace"><div className="teacher-class-title"><div><span className="teacher-kicker">CLASSROOM</span><h2>{String(selected.name)}</h2></div><span className="teacher-code">{String(selected.public_slug)}</span></div><nav className="teacher-tabs"><button className={view === 'students' ? 'active' : ''} onClick={() => setView('students')}><Users size={15} /> Students</button><button className={view === 'quiz' ? 'active' : ''} onClick={() => setView('quiz')}><BookOpen size={15} /> Upload quiz</button><button onClick={openAnalytics}><BarChart3 size={15} /> Analytics ↗</button></nav>{view === 'students' && <TeacherStudents slug={String(selected.public_slug)} />}{view === 'quiz' && <QuizComposer slug={String(selected.public_slug)} />}</section> : <div className="teacher-placeholder"><h3>Create your first classroom</h3><p>Classroom management starts here.</p></div>}</div></main></TeacherFrame>
}

function TeacherStudents({ slug }: { slug: string }) {
  const [students, setStudents] = useState<Array<Record<string, string | number>>>([])
  useEffect(() => { teacherStudents(slug).then(setStudents).catch(() => setStudents([])) }, [slug])
  return <div className="teacher-panel"><h3>Registered students</h3>{students.length ? students.map((student) => <a className="teacher-student-row" key={String(student.id)} href={`/teacher/classrooms/${encodeURIComponent(slug)}/students/${encodeURIComponent(String(student.id))}`} target="_blank" rel="noreferrer"><span className="teacher-avatar">{String(student.name).slice(0, 2).toUpperCase()}</span><span><b>{String(student.name)}</b><small>{String(student.email)}</small></span><strong>{String(student.attempts)} attempts · {String(student.solved)} solved ↗</strong></a>) : <p className="teacher-muted">No students have joined this classroom yet.</p>}</div>
}

function QuizComposer({ slug }: { slug: string }) {
  const [title, setTitle] = useState('')
  const [difficulty, setDifficulty] = useState('Medium')
  const [prompt, setPrompt] = useState('')
  const [choices, setChoices] = useState(['', '', '', ''])
  const [answer, setAnswer] = useState('')
  const [message, setMessage] = useState('')
  const submit = async (event: FormEvent) => { event.preventDefault(); try { await createTeacherQuiz({ classroom_slug: slug, title, description: 'Teacher-created classroom quiz', difficulty, time_limit_minutes: 30, questions: [{ prompt, question_type: 'MCQ', choices, answer, explanation: '', hints: [] }] }); setMessage('Quiz published. Students can now see it in Quizzes.'); setTitle(''); setPrompt(''); setChoices(['', '', '', '']); setAnswer('') } catch (error) { setMessage(error instanceof Error ? error.message : 'Could not publish quiz') } }
  return <div className="teacher-panel"><h3>Upload quiz manually</h3><Link className="teacher-quiz-bank-link" to="/teacher/learning"><span className="teacher-quiz-bank-icon"><Upload size={18} /></span><span><b>Upload CSV / Excel question bank</b><small>Review questions and Bloom level suggestions before adding them to the student practice bank.</small></span><ArrowRight className="teacher-quiz-bank-arrow" size={18} /></Link><form className="teacher-quiz-form" onSubmit={submit}><label>Quiz title<Input required value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Electrostatics checkpoint" /></label><label>Difficulty<select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}><option>Easy</option><option>Medium</option><option>Hard</option></select></label><label>Question<Input required value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Write the question" /></label>{choices.map((choice, index) => <label key={index}>Option {index + 1}<Input required value={choice} onChange={(event) => setChoices(choices.map((item, itemIndex) => itemIndex === index ? event.target.value : item))} /></label>)}<label>Correct answer<Input required value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="Must match one option" /></label>{message && <p className="teacher-success">{message}</p>}<Button className="teacher-submit" type="submit">Publish quiz <ArrowRight size={16} /></Button></form></div>
}
