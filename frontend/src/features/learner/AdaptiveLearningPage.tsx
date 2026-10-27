import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { ArrowRight, BookOpenCheck, BrainCircuit, Check, CircleHelp, LoaderCircle, Send, Sparkles } from 'lucide-react'
import { Navigate, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { StudentNav } from './StudentNav'
import { askTutor, generateWeakQuiz, getAILearningRecommendations, getLearningPreferences, getProgress, getTutorHistory, saveLearningPreferences, startAdaptiveAssessment, submitAdaptiveAttempt, type AdaptiveConcept, type AdaptiveQuestion, type AILearningRecommendation, type GeneratedWeakQuiz, type LearningCitation, type LearningPathStep, type TopicScores, type TutorMemory } from '../../services/adaptiveApi'
import './adaptive-learning.css'

const subjects = [{ id: 'physics', label: 'Physics' }, { id: 'chemistry', label: 'Chemistry' }, { id: 'mathematics', label: 'Mathematics' }]
const bloomLevels = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
const bloomLabel = (level: string) => {
  const normalized = level.toLowerCase()
  const code = bloomLevels.indexOf(normalized) + 1
  return code ? `BT${code} · ${normalized[0].toUpperCase()}${normalized.slice(1)}` : level
}
const tutorModes = [
  { id: 'hint', label: 'Hint', description: 'Nudge me without giving away the answer.' },
  { id: 'explanation', label: 'Explain', description: 'Walk through the concept from the source text.' },
  { id: 'check_question', label: 'Check my thinking', description: 'Help me test my current understanding.' },
] as const

function SourceEvidence({ source }: { source: LearningCitation }) {
  const sourceLabel = source.source_kind === 'official_ncert' ? 'Official NCERT' : source.source_kind === 'legacy_unclassified' ? 'Unclassified source' : 'Saved source'
  return <details className="rag-source"><summary><span>{source.citation}</span><small>{sourceLabel} · similarity {Math.round(source.score * 100)}%</small></summary><p>{source.text}</p><code>{source.source_id}</code></details>
}

export function AdaptiveLearningPage() {
  const { session } = useAuth()
  const navigate = useNavigate()
  const [subject, setSubject] = useState('physics')
  const [classLevel, setClassLevel] = useState(11)
  const [preferencesLoaded, setPreferencesLoaded] = useState(false)
  const [concepts, setConcepts] = useState<AdaptiveConcept[]>([])
  const [learningPath, setLearningPath] = useState<LearningPathStep[]>([])
  const [selectedConcept, setSelectedConcept] = useState('')
  const [assessmentId, setAssessmentId] = useState('')
  const [question, setQuestion] = useState<AdaptiveQuestion | null>(null)
  const [nextQuestion, setNextQuestion] = useState<AdaptiveQuestion | null>(null)
  const [questionIndex, setQuestionIndex] = useState(0)
  const [questionStartedAt, setQuestionStartedAt] = useState(() => Date.now())
  const [answer, setAnswer] = useState('')
  const [assessmentQuestionCount, setAssessmentQuestionCount] = useState(0)
  const [feedback, setFeedback] = useState<{ correct: boolean; explanation: string; answerGuide: string; adaptationReason?: string; questionText: string; submittedAnswer: string; grading: { score: number; method: 'ollama' | 'exact' | 'similarity'; feedback: string } } | null>(null)
  const [result, setResult] = useState<{ attempts: number; correct: number; accuracy: number; topic_scores: TopicScores } | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [tutorQuestion, setTutorQuestion] = useState('')
  const [tutorMode, setTutorMode] = useState<'hint' | 'explanation' | 'check_question'>('explanation')
  const [tutor, setTutor] = useState<{ message: string; check_question: string; citations: LearningCitation[]; provider: string } | null>(null)
  const [tutorHistory, setTutorHistory] = useState<TutorMemory[]>([])
  const [quizResult, setQuizResult] = useState<GeneratedWeakQuiz | null>(null)
  const [aiRecommendations, setAiRecommendations] = useState<AILearningRecommendation[]>([])
  const [recommendationCitations, setRecommendationCitations] = useState<LearningCitation[]>([])
  const [recommendationNotice, setRecommendationNotice] = useState('')

  const refresh = async () => {
    try {
      const data = await getProgress(subject, classLevel)
      setConcepts(data.concepts)
      setLearningPath(data.learning_path)
      setSelectedConcept((current) => current || data.concepts.find((item) => item.available_items)?.concept_id || data.concepts[0]?.concept_id || '')
      setError('')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not load learning progress.') }
  }
  useEffect(() => {
    let active = true
    getLearningPreferences().then(({ preferences }) => {
      if (!active) return
      setSubject(preferences.subject)
      setClassLevel(preferences.class_level)
      setPreferencesLoaded(true)
    }).catch(() => { if (active) setPreferencesLoaded(true) })
    return () => { active = false }
  }, [])
  useEffect(() => {
    if (!preferencesLoaded) return
    const timeout = window.setTimeout(() => { void saveLearningPreferences(subject, classLevel).catch(() => {}) }, 300)
    return () => window.clearTimeout(timeout)
  }, [subject, classLevel, preferencesLoaded])
  useEffect(() => { setSelectedConcept(''); void refresh() }, [subject, classLevel])
  useEffect(() => {
    if (!selectedConcept) { setTutorHistory([]); return }
    let active = true
    getTutorHistory(subject, classLevel, selectedConcept)
      .then((data) => { if (active) setTutorHistory(data.items) })
      .catch(() => { if (active) setTutorHistory([]) })
    return () => { active = false }
  }, [selectedConcept, subject, classLevel])

  const selected = useMemo(() => concepts.find((concept) => concept.concept_id === selectedConcept), [concepts, selectedConcept])
  if (!session) return <Navigate to="/sign-in" replace />

  const start = async () => {
    setBusy(true); setError(''); setResult(null); setFeedback(null); setAnswer('')
    try {
      const data = await startAdaptiveAssessment(subject, classLevel, selected?.concept_id)
      setAssessmentId(data.assessment_id); setQuestion(data.question); setQuestionIndex(1); setNextQuestion(null); setFeedback(null); setQuestionStartedAt(Date.now())
      setAssessmentQuestionCount(data.question_count)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not start an assessment.') }
    finally { setBusy(false) }
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!assessmentId || !answer.trim()) return
    setBusy(true); setError('')
    try {
      const data = await submitAdaptiveAttempt(assessmentId, answer, Math.max(0, Math.floor((Date.now() - questionStartedAt) / 1000)))
      setFeedback({ correct: data.correct, explanation: data.explanation, answerGuide: data.answer_guide, adaptationReason: data.adaptation_reason, questionText: question?.question ?? '', submittedAnswer: answer, grading: data.grading })
      if (data.completed && data.summary) { setResult(data.summary); setQuestion(null); setAssessmentId(''); void refresh() }
      else if (data.question) { setNextQuestion(data.question); setQuestionIndex(data.index + 1) }
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not save this answer.') }
    finally { setBusy(false) }
  }

  const ask = async (event: FormEvent) => {
    event.preventDefault()
    if (!selected || !tutorQuestion.trim()) return
    setBusy(true); setError(''); setTutor(null)
    try {
      const answer = await askTutor({ subject, class_level: classLevel, concept_id: selected.concept_id, question: tutorQuestion, mode: tutorMode })
      setTutor(answer)
      setTutorQuestion('')
      void getTutorHistory(subject, classLevel, selected.concept_id).then((history) => setTutorHistory(history.items)).catch(() => {})
    }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Tutor support is unavailable.') }
    finally { setBusy(false) }
  }

  const makeQuiz = async () => {
    if (!selected) return
    setBusy(true); setError(''); setQuizResult(null)
    try {
      const draft = await generateWeakQuiz({ subject, class_level: classLevel, concept_id: selected.concept_id, item_count: 5 })
      setQuizResult(draft)
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
    <section className="adaptive-path-card"><div className="path-title"><span className="adaptive-kicker">YOUR RECOMMENDED PATH</span><b>Small steps, in the right order</b><small>Prerequisites come first. Your results update this path after each assessment.</small><Button variant="neutral" disabled={busy} onClick={() => void requestRecommendations()}>{busy ? <LoaderCircle className="spin" size={15} /> : <Sparkles size={15} />} Get AI study recommendations</Button></div>{learningPath.slice(0, 4).map((step, index) => <article className="path-step" key={step.concept_id}><span className="path-step-number">{String(index + 1).padStart(2, '0')}</span><div><b>{step.name}</b><small>{step.chapter} · {step.action}</small></div><span className={`path-status status-${step.mastery_status}`}>{step.mastery_status.replaceAll('_', ' ')}</span></article>)}{recommendationNotice && <p className="recommendation-status">{recommendationNotice}</p>}{aiRecommendations.map((item) => <article className="ai-recommendation" key={item.concept_id}><b>{item.concept_name} · {item.chapter}</b><p>{item.action}</p><small>{item.reason}</small>{item.source_ids.map((sourceId) => { const source = recommendationCitations.find((citation) => citation.source_id === sourceId); return source ? <SourceEvidence key={sourceId} source={source} /> : null })}</article>)}</section>
    <div className="adaptive-grid">
      <section className="adaptive-card progress-card"><div className="adaptive-card-heading"><div><span className="adaptive-kicker">CONCEPT MASTERY</span><h2>Know what to work on</h2></div><BookOpenCheck size={20} /></div>
        {concepts.length ? <div className="concept-progress-list">{concepts.map((concept) => <button key={concept.concept_id} className={`concept-progress-row ${selectedConcept === concept.concept_id ? 'selected' : ''}`} onClick={() => { setSelectedConcept(concept.concept_id); setTutor(null); setResult(null) }}><span className="concept-progress-copy"><b>{concept.name}</b><small>{concept.chapter} · {concept.attempts ?? 0} attempts</small></span><span className={`mastery-pill mastery-${concept.mastery_status ?? 'new'}`}>{concept.attempts ? `${Math.round((concept.accuracy ?? 0) * 100)}%` : 'New'}</span></button>)}</div> : <p className="adaptive-empty">Loading your PCM concept map…</p>}
      </section>
      <section className="adaptive-card practice-card"><div className="adaptive-card-heading"><div><span className="adaptive-kicker">TARGETED ASSESSMENT</span><h2>{question ? `Question ${questionIndex}` : result ? 'Assessment complete' : 'Practice at your pace'}</h2></div><Sparkles size={20} /></div>
        {question ? <form onSubmit={submit} className="adaptive-question"><div className="assessment-progress"><div><b>Question {questionIndex}</b><span>of {assessmentQuestionCount}</span></div><div className="assessment-progress-track"><span style={{ width: `${assessmentQuestionCount ? Math.min(100, questionIndex / assessmentQuestionCount * 100) : 0}%` }} /></div></div><div className="question-tags"><span>{question.chapter}</span><span>{question.difficulty}</span><span>{bloomLabel(question.bloom_level)}</span></div><p>{question.question}</p><label className="adaptive-answer-label" htmlFor="adaptive-answer">Your answer</label><textarea id="adaptive-answer" className="adaptive-answer-input" value={answer} disabled={busy || Boolean(feedback)} onChange={(event) => setAnswer(event.target.value)} placeholder="Show your thinking in a few words" rows={3} />{feedback && <div className={`answer-feedback-box ${feedback.correct ? 'correct' : 'incorrect'}`}><b>{feedback.correct ? 'That matches the expected answer.' : 'Let’s use this as a learning signal.'}</b><p>{feedback.explanation}</p><div className="grading-result"><div><b>{feedback.grading.method === 'ollama' ? 'AI concept check' : feedback.grading.method === 'exact' ? 'Direct answer match' : 'Text similarity fallback'}</b><span>{Math.round(feedback.grading.score * 100)}% conceptual match</span></div><p>{feedback.grading.feedback}</p></div><small>Answer guide: {feedback.answerGuide}</small>{feedback.adaptationReason && <small className="adaptation-reason">Next step: {feedback.adaptationReason}</small>}</div>}{feedback && nextQuestion ? <Button type="button" disabled={busy} className="adaptive-primary" onClick={() => { setQuestion(nextQuestion); setNextQuestion(null); setFeedback(null); setAnswer(''); setQuestionStartedAt(Date.now()) }}>Continue to the next question <ArrowRight size={15} /></Button> : <Button type="submit" disabled={busy || !answer.trim()} className="adaptive-primary">{busy ? <LoaderCircle className="spin" size={16} /> : <Send size={15} />} Submit answer</Button>}</form> : result ? <div className="assessment-result"><span className="result-score">{result.correct}<small> / {result.attempts}</small></span><p>{Math.round(result.accuracy * 100)}% correct. Your answers shaped the next questions in this practice set.</p>{feedback && <article className={`final-answer-review ${feedback.correct ? 'correct' : 'incorrect'}`}><span className="adaptive-kicker">FINAL ANSWER · {feedback.correct ? 'CORRECT' : 'REVIEW THIS ONE'}</span><b>{feedback.questionText}</b><p>Your answer: {feedback.submittedAnswer || 'No answer entered'}</p><p>{feedback.explanation}</p><div className="grading-result"><div><b>{feedback.grading.method === 'ollama' ? 'AI concept check' : feedback.grading.method === 'exact' ? 'Direct answer match' : 'Text similarity fallback'}</b><span>{Math.round(feedback.grading.score * 100)}% conceptual match</span></div><p>{feedback.grading.feedback}</p></div><small>Expected answer: {feedback.answerGuide}</small></article>}<Button onClick={start} className="adaptive-primary">Try another set <ArrowRight size={15} /></Button><button type="button" className="ai-tutoring-cta" onClick={() => navigate('/student/ai-tutoring', { state: { subject, classLevel, topicScores: result.topic_scores, summary: { attempts: result.attempts, correct: result.correct, accuracy: result.accuracy } } })}><span className="ai-tutoring-icon"><Sparkles size={18} /></span><span><b>AI tutoring</b><small>Get help shaped by your topic scores</small></span><ArrowRight size={17} /></button></div> : <div className="adaptive-start"><p>{selected?.recommendation ?? 'Start a short assessment. Questions will adapt to your responses and saved learning history.'}</p>{(selected?.available_items ?? 0) === 0 ? <div className="adaptive-no-questions" role="status"><b>No practice questions are available yet.</b><span>Ask your teacher to approve questions, or wait for the starter bank to load.</span></div> : <><Button disabled={busy || !selected} onClick={start} className="adaptive-primary">{busy ? <LoaderCircle className="spin" size={16} /> : <ArrowRight size={15} />} Start adaptive practice</Button><small>{selected?.available_items ?? 0} starter questions available for {selected?.name ?? 'this concept'}.</small></>}</div>}
      </section>
      <section className="adaptive-card tutor-card"><div className="adaptive-card-heading"><div><span className="adaptive-kicker">RETRIEVAL-GROUNDED AI</span><h2>Study with your NCERT sources</h2></div><CircleHelp size={20} /></div><p className="tutor-caption">Choose how you want help with <b>{selected?.name ?? 'a PCM concept'}</b>. AdaptEd retrieves relevant indexed passages, then asks Ollama to answer from that evidence. Your tutor history is saved to your account.</p><div className="tutor-modes" role="group" aria-label="Choose tutor response style">{tutorModes.map((mode) => <button key={mode.id} type="button" className={tutorMode === mode.id ? 'active' : ''} aria-pressed={tutorMode === mode.id} title={mode.description} onClick={() => setTutorMode(mode.id)}>{mode.label}</button>)}</div><form className="tutor-form" onSubmit={ask}><Input value={tutorQuestion} onChange={(event) => setTutorQuestion(event.target.value)} placeholder={tutorMode === 'hint' ? 'Where are you getting stuck? I’ll give a nudge.' : tutorMode === 'check_question' ? 'What have you tried or what do you think is happening?' : 'What part feels confusing?'} /><Button disabled={busy || !selected || tutorQuestion.trim().length < 3} className="adaptive-primary" aria-label="Ask tutor">{busy ? <LoaderCircle className="spin" size={16} /> : <Send size={15} />}</Button></form>{tutor && <article className="tutor-answer"><div className="rag-answer-meta"><span>Grounded answer</span><small>{tutor.provider}</small></div><p>{tutor.message}</p><b>Check your understanding</b><p>{tutor.check_question}</p><div className="citation-list"><h3>Retrieved NCERT evidence · {tutor.citations.length} sources</h3>{tutor.citations.map((citation) => <SourceEvidence key={citation.source_id} source={citation} />)}</div></article>}{tutorHistory.length > 0 && <details className="tutor-history"><summary>Saved tutor history · {tutorHistory.length} exchanges</summary><div className="tutor-history-list">{tutorHistory.map((turn) => <article key={turn.id}><small>{turn.mode.replaceAll('_', ' ')} · {new Date(turn.created_at).toLocaleString()}</small><b>You asked</b><p>{turn.question}</p><b>AdaptEd</b><p>{turn.message}</p><b>Check your understanding</b><p>{turn.check_question}</p><div className="citation-list"><h3>Saved evidence · {turn.sources.length} sources</h3>{turn.sources.map((source) => <SourceEvidence key={source.source_id} source={source} />)}</div></article>)}</div></details>}<div className="weak-quiz-action"><span>Need more practice on {selected?.name ?? 'this concept'}?</span><Button variant="neutral" onClick={makeQuiz} disabled={busy || !selected}>{busy ? <LoaderCircle className="spin" size={14} /> : <Sparkles size={14} />} Generate cited quiz</Button></div>{quizResult && <div className="adaptive-success quiz-result"><Check size={15} /><div><b>{quizResult.question_count} question drafts created</b><p>Saved for teacher review. Once approved, they can be added to the practice bank.</p><small>Generated with {quizResult.status.replaceAll('_', ' ')} · Draft ID {quizResult.id}</small><div className="citation-list"><h3>Sources used for this quiz · {quizResult.citations.length}</h3>{quizResult.citations.map((citation) => <SourceEvidence key={citation.source_id} source={citation} />)}</div></div></div>}</section>
    </div>
  </main></div>
}
