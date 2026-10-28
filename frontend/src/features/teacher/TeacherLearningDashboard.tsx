import { useEffect, useRef, useState } from 'react'
import { AlertCircle, Check, FileSpreadsheet, LoaderCircle, RefreshCw, Upload } from 'lucide-react'
import { Navigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../../app/AuthProvider'
import { classifyTeacherQuestionBatch, getConcepts, getLearningPreferences, getTeacherQuestionBank, importTeacherQuestionBatch, reviewQuestion, saveLearningPreferences, type AdaptiveConcept } from '../../services/adaptiveApi'
import { StudentNav } from '../learner/StudentNav'
import { parseCsv, parseXlsx, rowsToQuestionBank, type QuestionBankRow } from './questionBankFile'
import './teacher-learning.css'

function uploadRowErrors(row: QuestionBankRow, concepts: AdaptiveConcept[], subject: string) {
  const errors: string[] = []
  if (!row.question.trim()) errors.push('Question is required.')
  if (!['mcq', 'numerical', 'short_answer', 'descriptive', 'coding'].includes(row.question_type)) errors.push('Choose a supported type.')
  if (!row.topic.trim()) errors.push('Topic is required.')
  if (row.subject.trim() && row.subject.trim().toLowerCase() !== subject) errors.push(`Choose ${row.subject} above or change this row to ${subject}.`)
  if (!row.correct_answer.trim() && row.question_type === 'descriptive' && !row.marking_rubric.trim()) errors.push('Provide an answer key or marking rubric.')
  else if (!row.correct_answer.trim() && row.question_type === 'coding' && !row.test_cases.trim()) errors.push('Provide an answer key or test cases.')
  else if (!row.correct_answer.trim() && !['descriptive', 'coding'].includes(row.question_type)) errors.push('Answer key is required.')
  if (row.question_type === 'mcq' && (!row.option_a.trim() || !row.option_b.trim())) errors.push('MCQ needs at least options A and B.')
  if (row.concept_id && !concepts.some((concept) => concept.concept_id === row.concept_id)) errors.push('Choose a valid concept or clear the mapping to create this topic.')
  if (row.difficulty && !['easy', 'medium', 'hard'].includes(row.difficulty.toLowerCase())) errors.push('Difficulty must be Easy, Medium, or Hard.')
  if (row.bloom_level && !/^(bt)?[1-6]$|^(remember|understand|apply|analyze|evaluate|create)$/i.test(row.bloom_level)) errors.push('Bloom level must be BT1–BT6 or a taxonomy name.')
  if (row.marks && (!Number.isFinite(Number(row.marks)) || Number(row.marks) <= 0)) errors.push('Marks must be a positive number.')
  if (row.time_seconds && (!Number.isInteger(Number(row.time_seconds)) || Number(row.time_seconds) <= 0)) errors.push('Time must be a positive whole number of seconds.')
  return errors
}

function bloomSelectValue(value: string) {
  const normalized = value.trim().toLowerCase()
  const names: Record<string, string> = { remember: 'BT1', understand: 'BT2', apply: 'BT3', analyze: 'BT4', evaluate: 'BT5', create: 'BT6' }
  if (/^bt[1-6]$/.test(normalized)) return normalized.toUpperCase()
  if (/^[1-6]$/.test(normalized)) return `BT${normalized}`
  return names[normalized] ?? ''
}

export function TeacherLearningDashboard() {
  const { session } = useAuth()
  const [subject, setSubject] = useState('physics')
  const [classLevel, setClassLevel] = useState(11)
  const [preferencesLoaded, setPreferencesLoaded] = useState(false)
  const [concepts, setConcepts] = useState<AdaptiveConcept[]>([])
  const [pendingQuestions, setPendingQuestions] = useState<Awaited<ReturnType<typeof getTeacherQuestionBank>>['items']>([])
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [uploadRows, setUploadRows] = useState<QuestionBankRow[]>([])
  const [uploadFileName, setUploadFileName] = useState('')
  const [uploadNotice, setUploadNotice] = useState('')
  const uploadRef = useRef<HTMLInputElement>(null)
  const refreshRequest = useRef(0)

  if (!session) return <Navigate to="/sign-in" replace />
  if (session.user.role !== 'teacher') return <Navigate to="/student/learn" replace />

  const refresh = async () => {
    const requestId = ++refreshRequest.current
    setBusy(true)
    try {
      const [conceptResult, bankResult] = await Promise.allSettled([
        getConcepts(subject, classLevel), getTeacherQuestionBank('pending', subject, classLevel),
      ])
      if (requestId !== refreshRequest.current) return
      if (conceptResult.status === 'fulfilled') setConcepts(conceptResult.value.concepts)
      if (bankResult.status === 'fulfilled') setPendingQuestions(bankResult.value.items)
      const failed = conceptResult.status === 'rejected' ? conceptResult.reason : bankResult.status === 'rejected' ? bankResult.reason : null
      setError(failed instanceof Error ? failed.message : failed ? 'Could not load question-bank drafts.' : '')
    } catch (reason) {
      if (requestId === refreshRequest.current) setError(reason instanceof Error ? reason.message : 'Could not load the teacher workspace.')
    } finally {
      if (requestId === refreshRequest.current) setBusy(false)
    }
  }
  useEffect(() => { void refresh() }, [subject, classLevel])
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
  const uploadBank = async (file?: File) => {
    if (!file) return
    setBusy(true); setNotice(''); setError(''); setUploadNotice('')
    try {
      const extension = file.name.split('.').pop()?.toLowerCase()
      if (!['csv', 'xlsx'].includes(extension ?? '')) throw new Error('Choose a .csv or .xlsx question bank.')
      const cells = extension === 'csv' ? parseCsv(await file.text()) : await parseXlsx(file)
      const parsed = rowsToQuestionBank(cells)
      const normalizedTopic = (value: string) => value.trim().toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
      const mapped = parsed.map((row) => {
        const explicit = concepts.find((concept) => concept.concept_id === row.concept_id)
        const topic = normalizedTopic(row.topic)
        const match = explicit ?? concepts.find((concept) => [concept.name, concept.chapter].some((value) => normalizedTopic(value) === topic))
        return { ...row, subject: row.subject || subject, concept_id: match?.concept_id ?? '' }
      })
      setUploadRows(mapped)
      setUploadFileName(file.name)
      setUploadNotice(`Parsed ${mapped.length} questions. Getting Bloom and difficulty suggestions from the rule-based classifier…`)
      let classified = mapped
      try {
        for (let index = 0; index < mapped.length; index += 100) {
          const batch = mapped.slice(index, index + 100)
          const { suggestions } = await classifyTeacherQuestionBatch(batch.map((row) => {
            const options = [row.option_a, row.option_b, row.option_c, row.option_d].filter((option) => option.trim())
            const answerLabel = row.correct_answer.trim().match(/^(?:option\\s*)?([A-D])$/i)?.[1]
            const answer = answerLabel ? options[answerLabel.toUpperCase().charCodeAt(0) - 65] ?? row.correct_answer : row.correct_answer
            return { question: row.question, question_type: row.question_type, subject: row.subject.trim().toLowerCase() || subject, topic: row.topic || 'General', correct_answer: answer, marking_rubric: row.marking_rubric, test_cases: row.test_cases, options, ...(row.marks ? { marks: Number(row.marks) } : {}), ...(row.time_seconds ? { time_seconds: Number(row.time_seconds) } : {}) }
          }))
          classified = classified.map((row, rowIndex) => {
            const suggestion = suggestions[rowIndex - index]
            return suggestion ? { ...row, suggested_bloom_level: suggestion.bloom_level, suggested_difficulty: suggestion.difficulty, bloom_confidence: suggestion.bloom_confidence, bloom_reason: suggestion.bloom_reason, difficulty_reason: suggestion.difficulty_reason } : row
          })
          setUploadRows([...classified])
        }
        setUploadNotice(`Parsed ${mapped.length} questions and generated rule-based suggestions. Review or override every field before saving drafts.`)
      } catch (reason) {
        setUploadNotice(`Parsed ${mapped.length} questions, but suggestions could not be loaded (${reason instanceof Error ? reason.message : 'classifier unavailable'}). The backend will still classify them when saved.`)
      }
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not read this question bank.') }
    finally { setBusy(false); if (uploadRef.current) uploadRef.current.value = '' }
  }

  const updateUploadRow = (index: number, update: Partial<QuestionBankRow>) => {
    setUploadRows((rows) => rows.map((row, rowIndex) => rowIndex === index ? { ...row, ...update } : row))
  }

  const saveUploadRows = async () => {
    if (!uploadRows.length) return
    const normalized = uploadRows.map((row) => {
      const concept = concepts.find((item) => item.concept_id === row.concept_id)
      const optionFields = [row.option_a, row.option_b, row.option_c, row.option_d]
      const lastOptionIndex = optionFields.reduce((last, option, index) => option.trim() ? index : last, -1)
      const options = optionFields.slice(0, lastOptionIndex + 1)
      const answerLabel = row.correct_answer.trim().match(/^(?:option\s*)?([A-D])$/i)?.[1]
      const answerKey = row.question_type === 'mcq'
        ? (options[answerLabel ? answerLabel.toUpperCase().charCodeAt(0) - 65 : options.findIndex((option) => option.trim().toLowerCase() === row.correct_answer.trim().toLowerCase())] ?? row.correct_answer)
        : row.correct_answer
      const question = row.question
      const level = row.bloom_level.trim().toLowerCase().replace(/^bt/, '')
      const bloomNames: Record<string, string> = { '1': 'remember', '2': 'understand', '3': 'apply', '4': 'analyze', '5': 'evaluate', '6': 'create' }
      return {
        subject, class_level: classLevel, chapter: concept?.chapter ?? row.topic, topic: row.topic,
        ...(concept ? { concept_id: concept.concept_id } : {}), question, question_type: row.question_type, options,
        answer_guide: answerKey || row.marking_rubric || row.test_cases,
        explanation: row.explanation,
        ...(row.marks.trim() ? { marks: Number(row.marks) } : {}),
        ...(row.time_seconds.trim() ? { time_seconds: Number(row.time_seconds) } : {}),
        ...(row.difficulty ? { difficulty: row.difficulty.toLowerCase() } : {}),
        ...(row.bloom_level ? { bloom_level: bloomNames[level] ?? level } : {}),
        source_reference_ids: [], supporting_chunk_ids: [],
      }
    })
    const invalid = uploadRows.findIndex((row) => uploadRowErrors(row, concepts, subject).length > 0)
    if (invalid >= 0) { setError(`Fix row ${invalid + 1} before importing. Every row needs a topic and valid answer.`); return }
    setBusy(true); setError(''); setNotice('')
    let savedCount = 0
    try {
      for (let index = 0; index < normalized.length; index += 100) {
        await importTeacherQuestionBatch(normalized.slice(index, index + 100))
        const batchLength = Math.min(100, normalized.length - index)
        savedCount += batchLength
        setUploadRows((current) => current.slice(batchLength))
      }
      setNotice(`Saved ${normalized.length} questions as drafts. Backend Bloom suggestions are now available in Question bank drafts for teacher review.`)
      setUploadFileName('')
      await refresh()
    } catch (reason) { if (savedCount) await refresh(); setError(`${savedCount ? `${savedCount} questions were saved. ` : ''}${reason instanceof Error ? reason.message : 'Could not save the uploaded questions.'} The remaining preview rows are still available.`) }
    finally { setBusy(false) }
  }

  const approveQuestion = async (itemId: string) => {
    setBusy(true); setError(''); setNotice('')
    try {
      const result = await reviewQuestion(itemId, true)
      setNotice(`Question approved and written to ${result.content_item_path ?? 'the adaptive question bank'} for student practice.`)
      await refresh()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not approve this question.')
    } finally { setBusy(false) }
  }

  return <div className="teacher-learning-app"><StudentNav /><main className="teacher-learning-main">
    <header className="teacher-learning-heading"><div><span className="teacher-kicker">TEACHER WORKSPACE · QUESTION BANK</span><h1>Upload question bank.</h1><p>Import a CSV or Excel file, review every question and its suggestions, then save it for approval.</p></div></header>
    <section className="teacher-filters"><div className="teacher-subject-tabs">{['physics', 'chemistry', 'mathematics'].map((option) => <button key={option} className={subject === option ? 'active' : ''} onClick={() => setSubject(option)}>{option[0].toUpperCase() + option.slice(1)}</button>)}</div><label>Class <select value={classLevel} onChange={(event) => setClassLevel(Number(event.target.value))}><option value={11}>Class 11</option><option value={12}>Class 12</option></select></label><Button variant="neutral" onClick={() => void refresh()} disabled={busy}><RefreshCw size={15} className={busy ? 'spin' : ''} /> Refresh topics</Button></section>
    {error && <div className="teacher-notice error"><AlertCircle size={16} />{error}</div>}{notice && <div className="teacher-notice success"><Check size={16} />{notice}</div>}
    <section className="teacher-panel teacher-bank-upload">
      <div className="teacher-panel-head"><div><span className="teacher-kicker">BULK QUESTION BANK</span><h2><FileSpreadsheet size={19} /> Upload CSV or Excel</h2></div><Upload size={19} /></div>
      <p>Upload a .csv or .xlsx file with <code>question</code> and <code>question_type</code> columns. Review the parsed rows, correct topic mapping and answer keys, then save drafts for teacher approval.</p>
      <div className="teacher-bank-upload-controls"><label className="teacher-file-picker"><input ref={uploadRef} type="file" accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" disabled={busy} onChange={(event) => void uploadBank(event.target.files?.[0])} /><Upload size={15} /> Choose CSV / Excel file</label><a href="data:text/csv;charset=utf-8,question%2Cquestion_type%2Ccorrect_answer%2Cdifficulty%2Cbloom_level%2Csubject%2Ctopic%2Cmarks%2Ctime_seconds%2Cexplanation%2Coption_a%2Coption_b%2Coption_c%2Coption_d%0A%22Calculate the acceleration of a 2 kg body under a 10 N force.%22%2Cnumerical%2C%225 m%2Fs%5E2%22%2C%2C%2Cphysics%2CNewton%27s%20second%20law%2C3%2C120%2C%22Use F%3Dma.%22%2C%2C%2C%2C" download="adapted-question-bank-template.csv">Download CSV template</a>{uploadFileName && <span>{uploadFileName} · {uploadRows.length} rows</span>}</div>
      {uploadNotice && <p className="teacher-upload-message">{uploadNotice}</p>}
      {uploadRows.length > 0 && <>
        <div className="teacher-bank-preview-list">{uploadRows.map((row, index) => {
          const rowErrors = uploadRowErrors(row, concepts, subject)
          return <article className="teacher-bank-preview-card" key={index}>
            <header><b>QUESTION {index + 1}</b><span>{row.question_type.replaceAll('_', ' ')}</span></header>
            <div className="teacher-preview-card-content">
              <label>Question<textarea aria-label={`Question ${index + 1}`} value={row.question} rows={3} onChange={(event) => updateUploadRow(index, { question: event.target.value })} /></label>
              <label>Question type<select aria-label={`Question type ${index + 1}`} value={row.question_type} onChange={(event) => updateUploadRow(index, { question_type: event.target.value })}>{['mcq', 'numerical', 'short_answer', 'descriptive', 'coding'].map((type) => <option key={type} value={type}>{type.replaceAll('_', ' ')}</option>)}</select></label>
              <label>Answer key<textarea aria-label={`Answer key ${index + 1}`} value={row.correct_answer} rows={2} onChange={(event) => updateUploadRow(index, { correct_answer: event.target.value })} /></label>
              {row.question_type === 'mcq' && <fieldset className="teacher-preview-options"><legend>Multiple choice options</legend>{(['option_a', 'option_b', 'option_c', 'option_d'] as const).map((field) => <label key={field}>{field.replace('_', ' ').toUpperCase()}<Input aria-label={`${field} row ${index + 1}`} placeholder={`Enter ${field.replace('_', ' ')}`} value={row[field]} onChange={(event) => updateUploadRow(index, { [field]: event.target.value })} /></label>)}</fieldset>}
              <div className="teacher-preview-meta-grid">
                <label className="teacher-topic-field"><span>Topic or chapter</span><Input aria-label={`Topic ${index + 1}`} value={row.topic} placeholder="Enter a new topic if needed" onChange={(event) => updateUploadRow(index, { topic: event.target.value })} /><small>Enter a topic even when it is not in the concept list.</small></label>
                <label className="teacher-topic-field"><span>Match existing concept (optional)</span><select aria-label={`Concept mapping ${index + 1}`} value={row.concept_id} onChange={(event) => updateUploadRow(index, { concept_id: event.target.value })}><option value="">Create/use entered topic</option>{concepts.map((concept) => <option key={concept.concept_id} value={concept.concept_id}>{concept.chapter} — {concept.name}</option>)}</select></label>
                <label className="teacher-topic-field"><span>Difficulty · Engine: {row.suggested_difficulty || 'pending'}</span>{row.difficulty_reason && <small>{row.difficulty_reason}</small>}<select aria-label={`Difficulty ${index + 1}`} value={row.difficulty ? row.difficulty.toLowerCase() : row.suggested_difficulty ? `suggested:${row.suggested_difficulty}` : ''} onChange={(event) => updateUploadRow(index, { difficulty: event.target.value.startsWith('suggested:') ? '' : event.target.value })}><option value="">Use engine suggestion</option>{row.suggested_difficulty && <option value={`suggested:${row.suggested_difficulty}`}>Suggested: {row.suggested_difficulty}</option>}<option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
                <label className="teacher-topic-field"><span>Bloom level · Engine: {row.suggested_bloom_level || 'pending'}{row.bloom_confidence !== null ? ` (${Math.round(row.bloom_confidence * 100)}%)` : ''}</span>{row.bloom_reason && <small>{row.bloom_reason}</small>}<select aria-label={`Bloom level ${index + 1}`} value={row.bloom_level ? bloomSelectValue(row.bloom_level) : row.suggested_bloom_level ? `suggested:${row.suggested_bloom_level}` : ''} onChange={(event) => updateUploadRow(index, { bloom_level: event.target.value.startsWith('suggested:') ? '' : event.target.value })}><option value="">Use engine suggestion</option>{row.suggested_bloom_level && <option value={`suggested:${row.suggested_bloom_level}`}>Suggested: {row.suggested_bloom_level}</option>}{['BT1 · Remember', 'BT2 · Understand', 'BT3 · Apply', 'BT4 · Analyze', 'BT5 · Evaluate', 'BT6 · Create'].map((level, levelIndex) => <option key={level} value={`BT${levelIndex + 1}`}>{level}</option>)}</select></label>
              </div>
              <div className={rowErrors.length ? 'teacher-preview-validation invalid' : 'teacher-preview-validation'}>{rowErrors.length ? <><b>Needs attention</b><ul>{rowErrors.map((message) => <li key={message}>{message}</li>)}</ul></> : <b>Ready to save</b>}</div>
            </div>
          </article>
        })}</div>
        <div className="teacher-upload-footer"><p>Rule-based engine suggestions are shown for review. Keep the suggestion or choose another value. Drafts remain hidden from learners until approved.</p><Button className="teacher-approve" disabled={busy || uploadRows.some((row) => uploadRowErrors(row, concepts, subject).length > 0)} onClick={() => void saveUploadRows()}>{busy ? <LoaderCircle className="spin" size={15} /> : <Check size={15} />} Save {uploadRows.length} questions for review</Button><Button variant="neutral" disabled={busy} onClick={() => { setUploadRows([]); setUploadFileName(''); setUploadNotice('') }}>Clear preview</Button></div>
      </>}
    </section>
    <section className="teacher-panel teacher-pending-bank">
      <div className="teacher-panel-head"><div><span className="teacher-kicker">TEACHER APPROVAL</span><h2>Questions waiting for review</h2></div><span>{pendingQuestions.length} drafts</span></div>
      {pendingQuestions.length ? <div className="teacher-pending-list">{pendingQuestions.map((item) => <article key={item.item_id}>
        <div><span className="teacher-kicker">{item.item_type.replaceAll('_', ' ')} · {item.chapter}</span><h3>{item.question}</h3>{item.item_type === 'mcq' && <ol type="A">{item.options?.map((option, index) => <li key={`${item.item_id}-${index}`}>{option}</li>)}</ol>}<small>Answer: {item.answer_guide}</small><div className="teacher-pending-tags"><span>{item.difficulty}</span><span>{item.bloom_level}</span></div></div>
        <Button className="teacher-approve" disabled={busy} onClick={() => void approveQuestion(item.item_id)}><Check size={15} /> Approve to student bank</Button>
      </article>)}</div> : <p className="teacher-empty">No saved drafts need approval. Each approved question is written to its own JSON file and becomes available to students.</p>}
    </section>
  </main></div>
}
