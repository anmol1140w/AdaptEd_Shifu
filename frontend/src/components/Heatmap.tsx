import { useMemo, useState } from 'react'
import { CalendarDays } from 'lucide-react'
import type { LearningActivity } from '../types'
import { activityLabel, calendarDates, getDateKey } from '../services/storage'

const levels = ['level-0', 'level-1', 'level-2', 'level-3', 'level-4']

export function ContributionHeatmap({ activity, days = 365, compact = false }: { activity: LearningActivity[]; days?: 30 | 90 | 365; compact?: boolean }) {
  const [selected, setSelected] = useState<string | null>(null)
  const dates = useMemo(() => calendarDates(days), [days])
  const byDate = useMemo(() => {
    const map = new Map<string, LearningActivity[]>()
    activity.forEach((event) => {
      const key = getDateKey(event.timestamp)
      map.set(key, [...(map.get(key) ?? []), event])
    })
    return map
  }, [activity])
  const max = Math.max(...[...byDate.values()].map((events) => events.reduce((sum, event) => sum + event.contributionPoints, 0)), 1)
  const selectedEvents = selected ? byDate.get(selected) ?? [] : []
  const weeks: Date[][] = []
  dates.forEach((date, index) => {
    const weekIndex = Math.floor(index / 7)
    if (!weeks[weekIndex]) weeks[weekIndex] = []
    weeks[weekIndex].push(date)
  })
  const monthLabels = weeks.map((week, index) => index === 0 || week[0].getMonth() !== weeks[index - 1]?.[0]?.getMonth() ? week[0].toLocaleDateString('en-US', { month: 'short' }) : '')
  const cellLevel = (points: number) => points === 0 ? 0 : Math.min(4, Math.ceil((points / max) * 4))
  return <div className={`heatmap-wrap ${compact ? 'heatmap-compact' : ''}`}>
    <div className="heatmap-caption"><div><CalendarDays size={15} />{days === 365 ? 'Learning activity' : `${days}-day activity`}</div><div className="heatmap-legend"><span>Less</span>{levels.map((level) => <i className={level} key={level} />)}<span>More</span></div></div>
    <div className="heatmap-scroll"><div className="heatmap"><div className="heatmap-months"><span />{monthLabels.map((label, index) => <span key={index}>{label}</span>)}</div><div className="heatmap-body"><div className="weekday-labels"><span>Mon</span><span>Wed</span><span>Fri</span></div><div className="heatmap-grid">{weeks.map((week, weekIndex) => <div className="heatmap-week" key={weekIndex}>{week.map((date) => { const key = getDateKey(date); const events = byDate.get(key) ?? []; const points = events.reduce((sum, event) => sum + event.contributionPoints, 0); return <button key={key} className={`heat-cell ${levels[cellLevel(points)]}`} aria-label={`${date.toLocaleDateString('en-US', { dateStyle: 'long' })}: ${points} learning points`} title={`${date.toLocaleDateString('en-US', { dateStyle: 'long' })} · ${points} learning points`} onClick={() => setSelected(key)} /> })}</div>)}</div></div></div></div>
    {selected && <div className="heatmap-detail"><div><strong>{new Date(`${selected}T12:00:00`).toLocaleDateString('en-US', { dateStyle: 'long' })}</strong><span>{selectedEvents.reduce((sum, event) => sum + event.contributionPoints, 0)} learning points</span></div><div className="activity-detail-list">{selectedEvents.length ? selectedEvents.map((event) => <span key={event.id}>{event.metadata?.label ?? activityLabel(event.type)} <b>+{event.contributionPoints}</b></span>) : <span>No recorded learning activity.</span>}</div></div>}
  </div>
}
