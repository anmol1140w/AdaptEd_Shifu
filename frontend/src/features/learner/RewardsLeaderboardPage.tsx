import { useEffect, useState } from 'react'
import { Crown, Flame, Medal, Sparkles, Target, Trophy, Users } from 'lucide-react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../app/AuthProvider'
import { StudentNav } from './StudentNav'
import { claimDailyCheckIn, getLeaderboard, getRewardSummary, type Leaderboard, type RewardSummary } from '../../services/rewardsApi'
import './rewards.css'

const rewardNames: Record<string, string> = {
  daily_check_in: 'Daily check-in',
  problem_solved: 'Solved a practice problem',
  assessment_daily_reward: 'Completed a quiz or assessment',
  teacher_quiz_first: 'Completed a new teacher quiz',
  teacher_quiz_week: 'Weekly quiz participation',
  external_quiz: 'Connected quiz completed',
  external_quiz_week: 'Weekly quiz participation',
  mock_assessment_fortnight: 'Mock assessment challenge',
  quiz_assessment_combo: 'Quiz + assessment weekly bonus',
  monthly_25_days: '25-day challenge bonus',
  monthly_full: 'Full-month challenge bonus',
  ai_tutor_daily: 'First AI tutor question today',
}

export function RewardsLeaderboardPage() {
  const { session } = useAuth()
  const [summary, setSummary] = useState<RewardSummary | null>(null)
  const [board, setBoard] = useState<Leaderboard | null>(null)
  const [period, setPeriod] = useState<'month' | 'all_time'>('month')
  const [classroomId, setClassroomId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    void (async () => {
      try {
        if (session?.user.role === 'student') await claimDailyCheckIn()
        const [summaryData, boardData] = await Promise.all([
          getRewardSummary(),
          getLeaderboard(period, classroomId || undefined),
        ])
        if (!active) return
        setSummary(summaryData)
        setBoard(boardData)
        if (!classroomId && boardData.classroom) setClassroomId(boardData.classroom.id)
      } catch (reason) {
        if (active) setError(reason instanceof Error ? reason.message : 'Rewards could not be loaded.')
      } finally {
        if (active) setLoading(false)
      }
    })()
    return () => { active = false }
  }, [session?.user.id, session?.user.role, period, classroomId])

  if (!session) return <Navigate to="/sign-in" replace />
  const teacher = session.user.role === 'teacher'
  const challengeGoal = summary?.challenge_days_goal ?? 25
  const challengeDays = summary?.challenge_days_this_month ?? 0
  const progress = Math.min(100, Math.round((challengeDays / Math.max(challengeGoal, 1)) * 100))

  return <div className="rewards-app">
    <StudentNav />
    <main className="rewards-main">
      <header className="rewards-hero">
        <div><span className="rewards-kicker">ADAPTED · LEARN, PRACTISE, RISE</span><h1>{teacher ? 'Your classroom leaderboard.' : 'Every practice step counts.'}</h1><p>{teacher ? 'See who is showing up, practising consistently, and leading the class.' : 'Earn AdaptCoins for steady practice, then see how your classroom is moving together.'}</p></div>
        <div className="rewards-hero-stamp"><Trophy size={34} /><b>{teacher ? 'CLASS RANK' : 'KEEP GOING'}</b><span>{teacher ? 'STUDENT MOMENTUM' : 'COINS + STREAKS'}</span></div>
      </header>

      {error && <div className="rewards-alert" role="alert">{error}</div>}
      {loading && !summary ? <div className="rewards-loading">Loading your rewards…</div> : <>
        {!teacher && <section className="rewards-metrics" aria-label="Points summary">
          <article className="rewards-balance"><span><Sparkles size={16} /> {teacher ? 'YOUR CLASSROOM SIGNAL' : 'YOUR ADAPTCOINS'}</span><strong>{summary?.coins ?? 0}</strong><small>{teacher ? 'Coins are earned by students.' : 'Persistent points saved to your account.'}</small></article>
          <article><span><Flame size={16} /> THIS MONTH</span><strong>{summary?.month_coins ?? 0}</strong><small>AdaptCoins earned</small></article>
          <article><span><Target size={16} /> CHALLENGE DAYS</span><strong>{challengeDays}<i> / {challengeGoal}</i></strong><div className="rewards-progress"><span style={{ width: `${progress}%` }} /></div><small>{challengeDays >= challengeGoal ? '25-day bonus reached' : `${Math.max(0, challengeGoal - challengeDays)} more active days for the bonus`}</small></article>
        </section>}

        <div className="rewards-layout">
          <section className="rewards-board-card">
            <div className="rewards-section-heading"><div><span className="rewards-kicker">CLASSROOM RANKS</span><h2>Leaderboard</h2></div><Trophy size={24} /></div>
            <div className="rewards-board-controls">
              {board?.classrooms && board.classrooms.length > 1 && <label>Classroom<select aria-label="Select classroom" value={classroomId || board.classroom?.id || ''} onChange={(event) => setClassroomId(event.target.value)}>{board.classrooms.map((classroom) => <option value={classroom.id} key={classroom.id}>{classroom.name} · Class {classroom.class_level}</option>)}</select></label>}
              <div className="rewards-period-tabs" role="group" aria-label="Leaderboard period"><button type="button" aria-pressed={period === 'month'} className={period === 'month' ? 'active' : ''} onClick={() => setPeriod('month')}>This month</button><button type="button" aria-pressed={period === 'all_time'} className={period === 'all_time' ? 'active' : ''} onClick={() => setPeriod('all_time')}>All time</button></div>
            </div>
            {board?.classroom && <p className="rewards-class-label"><Users size={14} /> {board.classroom.name} · Class {board.classroom.class_level}</p>}
            {board?.leaderboard.length ? <div className="leaderboard-list">{board.leaderboard.map((student) => <article className={`leaderboard-row ${student.student_id === session.user.id ? 'leaderboard-you' : ''} ${student.rank <= 3 ? `leaderboard-rank-${student.rank}` : ''}`} key={student.student_id}><span className="leaderboard-rank">{student.rank === 1 ? <Crown size={19} /> : student.rank <= 3 ? <Medal size={18} /> : String(student.rank).padStart(2, '0')}</span><span className="leaderboard-name">{student.name}{student.student_id === session.user.id && <small>YOU</small>}</span><b>{student.coins}<small> coins</small></b></article>)}</div> : <div className="rewards-empty"><Users size={25} /><b>{board?.classroom ? 'No student points yet.' : 'Join a classroom to see your leaderboard.'}</b><span>{teacher ? 'Students in your classroom will appear after they check in or complete a practice activity.' : 'Your points stay saved while you build your place in class.'}</span></div>}
            {board?.my_rank && !board.leaderboard.some((student) => student.student_id === session.user.id) && <p className="rewards-your-rank">Your place: <b>#{board.my_rank}</b></p>}
          </section>

          <aside className="rewards-side-column">
            {!teacher && <section className="monthly-challenge-card"><span className="rewards-kicker">MONTHLY CHALLENGE</span><h2>{challengeDays} active days</h2><p>Complete a quiz, assessment, or problem on 25 different days this month.</p><div className="rewards-progress"><span style={{ width: `${progress}%` }} /></div><b>{challengeDays >= challengeGoal ? '+25 AdaptCoins unlocked' : `${progress}% to +25 AdaptCoins`}</b><small>Complete every day in a full month to earn 25 more bonus coins.</small></section>}
            <section className="coin-rules-card"><span className="rewards-kicker">WAYS TO EARN</span><h2>Small wins add up.</h2><ul>
              <li><span>Daily check-in</span><b>1 coin / day</b></li>
              <li><span>Correct practice problem</span><b>10 / problem</b></li>
              <li><span>Finish an adaptive assessment</span><b>10 / day</b></li>
              <li><span>Finish a new teacher quiz</span><b>10 / quiz</b></li>
              <li><span>Join a quiz this week</span><b>+5 / week</b></li>
              <li><span>Finish a mock this fortnight</span><b>+5</b></li>
              <li><span>Quiz + assessment in same week</span><b>+35 bonus</b></li>
              <li><span>First successful AI tutor question</span><b>1 coin / day</b></li>
              <li><span>25 challenge days this month</span><b>+25 bonus</b></li>
            </ul><small>Repeat submissions cannot repeatedly claim the same quiz, problem, daily assessment, or period bonus.</small></section>
          </aside>
        </div>

        {!teacher && <section className="rewards-history-card"><div className="rewards-section-heading"><div><span className="rewards-kicker">YOUR RECENT WINS</span><h2>Coin history</h2></div><Sparkles size={22} /></div>{summary?.events.length ? <div className="coin-history-list">{summary.events.map((event, index) => <article key={`${event.event_type}-${event.created_at}-${index}`}><span className="coin-history-icon"><Sparkles size={15} /></span><b>{rewardNames[event.event_type] ?? event.description}</b><time>{new Date(event.created_at).toLocaleDateString()}</time><strong>+{event.points}</strong></article>)}</div> : <p className="rewards-empty-inline">Your first check-in or practice reward will show here.</p>}</section>}
      </>}
    </main>
  </div>
}
