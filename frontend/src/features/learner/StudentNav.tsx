import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ChevronDown, LogOut } from 'lucide-react'
import { useAuth } from '../../app/AuthProvider'
import { claimDailyCheckIn } from '../../services/rewardsApi'
import './problems.css'

export function StudentNav() {
  const { session, signOut } = useAuth()
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const [profileOpen, setProfileOpen] = useState(false)

  useEffect(() => {
    if (session?.user.role === 'student') {
      void claimDailyCheckIn().catch(() => {})
    }
  }, [session?.user.id, session?.user.role])

  if (!session) return null

  const onLearning = pathname.startsWith('/student/learn')
  const onProblems = pathname.startsWith('/student/problems')
  const onQuizzes = pathname.startsWith('/student/quizzes')
  const onLeaderboard = pathname.startsWith('/leaderboard')

  const initials = session.user.name
    .split(/\s+/)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  return (
    <header className="student-nav">
      <Link
        to="/student/learn"
        className="student-brand"
        aria-label="AdaptEd learning home"
      >
        <span className="student-brand-mark">A</span>
        <span>
          Adapt<span>Ed</span>
        </span>
      </Link>

      <nav className="student-links" aria-label="Student navigation">
        <Link
          className={`student-nav-link ${onLearning ? 'nav-current' : ''}`}
          to="/student/learn"
          aria-current={onLearning ? 'page' : undefined}
        >
          My learning
        </Link>

        <Link
          className={`student-nav-link ${onProblems ? 'nav-current' : ''}`}
          to="/student/problems"
          aria-current={onProblems ? 'page' : undefined}
        >
          Problems
        </Link>

        <Link
          className={`student-nav-link ${onQuizzes ? 'nav-current' : ''}`}
          to="/student/quizzes"
          aria-current={onQuizzes ? 'page' : undefined}
        >
          Quizzes
        </Link>

        <Link
          className={`student-nav-link ${onLeaderboard ? 'nav-current' : ''}`}
          to="/leaderboard"
          aria-current={onLeaderboard ? 'page' : undefined}
        >
          Leaderboard
        </Link>

        {session.user.role === 'teacher' && (
          <Link
            className={`student-nav-link ${
              pathname.startsWith('/teacher') ? 'nav-current' : ''
            }`}
            to="/teacher"
          >
            Teacher view
          </Link>
        )}
      </nav>

      <div className="student-profile-wrap">
        <button
          className={`student-profile-trigger ${
            profileOpen ? 'profile-open' : ''
          }`}
          aria-expanded={profileOpen}
          aria-haspopup="menu"
          onClick={() => setProfileOpen((open) => !open)}
        >
          <span className="student-avatar">{initials}</span>
          <span className="profile-name">Profile</span>
          <ChevronDown size={15} />
        </button>

        {profileOpen && (
          <div className="student-profile-menu" role="menu">
            <div className="profile-menu-identity">
              <b>{session.user.name}</b>
              <small>{session.user.email}</small>
            </div>

            <Link
              role="menuitem"
              to="/student/profile"
              onClick={() => setProfileOpen(false)}
            >
              View profile
            </Link>

            <button
              role="menuitem"
              onClick={() => {
                signOut()
                navigate('/', { replace: true })
              }}
            >
              <LogOut size={15} /> Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}