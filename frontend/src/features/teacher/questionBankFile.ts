export type QuestionBankRow = {
  question: string
  question_type: string
  correct_answer: string
  difficulty: string
  bloom_level: string
  subject: string
  topic: string
  marks: string
  time_seconds: string
  explanation: string
  marking_rubric: string
  test_cases: string
  option_a: string
  option_b: string
  option_c: string
  option_d: string
  concept_id: string
  suggested_bloom_level: string
  suggested_difficulty: string
  bloom_confidence: number | null
  bloom_reason: string
  difficulty_reason: string
  errors: string[]
}

const HEADERS = [
  'question', 'question_type', 'correct_answer', 'difficulty', 'bloom_level',
  'subject', 'topic', 'marks', 'time_seconds', 'explanation',
  'marking_rubric', 'test_cases',
  'option_a', 'option_b', 'option_c', 'option_d', 'concept_id',
] as const

function normalizeHeader(value: string) {
  return value.replace(/^\uFEFF/, '').trim().toLowerCase().replace(/[\s-]+/g, '_')
}

export function parseCsv(text: string): string[][] {
  const rows: string[][] = []
  let row: string[] = []
  let cell = ''
  let quoted = false
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index]
    if (char === '"') {
      if (quoted && text[index + 1] === '"') { cell += '"'; index += 1 }
      else quoted = !quoted
    } else if (char === ',' && !quoted) {
      row.push(cell); cell = ''
    } else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[index + 1] === '\n') index += 1
      row.push(cell); cell = ''
      if (row.some((value) => value.trim())) rows.push(row)
      row = []
    } else cell += char
  }
  if (quoted) throw new Error('The CSV contains an unclosed quoted field.')
  row.push(cell)
  if (row.some((value) => value.trim())) rows.push(row)
  return rows
}

export async function parseXlsx(file: File): Promise<string[][]> {
  const bytes = new Uint8Array(await file.arrayBuffer())
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
  const decoder = new TextDecoder()
  const findSignature = (signature: number) => {
    for (let offset = bytes.length - 22; offset >= Math.max(0, bytes.length - 65_557); offset -= 1) {
      if (view.getUint32(offset, true) === signature) return offset
    }
    return -1
  }
  const eocd = findSignature(0x06054b50)
  if (eocd < 0) throw new Error('This Excel file is not a valid .xlsx workbook.')
  const entries = view.getUint16(eocd + 10, true)
  const centralOffset = view.getUint32(eocd + 16, true)
  const files = new Map<string, { method: number; size: number; offset: number }>()
  let cursor = centralOffset
  for (let index = 0; index < entries; index += 1) {
    if (view.getUint32(cursor, true) !== 0x02014b50) throw new Error('Could not read the Excel workbook directory.')
    const method = view.getUint16(cursor + 10, true)
    const size = view.getUint32(cursor + 20, true)
    const nameLength = view.getUint16(cursor + 28, true)
    const extraLength = view.getUint16(cursor + 30, true)
    const commentLength = view.getUint16(cursor + 32, true)
    const offset = view.getUint32(cursor + 42, true)
    const name = decoder.decode(bytes.slice(cursor + 46, cursor + 46 + nameLength))
    files.set(name, { method, size, offset })
    cursor += 46 + nameLength + extraLength + commentLength
  }
  const readFile = async (path: string) => {
    const entry = files.get(path)
    if (!entry) return null
    const start = entry.offset
    const nameLength = view.getUint16(start + 26, true)
    const extraLength = view.getUint16(start + 28, true)
    const dataStart = start + 30 + nameLength + extraLength
    const compressed = bytes.slice(dataStart, dataStart + entry.size)
    if (entry.method === 0) return decoder.decode(compressed)
    if (entry.method !== 8 || typeof DecompressionStream === 'undefined') throw new Error('This browser cannot decompress this .xlsx file.')
    const stream = new Blob([compressed]).stream().pipeThrough(new DecompressionStream('deflate-raw' as CompressionFormat))
    return await new Response(stream).text()
  }
  let sheetPath = 'xl/worksheets/sheet1.xml'
  const workbook = await readFile('xl/workbook.xml')
  const rels = await readFile('xl/_rels/workbook.xml.rels')
  if (workbook && rels) {
    const workbookDoc = new DOMParser().parseFromString(workbook, 'application/xml')
    const relDoc = new DOMParser().parseFromString(rels, 'application/xml')
    const firstSheet = workbookDoc.querySelector('sheets sheet')
    const relationId = firstSheet?.getAttribute('r:id')
    const relationship = [...relDoc.querySelectorAll('Relationship')].find((item) => item.getAttribute('Id') === relationId)
    const target = relationship?.getAttribute('Target')
    if (target) sheetPath = target.startsWith('/') ? target.slice(1) : `xl/${target.replace(/^\.\//, '')}`
  }
  const sheet = await readFile(sheetPath)
  if (!sheet) throw new Error('The Excel workbook does not contain a readable first worksheet.')
  const sharedXml = await readFile('xl/sharedStrings.xml')
  const shared = sharedXml
    ? [...new DOMParser().parseFromString(sharedXml, 'application/xml').querySelectorAll('si')].map((item) => [...item.querySelectorAll('t')].map((node) => node.textContent ?? '').join(''))
    : []
  const doc = new DOMParser().parseFromString(sheet, 'application/xml')
  const cellValue = (cell: Element) => {
    const type = cell.getAttribute('t')
    if (type === 'inlineStr') return [...cell.querySelectorAll('is t')].map((node) => node.textContent ?? '').join('')
    const value = cell.querySelector('v')?.textContent ?? ''
    return type === 's' ? (shared[Number(value)] ?? '') : value
  }
  return [...doc.querySelectorAll('sheetData row')].map((xmlRow) => {
    const values: string[] = []
    for (const cell of [...xmlRow.querySelectorAll(':scope > c')]) {
      const ref = cell.getAttribute('r') ?? ''
      const letters = ref.match(/^[A-Z]+/)?.[0] ?? ''
      const column = [...letters].reduce((sum, char) => sum * 26 + char.charCodeAt(0) - 64, 0) - 1
      values[column] = cellValue(cell)
    }
    return values.map((value) => value ?? '')
  }).filter((values) => values.some((value) => value.trim()))
}

export function rowsToQuestionBank(rows: string[][]): QuestionBankRow[] {
  if (rows.length < 2) throw new Error('The file needs a header row and at least one question.')
  const headers = rows[0].map(normalizeHeader)
  const missing = ['question', 'question_type'].filter((required) => !headers.includes(required))
  if (missing.length) throw new Error(`Missing required column${missing.length > 1 ? 's' : ''}: ${missing.join(', ')}`)
  return rows.slice(1).map((cells, rowIndex) => {
    const values = Object.fromEntries(headers.map((header, column) => [header, cells[column]?.trim() ?? ''])) as Record<string, string>
    const record = Object.fromEntries(HEADERS.map((header) => [header, values[header] ?? ''])) as Omit<QuestionBankRow, 'errors' | 'suggested_bloom_level' | 'suggested_difficulty' | 'bloom_confidence' | 'bloom_reason' | 'difficulty_reason'>
    const errors: string[] = []
    const type = record.question_type.toLowerCase().replace(/[\s-]+/g, '_')
    record.question_type = type
    if (!record.question.trim()) errors.push('Question is required.')
    if (!['mcq', 'numerical', 'short_answer', 'descriptive', 'coding'].includes(type)) errors.push('Use mcq, numerical, short_answer, descriptive, or coding.')
    if (type === 'mcq') {
      if (!record.option_a || !record.option_b) errors.push('MCQ requires at least option_a and option_b.')
      if (!record.correct_answer) errors.push('MCQ correct_answer is required.')
    }
    if (['numerical', 'short_answer'].includes(type) && !record.correct_answer) errors.push('correct_answer is required for this question type.')
    if (type === 'descriptive' && !record.correct_answer && !record.marking_rubric) errors.push('Provide correct_answer or marking_rubric.')
    if (type === 'coding' && !record.correct_answer && !record.test_cases) errors.push('Provide correct_answer or test_cases.')
    if (record.difficulty && !['easy', 'medium', 'hard'].includes(record.difficulty.toLowerCase())) errors.push('Difficulty must be Easy, Medium, or Hard.')
    if (record.bloom_level && !/^(bt)?[1-6]$|^(remember|understand|apply|analyze|evaluate|create)$/i.test(record.bloom_level)) errors.push('Bloom level must be BT1–BT6 or a taxonomy name.')
    if (record.marks && (!Number.isFinite(Number(record.marks)) || Number(record.marks) <= 0)) errors.push('Marks must be a positive number.')
    if (record.time_seconds && (!Number.isInteger(Number(record.time_seconds)) || Number(record.time_seconds) <= 0)) errors.push('time_seconds must be a positive whole number.')
    if (!record.topic.trim()) errors.push('Topic is required to map the question to an adaptive concept.')
    return { ...record, suggested_bloom_level: '', suggested_difficulty: '', bloom_confidence: null, bloom_reason: '', difficulty_reason: '', errors: errors.map((error) => `Row ${rowIndex + 2}: ${error}`) }
  })
}
