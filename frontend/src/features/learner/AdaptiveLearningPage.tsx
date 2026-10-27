import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { ArrowRight, BookOpenCheck, BrainCircuit, Check, CircleHelp, LoaderCircle, Send, Sparkles } from 'lucide-react'
import { Navigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { StudentNav } from './StudentNav'
import { askTutor, generateWeakQuiz, getAILearningRecommendations, getProgress, startAdaptiveAssessment, submitAdaptiveAttempt, type AdaptiveConcept, type AdaptiveQuestion, type AILearningRecommendation, type LearningCitation, type LearningPathStep } from '../../services/adaptiveApi'
import './adaptive-learning.css'

const subjects = [{ id: 'physics', label: 'Physics' }, { id: 'chemistry', label: 'Chemistry' }, { id: 'mathematics', label: 'Mathematics' }]

export function AdaptiveLearningPage() {
  const { session } = useAuth()
  const [subject, setSubject] = useState('physics')
  const [classLevel, setClassLevel] = useState(11)
  const [concepts, setConcepts] = useState<AdaptiveConcept[]>([])
  const [learningPath, setLearningPath] = useState<LearningPathStep[]>([])
  const [selectedConcept, setSelectedConcept] = useState('')
  const [assessmentId, setAssessmentId] = useState('')
  const [question, setQuestion] = useState<AdaptiveQuestion | null>(null)
  const [nextQuestion, setNextQuestion] = useState<AdaptiveQuestion | null>(null)
  const [questionIndex, setQuestionIndex] = useState(0)
  const [questionStartedAt, setQuestionStartedAt] = useState(() => Date.now())
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState<{ correct: boolean; explanation: string; answerGuide: string } | null>(null)
  const [result, setResult] = useState<{ attempts: number; correct: number; accuracy: number } | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [tutorQuestion, setTutorQuestion] = useState('')
  const [tutor, setTutor] = useState<{ message: string; check_question: string; citations: { source_id: string; citation: string; text: string; score: number }[] } | null>(null)
  const [quizNotice, setQuizNotice] = useState('')
  const [aiRecommendations, setAiRecommendations] = useState<AILearningRecommendation[]>([])
  const [recommendationCitations, setRecommendationCitations] = useState<LearningCitation[]>([])
  const [recommendationNotice, setRecommendationNotice] = useState('')

  const refresh = async () => {
    try {
      const data = await getProgress(subject, classLevel)
      setConcepts(data.concepts)
      setLearningPath(data.learning_path)
      setSelectedConcept((current) => current || data.concepts.find((item) => item.approved_items)?.concept_id || data.concepts[0]?.concept_id || '')
      setError('')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not load learning progress.') }
  }
  useEffect(() => { setSelectedConcept(''); void refresh() }, [subject, classLevel])

  const selected = useMemo(() => concepts.find((concept) => concept.concept_id === selectedConcept), [concepts, selectedConcept])
  if (!session) return <Navigate to="/sign-in" replace />

  const start = async () => {
    setBusy(true); setError(''); setResult(null); setFeedback(null); setAnswer('')
    try {
      const data = await startAdaptiveAssessment(subject, classLevel)
      setAssessmentId(data.assessment_id); setQuestion(data.question); setQuestionIndex(1); setNextQuestion(null); setFeedback(null); setQuestionStartedAt(Date.now())
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not start an assessment.') }
    finally { setBusy(false) }
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!assessmentId || !answer.trim()) return
    setBusy(true); setError('')
    try {
      const data = await submitAdaptiveAttempt(assessmentId, answer, Math.max(0, Math.floor((Date.now() - questionStartedAt) / 1000)))
      setFeedback({ correct: data.correct, explanation: data.explanation, answerGuide: data.answer_guide })
      if (data.completed && data.summary) { setResult(data.summary); setQuestion(null); setAssessmentId(''); await refresh() }
      else if (data.question) { setNextQuestion(data.question); setQuestionIndex(data.index + 1) }
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not save this answer.') }
    finally { setBusy(false) }
  }

  const ask = async (event: FormEvent) => {
    event.preventDefault()
    if (!selected || !tutorQuestion.trim()) return
    setBusy(true); setError(''); setTutor(null)
    try { setTutor(await askTutor({ subject, class_level: classLevel, concept_id: selected.concept_id, question: tutorQuestion, mode: 'explanation' })) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Tutor support is unavailable.') }
    finally { setBusy(false) }
  }

  const makeQuiz = async () => {
    if (!selected) return
    setBusy(true); setError(''); setQuizNotice('')
    try {
      const draft = await generateWeakQuiz({ subject, class_level: classLevel, concept_id: selected.concept_id, item_count: 5 })
      setQuizNotice(`Generated ${draft.question_count} questions. They are saved for teacher review before students can attempt them.`)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not generate a quiz.') }
    finally { setBusy(false) }
  }

  const requestRecommendations = async () => {
    setBusy(true); setError(''); setRecommendationNotice('')
    try {
      const data = await getAILearningRecommendations(subject, classLevel)
      setAiRecommendations(data.recommendations); setRecommendationCitations(data.citations)
      setRecommendationNotice(data.recommendations.length ? `Personalized with ${data.provider}.` : 'You are on track across the mapped concepts. Keep practicing to build more evidence.')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'AI recommendations are unavailable.') }
    finally { setBusy(false) }
  }

  return <div className="adaptive-app"><StudentNav /><main className="adaptive-main">
    <header className="adaptive-heading"><div><span className="adaptive-kicker">YOUR LEARNING SPACE</span><h1>Make your next step count.</h1><p>Practice adapts to your concept-level results. Ask for a cited explanation whenever you get stuck.</p></div><div className="adaptive-heading-mark"><BrainCircuit size={31} /><span>PCM · ADAPTIVE</span></div></header>
    <section className="adaptive-controls" aria-label="Choose subject and class">
      <div className="adaptive-subjects">{subjects.map((item) => <button key={item.id} className={subject === item.id ? 'active' : ''} onClick={() => setSubject(item.id)}>{item.label}</button>)}</div>
      <label>Class <select value={classLevel} onChange={(event) => setClassLevel(Number(event.target.value))}><option value={11}>Class 11</option><option value={12}>Class 12</option></select></label>
    </section>
    {error && <div className="adaptive-alert" role="alert">{error}</div>}
    <section className="adaptive-path-card"><div className="path-title"><span className="adaptive-kicker">YOUR RECOMMENDED PATH</span><b>Small steps, in the right order</b><small>Prerequisites come first. Your results update this path after each assessment.</small><Button variant="neutral" disabled={busy} onClick={() => void requestRecommendations()}>{busy ? <LoaderCircle className="spin" size={15} /> : <Sparkles size={15} />} Get AI study recommendations</Button></div>{learningPath.slice(0, 4).map((step, index) => <article className="path-step" key={step.concept_id}><span className="path-step-number">{String(index + 1).padStart(2, '0')}</span><div><b>{step.name}</b><small>{step.chapter} · {step.action}</small></div><span className={`path-status status-${step.mastery_status}`}>{step.mastery_status.replaceAll('_', ' ')}</span></article>)}{recommendationNotice && <p className="recommendation-status">{recommendationNotice}</p>}{aiRecommendations.map((item) => <article className="ai-recommendation" key={item.concept_id}><b>{item.concept_name} · {item.chapter}</b><p>{item.action}</p><small>{item.reason}</small>{item.source_ids.map((sourceId) => { const source = recommendationCitations.find((citation) => citation.source_id === sourceId); return source ? <details key={sourceId}><summary>NCERT source: {source.citation}</summary><p>{source.text}</p></details> : null })}</article>)}</section>
    <div className="adaptive-grid">
      <section className="adaptive-card progress-card"><div className="adaptive-card-heading"><div><span className="adaptive-kicker">CONCEPT MASTERY</span><h2>Know what to work on</h2></div><BookOpenCheck size={20} /></div>
        {concepts.length ? <div className="concept-progress-list">{concepts.map((concept) => <button key={concept.concept_id} className={`concept-progress-row ${selectedConcept === concept.concept_id ? 'selected' : ''}`} onClick={() => { setSelectedConcept(concept.concept_id); setTutor(null); setResult(null) }}><span className="concept-progress-copy"><b>{concept.name}</b><small>{concept.chapter} · {concept.attempts ?? 0} attempts</small></span><span className={`mastery-pill mastery-${concept.mastery_status ?? 'new'}`}>{concept.attempts ? `${Math.round((concept.accuracy ?? 0) * 100)}%` : 'New'}</span></button>)}</div> : <p className="adaptive-empty">Loading your PCM concept map…</p>}
      </section>
      <section className="adaptive-card practice-card"><div className="adaptive-card-heading"><div><span className="adaptive-kicker">TARGETED ASSESSMENT</span><h2>{question ? `Question ${questionIndex}` : result ? 'Assessment complete' : 'Practice at your pace'}</h2></div><Sparkles size={20} /></div>
        {question ? <form onSubmit={submit} className="adaptive-question"><div className="question-tags"><span>{question.chapter}</span><span>{question.difficulty}</span><span>Bloom · {question.bloom_level}</span></div><p>{question.question}</p><label className="adaptive-answer-label" htmlFor="adaptive-answer">Your answer</label><Input id="adaptive-answer" value={answer} disabled={busy || Boolean(feedback)} onChange={(event) => setAnswer(event.target.value)} placeholder="Show your thinking in a few words" autoComplete="off" />{feedback && <div className={`answer-feedback-box ${feedback.correct ? 'correct' : 'incorrect'}`}><b>{feedback.correct ? 'That matches the answer guide.' : 'Let’s use this as a learning signal.'}</b><p>{feedback.explanation}</p><small>Answer guide: {feedback.answerGuide}</small></div>}{feedback && nextQuestion ? <Button type="button" disabled={busy} className="adaptive-primary" onClick={() => { setQuestion(nextQuestion); setNextQuestion(null); setFeedback(null); setAnswer(''); setQuestionStartedAt(Date.now()) }}>Continue to the next question <ArrowRight size={15} /></Button> : <Button type="submit" disabled={busy || !answer.trim()} className="adaptive-primary">{busy ? <LoaderCircle className="spin" size={16} /> : <Send size={15} />} Submit answer</Button>}</form> : result ? <div className="assessment-result"><span className="result-score">{result.correct}<small> / {result.attempts}</small></span><p>{Math.round(result.accuracy * 100)}% correct. Your progress has been saved and will shape future practice.</p><Button onClick={start} className="adaptive-primary">Try another set <ArrowRight size={15} /></Button></div> : <div className="adaptive-start"><p>{selected?.recommendation ?? 'Start a short assessment. Questions will adapt to your responses and saved learning history.'}</p><Button disabled={busy} onClick={start} className="adaptive-primary">{busy ? <LoaderCircle className="spin" size={16} /> : <ArrowRight size={15} />} Start adaptive practice</Button><small>Questions are teacher-reviewed before they appear here.</small></div>}
      </section>
      <section className="adaptive-card tutor-card"><div className="adaptive-card-heading"><div><span className="adaptive-kicker">AI STUDY ASSISTANT</span><h2>Talk through a hard idea</h2></div><CircleHelp size={20} /></div><p className="tutor-caption">Ask about {selected?.name ?? 'a PCM concept'} and get an explanation grounded in the indexed NCERT text.</p><form className="tutor-form" onSubmit={ask}><Input value={tutorQuestion} onChange={(event) => setTutorQuestion(event.target.value)} placeholder="What part feels confusing?" /><Button disabled={busy || !selected} className="adaptive-primary" aria-label="Ask tutor">{busy ? <LoaderCircle className="spin" size={16} /> : <Send size={15} />}</Button></form>{tutor && <article className="tutor-answer"><p>{tutor.message}</p><b>Check your understanding</b><p>{tutor.check_question}</p><div className="citation-list">{tutor.citations.map((citation) => <details key={citation.source_id}><summary>{citation.citation}</summary><p>{citation.text}</p></details>)}</div></article>}<div className="weak-quiz-action"><span>Need more practice on this concept?</span><Button variant="neutral" onClick={makeQuiz} disabled={busy || !selected}>Generate a quiz <Sparkles size={14} /></Button></div>{quizNotice && <div className="adaptive-success"><Check size={15} />{quizNotice}</div>}</section>
    </div>
  </main></div>
}
