import { useEffect, useState, type FormEvent } from 'react'
import { ArrowRight, Check, Clock3, Play } from 'lucide-react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useAuth } from '../../app/AuthProvider'
import { StudentNav } from './StudentNav'
import { getJeeProblem, listJeeProblems, listJeeTopics, studentQuizDetail, submitJeeAttempt, type JeeProblem, type JeeTopic } from '../../services/api'
import './problems.css'

export function TopicQuizzesPage() {
  const { session } = useAuth()
  const navigate = useNavigate()
  const [topics, setTopics] = useState<JeeTopic[]>([])
  const [subject, setSubject] = useState('physics')
  const [error, setError] = useState('')
  useEffect(() => { listJeeTopics().then(setTopics).catch((reason) => setError(reason instanceof Error ? reason.message : 'Could not load quizzes')) }, [])
  const visible = topics.filter((topic) => topic.subject === subject)
  if (!session) return <Navigate to="/sign-in" replace />
  return <div className="problems-app"><StudentNav /><main className="problems-main"><div className="problems-heading"><div><span className="problems-kicker">STUDENT WORKSPACE / QUIZZES</span><h1>Topic quizzes</h1><p>Each quiz uses the same two questions stored for that topic.</p></div><div className="problem-count-box"><b>{visible.length}</b><span>quizzes</span></div></div><div className="subject-tabs quiz-subject-tabs">{['physics', 'chemistry', 'mathematics'].map((item) => <button key={item} className={`subject-tab ${subject === item ? 'subject-tab-active' : ''}`} onClick={() => setSubject(item)}>{item[0].toUpperCase() + item.slice(1)}</button>)}</div>{error && <div className="answer-feedback answer-incorrect">{error}</div>}<div className="topic-quiz-list">{visible.map((topic) => <article className="topic-quiz-card" key={topic.id}><div><span className="problems-kicker">{topic.subject.toUpperCase()}</span><h2>{topic.name}</h2><p>{topic.problem_count} questions · shared topic bank</p></div><Button className="practice-button" onClick={() => navigate(`/student/quizzes/topic/${topic.subject}/${topic.slug}`)}><Play size={14} /> Attempt quiz</Button></article>)}</div></main></div>
}

export function TopicQuizAttemptPage() {
  const { subject, slug } = useParams()
  const { session } = useAuth()
  const navigate = useNavigate()
  const [problems, setProblems] = useState<JeeProblem[]>([])
  const [index, setIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [startedAt] = useState(() => Date.now())
  const [finished, setFinished] = useState(false)
  const [score, setScore] = useState(0)
  const [seconds, setSeconds] = useState(0)
  useEffect(() => { if (!slug) return; listJeeProblems(slug).then(async (rows) => setProblems(await Promise.all(rows.map((row) => getJeeProblem(row.id))))).catch(() => setProblems([])) }, [slug])
  useEffect(() => { if (finished) return; const timer = window.setInterval(() => setSeconds(Math.floor((Date.now() - startedAt) / 1000)), 1000); return () => window.clearInterval(timer) }, [finished, startedAt])
  const current = problems[index]
  const time = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
  const submit = async (event: FormEvent) => { event.preventDefault(); if (!current || !answer.trim()) return; const attempt = await submitJeeAttempt(current.id, { answer, time_taken: seconds, hint_used: false }); setScore((value) => value + (attempt.correct ? 1 : 0)); if (index >= problems.length - 1) setFinished(true); else { setIndex((value) => value + 1); setAnswer('') } }
  if (!session) return <Navigate to="/sign-in" replace />
  if (!current && !finished) return <div className="phase-loading">Loading quiz…</div>
  return <div className="problems-app"><StudentNav /><main className="problem-detail-main">{finished ? <article className="problem-detail-card quiz-result-card"><span className="problems-kicker">QUIZ COMPLETE</span><h1>{slug?.split('-').slice(1).join(' ')}</h1><p className="quiz-score-large">{score} / {problems.length} correct</p><Button className="check-answer-button" onClick={() => navigate(`/student/topics/${subject}/${slug}`)}>Back to topic <ArrowRight size={15} /></Button></article> : <article className="problem-detail-card"><div className="detail-meta"><span>QUESTION {index + 1} / {problems.length}</span><span>{current?.difficulty}</span></div><h1>{current?.title}</h1><div className="question-statement"><span className="problems-kicker">QUIZ QUESTION</span><p>{current?.statement}</p></div><form className="answer-form" onSubmit={submit}>{current?.choices?.map((choice) => <label className={`problem-choice ${answer === choice ? 'choice-picked' : ''}`} key={choice}><input type="radio" name="quiz-answer" value={choice} checked={answer === choice} onChange={() => setAnswer(choice)} /><span className="choice-radio" />{choice}</label>)}<Button className="check-answer-button" type="submit" disabled={!answer}><Check size={15} /> Submit and continue</Button></form></article>}</main></div>
}

export function TeacherQuizAttemptPage() {
  const { quizId } = useParams()
  const { session } = useAuth()
  const navigate = useNavigate()
  const [quiz, setQuiz] = useState<Awaited<ReturnType<typeof studentQuizDetail>> | null>(null)
  const [index, setIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [score, setScore] = useState(0)
  const [finished, setFinished] = useState(false)
  useEffect(() => { if (quizId) studentQuizDetail(quizId).then(setQuiz).catch(() => setQuiz(null)) }, [quizId])
  if (!session) return <Navigate to="/sign-in" replace />
  if (!quiz) return <div className="phase-loading">Loading quiz…</div>
  const question = quiz.questions[index]
  const submit = async (event: FormEvent) => { event.preventDefault(); if (!answer.trim()) return; const correct = answer.trim().toLowerCase() === question.answer.trim().toLowerCase(); setScore((value) => value + (correct ? 1 : 0)); if (index === quiz.questions.length - 1) setFinished(true); else { setIndex((value) => value + 1); setAnswer('') } }
  return <div className="problems-app"><StudentNav /><main className="problem-detail-main"><article className="problem-detail-card">{finished ? <><span className="problems-kicker">QUIZ COMPLETE</span><h1>{quiz.title}</h1><p className="quiz-score-large">{score} / {quiz.questions.length} correct</p><Button className="check-answer-button" onClick={() => navigate('/student/quizzes')}>Back to quizzes <ArrowRight size={15} /></Button></> : <><div className="detail-meta"><span>QUESTION {index + 1} / {quiz.questions.length}</span><span>{quiz.difficulty}</span></div><h1>{quiz.title}</h1><div className="question-statement"><span className="problems-kicker">CLASSROOM QUIZ</span><p>{question.prompt}</p></div><form className="answer-form" onSubmit={submit}>{question.choices.map((choice) => <label className={`problem-choice ${answer === choice ? 'choice-picked' : ''}`} key={choice}><input type="radio" name="teacher-quiz-answer" value={choice} checked={answer === choice} onChange={() => setAnswer(choice)} /><span className="choice-radio" />{choice}</label>)}<Button className="check-answer-button" type="submit" disabled={!answer}>Submit and continue <ArrowRight size={15} /></Button></form></>}</article></main></div>
}
