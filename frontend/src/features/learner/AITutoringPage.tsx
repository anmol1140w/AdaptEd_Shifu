import { useMemo, useState, type FormEvent } from 'react'
import { ArrowLeft, ArrowRight, BrainCircuit, LoaderCircle, Send, Sparkles } from 'lucide-react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { askTutor, type LearningCitation, type TopicScores } from '../../services/adaptiveApi'
import { StudentNav } from './StudentNav'
import './adaptive-learning.css'

type TutorRouteState = {
  subject: string
  classLevel: number
  topicScores: TopicScores
  summary: { attempts: number; correct: number; accuracy: number }
}

function SourceEvidence({ source }: { source: LearningCitation }) {
  return <details className="rag-source"><summary>{source.citation} · {Math.round(source.score * 100)}% match</summary><p>{source.text}</p></details>
}

export function AITutoringPage() {
  const { session } = useAuth()
  const location = useLocation()
  const routeState = location.state as TutorRouteState | null
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [answer, setAnswer] = useState<{ message: string; check_question: string; citations: LearningCitation[]; provider: string } | null>(null)
  const topicScores = routeState?.topicScores
  const weakestTopic = useMemo(() => topicScores
    ? Object.entries(topicScores).sort(([, left], [, right]) => left.accuracy - right.accuracy)[0]
    : undefined, [topicScores])

  if (!session) return <Navigate to="/sign-in" replace />
  if (!routeState || !topicScores || !weakestTopic) return <Navigate to="/student/learn" replace />

  const ask = async (event: FormEvent) => {
    event.preventDefault()
    if (!question.trim()) return
    setBusy(true)
    setError('')
    setAnswer(null)
    try {
      const response = await askTutor({
        subject: routeState.subject,
        class_level: routeState.classLevel,
        concept_id: weakestTopic[0],
        question,
        mode: 'explanation',
        topic_scores: topicScores,
      })
      setAnswer(response)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'AI tutoring is unavailable right now.')
    } finally {
      setBusy(false)
    }
  }

  return <div className="adaptive-app"><StudentNav /><main className="adaptive-main">
    <Link to="/student/learn" className="ai-tutoring-back"><ArrowLeft size={15} /> Back to learning</Link>
    <header className="adaptive-heading"><div><span className="adaptive-kicker">AI TUTORING · {routeState.subject.toUpperCase()} · CLASS {routeState.classLevel}</span><h1>Let’s work on what needs you.</h1><p>Your assessment scores are included as learning context. Ask a question and the tutor will use NCERT evidence to guide the explanation.</p></div><div className="adaptive-heading-mark"><BrainCircuit size={31} /><span>LEARN WITH CONTEXT</span></div></header>
    {error && <div className="adaptive-alert" role="alert">{error}</div>}
    <div className="ai-tutoring-layout">
      <section className="adaptive-card ai-tutoring-focus"><span className="adaptive-kicker">ASSESSMENT SIGNAL</span><h2>{routeState.summary.correct} of {routeState.summary.attempts} correct</h2><p>{Math.round(routeState.summary.accuracy * 100)}% overall accuracy · starting with your lowest-scoring topic.</p>
        <div className="topic-score-list">{Object.entries(topicScores).map(([conceptId, score]) => <article key={conceptId} className={conceptId === weakestTopic[0] ? 'topic-score-row topic-score-focus' : 'topic-score-row'}><span><b>{score.topic}</b><small>{score.correct}/{score.attempts} correct · mastery {Math.round(score.mastery_score * 100)}%</small></span><strong>{Math.round(score.accuracy * 100)}%</strong></article>)}</div>
        <details className="topic-score-json"><summary>View topic score dictionary</summary><pre>{JSON.stringify(topicScores, null, 2)}</pre></details>
      </section>
      <section className="adaptive-card ai-tutoring-chat"><div className="adaptive-card-heading"><div><span className="adaptive-kicker">RETRIEVAL-GROUNDED SUPPORT</span><h2>Ask about {weakestTopic[1].topic}</h2></div><Sparkles size={20} /></div><p className="tutor-caption">The lowest-scoring topic is preselected. Your topic score dictionary is sent with the request so the tutor can focus its help.</p>
        <form className="tutor-form" onSubmit={ask}><Input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={`What would you like help with in ${weakestTopic[1].topic}?`} /><Button disabled={busy || question.trim().length < 3} className="adaptive-primary" aria-label="Ask AI tutor">{busy ? <LoaderCircle className="spin" size={16} /> : <Send size={15} />}</Button></form>
        {answer && <article className="tutor-answer"><div className="rag-answer-meta"><span>Grounded answer</span><small>{answer.provider}</small></div><p>{answer.message}</p><b>Check your understanding</b><p>{answer.check_question}</p><div className="citation-list"><h3>Retrieved NCERT evidence · {answer.citations.length} sources</h3>{answer.citations.map((citation) => <SourceEvidence key={citation.source_id} source={citation} />)}</div></article>}
      </section>
    </div>
    <Link to="/student/learn" className="ai-tutoring-next">Return to your learning page <ArrowRight size={15} /></Link>
  </main></div>
}
