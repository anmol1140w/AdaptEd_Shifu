import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, Search } from 'lucide-react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { listJeeTopics, type JeeTopic } from '../../services/api'
import { StudentNav } from './StudentNav'
import './problems.css'

const subjects = [
  { id: 'physics', label: 'Physics', color: 'subject-physics' },
  { id: 'chemistry', label: 'Chemistry', color: 'subject-chemistry' },
  { id: 'mathematics', label: 'Mathematics', color: 'subject-mathematics' },
] as const

export function TopicWiseProblemsPage() {
  const { session } = useAuth()
  const navigate = useNavigate()
  const [subject, setSubject] = useState<(typeof subjects)[number]['id']>('physics')
  const [query, setQuery] = useState('')
  const [topics, setTopics] = useState<JeeTopic[]>([])
  const [error, setError] = useState('')
  useEffect(() => { listJeeTopics().then(setTopics).catch((reason) => setError(reason instanceof Error ? reason.message : 'Could not load topics')) }, [])
  const visible = useMemo(() => topics.filter((topic) => topic.subject === subject && topic.name.toLowerCase().includes(query.trim().toLowerCase())), [query, subject, topics])
  if (!session) return <Navigate to="/sign-in" replace />
  return <div className="problems-app"><StudentNav /><main className="problems-main"><div className="problems-heading"><div><span className="problems-kicker">STUDENT WORKSPACE / PROBLEMS</span><h1>Problems</h1><p>Choose a subject, then practise by topic.</p></div><div className="problem-count-box"><b>{visible.length}</b><span>topics</span></div></div><section className="topic-wise-panel"><div className="subject-tabs" role="tablist" aria-label="Choose subject">{subjects.map((item) => <button key={item.id} className={`subject-tab ${subject === item.id ? 'subject-tab-active' : ''}`} onClick={() => setSubject(item.id)}><span className={`subject-dot ${item.color}`} />{item.label}</button>)}</div><label className="topic-search"><Search size={16} /><Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search topics" /></label>{error && <div className="answer-feedback answer-incorrect">{error}</div>}<div className="topic-wise-list">{visible.map((topic) => <button className="topic-wise-row" key={topic.id} onClick={() => navigate(`/student/topics/${topic.subject}/${topic.slug}`)}><span><b>{topic.name}</b><small>{topic.problem_count} questions · 2 per topic</small></span><ArrowRight size={16} /></button>)}</div></section></main></div>
}
