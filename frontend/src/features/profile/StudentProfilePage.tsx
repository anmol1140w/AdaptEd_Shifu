import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, CalendarDays, Check, Flame, LoaderCircle, Mail, Target, Trophy } from 'lucide-react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../../app/AuthProvider'
import { StudentNav } from '../learner/ProblemsPage'
import type { Difficulty } from '../../types'
import { loadStudentProfileData, type ProfileSubmission, type StudentProfileData } from './services/studentProfileService'
import './student-profile.css'

const difficultyOrder: Difficulty[] = ['Easy', 'Medium', 'Hard']

function dateKey(value: Date | string) {
  const date = typeof value === 'string' ? new Date(value) : value
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function streakStats(submissions: ProfileSubmission[]) {
  const keys = [...new Set(submissions.map((submission) => dateKey(submission.timestamp)))].sort()
  const set = new Set(keys)
  const today = new Date()
  const todayKey = dateKey(today)
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  let current = 0
  let cursor: Date | null = set.has(todayKey) ? today : set.has(dateKey(yesterday)) ? yesterday : null
  while (cursor && set.has(dateKey(cursor))) {
    current += 1
    const next = new Date(cursor)
    next.setDate(next.getDate() - 1)
    cursor = next
  }
  let longest = 0
  let run = 0
  keys.forEach((key, index) => {
    const previous = index ? new Date(`${keys[index - 1]}T12:00:00`) : null
    const currentDate = new Date(`${key}T12:00:00`)
    if (previous && (currentDate.getTime() - previous.getTime()) / 86400000 === 1) run += 1
    else run = 1
    longest = Math.max(longest, run)
  })
  return { activeDays: keys.length, current, longest }
}

function ProfileAvatar({ name, large = false }: { name: string; large?: boolean }) {
  const initials = name.split(/\s+/).map((part) => part[0]).join('').slice(0, 2).toUpperCase()
  return <span className={`profile-avatar ${large ? 'profile-avatar-large' : ''}`}>{initials || 'ST'}</span>
}

function StatCard({ icon, label, value, detail, tone = 'mint' }: { icon: React.ReactNode; label: string; value: string | number; detail: string; tone?: 'mint' | 'yellow' | 'blue' | 'coral' }) {
  return <article className={`profile-stat profile-stat-${tone}`}><span className="profile-stat-icon">{icon}</span><span className="profile-stat-label">{label}</span><strong>{value}</strong><small>{detail}</small></article>
}

function SolvedChart({ solvedByDifficulty, total, source }: { solvedByDifficulty: Record<Difficulty, number>; total: number; source: StudentProfileData['source'] }) {
  const solved = difficultyOrder.reduce((sum, difficulty) => sum + solvedByDifficulty[difficulty], 0)
  const radius = 48
  const circumference = 2 * Math.PI * radius
  let offset = 0
  const colors: Record<Difficulty, string> = { Easy: '#65b985', Medium: '#f0bb4d', Hard: '#ef725e' }
  return <div className="solved-chart-card"><div className="profile-card-heading"><div><span className="profile-kicker">QUESTION PROGRESS</span><h2>Solved questions</h2></div><span className="profile-card-count">{solved}/{total || 0}</span></div><div className="solved-chart-body"><div className="solved-ring-wrap"><svg className="solved-ring" viewBox="0 0 120 120" role="img" aria-label={`${solved} solved questions out of ${total || 0}`}><circle className="solved-ring-track" cx="60" cy="60" r={radius} />{difficultyOrder.map((difficulty) => { const length = total ? (solvedByDifficulty[difficulty] / total) * circumference : 0; const dash = `${length} ${circumference - length}`; const circle = <circle key={difficulty} className="solved-ring-segment" cx="60" cy="60" r={radius} stroke={colors[difficulty]} strokeDasharray={dash} strokeDashoffset={-offset} />; offset += length; return circle })}</svg><div className="solved-ring-label"><strong>{solved}</strong><span>solved</span></div></div><div className="solved-breakdown">{difficultyOrder.map((difficulty) => <div className="solved-breakdown-row" key={difficulty}><span><i style={{ background: colors[difficulty] }} />{difficulty}</span><b>{solvedByDifficulty[difficulty]}</b></div>)}<p>{source === 'api' ? 'Counts reflect successful submissions returned for this account.' : 'Development-only question bank denominator; solved counts are still scoped to this account.'}</p></div></div></div>
}

function ActivityHeatmap({ submissions }: { submissions: ProfileSubmission[] }) {
  const [selected, setSelected] = useState<string | null>(null)
  const { weeks, pointsByDate, entriesByDate, monthLabels } = useMemo(() => {
    const today = new Date()
    today.setHours(12, 0, 0, 0)
    const start = new Date(today)
    start.setDate(start.getDate() - 364)
    start.setDate(start.getDate() - ((start.getDay() + 6) % 7))
    const dates: Date[] = []
    for (const cursor = new Date(start); cursor <= today; cursor.setDate(cursor.getDate() + 1)) dates.push(new Date(cursor))
    const points = new Map<string, number>()
    const entries = new Map<string, ProfileSubmission[]>()
    submissions.forEach((submission) => {
      const key = dateKey(submission.timestamp)
      points.set(key, (points.get(key) ?? 0) + 1)
      entries.set(key, [...(entries.get(key) ?? []), submission])
    })
    const grouped: Date[][] = []
    dates.forEach((date, index) => { const week = Math.floor(index / 7); grouped[week] = [...(grouped[week] ?? []), date] })
    const labels = grouped.map((week, index) => index === 0 || week[0].getMonth() !== grouped[index - 1]?.[0]?.getMonth() ? week[0].toLocaleDateString('en-US', { month: 'short' }) : '')
    return { weeks: grouped, pointsByDate: points, entriesByDate: entries, monthLabels: labels }
  }, [submissions])
  const max = Math.max(...pointsByDate.values(), 1)
  const selectedEntries = selected ? entriesByDate.get(selected) ?? [] : []
  const selectedDate = selected ? new Date(`${selected}T12:00:00`) : null
  const levelFor = (points: number) => points === 0 ? 0 : Math.min(4, Math.ceil((points / max) * 4))
  return <section className="profile-panel profile-activity-panel"><div className="profile-card-heading"><div><span className="profile-kicker">LAST 12 MONTHS</span><h2>Submission activity</h2></div><span className="profile-card-count">{submissions.length} submissions</span></div><div className="profile-heatmap-caption"><span><CalendarDays size={15} /> Each square is one day</span><span className="profile-heatmap-legend"><span>Less</span>{[0, 1, 2, 3, 4].map((level) => <i className={`activity-level-${level}`} key={level} />)}<span>More</span></span></div><div className="profile-heatmap-scroll"><div className="profile-heatmap"><div className="profile-heatmap-months"><span />{monthLabels.map((label, index) => <span key={index}>{label}</span>)}</div><div className="profile-heatmap-body"><div className="profile-weekday-labels"><span>Mon</span><span>Wed</span><span>Fri</span></div><div className="profile-heatmap-grid">{weeks.map((week, weekIndex) => <div className="profile-heatmap-week" key={weekIndex}>{week.map((date) => { const key = dateKey(date); const points = pointsByDate.get(key) ?? 0; const label = `${date.toLocaleDateString('en-US', { dateStyle: 'long' })}: ${points} submission${points === 1 ? '' : 's'}`; return <button type="button" key={key} className={`profile-heat-cell activity-level-${levelFor(points)}`} aria-label={label} title={label} data-tooltip={label} onMouseEnter={() => setSelected(key)} onFocus={() => setSelected(key)} onClick={() => setSelected(key)} /> })}</div>)}</div></div></div></div>{selectedDate ? <div className="profile-activity-detail" aria-live="polite"><strong>{selectedDate.toLocaleDateString('en-US', { dateStyle: 'long' })}</strong>{selectedEntries.length ? <div>{selectedEntries.map((entry) => <span key={entry.id}>{entry.label}<b>{entry.correct ? 'Correct' : 'Attempted'}</b></span>)}</div> : <span>No recorded submissions.</span>}</div> : <p className="profile-activity-hint">Hover or focus a day to inspect submissions.</p>}</section>
}

function ProfileDataNotice({ data }: { data: StudentProfileData }) {
  if (data.source === 'api') return <p className="profile-data-note"><span className="profile-live-dot" /> {data.sourceLabel}. Only records returned for your authenticated account are shown.</p>
  if (data.source === 'browser') return <p className="profile-data-note profile-data-note-warning">Development-only browser data: {data.limitation}</p>
  return <p className="profile-data-note profile-data-note-warning">No submission history is available yet. Complete a question to start building your profile.</p>
}

export function StudentProfilePage() {
  const { session, status } = useAuth()
  const [data, setData] = useState<StudentProfileData | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    if (!session || session.user.role !== 'student') return
    let active = true
    setData(null)
    setError('')
    void loadStudentProfileData(session.user.id).then((next) => { if (active) setData(next) }).catch(() => { if (active) setError('We could not load your submission history. Try again shortly.') })
    return () => { active = false }
  }, [session])
  if (status === 'loading') return <div className="phase-loading">Loading your workspace…</div>
  if (!session || session.user.role !== 'student') return <Navigate to="/classroom" replace />
  const onboarding = session.user.studentOnboarding
  const stats = data ? streakStats(data.submissions) : { activeDays: 0, current: 0, longest: 0 }
  const totalSolved = data ? difficultyOrder.reduce((sum, difficulty) => sum + data.solvedByDifficulty[difficulty], 0) : 0
  const trackedDetail = data?.source === 'api' ? `of ${data?.trackedQuestionCount ?? 0} tracked` : `of ${data?.trackedQuestionCount ?? 0} demo questions`
  return <div className="profile-app"><StudentNav /><main className="profile-main"><Link className="profile-back-link" to="/student/problems"><ArrowRight size={14} /> Back to practice</Link><section className="profile-hero"><div className="profile-identity"><ProfileAvatar name={session.user.name} large /><div><span className="profile-kicker">STUDENT PROFILE</span><h1>{session.user.name}</h1><p><Mail size={14} /> {session.user.email}</p><div className="profile-tags"><span>{onboarding?.currentClass ?? 'Student'}</span><span>{onboarding?.jeeGoal ?? 'JEE preparation'}</span></div></div></div><div className="profile-hero-note"><Target size={18} /><span>Keep showing up.<b>Your practice history belongs to you.</b></span></div></section>{error && <div className="profile-error" role="alert">{error} <button type="button" onClick={() => window.location.reload()}>Retry</button></div>}{!data && !error ? <div className="profile-loading"><LoaderCircle size={20} /> Loading your submission history…</div> : data && <><ProfileDataNotice data={data} /><section className="profile-stats-grid"><StatCard icon={<Check size={17} />} label="Total submissions" value={data.submissions.length} detail="Recorded attempts" tone="mint" /><StatCard icon={<CalendarDays size={17} />} label="Active days" value={stats.activeDays} detail="Days with a submission" tone="blue" /><StatCard icon={<Flame size={17} />} label="Current streak" value={`${stats.current}d`} detail={`Longest ${stats.longest}d`} tone="coral" /><StatCard icon={<Trophy size={17} />} label="Solved" value={totalSolved} detail={trackedDetail} tone="yellow" /></section><ActivityHeatmap submissions={data.submissions} /><SolvedChart solvedByDifficulty={data.solvedByDifficulty} total={data.trackedQuestionCount} source={data.source} /></>}</main></div>
}
