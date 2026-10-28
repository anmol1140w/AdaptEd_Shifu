import { useEffect, useState } from 'react'
import { ArrowLeft, BarChart3, Check, LoaderCircle, Target, TrendingDown, Users } from 'lucide-react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { useAuth } from '../../app/AuthProvider'
import { teacherClassAnalytics, teacherStudentProfile } from '../../services/api'
import { TeacherFrame } from './TeacherPages'
import './teacher.css'

function percent(value: unknown) {
  return `${Math.round(Number(value ?? 0) * 100)}%`
}

function TeacherLoading() {
  return <div className="teacher-insight-loading"><LoaderCircle className="spin" size={18} /> Loading classroom data…</div>
}

export function TeacherStudentProfilePage() {
  const { slug, studentId } = useParams()
  const { session } = useAuth()
  const [data, setData] = useState<Awaited<ReturnType<typeof teacherStudentProfile>> | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    if (!slug || !studentId) return
    void teacherStudentProfile(slug, studentId).then(setData).catch((reason) => setError(reason instanceof Error ? reason.message : 'Could not load student profile'))
  }, [slug, studentId])
  if (!session || session.user.role !== 'teacher') return <Navigate to="/teacher-login" replace />
  return <TeacherFrame><main className="teacher-insight-main"><Link className="teacher-back-link" to="/teacher"><ArrowLeft size={15} /> Back to teacher dashboard</Link>{error ? <div className="teacher-error">{error}</div> : !data ? <TeacherLoading /> : <><section className="teacher-insight-hero"><div><span className="teacher-kicker">STUDENT PROFILE</span><h1>{String(data.student.name)}</h1><p>{String(data.student.email)} · Joined {new Date(String(data.student.joined_at)).toLocaleDateString()}</p></div><div className="teacher-profile-mark"><Users size={27} /><span>CLASSROOM STUDENT</span></div></section><section className="teacher-insight-stats"><article><Check size={17} /><span>Questions solved</span><b>{String(data.summary.solved ?? 0)}</b></article><article><Target size={17} /><span>Questions attempted</span><b>{String(data.summary.attempts ?? 0)}</b></article><article><TrendingDown size={17} /><span>Accuracy</span><b>{percent(data.summary.accuracy)}</b></article><article><BarChart3 size={17} /><span>Active days</span><b>{String(data.summary.active_days ?? 0)}</b></article></section><div className="teacher-insight-grid"><section className="teacher-insight-card"><div className="teacher-insight-card-head"><div><span className="teacher-kicker">WEAKEST TOPICS</span><h2>Where to focus</h2></div><span>{data.topics.length} topics</span></div>{data.topics.length ? data.topics.map((topic) => <div className="teacher-topic-row" key={String(topic.name)}><div><b>{String(topic.name)}</b><small>{String(topic.attempts)} attempts · {String(topic.students ?? 1)} student activity</small></div><strong>{percent(topic.accuracy)}</strong></div>) : <p className="teacher-muted">No topic attempts recorded yet.</p>}</section><section className="teacher-insight-card"><div className="teacher-insight-card-head"><div><span className="teacher-kicker">RECENT ACTIVITY</span><h2>Latest submissions</h2></div></div>{data.recent.length ? data.recent.map((item, index) => <div className="teacher-recent-row" key={`${String(item.title)}-${String(item.created_at)}-${index}`}><div><b>{String(item.title)}</b><small>{String(item.subject)} · {String(item.chapter)}</small></div><span className={item.correct ? 'teacher-correct' : 'teacher-attempted'}>{item.correct ? 'Solved' : 'Attempted'}</span></div>) : <p className="teacher-muted">No submissions recorded yet.</p>}</section></div></>}</main></TeacherFrame>
}

export function TeacherAnalyticsPage() {
  const { slug } = useParams()
  const { session } = useAuth()
  const [data, setData] = useState<Awaited<ReturnType<typeof teacherClassAnalytics>> | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    if (!slug) return
    void teacherClassAnalytics(slug).then(setData).catch((reason) => setError(reason instanceof Error ? reason.message : 'Could not load analytics'))
  }, [slug])
  if (!session || session.user.role !== 'teacher') return <Navigate to="/teacher-login" replace />
  return <TeacherFrame><main className="teacher-insight-main"><Link className="teacher-back-link" to="/teacher"><ArrowLeft size={15} /> Back to teacher dashboard</Link>{error ? <div className="teacher-error">{error}</div> : !data ? <TeacherLoading /> : <><section className="teacher-insight-hero teacher-analytics-hero"><div><span className="teacher-kicker">CLASS ANALYTICS</span><h1>{String(data.classroom.name)}</h1><p>Aggregated performance from students in this classroom.</p></div><div className="teacher-profile-mark"><BarChart3 size={27} /><span>CLASS OVERVIEW</span></div></section><section className="teacher-insight-stats"><article><Users size={17} /><span>Students</span><b>{String(data.overview.students ?? 0)}</b></article><article><Target size={17} /><span>Average attempts</span><b>{Number(data.overview.average_attempts ?? 0).toFixed(1)}</b></article><article><Check size={17} /><span>Average solved</span><b>{Number(data.overview.average_solved ?? 0).toFixed(1)}</b></article><article><TrendingDown size={17} /><span>Average accuracy</span><b>{percent(data.overview.accuracy)}</b></article></section><div className="teacher-threshold-card"><strong>{String(data.overview.below_threshold ?? 0)}</strong><span>students below the 50% accuracy threshold</span></div><section className="teacher-insight-card"><div className="teacher-insight-card-head"><div><span className="teacher-kicker">TOPIC PERFORMANCE</span><h2>Weakest topics across the class</h2></div><span>Sorted by accuracy</span></div>{data.topics.length ? data.topics.map((topic) => <div className="teacher-topic-row" key={String(topic.name)}><div><b>{String(topic.name)}</b><small>{String(topic.students)} students · {String(topic.attempts)} attempts · {String(topic.solved)} solved</small></div><strong>{percent(topic.accuracy)}</strong></div>) : <p className="teacher-muted">No class attempts recorded yet.</p>}</section></>}</main></TeacherFrame>
}
