import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Check, Clock3, Flag, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { StudentNav } from './ProblemsPage'
import { CHAPTER_QUIZZES, type QuizAttempt } from './services/quizCatalog'
import { beginQuiz, loadQuizAttempts, persistQuizAttempt, quizScore, remainingQuizSeconds } from './services/quizAttempts'
import './problems.css'

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const remainder = seconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`
}

export function QuizAttemptPage() {
  const { quizId } = useParams()
  const navigate = useNavigate()
  const { session } = useAuth()
  const quiz = CHAPTER_QUIZZES.find((item) => item.id === quizId)
  const [attempts, setAttempts] = useState<QuizAttempt[]>(() => loadQuizAttempts())
  const [attempt, setAttempt] = useState<QuizAttempt | null>(() => loadQuizAttempts().find((item) => item.quizId === quizId) ?? null)
  const [questionIndex, setQuestionIndex] = useState(0)
  const [now, setNow] = useState(Date.now())
  const [confirmSubmit, setConfirmSubmit] = useState(false)
  const [submittedResult, setSubmittedResult] = useState<QuizAttempt | null>(null)

  const completeAttempt = useCallback((current: QuizAttempt) => {
    if (!quiz || current.status === 'completed') return current
    const completed: QuizAttempt = {
      ...current,
      status: 'completed',
      submittedAt: new Date().toISOString(),
      score: quizScore(quiz.questions, current.answers),
    }
    setAttempts(persistQuizAttempt(completed))
    setAttempt(completed)
    setSubmittedResult(completed)
    setConfirmSubmit(false)
    return completed
  }, [quiz])

  useEffect(() => {
    if (attempt?.status !== 'in_progress') return
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [attempt?.status])

  const secondsLeft = useMemo(() => attempt?.status === 'in_progress' && quiz
    ? remainingQuizSeconds(quiz.timeLimitMinutes, attempt.startedAt, now)
    : null, [attempt, now, quiz])

  useEffect(() => {
    if (secondsLeft === 0 && attempt?.status === 'in_progress') completeAttempt(attempt)
  }, [attempt, completeAttempt, secondsLeft])

  if (!session) return <Navigate to="/sign-in" replace />
  if (!session.user.onboardingComplete || session.user.role !== 'student') return <Navigate to="/classroom" replace />
  if (!quiz) return <Navigate to="/student/problems?view=quizzes" replace />

  const currentQuestion = quiz.questions[questionIndex]
  const isCompleted = submittedResult ?? (attempt?.status === 'completed' ? attempt : null)
  const saveAnswer = (answer: string) => {
    if (!attempt || attempt.status !== 'in_progress' || !currentQuestion) return
    const updated: QuizAttempt = { ...attempt, answers: { ...attempt.answers, [currentQuestion.id]: answer } }
    setAttempt(updated)
    setAttempts(persistQuizAttempt(updated))
  }
  const start = () => {
    const started = beginQuiz(quiz.id, attempts)
    setAttempt(started)
    setAttempts(persistQuizAttempt(started))
    setSubmittedResult(null)
    setQuestionIndex(0)
    setNow(Date.now())
  }
  const onSubmit = (event: FormEvent) => { event.preventDefault(); setConfirmSubmit(true) }
  const answeredCount = quiz.questions.filter((question) => Boolean(attempt?.answers[question.id]?.trim())).length

  if (isCompleted) {
    const score = isCompleted.score ?? quizScore(quiz.questions, isCompleted.answers)
    return <div className="problems-app"><StudentNav /><main className="quiz-page-main"><div className="quiz-result-card"><span className="quiz-result-mark"><Check size={27} /></span><span className="problems-kicker">QUIZ COMPLETE · LOCAL DEMO RESULT</span><h1>{quiz.name} results</h1><p>{quiz.chapter} · {quiz.questionCount} questions</p><div className="quiz-score-box"><strong>{score}</strong><span>/ {quiz.maxMarks} marks</span></div><div className="quiz-result-summary"><span>{Math.round((score / Math.max(1, quiz.maxMarks)) * 100)}% score</span><span>{answeredCount} of {quiz.questionCount} answered</span></div><div className="quiz-result-review">{quiz.questions.map((question, index) => { const correct = isCompleted.answers[question.id]?.trim().toLocaleLowerCase() === question.answer.trim().toLocaleLowerCase(); return <div className="quiz-review-row" key={question.id}><span className={`review-result-dot ${correct ? 'review-correct' : 'review-wrong'}`}>{correct ? <Check size={12} /> : <Flag size={11} />}</span><div><b>Question {index + 1} · {correct ? 'Correct' : 'Review'}</b><p>{question.explanation}</p></div></div> })}</div><Button className="quiz-primary-button" onClick={() => navigate('/student/problems?view=quizzes')}>Back to chapter quizzes <ArrowRight size={15} /></Button><p className="quiz-local-note">This result is saved in this browser only. No server is connected.</p></div></main></div>
  }

  if (!attempt || attempt.status !== 'in_progress') return <div className="problems-app"><StudentNav /><main className="quiz-page-main"><Link className="back-to-problems" to="/student/problems?view=quizzes"><ArrowLeft size={15} /> Back to chapter quizzes</Link><section className="quiz-intro-card"><div className="quiz-source-mark">{quiz.source === 'mock' ? 'MOCK' : 'DEMO BANK'}</div><span className="problems-kicker">{quiz.chapter}</span><h1>{quiz.name}</h1><p className="quiz-intro-subtitle">Get set to focus. The timer starts when you begin.</p><div className="quiz-metadata-grid"><div><span>QUESTIONS</span><b>{quiz.questionCount}</b></div><div><span>MAX MARKS</span><b>{quiz.maxMarks}</b></div><div><span>TIME LIMIT</span><b>{quiz.timeLimitMinutes} min</b></div><div><span>DIFFICULTY</span><b className={`difficulty-text-${quiz.difficulty.toLowerCase()}`}>{quiz.difficulty}</b></div></div><p className="quiz-mock-disclaimer">{quiz.source === 'mock' ? 'This quiz uses a mock sample question.' : 'Questions are drawn from AdaptEd’s local demo question bank.'} Answers and scores are stored in this browser only.</p><Button className="quiz-primary-button" onClick={start}>{attempt?.status === 'completed' ? 'Start a new attempt' : attempt?.status === 'in_progress' ? 'Resume quiz' : 'Begin quiz'} <ArrowRight size={15} /></Button></section></main></div>

  return <div className="problems-app"><StudentNav /><main className="quiz-page-main"><div className="quiz-attempt-header"><div><Link className="back-to-problems" to="/student/problems?view=quizzes"><ArrowLeft size={15} /> Chapter quizzes</Link><span className="problems-kicker">{quiz.chapter} / {quiz.name}</span><h1>{quiz.name}</h1></div><div className={`quiz-timer ${secondsLeft !== null && secondsLeft < 60 ? 'timer-low' : ''}`} aria-live="polite"><Clock3 size={17} /><span>{formatTime(secondsLeft ?? 0)}</span></div></div><div className="quiz-details-strip"><span>{quiz.questionCount} questions</span><span>{quiz.maxMarks} max marks</span><span>{quiz.timeLimitMinutes} minutes</span><span className="quiz-data-badge">{quiz.source === 'mock' ? 'MOCK QUESTIONS' : 'DEMO BANK'}</span></div><div className="quiz-workspace"><nav className="quiz-question-nav" aria-label="Quiz questions">{quiz.questions.map((question, index) => <button type="button" key={question.id} className={`quiz-number-button ${questionIndex === index ? 'question-current' : ''} ${attempt.answers[question.id] ? 'question-answered' : ''}`} aria-label={`Go to question ${index + 1}${attempt.answers[question.id] ? ', answered' : ''}`} aria-current={questionIndex === index ? 'step' : undefined} onClick={() => setQuestionIndex(index)}>{index + 1}</button>)}</nav><form className="quiz-question-card" onSubmit={onSubmit}><div className="quiz-question-top"><span>QUESTION {questionIndex + 1} / {quiz.questions.length}</span><span>{attempt.answers[currentQuestion.id] ? 'ANSWERED' : 'NOT ANSWERED'}</span></div><h2>{currentQuestion.prompt}</h2>{currentQuestion.choices ? <div className="quiz-choice-list">{currentQuestion.choices.map((choice) => <label className={`quiz-choice ${attempt.answers[currentQuestion.id] === choice ? 'quiz-choice-picked' : ''}`} key={choice}><input type="radio" name={`quiz-${quiz.id}-${currentQuestion.id}`} value={choice} checked={attempt.answers[currentQuestion.id] === choice} onChange={() => saveAnswer(choice)} /><span className="quiz-radio" />{choice}</label>)}</div> : <label className="quiz-answer-field"><span>Your answer</span><Input value={attempt.answers[currentQuestion.id] ?? ''} onChange={(event) => saveAnswer(event.target.value)} autoComplete="off" /></label>}<div className="quiz-question-actions"><Button type="button" variant="neutral" disabled={questionIndex === 0} onClick={() => setQuestionIndex((index) => Math.max(0, index - 1))}><ArrowLeft size={14} /> Previous</Button>{questionIndex < quiz.questions.length - 1 ? <Button type="button" className="quiz-primary-button" onClick={() => setQuestionIndex((index) => Math.min(quiz.questions.length - 1, index + 1))}>Next <ArrowRight size={14} /></Button> : <Button type="submit" className="quiz-primary-button"><Send size={14} /> Submit quiz</Button>}</div><p className="quiz-answer-progress">{answeredCount} of {quiz.questionCount} answered</p></form></div></main>{confirmSubmit && <div className="quiz-confirm-backdrop" role="presentation"><section className="quiz-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-submit-title"><span className="section-kicker">FINAL CHECK</span><h2 id="confirm-submit-title">Submit this quiz?</h2><p>You’ve answered {answeredCount} of {quiz.questionCount} questions. You can’t change your answers after submission.</p><div><Button variant="neutral" onClick={() => setConfirmSubmit(false)}>Keep working</Button><Button className="quiz-primary-button" onClick={() => completeAttempt(attempt)}><Check size={14} /> Confirm submit</Button></div></section></div>}</div>
}
