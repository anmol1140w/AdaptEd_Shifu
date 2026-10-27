import { useEffect, useRef, useState, type FormEvent } from 'react'
import { AlertCircle, BarChart3, Check, ClipboardCheck, GraduationCap, LoaderCircle, Plus, RefreshCw, Send } from 'lucide-react'
import { Link, Navigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { askTutor, getConcepts, getLearningPreferences, getTeacherAnalytics, getTeacherGeneratedContent, getTeacherQuestionBank, getTutorHistory, importTeacherQuestion, importTeacherQuestionBatch, reviewGeneratedContent, reviewQuestion, saveLearningPreferences, type AdaptiveConcept, type AdaptiveQuestion, type LearnerSummary, type LearningCitation, type TutorMemory } from '../../services/adaptiveApi'
import { StudentNav } from '../learner/StudentNav'
import './teacher-learning.css'

export function TeacherLearningDashboard() {
  const { session } = useAuth()
  const [subject, setSubject] = useState('physics')
  const [classLevel, setClassLevel] = useState(11)
  const [preferencesLoaded, setPreferencesLoaded] = useState(false)
  const [concepts, setConcepts] = useState<AdaptiveConcept[]>([])
  const [analytics, setAnalytics] = useState<AdaptiveConcept[]>([])
  const [learners, setLearners] = useState<LearnerSummary[]>([])
  const [items, setItems] = useState<(AdaptiveQuestion & { answer_guide: string; explanation: string; approved: boolean; citation_status: string; bloom_source: string; bloom_teacher_verified: boolean; difficulty_teacher_verified: boolean; source_reference_ids: string[]; supporting_chunk_ids: string[] })[]>([])
  const [generated, setGenerated] = useState<{ id: string; subject: string; class_level: number; concept_id: string; payload: { question: string; answer_guide: string; explanation: string; bloom_level: string }[]; source_ids: string[]; sources: { source_id: string; citation: string; text: string; score: number }[] }[]>([])
  const [conceptId, setConceptId] = useState('')
  const [draft, setDraft] = useState({ chapter: '', question: '', answer_guide: '', explanation: '', difficulty: 'medium', bloom_level: '' })
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [teacherQuestion, setTeacherQuestion] = useState('')
  const [teacherTutor, setTeacherTutor] = useState<{ message: string; check_question: string; citations: LearningCitation[]; provider: string } | null>(null)
  const [teacherTutorHistory, setTeacherTutorHistory] = useState<TutorMemory[]>([])
  const uploadRef = useRef<HTMLInputElement>(null)

  if (!session) return <Navigate to="/sign-in" replace />
  if (session.user.role !== 'teacher') return <Navigate to="/student/learn" replace />

  const refresh = async () => {
    setBusy(true)
    try {
      const [conceptData, analyticsData, bankData, generatedData] = await Promise.all([
        getConcepts(subject, classLevel), getTeacherAnalytics(subject, classLevel), getTeacherQuestionBank('pending', subject, classLevel), getTeacherGeneratedContent(),
      ])
      setConcepts(conceptData.concepts); setAnalytics(analyticsData.concepts); setLearners(analyticsData.learners); setItems(bankData.items); setGenerated(generatedData.items)
      setConceptId((current) => current || conceptData.concepts[0]?.concept_id || '')
      setError('')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not load the teacher workspace.') }
    finally { setBusy(false) }
  }
  useEffect(() => { setConceptId(''); void refresh() }, [subject, classLevel])
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
  useEffect(() => {
    if (!conceptId) { setTeacherTutorHistory([]); return }
    let active = true
    getTutorHistory(subject, classLevel, conceptId).then((data) => { if (active) setTeacherTutorHistory(data.items) }).catch(() => { if (active) setTeacherTutorHistory([]) })
    return () => { active = false }
  }, [subject, classLevel, conceptId])

  const askTeacherTutor = async (event: FormEvent) => {
    event.preventDefault()
    if (!conceptId || teacherQuestion.trim().length < 3) return
    setBusy(true); setError(''); setNotice('')
    try {
      const answer = await askTutor({ subject, class_level: classLevel, concept_id: conceptId, question: teacherQuestion, mode: 'explanation' })
      setTeacherTutor(answer)
      setTeacherQuestion('')
      void getTutorHistory(subject, classLevel, conceptId).then((history) => setTeacherTutorHistory(history.items)).catch(() => {})
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not reach the NCERT tutor.') }
    finally { setBusy(false) }
  }

  const approve = async (itemId: string, approved: boolean) => {
    setBusy(true); setError('')
    try { await reviewQuestion(itemId, approved); setNotice(approved ? 'Question approved and available for adaptive practice.' : 'Question returned to the review queue.'); await refresh() }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Review could not be saved.') }
    finally { setBusy(false) }
  }

  const submitDraft = async (event: FormEvent) => {
    event.preventDefault()
    const concept = concepts.find((item) => item.concept_id === conceptId)
    if (!concept) return
    setBusy(true); setNotice(''); setError('')
    try {
      const imported = await importTeacherQuestion({ subject, class_level: classLevel, chapter: draft.chapter || concept.chapter, concept_id: conceptId, question: draft.question, answer_guide: draft.answer_guide, explanation: draft.explanation, difficulty: draft.difficulty, ...(draft.bloom_level ? { bloom_level: draft.bloom_level } : {}) })
      setNotice(`Question saved as a draft. Bloom level: ${imported.bloom_level}. Review it below before publishing.`)
      setDraft({ chapter: '', question: '', answer_guide: '', explanation: '', difficulty: 'medium', bloom_level: '' })
      await refresh()
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not save this question.') }
    finally { setBusy(false) }
  }

  const uploadBank = async (file?: File) => {
    if (!file) return
    setBusy(true); setNotice(''); setError('')
    try {
      const parsed = JSON.parse(await file.text()) as { subject?: string; class?: number; items?: Record<string, unknown>[] } | Record<string, unknown>[]
      const rows = Array.isArray(parsed) ? parsed : parsed.items ?? []
      const documentSubject = Array.isArray(parsed) ? subject : (parsed.subject ?? subject).toLowerCase()
      const documentClass = Array.isArray(parsed) ? classLevel : Number(parsed.class ?? classLevel)
      if (!rows.length) throw new Error('The JSON file must contain an items array or be an array of question records.')
      const normalized = rows.map((row) => ({
        subject: String(row.subject ?? documentSubject).toLowerCase(),
        class_level: Number(row.class_level ?? row.class ?? documentClass),
        chapter: String(row.chapter ?? ''),
        concept_id: String(row.concept_id ?? ''),
        question: String(row.question ?? ''),
        answer_guide: String(row.answer_guide ?? row.answer ?? ''),
        explanation: String(row.explanation ?? ''),
        difficulty: String(row.difficulty ?? 'medium').toLowerCase(),
        ...(row.bloom_level ? { bloom_level: String(row.bloom_level).toLowerCase() } : {}),
        source_reference_ids: Array.isArray(row.source_reference_ids) ? row.source_reference_ids.map(String) : [],
        supporting_chunk_ids: Array.isArray(row.supporting_chunk_ids) ? row.supporting_chunk_ids.map(String) : [],
      }))
      const uploaded = await importTeacherQuestionBatch(normalized)
      setNotice(uploaded.message)
      await refresh()
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not import that JSON question bank.') }
    finally { setBusy(false); if (uploadRef.current) uploadRef.current.value = '' }
  }

  const reviewGenerated = async (id: string, approved: boolean) => {
    setBusy(true); setError('')
    try { await reviewGeneratedContent(id, approved); setNotice(approved ? 'AI quiz reviewed and added to the approved question bank.' : 'AI quiz rejected.'); await refresh() }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not save this review.') }
    finally { setBusy(false) }
  }

  const focus = analytics.filter((concept) => (concept.attempts ?? 0) > 0).slice(0, 6)
  const totalAttempts = analytics.reduce((sum, concept) => sum + (concept.attempts ?? 0), 0)
  const pending = items.length

  return <div className="teacher-learning-app"><StudentNav /><main className="teacher-learning-main">
    <header className="teacher-learning-heading"><div><span className="teacher-kicker">TEACHER WORKSPACE · PCM</span><h1>See the learning behind the scores.</h1><p>Review question quality, spot concept-level gaps, and decide where your class needs support.</p></div><div className="teacher-heading-actions"><Link className="teacher-classroom-link" to="/classroom/create">Create classroom <Plus size={14} /></Link><div className="teacher-heading-icon"><GraduationCap size={27} /></div></div></header>
    <section className="teacher-filters"><div className="teacher-subject-tabs">{['physics', 'chemistry', 'mathematics'].map((option) => <button key={option} className={subject === option ? 'active' : ''} onClick={() => setSubject(option)}>{option[0].toUpperCase() + option.slice(1)}</button>)}</div><label>Class <select value={classLevel} onChange={(event) => setClassLevel(Number(event.target.value))}><option value={11}>Class 11</option><option value={12}>Class 12</option></select></label><Button variant="neutral" onClick={() => void refresh()} disabled={busy}><RefreshCw size={15} className={busy ? 'spin' : ''} /> Refresh</Button></section>
    {error && <div className="teacher-notice error"><AlertCircle size={16} />{error}</div>}{notice && <div className="teacher-notice success"><Check size={16} />{notice}</div>}
    <section className="teacher-metrics"><article><span>ATTEMPTS RECORDED</span><b>{totalAttempts}</b><small>From authenticated student attempts</small></article><article><span>CONCEPTS WITH EVIDENCE</span><b>{analytics.filter((concept) => (concept.attempts ?? 0) > 0).length}</b><small>Across {subject} · Class {classLevel}</small></article><article><span>QUESTIONS TO REVIEW</span><b>{pending}</b><small>Drafts are hidden from students</small></article></section>
    <section className="teacher-panel teacher-ai-panel"><div className="teacher-panel-head"><div><span className="teacher-kicker">PERSISTENT, SOURCE-GROUNDED AI</span><h2>Plan a lesson with NCERT evidence</h2></div><GraduationCap size={20} /></div><p>Ask about the selected concept. Your conversation is saved to your teacher account and remains available after you sign in again.</p><form className="teacher-ai-form" onSubmit={askTeacherTutor}><label>Concept<select value={conceptId} onChange={(event) => { setConceptId(event.target.value); setTeacherTutor(null) }}><option value="" disabled>Choose concept</option>{concepts.map((concept) => <option key={concept.concept_id} value={concept.concept_id}>{concept.chapter} — {concept.name}</option>)}</select></label><div className="teacher-ai-input"><Input value={teacherQuestion} onChange={(event) => setTeacherQuestion(event.target.value)} placeholder="Ask for a clear explanation, misconception, or lesson angle" /><Button className="teacher-approve" disabled={busy || !conceptId || teacherQuestion.trim().length < 3}>{busy ? <LoaderCircle className="spin" size={15} /> : <Send size={15} />} Ask NCERT tutor</Button></div></form>{teacherTutor && <article className="teacher-ai-answer"><small>{teacherTutor.provider} · cited answer</small><p>{teacherTutor.message}</p><b>Ask students to check:</b><p>{teacherTutor.check_question}</p><h3>Retrieved textbook evidence</h3>{teacherTutor.citations.map((source) => <details key={source.source_id}><summary>{source.citation} · match {Math.round(source.score * 100)}%</summary><p>{source.text}</p><code>{source.source_id}</code></details>)}</article>}{teacherTutorHistory.length > 0 && <details className="teacher-ai-history"><summary>Saved exchanges · {teacherTutorHistory.length}</summary>{teacherTutorHistory.map((turn) => <article key={turn.id}><small>{new Date(turn.created_at).toLocaleString()}</small><b>You asked: {turn.question}</b><p>{turn.message}</p><b>Ask students to check:</b><p>{turn.check_question}</p><details><summary>Saved NCERT evidence · {turn.sources.length} sources</summary>{turn.sources.map((source) => <p key={source.source_id}>{source.citation} · {source.text}</p>)}</details></article>)}</details>}</section>
    <section className="teacher-panel teacher-learner-panel"><div className="teacher-panel-head"><div><span className="teacher-kicker">LEARNER CHECK-INS</span><h2>Students who may need support</h2></div><GraduationCap size={20} /></div>{learners.length ? <div className="teacher-learner-list">{learners.map((learner) => <article key={learner.learner_id}><div><b>{learner.name}</b><small>{learner.attempts} attempts · {Math.round(learner.accuracy * 100)}% overall</small>{learner.weak_concepts.length > 0 && <small>Needs support: {learner.weak_concepts.join(', ')}</small>}</div><span className={learner.weak_concepts.length ? 'learner-needs-support' : 'learner-on-track'}>{learner.intervention}</span></article>)}</div> : <p className="teacher-empty">No learner attempts are available in your classrooms for this subject and class yet.</p>}</section>
    <div className="teacher-learning-grid"><section className="teacher-panel"><div className="teacher-panel-head"><div><span className="teacher-kicker">CLASS SIGNALS</span><h2>Concepts needing attention</h2></div><BarChart3 size={20} /></div>{focus.length ? <div className="teacher-concept-list">{focus.map((concept) => <article key={concept.concept_id}><div><b>{concept.name}</b><small>{concept.chapter} · {concept.learners ?? 0} learners · {concept.attempts} attempts</small></div><div className="teacher-accuracy"><b>{Math.round((concept.accuracy ?? 0) * 100)}%</b><span>{concept.intervention}</span></div></article>)}</div> : <div className="teacher-empty">No student attempts are available for your classrooms yet. Have learners complete adaptive practice to populate this view.</div>}</section>
    <section className="teacher-panel question-review-panel"><div className="teacher-panel-head"><div><span className="teacher-kicker">TEACHER REVIEW</span><h2>Question bank drafts</h2></div><ClipboardCheck size={20} /></div>{items.length ? <div className="teacher-question-list">{items.map((item) => <article key={item.item_id}><div className="teacher-question-meta"><span>{item.chapter}</span><span>{item.difficulty}{item.difficulty_teacher_verified ? ' · verified' : ' · suggested'}</span><span>BT · {item.bloom_level}</span><span>{item.bloom_teacher_verified ? 'BT teacher verified' : `BT ${item.bloom_source.replaceAll('_', ' ')}`}</span></div><h3>{item.question}</h3><p><b>Answer guide:</b> {item.answer_guide}</p><details className="question-review-details"><summary>Explanation and source metadata</summary><p>{item.explanation || 'No explanation supplied.'}</p><small>References: {item.source_reference_ids.length ? item.source_reference_ids.join(', ') : 'None supplied'}</small><small>Chunk IDs: {item.supporting_chunk_ids.length ? item.supporting_chunk_ids.join(', ') : 'None supplied'}</small></details><p className="teacher-citation-status">{item.citation_status.replaceAll('_', ' ')}</p><div className="teacher-review-actions"><Button className="teacher-approve" disabled={busy} onClick={() => void approve(item.item_id, true)}><Check size={14} /> Approve</Button><Button variant="neutral" disabled={busy} onClick={() => void approve(item.item_id, false)}>Keep pending</Button></div></article>)}</div> : <div className="teacher-empty">No questions are waiting for review in this subject. Import your first question below.</div>}</section></div>
    {generated.length > 0 && <section className="teacher-panel generated-review-panel"><div className="teacher-panel-head"><div><span className="teacher-kicker">AI CONTENT REVIEW</span><h2>Weak-area quizzes submitted by students</h2></div><ClipboardCheck size={20} /></div><div className="teacher-question-list">{generated.map((draft) => <article key={draft.id}><div className="teacher-question-meta"><span>{draft.subject} · Class {draft.class_level}</span><span>{draft.payload.length} questions</span><span>{draft.sources.length} cited chunks</span></div>{draft.payload.map((item, index) => <div className="generated-item-preview" key={`${draft.id}-${index}`}><b>Q{index + 1} · BT {item.bloom_level}</b><p>{item.question}</p><small>Answer guide: {item.answer_guide}</small><details><summary>Reasoning and explanation</summary><p>{item.explanation}</p></details></div>)}<div className="generated-source-review"><h3>Retrieved NCERT evidence used</h3>{draft.sources.map((source) => <details key={source.source_id}><summary>{source.citation} · match {Math.round(source.score * 100)}%</summary><p>{source.text}</p><code>{source.source_id}</code></details>)}</div><div className="teacher-review-actions"><Button className="teacher-approve" disabled={busy} onClick={() => void reviewGenerated(draft.id, true)}><Check size={14} /> Approve quiz</Button><Button variant="neutral" disabled={busy} onClick={() => void reviewGenerated(draft.id, false)}>Reject</Button></div></article>)}</div></section>}
    <section className="teacher-panel teacher-import-panel"><div className="teacher-panel-head"><div><span className="teacher-kicker">BUILD THE BANK</span><h2><Plus size={18} /> Add a reviewed question</h2></div></div><form className="teacher-question-form" onSubmit={submitDraft}><label>Concept<select required value={conceptId} onChange={(event) => setConceptId(event.target.value)}><option value="" disabled>Choose concept</option>{concepts.map((concept) => <option key={concept.concept_id} value={concept.concept_id}>{concept.chapter} — {concept.name}</option>)}</select></label><label>Question<Input required value={draft.question} onChange={(event) => setDraft({ ...draft, question: event.target.value })} placeholder="Write a clear, standalone question" /></label><div className="teacher-form-row"><label>Answer guide<Input required value={draft.answer_guide} onChange={(event) => setDraft({ ...draft, answer_guide: event.target.value })} placeholder="Expected answer or key points" /></label><label>Difficulty<select value={draft.difficulty} onChange={(event) => setDraft({ ...draft, difficulty: event.target.value })}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label></div><div className="teacher-form-row"><label>Bloom / BT level<select value={draft.bloom_level} onChange={(event) => setDraft({ ...draft, bloom_level: event.target.value })}><option value="">Infer from prompt</option>{['remember','understand','apply','analyze','evaluate','create'].map((level) => <option key={level} value={level}>{level[0].toUpperCase() + level.slice(1)}</option>)}</select></label><label>Chapter override (optional)<Input value={draft.chapter} onChange={(event) => setDraft({ ...draft, chapter: event.target.value })} placeholder={concepts.find((concept) => concept.concept_id === conceptId)?.chapter ?? 'Chapter'} /></label></div><label>Explanation (optional)<textarea value={draft.explanation} onChange={(event) => setDraft({ ...draft, explanation: event.target.value })} placeholder="Explain the key reasoning steps" rows={3} /></label><div className="teacher-form-footer"><p>New questions stay out of student assessments until a teacher approves them.</p><Button className="teacher-approve" disabled={busy || !conceptId}><Plus size={15} /> Save for review</Button></div></form></section>
  </main></div>
}
