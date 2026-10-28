import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { ArrowRight, BookOpenCheck, BrainCircuit, Check, CircleHelp, LoaderCircle, Send, Sparkles } from 'lucide-react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { StudentNav } from './StudentNav'
import { TutorAnswerText } from './TutorAnswerText'
import { askTutor, generateWeakQuiz, getAILearningRecommendations, getLearningPreferences, getProgress, getTutorHistory, resumeAdaptiveAssessment, saveLearningPreferences, startAdaptiveAssessment, submitAdaptiveAttempt, type AdaptiveConcept, type AdaptiveQuestion, type AILearningRecommendation, type AssessmentSummary, type GeneratedWeakQuiz, type LearningCitation, type LearningPathStep, type TopicScores, type TutorMemory } from '../../services/adaptiveApi'
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
  const [allowedClassLevels, setAllowedClassLevels] = useState<number[]>([])
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
  const [feedback, setFeedback] = useState<{ correct: boolean | null; explanation: string; answerGuide: string; adaptationReason?: string; questionText: string; submittedAnswer: string; grading: { score: number | null; method: 'ollama' | 'exact' | 'manual_review'; feedback: string } } | null>(null)
  const [result, setResult] = useState<AssessmentSummary | null>(null)
  const [assessmentReward, setAssessmentReward] = useState<{ points_awarded: number; coins: number } | null>(null)
  const [assessmentType, setAssessmentType] = useState<'adaptive' | 'mock'>('adaptive')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [tutorQuestion, setTutorQuestion] = useState('')
  const [tutorMode, setTutorMode] = useState<'hint' | 'explanation' | 'check_question'>('explanation')
  const [tutor, setTutor] = useState<{ message: string; check_question: string; citations: LearningCitation[]; provider: string; points_awarded?: number; coins?: number | null } | null>(null)
  const [tutorHistory, setTutorHistory] = useState<TutorMemory[]>([])
  const [quizResult, setQuizResult] = useState<GeneratedWeakQuiz | null>(null)
  const [aiRecommendations, setAiRecommendations] = useState<AILearningRecommendation[]>([])
  const [recommendationCitations, setRecommendationCitations] = useState<LearningCitation[]>([])
  const [recommendationNotice, setRecommendationNotice] = useState('')
  const progressRequest = useRef(0)

  const refresh = async () => {
    const requestId = ++progressRequest.current
    try {
      const data = await getProgress(subject, classLevel)
      if (requestId !== progressRequest.current) return
      setConcepts(data.concepts)
      setLearningPath(data.learning_path)
      setSelectedConcept((current) => data.concepts.some((item) => item.concept_id === current && item.subject === subject && item.class_level === classLevel)
        ? current
        : data.concepts.find((item) => item.available_items)?.concept_id || data.concepts[0]?.concept_id || '')
      setError('')
    } catch (reason) {
      if (requestId === progressRequest.current) setError(reason instanceof Error ? reason.message : 'Could not load learning progress.')
    }
  }
  useEffect(() => {
    let active = true
    getLearningPreferences().then(({ preferences, allowed_class_levels }) => {
      if (!active) return
      setSubject(preferences.subject)
      const permittedLevels: number[] = [...new Set(allowed_class_levels)].filter((level) => level === 11 || level === 12).sort()
      setAllowedClassLevels(permittedLevels)
      setClassLevel(permittedLevels.includes(preferences.class_level) ? preferences.class_level : (permittedLevels[0] ?? preferences.class_level))
      if (permittedLevels.length === 0) setError('Join a Class 11 or Class 12 classroom to access adaptive learning.')
      setPreferencesLoaded(true)
    }).catch((reason) => {
      if (!active) return
      setError(reason instanceof Error ? reason.message : 'Could not load your classroom access.')
      setPreferencesLoaded(true)
    })
    return () => { active = false }
  }, [])
  useEffect(() => {
    if (!preferencesLoaded || !allowedClassLevels.includes(classLevel)) return
    const timeout = window.setTimeout(() => { void saveLearningPreferences(subject, classLevel).catch(() => {}) }, 300)
    return () => window.clearTimeout(timeout)
  }, [subject, classLevel, preferencesLoaded, allowedClassLevels])
  useEffect(() => {
    if (!preferencesLoaded || !allowedClassLevels.includes(classLevel)) return
    setSelectedConcept('')
    setConcepts([])
    setLearningPath([])
    void refresh()
  }, [subject, classLevel, preferencesLoaded, allowedClassLevels])
  useEffect(() => {
    if (!preferencesLoaded) return
    let refreshTimer: number | undefined
    const refreshWhenVisible = () => {
      if (document.visibilityState !== 'visible') return
      window.clearTimeout(refreshTimer)
      refreshTimer = window.setTimeout(() => { void refresh() }, 250)
    }
    const interval = window.setInterval(() => {
      if (document.visibilityState === 'visible') void refresh()
    }, 30_000)
    window.addEventListener('focus', refreshWhenVisible)
    document.addEventListener('visibilitychange', refreshWhenVisible)
    return () => {
      window.clearInterval(interval)
      window.clearTimeout(refreshTimer)
      window.removeEventListener('focus', refreshWhenVisible)
      document.removeEventListener('visibilitychange', refreshWhenVisible)
    }
  }, [subject, classLevel, preferencesLoaded])
  useEffect(() => {
    if (!session?.user.id) return
    const key = `adaptive-assessment:${session.user.id}`
    const savedId = window.sessionStorage.getItem(key)
    if (!savedId) return
    let active = true
    resumeAdaptiveAssessment(savedId).then((data) => {
      if (!active || data.status !== 'in_progress' || !data.question) {
        window.sessionStorage.removeItem(key)
        return
      }
      setAssessmentId(data.assessment_id); setQuestion(data.question); setAssessmentType(data.assessment_type)
      setAssessmentQuestionCount(data.question_count); setQuestionIndex(data.index + 1); setQuestionStartedAt(Date.now())
    }).catch(() => { if (active) window.sessionStorage.removeItem(key) })
    return () => { active = false }
  }, [session?.user.id])
  const selected = useMemo(() => concepts.find((concept) => concept.concept_id === selectedConcept && concept.subject === subject && concept.class_level === classLevel), [concepts, selectedConcept, subject, classLevel])
  useEffect(() => {
    if (!selected) { setTutorHistory([]); return }
    let active = true
    getTutorHistory(subject, classLevel, selected.concept_id)
      .then((data) => { if (active) setTutorHistory(data.items) })
      .catch(() => { if (active) setTutorHistory([]) })
    return () => { active = false }
  }, [selected, subject, classLevel])

  const availableQuestionCount = concepts.reduce((total, concept) => total + (concept.available_items ?? 0), 0)
  const mockQuestionCount = Math.min(10, availableQuestionCount)
  if (!session) return <Navigate to="/sign-in" replace />

  const start = async (type: 'adaptive' | 'mock' = 'adaptive') => {
    setBusy(true); setError(''); setResult(null); setAssessmentReward(null); setFeedback(null); setAnswer('')
    try {
      const data = await startAdaptiveAssessment(subject, classLevel, type === 'adaptive' ? selected?.concept_id : undefined, type)
      setAssessmentId(data.assessment_id); setQuestion(data.question); setQuestionIndex(1); setNextQuestion(null); setFeedback(null); setQuestionStartedAt(Date.now())
      setAssessmentQuestionCount(data.question_count)
      setAssessmentType(type)
      if (session?.user.id) window.sessionStorage.setItem(`adaptive-assessment:${session.user.id}`, data.assessment_id)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not start an assessment.') }
    finally { setBusy(false) }
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!assessmentId || !answer.trim()) return
    setBusy(true); setError('')
    try {
      if (!question) return
      const data = await submitAdaptiveAttempt(assessmentId, question.item_id, answer, Math.max(0, Math.floor((Date.now() - questionStartedAt) / 1000)))
      setFeedback({ correct: data.correct, explanation: data.explanation, answerGuide: data.answer_guide, adaptationReason: data.adaptation_reason, questionText: question?.question ?? '', submittedAnswer: answer, grading: data.grading })
      if (data.completed && data.summary) { setResult(data.summary); setAssessmentReward(data.reward ?? null); setQuestion(null); setAssessmentId(''); if (session?.user.id) window.sessionStorage.removeItem(`adaptive-assessment:${session.user.id}`); void refresh() }
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
      <div className="adaptive-subjects">{subjects.map((item) => <button key={item.id} className={subject === item.id ? 'active' : ''} onClick={() => { setSelectedConcept(''); setSubject(item.id) }}>{item.label}</button>)}</div>
      <label>Class {allowedClassLevels.length > 1
        ? <select value={classLevel} onChange={(event) => { setSelectedConcept(''); setClassLevel(Number(event.target.value)) }}>{allowedClassLevels.map((level) => <option value={level} key={level}>Class {level}</option>)}</select>
        : <span className="adaptive-class-value">{allowedClassLevels.length ? `Class ${allowedClassLevels[0]}` : 'Join a classroom'}</span>}</label>
    </section>
    {error && <div className="adaptive-alert" role="alert">{error}{preferencesLoaded && allowedClassLevels.length === 0 && <Link to="/classroom/join">Join a classroom</Link>}</div>}
    <section className="adaptive-path-card"><div className="path-title"><span className="adaptive-kicker">YOUR RECOMMENDED PATH</span><b>Small steps, in the right order</b><small>Prerequisites come first. Your results update this path after each assessment.</small><Button variant="neutral" disabled={busy || !allowedClassLevels.includes(classLevel)} onClick={() => void requestRecommendations()}>{busy ? <LoaderCircle className="spin" size={15} /> : <Sparkles size={15} />} Get AI study recommendations</Button></div>{learningPath.slice(0, 4).map((step, index) => <article className="path-step" key={step.concept_id}><span className="path-step-number">{String(index + 1).padStart(2, '0')}</span><div><b>{step.name}</b><small>{step.chapter} · {step.action}</small></div><span className={`path-status status-${step.mastery_status}`}>{step.mastery_status.replaceAll('_', ' ')}</span></article>)}{recommendationNotice && <p className="recommendation-status">{recommendationNotice}</p>}{aiRecommendations.map((item) => <article className="ai-recommendation" key={item.concept_id}><b>{item.concept_name} · {item.chapter}</b><p>{item.action}</p><small>{item.reason}</small>{item.source_ids.map((sourceId) => { const source = recommendationCitations.find((citation) => citation.source_id === sourceId); return source ? <SourceEvidence key={sourceId} source={source} /> : null })}</article>)}</section>
    <div className="adaptive-grid">
      <section className="adaptive-card progress-card"><div className="adaptive-card-heading"><div><span className="adaptive-kicker">CONCEPT MASTERY</span><h2>Know what to work on</h2></div><BookOpenCheck size={20} /></div>
        {concepts.length ? <div className="concept-progress-list">{concepts.map((concept) => <button key={concept.concept_id} className={`concept-progress-row ${selectedConcept === concept.concept_id ? 'selected' : ''}`} onClick={() => { setSelectedConcept(concept.concept_id); setTutor(null); setResult(null) }}><span className="concept-progress-copy"><b>{concept.name}</b><small>{concept.chapter} · {concept.attempts ?? 0} attempts</small></span><span className={`mastery-pill mastery-${concept.mastery_status ?? 'new'}`}>{concept.attempts ? `${Math.round((concept.accuracy ?? 0) * 100)}%` : 'New'}</span></button>)}</div> : <p className="adaptive-empty">{allowedClassLevels.length ? 'Loading your PCM concept map…' : 'Join a classroom to load the concepts for your class.'}</p>}
      </section>
      <section className="adaptive-card practice-card"><div className="adaptive-card-heading"><div><span className="adaptive-kicker">{assessmentType === 'mock' ? 'MOCK ASSESSMENT' : 'TARGETED ASSESSMENT'}</span><h2>{question ? `Question ${questionIndex}` : result ? 'Assessment complete' : 'Practice at your pace'}</h2></div><Sparkles size={20} /></div>
        {question ? <form onSubmit={submit} className="adaptive-question"><div className="assessment-progress"><div><b>Question {questionIndex}</b><span>of {assessmentQuestionCount}</span></div><div className="assessment-progress-track"><span style={{ width: `${assessmentQuestionCount ? Math.min(100, questionIndex / assessmentQuestionCount * 100) : 0}%` }} /></div></div><div className="question-tags"><span>{question.chapter}</span><span>{question.difficulty}</span><span>{bloomLabel(question.bloom_level)}</span></div><p>{question.question}</p>{question.item_type === 'mcq' && question.options?.length ? <fieldset className="adaptive-mcq-options" disabled={busy || Boolean(feedback)}><legend>Your answer</legend>{question.options.map((option, index) => <label key={`${index}-${option}`}><input type="radio" name="adaptive-answer" value={option} checked={answer === option} onChange={() => setAnswer(option)} /><span>{String.fromCharCode(65 + index)}.</span>{option}</label>)}</fieldset> : <><label className="adaptive-answer-label" htmlFor="adaptive-answer">Your answer</label><textarea id="adaptive-answer" className="adaptive-answer-input" value={answer} disabled={busy || Boolean(feedback)} onChange={(event) => setAnswer(event.target.value)} placeholder="Show your thinking in a few words" rows={3} /></>}{feedback && <div className={`answer-feedback-box ${feedback.correct === null ? 'review' : feedback.correct ? 'correct' : 'incorrect'}`}><b>{feedback.correct === null ? 'This answer was saved for review.' : feedback.correct ? 'That matches the expected answer.' : 'Let’s use this as a learning signal.'}</b><p>{feedback.explanation}</p><div className="grading-result"><div><b>{feedback.grading.method === 'ollama' ? 'AI concept check' : feedback.grading.method === 'exact' ? 'Direct answer match' : 'Teacher review needed'}</b><span>{feedback.grading.score === null ? 'Not scored' : `${Math.round(feedback.grading.score * 100)}% conceptual match`}</span></div><p>{feedback.grading.feedback}</p></div><small>Answer guide: {feedback.answerGuide}</small>{feedback.adaptationReason && <small className="adaptation-reason">Next step: {feedback.adaptationReason}</small>}</div>}{feedback && nextQuestion ? <Button type="button" disabled={busy} className="adaptive-primary" onClick={() => { setQuestion(nextQuestion); setNextQuestion(null); setFeedback(null); setAnswer(''); setQuestionStartedAt(Date.now()) }}>Continue to the next question <ArrowRight size={15} /></Button> : <Button type="submit" disabled={busy || !answer.trim()} className="adaptive-primary">{busy ? <LoaderCircle className="spin" size={16} /> : <Send size={15} />} Submit answer</Button>}</form> : result ? <div className="assessment-result"><span className="result-score">{result.correct}<small> / {result.scored_attempts}</small></span><p>{Math.round(result.accuracy * 100)}% correct across scored answers. {result.ungraded_attempts ? `${result.ungraded_attempts} answer(s) were saved for review and excluded from mastery.` : 'Your answers shaped the next questions in this practice set.'}</p>{assessmentReward && <p className="adapt-coins-earned">+{assessmentReward.points_awarded} AdaptCoins earned · {assessmentReward.coins} total</p>}{feedback && <article className={`final-answer-review ${feedback.correct === null ? 'review' : feedback.correct ? 'correct' : 'incorrect'}`}><span className="adaptive-kicker">FINAL ANSWER · {feedback.correct === null ? 'TEACHER REVIEW' : feedback.correct ? 'CORRECT' : 'REVIEW THIS ONE'}</span><b>{feedback.questionText}</b><p>Your answer: {feedback.submittedAnswer || 'No answer entered'}</p><p>{feedback.explanation}</p><div className="grading-result"><div><b>{feedback.grading.method === 'ollama' ? 'AI concept check' : feedback.grading.method === 'exact' ? 'Direct answer match' : 'Teacher review needed'}</b><span>{feedback.grading.score === null ? 'Not scored' : `${Math.round(feedback.grading.score * 100)}% conceptual match`}</span></div><p>{feedback.grading.feedback}</p></div><small>Expected answer: {feedback.answerGuide}</small></article>}<Button onClick={() => void start(assessmentType)} className="adaptive-primary">Try another set <ArrowRight size={15} /></Button><button type="button" className="ai-tutoring-cta" onClick={() => navigate('/student/adaptive-learning', { state: { subject, classLevel, topicScores: result.topic_scores, summary: { attempts: result.attempts, correct: result.correct, accuracy: result.accuracy } } })}><span className="ai-tutoring-icon"><BrainCircuit size={18} /></span><span><b>Adaptive Learning</b><small>Ask about your results and get a focused explanation</small></span><ArrowRight size={17} /></button></div> : <div className="adaptive-start"><p>{selected?.recommendation ?? 'Start a short assessment. Questions will adapt to your responses and saved learning history.'}</p>{(selected?.available_items ?? 0) === 0 ? <div className="adaptive-no-questions" role="status"><b>No reviewed practice questions are available for this concept.</b><span>{selected?.pending_review_items ? `${selected.pending_review_items} questions are waiting for teacher review. Teachers can review them in Teacher view → Adaptive PCM insights → Question bank drafts.` : 'Ask your teacher to add or approve questions. Assessments only use teacher-approved items.'}</span></div> : <><Button disabled={busy || !selected} onClick={() => void start('adaptive')} className="adaptive-primary">{busy ? <LoaderCircle className="spin" size={16} /> : <ArrowRight size={15} />} Start adaptive practice</Button><small>{selected?.approved_items ?? 0} approved · {selected?.starter_items ?? 0} built-in starter questions available for {selected?.name ?? 'this concept'}.</small></> }<Button variant="neutral" disabled={busy || mockQuestionCount === 0} onClick={() => void start('mock')}>{mockQuestionCount ? `Start ${mockQuestionCount}-question mock quiz` : 'Mock quiz needs available questions'} <ArrowRight size={15} /></Button>{mockQuestionCount === 0 && <small>{availableQuestionCount === 0 ? 'The mock quiz will appear when questions are available in this subject and class.' : `${availableQuestionCount} approved or built-in starter questions are available in this class.`}</small>}</div>}
      </section>
      <section className="adaptive-card tutor-card"><div className="adaptive-card-heading"><div><span className="adaptive-kicker">RETRIEVAL-GROUNDED AI</span><h2>Study with your NCERT sources</h2></div><CircleHelp size={20} /></div><p className="tutor-caption">Choose how you want help with <b>{selected?.name ?? 'a PCM concept'}</b>. AdaptEd retrieves relevant indexed passages, then asks Ollama to answer from that evidence. Your tutor history is saved to your account.</p><div className="tutor-modes" role="group" aria-label="Choose tutor response style">{tutorModes.map((mode) => <button key={mode.id} type="button" className={tutorMode === mode.id ? 'active' : ''} aria-pressed={tutorMode === mode.id} title={mode.description} onClick={() => setTutorMode(mode.id)}>{mode.label}</button>)}</div><form className="tutor-form" onSubmit={ask}><Input value={tutorQuestion} onChange={(event) => setTutorQuestion(event.target.value)} placeholder={tutorMode === 'hint' ? 'Where are you getting stuck? I’ll give a nudge.' : tutorMode === 'check_question' ? 'What have you tried or what do you think is happening?' : 'What part feels confusing?'} /><Button disabled={busy || !selected || tutorQuestion.trim().length < 3} className="adaptive-primary" aria-label="Ask tutor">{busy ? <LoaderCircle className="spin" size={16} /> : <Send size={15} />}</Button></form>{tutor && <article className="tutor-answer"><div className="rag-answer-meta"><span>Grounded answer</span><small>{tutor.provider}</small></div><TutorAnswerText text={tutor.message} />{Boolean(tutor.points_awarded) && <small className="adapt-coins-earned">+{tutor.points_awarded} AdaptCoin earned today</small>}<b>Check your understanding</b><TutorAnswerText text={tutor.check_question} /><div className="citation-list"><h3>Retrieved NCERT evidence · {tutor.citations.length} sources</h3>{tutor.citations.map((citation) => <SourceEvidence key={citation.source_id} source={citation} />)}</div></article>}{tutorHistory.length > 0 && <details className="tutor-history"><summary>Saved tutor history · {tutorHistory.length} exchanges</summary><div className="tutor-history-list">{tutorHistory.map((turn) => <article key={turn.id}><small>{turn.mode.replaceAll('_', ' ')} · {new Date(turn.created_at).toLocaleString()}</small><b>You asked</b><p>{turn.question}</p><b>AdaptEd</b><TutorAnswerText text={turn.message} /><b>Check your understanding</b><TutorAnswerText text={turn.check_question} /><div className="citation-list"><h3>Saved evidence · {turn.sources.length} sources</h3>{turn.sources.map((source) => <SourceEvidence key={source.source_id} source={source} />)}</div></article>)}</div></details>}<div className="weak-quiz-action"><span>Need more practice on {selected?.name ?? 'this concept'}?</span><Button variant="neutral" onClick={makeQuiz} disabled={busy || !selected}>{busy ? <LoaderCircle className="spin" size={14} /> : <Sparkles size={14} />} Generate cited quiz</Button></div>{quizResult && <div className="adaptive-success quiz-result"><Check size={15} /><div><b>{quizResult.question_count} question drafts created</b><p>Saved for teacher review. Once approved, they can be added to the practice bank.</p><small>Generated with {quizResult.status.replaceAll('_', ' ')} · Draft ID {quizResult.id}</small><div className="citation-list"><h3>Sources used for this quiz · {quizResult.citations.length}</h3>{quizResult.citations.map((citation) => <SourceEvidence key={citation.source_id} source={citation} />)}</div></div></div>}</section>
    </div>
  </main></div>
}
