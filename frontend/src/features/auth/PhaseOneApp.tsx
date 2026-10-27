import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { ArrowDownRight, ArrowLeft, ArrowRight, Atom, BookOpen, Check, ChevronRight, GraduationCap, LogOut, Mail, Orbit, Plus, School, Sparkles, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { PrivacyPage, TermsPage } from '../../app/LegalPages'
import { StudentProblemDetailPage } from '../learner/ProblemsPage'
import { QuizAttemptPage } from '../learner/QuizAttemptPage'
import { StudentQuizzesPage } from '../learner/StudentQuizzesPage'
import { JeeProblemPage, TopicProblemsPage } from '../learner/JeeContentPages'
import { TopicWiseProblemsPage } from '../learner/TopicWiseProblemsPage'
import { TeacherQuizAttemptPage, TopicQuizAttemptPage, TopicQuizzesPage } from '../learner/TopicQuizzesPage'
import { TeacherDashboardPage, TeacherLoginPage } from '../teacher/TeacherPages'
import { ACADEMIC_YEARS, CLASS_LEVELS, EXAM_TARGETS, JEE_SUBJECTS, subjectLabel } from '../onboarding/services/classroomService'
import type { AuthSession, ClassLevel, Classroom, CreateClassroomInput, ExamTarget, JeeSubjectId, StudentClassLevel, StudentImprovementSubject, StudentJeeGoal, StudentLearningStyle, StudentOnboardingProfile, StudentStrengthSubject } from '../../types'

function postAuthRoute(session: AuthSession) {
  const studentOnboardingComplete = session.user.studentOnboardingComplete
    ?? (session.user.role === 'student' && session.user.onboardingComplete)
  if (session.user.role === 'student' && !studentOnboardingComplete) return '/student-onboarding'
  return '/classroom'
}

function Brand({ compact = false }: { compact?: boolean }) {
  return <Link to="/" className={`brand-mark-lockup ${compact ? 'brand-compact' : ''}`} aria-label="AdaptEd home"><span className="brand-symbol">A</span><span>Adapt<span className="brand-dot">Ed</span></span></Link>
}

function Notice({ children, tone = 'error' }: { children: ReactNode; tone?: 'error' | 'success' | 'info' }) {
  return <div className={`phase-notice notice-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>{children}</div>
}

function Frame({ children, side }: { children: ReactNode; side?: ReactNode }) {
  return <main className="phase-shell"><header className="phase-nav"><Brand /><span className="phase-nav-note"><span className="live-dot" /> LEARN WITH INTENT</span><span className="phase-nav-right">A clearer way to keep moving forward</span></header><div className={`phase-main ${side ? 'phase-main-split' : ''}`}><section className="phase-form-area">{children}</section>{side && <aside className="phase-art-area">{side}</aside>}</div><footer className="phase-footer"><span>AdaptEd © 2026</span><nav className="phase-footer-links" aria-label="Policies and project links"><Link to="/terms">Terms &amp; Conditions</Link><Link to="/privacy">Privacy Policy</Link><a href="https://github.com/sharadvyas123/AdaptEd_Shifu" target="_blank" rel="noreferrer"><span className="github-mark" aria-hidden="true">GH</span> GitHub</a></nav><span>Built for focused learning <Sparkles size={13} /></span></footer></main>
}

function BrandPanel({ eyebrow, title, copy, visual = 'orbit' }: { eyebrow: string; title: ReactNode; copy: string; visual?: 'orbit' | 'classroom' }) {
  return <div className={`brand-panel panel-${visual}`}><div className="panel-sticker">{visual === 'orbit' ? <Orbit size={19} /> : <School size={19} />}<span>{visual === 'orbit' ? 'YOUR NEXT CHAPTER' : 'BETTER TOGETHER'}</span></div><div className="panel-copy"><p className="panel-eyebrow">{eyebrow}</p><h2>{title}</h2><p>{copy}</p></div><div className="panel-graphic" aria-hidden="true">{visual === 'orbit' ? <><div className="orbit-ring ring-one" /><div className="orbit-ring ring-two" /><div className="orbit-core"><Atom size={42} /></div><span className="orbit-tag tag-phy">FOCUS</span><span className="orbit-tag tag-chem">PRACTISE</span><span className="orbit-tag tag-math">GROW</span></> : <><div className="class-card class-card-back"><span>STUDY · TOGETHER</span><b>Study group</b><i>•••</i></div><div className="class-card class-card-front"><span className="class-card-icon"><Users size={22} /></span><span>YOUR CLASSROOM</span><b>Better learning,<br />together.</b><div className="class-avatars"><i>AS</i><i>PM</i><i>RK</i><em>+8</em></div></div><div className="panel-spark">✳</div></>}</div><div className="panel-bottom"><span>01 / LEARN WITH PURPOSE</span><ArrowDownRight size={19} /></div></div>
}

function GoogleButton({ onClick, disabled, message }: { onClick: () => void; disabled?: boolean; message?: string }) {
  return <><Button type="button" variant="neutral" className="google-button" onClick={onClick} disabled={disabled}><span className="google-g" aria-hidden="true">G</span>Continue with Google</Button>{message && <Notice tone="info">{message}</Notice>}</>
}

function Divider() { return <div className="form-divider"><span />OR CONTINUE WITH EMAIL<span /></div> }

function Field({ label, id, error, hint, ...props }: React.ComponentProps<typeof Input> & { label: string; id: string; error?: string; hint?: string }) {
  return <label className="phase-field" htmlFor={id}><span className="field-label">{label}</span><Input id={id} className={`phase-input ${error ? 'input-error' : ''}`} aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined} {...props} />{error ? <span id={`${id}-error`} className="field-error">{error}</span> : hint ? <span id={`${id}-hint`} className="field-hint">{hint}</span> : null}</label>
}

function AuthLayout({ children, eyebrow, title, subtitle, mode }: { children: ReactNode; eyebrow: string; title: ReactNode; subtitle: string; mode: 'sign-in' | 'sign-up' }) {
  return <Frame side={<BrandPanel eyebrow={eyebrow} title={title} copy={subtitle} />}><div className="auth-content"><Brand compact /><div className="auth-heading"><span className="section-kicker">{eyebrow}</span><h1>{mode === 'sign-in' ? 'Welcome back.' : <>Make room for<br />your next big idea.</>}</h1><p>{mode === 'sign-in' ? 'Sign in to pick up where your learning left off.' : 'Create your account and start building better study habits.'}</p></div>{children}<p className="switch-auth">{mode === 'sign-in' ? 'New to AdaptEd?' : 'Already have an account?'} <Link to={mode === 'sign-in' ? '/sign-up' : '/sign-in'}>{mode === 'sign-in' ? 'Create account' : 'Sign in'} <ArrowRight size={14} /></Link></p><p className="demo-disclaimer">Email access is a local demo until the authentication API is configured.</p></div></Frame>
}

function SignInPage() {
  const { signIn, continueWithGoogle, google } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [googleMessage, setGoogleMessage] = useState('')
  const submit = (event: FormEvent) => {
    event.preventDefault()
    const result = signIn({ email, password })
    if (!result.ok) { setError(result.message); return }
    navigate(postAuthRoute(result.data), { replace: true })
  }
  return <AuthLayout eyebrow="SIGN IN" title={<>Turn effort<br />into progress.</>} subtitle="Keep your PCM preparation moving, one clear next step at a time." mode="sign-in"><GoogleButton onClick={() => { const result = continueWithGoogle(); setGoogleMessage(result.ok ? '' : result.message) }} message={googleMessage || (google.configured ? '' : 'Google sign-in needs OAuth configuration before it can be used.')} /><Divider /><form onSubmit={submit} className="phase-form" noValidate><Field id="signin-email" label="Email address" type="email" autoComplete="email" placeholder="you@example.com" value={email} onChange={(event) => { setEmail(event.target.value); setError('') }} /><Field id="signin-password" label="Password" type="password" autoComplete="current-password" placeholder="Enter your password" value={password} onChange={(event) => { setPassword(event.target.value); setError('') }} />{error && <Notice>{error}</Notice>}<Button type="submit" className="submit-button">Sign in <ArrowRight size={17} /></Button></form></AuthLayout>
}

function SignUpPage() {
  const { signUp, continueWithGoogle, google } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [googleMessage, setGoogleMessage] = useState('')
  const update = (key: keyof typeof form, value: string) => { setForm((current) => ({ ...current, [key]: value })); setError('') }
  const submit = (event: FormEvent) => {
    event.preventDefault()
    const result = signUp(form)
    if (!result.ok) { setError(result.message); return }
    navigate(postAuthRoute(result.data), { replace: true })
  }
  return <AuthLayout eyebrow="GET STARTED" title={<>Make room<br />to get better.</>} subtitle="A focused classroom and a useful next step can change your whole prep routine." mode="sign-up"><GoogleButton onClick={() => { const result = continueWithGoogle(); setGoogleMessage(result.ok ? '' : result.message) }} message={googleMessage || (google.configured ? '' : 'Google sign-in needs OAuth configuration before it can be used.')} /><Divider /><form onSubmit={submit} className="phase-form" noValidate><Field id="signup-name" label="Full name" autoComplete="name" placeholder="Your name" value={form.name} onChange={(event) => update('name', event.target.value)} /><Field id="signup-email" label="Email address" type="email" autoComplete="email" placeholder="you@example.com" value={form.email} onChange={(event) => update('email', event.target.value)} /><Field id="signup-password" label="Password" type="password" autoComplete="new-password" placeholder="At least 8 characters" value={form.password} onChange={(event) => update('password', event.target.value)} /><Field id="signup-confirm" label="Confirm password" type="password" autoComplete="new-password" placeholder="Enter it once more" value={form.confirm} onChange={(event) => update('confirm', event.target.value)} />{error && <Notice>{error}</Notice>}<Button type="submit" className="submit-button">Create account <ArrowRight size={17} /></Button></form></AuthLayout>
}

type StudentOnboardingForm = Omit<StudentOnboardingProfile, 'completedAt'>

const INITIAL_STUDENT_ONBOARDING: StudentOnboardingForm = {
  displayName: '',
  currentClass: '' as StudentClassLevel,
  jeeGoal: '' as StudentJeeGoal,
  strongestSubject: '' as StudentStrengthSubject,
  improvementSubject: '' as StudentImprovementSubject,
  learningStyle: '' as StudentLearningStyle,
}

const studentClassOptions: Array<{ value: StudentClassLevel; label: string }> = [
  { value: 'Class 11', label: 'Class 11' },
  { value: 'Class 12', label: 'Class 12' },
  { value: 'Dropper', label: 'Dropper' },
  { value: 'Other', label: 'Other' },
]

const studentGoalOptions: Array<{ value: StudentJeeGoal; label: string; description: string }> = [
  { value: 'JEE Main', label: 'JEE Main', description: 'Build speed and accuracy for the main exam.' },
  { value: 'JEE Advanced', label: 'JEE Advanced', description: 'Go deeper with challenging, multi-step problems.' },
  { value: 'Both', label: 'Both', description: 'Prepare for both exams with one focused path.' },
]

const studentSubjectOptions: Array<{ value: StudentStrengthSubject; label: string }> = [
  { value: 'physics', label: 'Physics' },
  { value: 'chemistry', label: 'Chemistry' },
  { value: 'mathematics', label: 'Mathematics' },
  { value: 'all', label: 'About the same in all' },
]

const studentImprovementOptions: Array<{ value: StudentImprovementSubject; label: string }> = [
  { value: 'physics', label: 'Physics' },
  { value: 'chemistry', label: 'Chemistry' },
  { value: 'mathematics', label: 'Mathematics' },
  { value: 'not-sure', label: 'Not sure yet' },
]

const learningStyleOptions: Array<{ value: StudentLearningStyle; label: string }> = [
  { value: 'concepts-first', label: 'Concept explanations first' },
  { value: 'questions-first', label: 'Solve questions first' },
  { value: 'worked-examples', label: 'Learn through worked examples' },
  { value: 'mix', label: 'Mix of all three' },
]

function StudentChoice({
  name,
  value,
  selected,
  label,
  onChange,
}: {
  name: string
  value: string
  selected: boolean
  label: string
  onChange: () => void
}) {
  return <label className={`student-onboarding-choice ${selected ? 'student-onboarding-choice-selected' : ''}`}><input type="radio" name={name} value={value} checked={selected} onChange={onChange} /><span>{label}</span></label>
}

function StudentOnboardingPage() {
  const { session, completeStudentOnboarding } = useAuth()
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [form, setForm] = useState<StudentOnboardingForm>(INITIAL_STUDENT_ONBOARDING)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (!session) return <Navigate to="/sign-in" replace />
  if (session.user.role !== 'student') return <Navigate to="/classroom" replace />
  const alreadyComplete = session.user.studentOnboardingComplete
    ?? session.user.onboardingComplete
  if (alreadyComplete) return <Navigate to="/classroom" replace />

  const update = <K extends keyof StudentOnboardingForm>(key: K, value: StudentOnboardingForm[K]) => {
    setForm((current) => ({ ...current, [key]: value }))
    setError('')
  }

  const validateStep = () => {
    if (step === 1 && !form.displayName.trim()) return 'Tell us what you should be called.'
    if (step === 1 && !form.currentClass) return 'Choose your current class.'
    if (step === 2 && !form.jeeGoal) return 'Choose the exam you are preparing for.'
    if (step === 3 && !form.strongestSubject) return 'Choose your strongest subject.'
    if (step === 3 && !form.improvementSubject) return 'Choose the subject that needs improvement.'
    if (step === 3 && !form.learningStyle) return 'Choose a learning style.'
    return ''
  }

  const continueStep = () => {
    const message = validateStep()
    if (message) { setError(message); return }
    setError('')
    setStep((current) => Math.min(3, current + 1))
  }

  const finish = () => {
    const message = validateStep()
    if (message) { setError(message); return }
    setBusy(true)
    const profile: StudentOnboardingProfile = { ...form, displayName: form.displayName.trim(), completedAt: new Date().toISOString() }
    completeStudentOnboarding(profile)
    navigate('/classroom', { replace: true })
  }

  return <Frame side={<BrandPanel eyebrow="A PATH THAT FITS" title={<>Make your<br />next step yours.</>} copy="A few quick answers help AdaptEd shape a clearer JEE preparation path around how you learn." />}><div className="student-onboarding-wrap"><Brand compact /><div className="auth-heading student-onboarding-heading"><span className="section-kicker">STUDENT SETUP</span><h1>Let’s get to know<br />your prep.</h1><p>Three quick steps, then we’ll take you to classroom setup.</p></div><Card className="phase-card student-onboarding-card"><div className="student-onboarding-progress" aria-label={`Step ${step} of 3`}><div className="student-onboarding-progress-head"><span>YOUR STARTING POINT</span><b>STEP {String(step).padStart(2, '0')} / 03</b></div><div className="student-onboarding-progress-track">{[1, 2, 3].map((item) => <span className={item <= step ? 'student-onboarding-progress-active' : ''} key={item} />)}</div></div>{step === 1 && <section className="student-onboarding-step" aria-labelledby="student-step-one-title"><span className="section-kicker">01 / BASIC PROFILE</span><h2 id="student-step-one-title">What should we call you?</h2><p className="student-onboarding-copy">Use the name you want to see across your learning space.</p><Field id="student-display-name" label="Display name" autoComplete="name" placeholder={session.user.name} value={form.displayName} onChange={(event) => update('displayName', event.target.value)} /><fieldset className="student-onboarding-fieldset"><legend>Current class</legend><div className="student-onboarding-choice-grid student-onboarding-choice-grid-four">{studentClassOptions.map((option) => <StudentChoice key={option.value} name="current-class" value={option.value} label={option.label} selected={form.currentClass === option.value} onChange={() => update('currentClass', option.value)} />)}</div></fieldset></section>}{step === 2 && <section className="student-onboarding-step" aria-labelledby="student-step-two-title"><span className="section-kicker">02 / JEE GOAL</span><h2 id="student-step-two-title">Which exam are you preparing for?</h2><p className="student-onboarding-copy">We’ll use this to keep the recommendations focused.</p><fieldset className="student-onboarding-fieldset"><legend>Exam goal</legend><div className="student-onboarding-goal-list">{studentGoalOptions.map((option) => <label className={`student-onboarding-goal ${form.jeeGoal === option.value ? 'student-onboarding-choice-selected' : ''}`} key={option.value}><input type="radio" name="jee-goal" value={option.value} checked={form.jeeGoal === option.value} onChange={() => update('jeeGoal', option.value)} /><span><b>{option.label}</b><small>{option.description}</small></span></label>)}</div></fieldset></section>}{step === 3 && <section className="student-onboarding-step" aria-labelledby="student-step-three-title"><span className="section-kicker">03 / LEARNING PREFERENCES</span><h2 id="student-step-three-title">How should we shape your practice?</h2><p className="student-onboarding-copy">There’s no wrong answer. Pick what feels most useful today.</p><fieldset className="student-onboarding-fieldset"><legend>Strongest subject</legend><div className="student-onboarding-choice-grid">{studentSubjectOptions.map((option) => <StudentChoice key={option.value} name="strongest-subject" value={option.value} label={option.label} selected={form.strongestSubject === option.value} onChange={() => update('strongestSubject', option.value)} />)}</div></fieldset><fieldset className="student-onboarding-fieldset"><legend>Subject needing improvement</legend><div className="student-onboarding-choice-grid">{studentImprovementOptions.map((option) => <StudentChoice key={option.value} name="improvement-subject" value={option.value} label={option.label} selected={form.improvementSubject === option.value} onChange={() => update('improvementSubject', option.value)} />)}</div></fieldset><fieldset className="student-onboarding-fieldset"><legend>Preferred learning style</legend><div className="student-onboarding-style-list">{learningStyleOptions.map((option) => <StudentChoice key={option.value} name="learning-style" value={option.value} label={option.label} selected={form.learningStyle === option.value} onChange={() => update('learningStyle', option.value)} />)}</div></fieldset></section>}{error && <Notice>{error}</Notice>}<div className="student-onboarding-actions"><Button type="button" variant="neutral" onClick={() => { setError(''); setStep((current) => Math.max(1, current - 1)) }} disabled={step === 1 || busy}><ArrowLeft size={16} /> Back</Button>{step < 3 ? <Button type="button" className="submit-button" onClick={continueStep}>Continue <ArrowRight size={17} /></Button> : <Button type="button" className="submit-button" onClick={finish} disabled={busy}>{busy ? 'Saving…' : 'Finish setup'} <Check size={17} /></Button>}</div></Card><p className="demo-disclaimer student-onboarding-disclaimer">Development-only save: your answers are stored in this browser for this account until a supported profile API is available.</p></div></Frame>
}

function Protected({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  if (status === 'loading') return <div className="phase-loading">Loading your workspace…</div>
  if (status !== 'authenticated') return <Navigate to="/sign-in" replace />
  return children
}

function ProtectedTeacher({ children }: { children: ReactNode }) {
  const { status, session } = useAuth()
  if (status === 'loading') return <div className="phase-loading">Loading your workspace…</div>
  if (status !== 'authenticated' || session?.user.role !== 'teacher') return <Navigate to="/teacher-login" replace />
  return children
}

function ProtectedStudent({ children }: { children: ReactNode }) {
  const { status, session } = useAuth()
  const location = useLocation()
  const preview = new URLSearchParams(location.search).get('preview') === '1'
  if (preview) return children
  if (status === 'loading') return <div className="phase-loading">Loading your workspace…</div>
  if (status !== 'authenticated' || !session) return <Navigate to="/sign-in" replace />
  if (session.user.role !== 'student') return <Navigate to="/classroom" replace />
  const studentOnboardingComplete = session.user.studentOnboardingComplete
    ?? session.user.onboardingComplete
  if (!studentOnboardingComplete) return <Navigate to="/student-onboarding" replace />
  if (!session.user.onboardingComplete) return <Navigate to="/classroom" replace />
  return children
}

function ClassroomHome() {
  const { session, classrooms, signOut } = useAuth()
  const navigate = useNavigate()
  if (!session) return <Navigate to="/sign-in" replace />
  const openCreate = () => navigate('/classroom/create')
  return <Frame side={<BrandPanel visual="classroom" eyebrow="YOUR LEARNING COMMUNITY" title={<>Your people.<br />Your pace.</>} copy="Bring your JEE prep group into one space and keep the next step clear." />}><div className="onboard-content"><Brand compact /><div className="auth-heading"><span className="section-kicker">CLASSROOM SETUP</span><h1>Where will you<br />learn today?</h1><p>Hi {session.user.name.split(' ')[0]}, create a classroom for your group or join one with a code.</p></div><Notice tone="info">{session.user.role === 'teacher' ? 'Teacher workspace ready.' : 'Signed in successfully.'}</Notice><div className="classroom-actions">{session.user.role === 'teacher' && <button className="choice-card choice-create" onClick={openCreate}><span className="choice-icon"><Plus size={21} /></span><span className="choice-copy"><b>Create classroom</b><small>Set up a space for your JEE batch</small></span><ArrowRight size={18} /></button>}<button className="choice-card choice-join" onClick={() => navigate('/classroom/join')}><span className="choice-icon"><Users size={21} /></span><span className="choice-copy"><b>Join classroom</b><small>Enter the invite code from your teacher</small></span><ArrowRight size={18} /></button></div>{classrooms.length > 0 && <div className="existing-classrooms"><div className="existing-heading"><span>YOUR CLASSROOMS</span><span>{classrooms.length} ACTIVE</span></div>{classrooms.map((classroom) => <ClassroomRow key={classroom.id} classroom={classroom} />)}</div>}<button className="text-button signout-button" onClick={() => { signOut(); navigate('/', { replace: true }) }}><LogOut size={15} /> Sign out</button></div></Frame>
}

function ClassroomRow({ classroom }: { classroom: Classroom }) {
  return <div className="classroom-row"><span className="classroom-row-icon"><School size={18} /></span><span className="classroom-row-copy"><b>{classroom.name}</b><small>{classroom.classLevel} · {classroom.examTarget}</small></span><span className="classroom-code">{classroom.code}</span></div>
}

function FormShell({ title, description, children, onBack }: { title: string; description: string; children: ReactNode; onBack: () => void }) {
  return <Frame><div className="class-form-wrap"><button className="back-button" onClick={onBack}><ArrowLeft size={16} /> Classroom options</button><Card className="phase-card"><div className="phase-card-head"><span className="section-kicker">JEE PCM CLASSROOM</span><span className="step-count">STEP 01 / 01</span></div><h1>{title}</h1><p className="card-intro">{description}</p>{children}</Card></div></Frame>
}

function CreateClassroomPage() {
  const { session, createClassroom, completeOnboarding } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<CreateClassroomInput>({ name: '', teacherName: session?.user.name ?? '', classLevel: 'Class 12', academicYear: ACADEMIC_YEARS[1], examTarget: 'JEE Main + Advanced', subjects: [...JEE_SUBJECTS] })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const change = <K extends keyof CreateClassroomInput>(key: K, value: CreateClassroomInput[K]) => { setForm((current) => ({ ...current, [key]: value })); setError('') }
  const toggleSubject = (subject: JeeSubjectId) => change('subjects', form.subjects.includes(subject) ? form.subjects.filter((item) => item !== subject) : [...form.subjects, subject])
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true)
    const result = await createClassroom(form)
    setBusy(false)
    if (!result.ok) { setError(result.message); return }
    completeOnboarding()
    navigate('/classroom/created', { replace: true, state: { classroom: result.data } })
  }
  return <FormShell title="Create your classroom." description="Set the focus for your batch. You can change the details as your preparation evolves." onBack={() => navigate('/classroom')}><form className="phase-form create-form" onSubmit={submit} noValidate><Field id="classroom-name" label="Classroom name" placeholder="e.g. JEE 2027 · Evening Batch" value={form.name} maxLength={60} onChange={(event) => change('name', event.target.value)} /><Field id="teacher-name" label="Your name" placeholder="Teacher or batch lead" value={form.teacherName} onChange={(event) => change('teacherName', event.target.value)} /><div className="form-grid"><label className="phase-field" htmlFor="class-level"><span className="field-label">Class level</span><select id="class-level" className="phase-select" value={form.classLevel} onChange={(event) => change('classLevel', event.target.value as ClassLevel)}>{CLASS_LEVELS.map((level) => <option key={level}>{level}</option>)}</select></label><label className="phase-field" htmlFor="academic-year"><span className="field-label">Academic year</span><select id="academic-year" className="phase-select" value={form.academicYear} onChange={(event) => change('academicYear', event.target.value)}>{ACADEMIC_YEARS.map((year) => <option key={year}>{year}</option>)}</select></label></div><label className="phase-field" htmlFor="exam-target"><span className="field-label">Exam target</span><select id="exam-target" className="phase-select" value={form.examTarget} onChange={(event) => change('examTarget', event.target.value as ExamTarget)}>{EXAM_TARGETS.map((exam) => <option key={exam}>{exam}</option>)}</select></label><fieldset className="subject-fieldset"><legend>Subjects <small>Choose at least one</small></legend><div className="subject-options">{JEE_SUBJECTS.map((subject) => <label className={`subject-option ${form.subjects.includes(subject) ? 'subject-selected' : ''}`} key={subject}><input type="checkbox" checked={form.subjects.includes(subject)} onChange={() => toggleSubject(subject)} /><span className="subject-check"><Check size={13} /></span><span>{subjectLabel(subject)}</span></label>)}</div></fieldset>{error && <Notice>{error}</Notice>}<Button type="submit" className="submit-button" disabled={busy}>{busy ? 'Creating…' : 'Create classroom'} <ArrowRight size={17} /></Button></form><p className="demo-disclaimer">Classroom data is now stored in PostgreSQL.</p></FormShell>
}

function CreatedPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const classroom = (location.state as { classroom?: Classroom } | null)?.classroom
  if (!classroom) return <Navigate to="/classroom" replace />
  return <Frame><div className="created-wrap"><span className="created-check"><Check size={30} /></span><span className="section-kicker">CLASSROOM READY</span><h1>Nice. Your classroom<br />is ready to roll.</h1><p>Send this code to your students so they can join the batch.</p><div className="share-code"><span>CLASSROOM CODE</span><strong>{classroom.code}</strong><small>Tap to select and share</small></div><Button className="submit-button" onClick={() => navigate('/classroom', { replace: true })}>Go to classroom options <ArrowRight size={17} /></Button></div></Frame>
}

function JoinClassroomPage() {
  const { joinClassroom, completeOnboarding } = useAuth()
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [joined, setJoined] = useState<Classroom | null>(null)
  useEffect(() => {
    if (!joined) return
    const timer = window.setTimeout(() => navigate('/student/problems', { replace: true }), 0)
    return () => window.clearTimeout(timer)
  }, [joined, navigate])
  const submit = async (event: FormEvent) => { event.preventDefault(); const result = await joinClassroom({ code }); if (!result.ok) { setError(result.message); setJoined(null); return }; completeOnboarding('student'); setError(''); setJoined(result.data) }
  return <FormShell title="Join a classroom." description="Ask your teacher or batch lead for the invite code." onBack={() => navigate('/classroom')}><form className="phase-form join-form" onSubmit={submit} noValidate><label className="phase-field" htmlFor="join-code"><span className="field-label">Classroom code</span><div className="code-input-wrap"><Mail size={17} /><Input id="join-code" className="phase-input code-input" placeholder="Enter code" value={code} maxLength={10} onChange={(event) => { setCode(event.target.value.replace(/[^A-Za-z0-9]/g, '')); setError(''); setJoined(null) }} /></div><span className="field-hint">Codes have 10 letters or numbers. Enter it exactly as shown.</span></label>{error && <Notice>{error}</Notice>}{joined && <Notice tone="success">You joined <b>{joined.name}</b>. Your classroom is saved in this browser.</Notice>}<Button type="submit" className="submit-button">Join classroom <ArrowRight size={17} /></Button></form><div className="join-help"><BookOpen size={17} /><p>Don't have a code yet? Ask your teacher to create a classroom and share its invite code.</p></div></FormShell>
}

function CallbackPage() {
  const { finishCallback } = useAuth()
  const navigate = useNavigate()
  const [message, setMessage] = useState('')
  const started = useRef(false)
  useEffect(() => {
    if (started.current) return
    started.current = true
    let active = true
    finishCallback().then((result) => { if (!active) return; if (result.ok) navigate(postAuthRoute(result.data), { replace: true }); else setMessage(result.message) })
    return () => { active = false }
  }, [finishCallback, navigate])
  return message ? <Frame><div className="created-wrap"><span className="section-kicker">SIGN-IN LINK</span><h1>We couldn't complete sign in.</h1><Notice>{message}</Notice><Link className="inline-link" to="/sign-in">Back to sign in <ChevronRight size={15} /></Link></div></Frame> : <div className="phase-loading">Completing sign in…</div>
}

function LandingPage() {
  const { status, session } = useAuth()
  if (status === 'loading') return <div className="phase-loading">Loading AdaptEd…</div>
  if (session) return <Navigate to={postAuthRoute(session)} replace />
  return <Frame><div className="landing-story">
    <section className="landing-content landing-hero-section">
      <div className="landing-copy"><span className="section-kicker"><span className="live-dot" /> A MORE PERSONAL WAY TO LEARN</span><h1>Learning that<br /><span>moves with you.</span></h1><p>Build understanding one step at a time. AdaptEd helps learners see what they know, what to focus on next, and how to keep making progress.</p><div className="landing-actions"><Link className="landing-primary" to="/sign-up">Get started <ArrowRight size={18} /></Link><Link className="landing-secondary" to="/sign-in">I already have an account <ChevronRight size={17} /></Link><Link className="landing-secondary" to="/teacher-login">Teacher Login <ChevronRight size={17} /></Link></div><div className="landing-proof"><span><Check size={14} /> A path shaped around you</span><span><Check size={14} /> Progress you can understand</span></div></div>
      <div className="landing-visual"><div className="visual-sticker"><Orbit size={15} /> YOUR NEXT STEP</div><div className="visual-center"><div className="visual-orbit orbit-a" /><div className="visual-orbit orbit-b" /><div className="visual-core"><GraduationCap size={45} /></div><span className="subject-chip chip-physics">LEARN</span><span className="subject-chip chip-chem">PRACTISE</span><span className="subject-chip chip-math">GROW</span><span className="visual-plus plus-one">+</span><span className="visual-plus plus-two">✳</span></div><div className="visual-caption"><span>01</span><b>Small steps.<br />Real understanding.</b><ArrowDownRight size={20} /></div></div>
      <a className="landing-scroll-cue" href="#adapt-learning">SCROLL TO EXPLORE <ArrowDownRight size={15} /></a>
    </section>
    <section className="landing-feature-section feature-adapt" id="adapt-learning"><div className="feature-copy"><span className="section-kicker">01 / A PATH THAT ADAPTS</span><h2>Start where<br />you are.</h2><p>Practice should respond to your understanding. Get a useful next activity based on what is feeling clear and what needs another look.</p><Link to="/sign-up" className="feature-link">Find your next step <ArrowRight size={16} /></Link></div><div className="feature-visual adapt-visual"><div className="feature-stamp">NOT ONE-SIZE-FITS-ALL</div><div className="path-card path-card-one"><span>01 · FOUNDATION</span><b>Build the basics</b><div className="path-line"><i /></div></div><div className="path-arrow"><ArrowDownRight size={22} /></div><div className="path-card path-card-two"><span>02 · YOUR NEXT STEP</span><b>Practise with purpose</b><div className="path-line"><i /></div></div><div className="path-arrow"><ArrowDownRight size={22} /></div><div className="path-card path-card-three"><span>03 · KEEP GOING</span><b>Try something new</b><div className="path-line"><i /></div></div></div><span className="feature-index">A / ADAPT</span></section>
    <section className="landing-feature-section feature-progress"><div className="feature-visual progress-visual"><div className="progress-window"><div className="progress-window-top"><span>YOUR LEARNING MAP</span><span className="map-dots">•••</span></div><div className="map-row"><i className="map-node node-done"><Check size={13} /></i><div><b>Core ideas</b><small>Building confidence</small></div><span className="map-status">IN PROGRESS</span></div><div className="map-connector" /><div className="map-row"><i className="map-node node-current"><Orbit size={14} /></i><div><b>Putting it together</b><small>Your current focus</small></div><span className="map-status map-current">YOUR NEXT STEP</span></div><div className="map-connector" /><div className="map-row"><i className="map-node node-later"><Sparkles size={13} /></i><div><b>New challenges</b><small>Ready when you are</small></div><span className="map-status">UP NEXT</span></div><div className="map-progress"><span /><b>You're making progress</b></div></div><span className="progress-spark">✳</span></div><div className="feature-copy"><span className="section-kicker">02 / PROGRESS WITH CONTEXT</span><h2>See how far<br />you've come.</h2><p>Progress means more than a single score. Follow your growth, revisit important ideas, and understand what your learning signals are telling you.</p><Link to="/sign-up" className="feature-link">Make progress visible <ArrowRight size={16} /></Link></div><span className="feature-index">B / UNDERSTAND</span></section>
    <section className="landing-feature-section feature-together"><div className="feature-copy"><span className="section-kicker">03 / LEARN TOGETHER</span><h2>Better with<br />your people.</h2><p>Create a classroom for your group or join one with an invite. Make space for shared goals, steady practice, and support along the way.</p><div className="landing-actions"><Link className="landing-primary" to="/sign-up">Create your account <ArrowRight size={17} /></Link><Link className="landing-secondary" to="/sign-in">Sign in <ChevronRight size={16} /></Link></div><p className="feature-footnote">Your next step starts here. Make learning feel like yours.</p></div><div className="feature-visual together-visual"><div className="together-sun">✳</div><div className="together-note note-one"><span>STUDY GROUP</span><b>Progress feels<br />better together.</b></div><div className="together-note note-two"><span className="avatar-stack"><i>A</i><i>M</i><i>R</i><em>+12</em></span><b>One place to<br />keep moving.</b></div><div className="together-arrow"><ArrowDownRight size={30} /></div></div><span className="feature-index">C / TOGETHER</span></section>
  </div></Frame>
}

export function PhaseOneApp() {
  const { status, session } = useAuth()
  return <Routes><Route path="/" element={<LandingPage />} /><Route path="/terms" element={<TermsPage />} /><Route path="/privacy" element={<PrivacyPage />} /><Route path="/sign-in" element={status === 'authenticated' && session ? <Navigate to={postAuthRoute(session)} replace /> : <SignInPage />} /><Route path="/sign-up" element={status === 'authenticated' && session ? <Navigate to={postAuthRoute(session)} replace /> : <SignUpPage />} /><Route path="/teacher-login" element={status === 'authenticated' && session?.user.role === 'teacher' ? <Navigate to="/teacher" replace /> : <TeacherLoginPage />} /><Route path="/teacher" element={<ProtectedTeacher><TeacherDashboardPage /></ProtectedTeacher>} /><Route path="/auth/callback" element={<CallbackPage />} /><Route path="/student-onboarding" element={<Protected><StudentOnboardingPage /></Protected>} /><Route path="/classroom" element={<Protected><ClassroomHome /></Protected>} /><Route path="/classroom/create" element={<ProtectedTeacher><CreateClassroomPage /></ProtectedTeacher>} /><Route path="/classroom/join" element={<Protected><JoinClassroomPage /></Protected>} /><Route path="/classroom/created" element={<ProtectedTeacher><CreatedPage /></ProtectedTeacher>} /><Route path="/student/problems" element={<ProtectedStudent><TopicWiseProblemsPage /></ProtectedStudent>} /><Route path="/student/topics/:subject/:slug" element={<ProtectedStudent><TopicProblemsPage /></ProtectedStudent>} /><Route path="/student/problems/:id" element={<ProtectedStudent><JeeProblemPage /></ProtectedStudent>} /><Route path="/student/quizzes" element={<ProtectedStudent><TopicQuizzesPage /></ProtectedStudent>} /><Route path="/student/quizzes/topic/:subject/:slug" element={<ProtectedStudent><TopicQuizAttemptPage /></ProtectedStudent>} /><Route path="/student/quizzes/:quizId" element={<ProtectedStudent><TeacherQuizAttemptPage /></ProtectedStudent>} /><Route path="*" element={<Navigate to="/" replace />} /></Routes>
}

