const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...init,
    headers: { 'Content-Type': 'application/json', ...init.headers },
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail ?? 'Rewards are temporarily unavailable.')
  return body as T
}

export type RewardEvent = {
  event_type: string
  points: number
  description: string
  metadata: Record<string, string | number>
  created_at: string
}

export type RewardSummary = {
  coins: number
  month_coins: number
  today_coins: number
  challenge_days_this_month: number
  challenge_days_goal: number
  events: RewardEvent[]
}

export type RewardClassroom = { id: string; name: string; class_level: number }
export type LeaderboardRow = { student_id: string; name: string; coins: number; rank: number }
export type Leaderboard = {
  classrooms: RewardClassroom[]
  classroom: RewardClassroom | null
  period: 'month' | 'all_time'
  leaderboard: LeaderboardRow[]
  my_rank: number | null
}

export function claimDailyCheckIn() {
  return request<{ points_awarded: number; coins: number; already_checked_in: boolean }>('/rewards/check-in', { method: 'POST' })
}

export function getRewardSummary() {
  return request<RewardSummary>('/rewards/summary')
}

export function getLeaderboard(period: 'month' | 'all_time' = 'month', classroomId?: string) {
  const query = new URLSearchParams({ period })
  if (classroomId) query.set('classroom_id', classroomId)
  return request<Leaderboard>(`/rewards/leaderboard?${query.toString()}`)
}
