import { useEffect, useState, type FormEvent } from 'react'
import { ArrowLeft, ArrowRight, Check, Clock3, Flag, Lightbulb, Pause, Play, RotateCcw } from 'lucide-react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { StudentNav } from './ProblemsPage'
import { getJeeProblem, listJeeProblems, submitJeeAttempt, type JeeProblem } from '../../services/api'
import './problems.css'

function CircleProgress({ solved, attempting, total }: { solved: number; attempting: number; total: number }) {
  const percentage = total ? Math.round((solved / total) * 100) : 0
  const radius = 56
  const circumference = 2 * Math.PI * radius
  return <div className="topic-progress-card"><div className="progress-ring-wrap"><svg viewBox="0 0 140 140" className="progress-ring"><circle cx="70" cy="70" r={radius} className="progress-ring-track" /><circle cx="70" cy="70" r={radius} className="progress-ring-value" strokeDasharray={circumference} strokeDashoffset={circumference * (1 - percentage / 100)} /></svg><div className="progress-ring-label"><strong>{solved}</strong><span>/{total}</span><small>Solved</small></div></div><div className="progress-attempting">{attempting} Attempting</div></div>
}

export function TopicProblemsPage() {
  const { subject, slug } = useParams()
  const navigate = useNavigate()
  const { session } = useAuth()
  const [problems, setProblems] = useState<JeeProblem[]>([])
  const [error, setError] = useState('')
  useEffect(() => {
    if (!slug) return
    const load = () => listJeeProblems(slug).then(setProblems).catch((reason) => setError(reason instanceof Error ? reason.message : 'Could not load topic'))
    void load()
    window.addEventListener('focus', load)
    return () => window.removeEventListener('focus', load)
  }, [slug])
  if (!session) return <Navigate to="/sign-in" replace />
  const title = problems[0]?.chapter ?? (slug ?? '').split('-').slice(1).join(' ')
  const solved = problems.filter((problem) => problem.solved).length
  const attempting = problems.filter((problem) => problem.attempted && !problem.solved).length
  const counts = { Easy: problems.filter((p) => p.difficulty === 'Easy').length, Medium: problems.filter((p) => p.difficulty === 'Medium').length, Hard: problems.filter((p) => p.difficulty === 'Hard').length }
  return <div className="problems-app"><StudentNav /><main className="topic-page-main"><button className="back-to-problems topic-back" onClick={() => navigate('/student/problems')}><ArrowLeft size={15} /> Topic-wise Problems</button><div className="topic-page-grid"><aside className="topic-progress-sidebar"><div className="topic-icon">{subject === 'physics' ? 'Φ' : subject === 'chemistry' ? '⚗' : '∑'}</div><h1>{title}</h1><p>JEE-style practice set · {problems.length} questions</p><div className="topic-actions"><Button className="practice-button" onClick={() => problems[0] && navigate(`/student/problems/${problems[0].id}`)}><Play size={14} /> Practice</Button><button className="round-action" aria-label="Reset progress"><RotateCcw size={15} /></button></div><CircleProgress solved={solved} attempting={attempting} total={problems.length} /><div className="difficulty-progress"><div><span className="difficulty-label difficulty-easy"><i />Easy</span><b>{counts.Easy}/{problems.length}</b></div><div><span className="difficulty-label difficulty-medium"><i />Medium</span><b>{counts.Medium}/{problems.length}</b></div><div><span className="difficulty-label difficulty-hard"><i />Hard</span><b>{counts.Hard}/{problems.length}</b></div></div></aside><section className="topic-problem-list"><div className="topic-list-header"><div><span className="problems-kicker">PROBLEM SET</span><h2>{title}</h2></div><span className="topic-list-count">{problems.length} questions</span></div>{error && <div className="answer-feedback answer-incorrect">{error}</div>}{problems.map((problem, index) => <button className="topic-problem-row" key={problem.id} onClick={() => navigate(`/student/problems/${problem.id}`)}><span className="topic-problem-number">{index + 1}</span><span className="topic-problem-copy"><b>{problem.title}</b><small>{problem.question_type} · {problem.estimated_minutes} min · {problem.exam_relevance.join(' / ')}</small></span><span className={`difficulty-label difficulty-${problem.difficulty.toLowerCase()}`}><i />{problem.difficulty}</span><span className="topic-problem-status"><Flag size={14} /> {problem.solved ? 'Solved' : problem.attempted ? 'Attempted' : 'Unsolved'}</span><ArrowRight size={15} /></button>)}</section></div></main></div>
}

export function JeeProblemPage() {
  const { id } = useParams()
  const { session } = useAuth()
  const navigate = useNavigate()
  const [problem, setProblem] = useState<JeeProblem | null>(null)
  const [answer, setAnswer] = useState('')
  const [hintUsed, setHintUsed] = useState(false)
  const [outcome, setOutcome] = useState<boolean | null>(null)
  const [seconds, setSeconds] = useState(0)
  const [running, setRunning] = useState(false)
  const [hintIndex, setHintIndex] = useState(-1)
  useEffect(() => { if (!id) return; getJeeProblem(id).then(setProblem).catch(() => setProblem(null)) }, [id])
  useEffect(() => { if (!running) return; const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000); return () => window.clearInterval(timer) }, [running])
  if (!session) return <Navigate to="/sign-in" replace />
  if (!problem) return <div className="phase-loading">Loading problem…</div>
  const submit = async (event: FormEvent) => { event.preventDefault(); if (!answer.trim()) return; try { const attempt = await submitJeeAttempt(problem.id, { answer, time_taken: seconds, hint_used: hintUsed }); setOutcome(Boolean(attempt.correct)); setRunning(false) } catch { setOutcome(null) } }
  const time = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
  return <div className="problems-app"><StudentNav /><main className="problem-detail-main"><button className="back-to-problems" onClick={() => navigate(-1)}><ArrowLeft size={15} /> Back to problem set</button><article className="problem-detail-card"><div className="detail-meta"><span>{problem.subject.toUpperCase()}</span><span>{problem.chapter}</span><span className={`difficulty-label difficulty-${problem.difficulty.toLowerCase()}`}><i />{problem.difficulty}</span><span className={`status-label ${outcome === true ? 'status-solved' : outcome === false ? 'status-attempted' : 'status-unsolved'}`}><i />{outcome === true ? 'Solved' : outcome === false ? 'Attempted' : 'Unsolved'}</span></div><div className="problem-detail-title-row"><div><span className="problems-kicker">{problem.question_type} · {problem.exam_relevance.join(' / ')}</span><h1>{problem.title}</h1></div><span className="attempt-flag"><Flag size={16} /> {outcome === true ? 'Solved' : outcome === false ? 'Attempted' : 'Not attempted'}</span></div><div className="question-statement"><span className="problems-kicker">QUESTION</span><p>{problem.statement}</p></div>{problem.choices && <div className="problem-choice-list">{problem.choices.map((choice) => <label className={`problem-choice ${answer === choice ? 'choice-picked' : ''}`} key={choice}><input type="radio" name="jee-answer" value={choice} checked={answer === choice} onChange={() => { setAnswer(choice); setOutcome(null) }} /><span className="choice-radio" />{choice}</label>)}</div>} {!problem.choices && <Input value={answer} onChange={(event) => { setAnswer(event.target.value); setOutcome(null) }} placeholder="Enter your answer" />}<div className="problem-actions"><Button className="check-answer-button" onClick={submit} disabled={!answer.trim()}><Check size={16} /> Submit answer</Button><button className="hint-button" onClick={() => { setHintUsed(true); setHintIndex((value) => Math.min(value + 1, problem.hints.length - 1)) }}><Lightbulb size={15} /> Hint {hintIndex + 1}/{problem.hints.length}</button></div>{hintIndex >= 0 && <div className="hint-panel"><Lightbulb size={15} /><span>{problem.hints[hintIndex]}</span></div>}{outcome !== null && <div className={`answer-feedback ${outcome ? 'answer-correct' : 'answer-incorrect'}`}><b>{outcome ? 'Solved — nice work.' : 'Attempt recorded. Review the explanation.'}</b><p>{problem.explanation}</p></div>}</article></main></div>
}
