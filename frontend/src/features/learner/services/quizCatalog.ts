import { PROBLEMS } from '../../../services/data'
import type { Difficulty, JeeSubjectId, Problem } from '../../../types'
import { SUBJECTS } from './problemCatalog'

export interface QuizQuestion {
  id: string
  prompt: string
  choices?: string[]
  answer: string
  explanation: string
}

export interface ChapterQuiz {
  id: string
  subject: JeeSubjectId
  chapter: string
  name: string
  questionCount: number
  maxMarks: number
  timeLimitMinutes: number
  difficulty: Difficulty
  questions: QuizQuestion[]
  source: 'local-demo-bank' | 'mock'
}

export const CHAPTERS_BY_SUBJECT: Record<JeeSubjectId, string[]> = {
  physics: [
    'Units and Dimensions', 'Kinematics', "Newton's Laws of Motion (NLM)", 'Work, Energy and Power',
    'Centre of Mass', 'Rotational Motion', 'Gravitation', 'Thermodynamics', 'Oscillations and Waves',
    'Electrostatics', 'Current Electricity', 'Magnetism', 'Optics', 'Modern Physics',
  ],
  chemistry: [
    'Some Basic Concepts of Chemistry', 'Atomic Structure', 'Chemical Bonding', 'Chemical Thermodynamics',
    'Chemical Equilibrium', 'Ionic Equilibrium', 'Solutions', 'Electrochemistry', 'Chemical Kinetics',
    'Coordination Compounds', 'General Organic Chemistry (GOC)', 'Hydrocarbons',
    'Aldehydes, Ketones and Carboxylic Acids',
  ],
  mathematics: [
    'Sets, Relations and Functions', 'Trigonometry', 'Complex Numbers', 'Quadratic Equations',
    'Sequences and Series', 'Permutations and Combinations', 'Binomial Theorem',
    'Limits, Continuity and Differentiability', 'Applications of Derivatives', 'Indefinite Integration',
    'Definite Integration', 'Area Under the Curve', 'Differential Equations', 'Matrices and Determinants',
    'Probability', 'Vectors and 3D Geometry', 'Coordinate Geometry',
  ],
}

type MockQuestion = Omit<QuizQuestion, 'id'>
const mockQuestions: Partial<Record<JeeSubjectId, Record<string, MockQuestion>>> = {
  physics: {
    'Units and Dimensions': { prompt: 'The dimensions of force are:', choices: ['[MLT⁻²]', '[ML²T⁻²]', '[ML⁻¹T⁻²]', '[M⁰LT⁻¹]'], answer: '[MLT⁻²]', explanation: 'Force = mass × acceleration, so its dimensions are [M][LT⁻²] = [MLT⁻²].' },
    Kinematics: { prompt: 'The slope of a position–time graph represents:', choices: ['Acceleration', 'Velocity', 'Displacement', 'Force'], answer: 'Velocity', explanation: 'The derivative of position with respect to time is velocity.' },
    "Newton's Laws of Motion (NLM)": { prompt: 'If the net external force on a body is zero, its momentum:', choices: ['Must be zero', 'Remains constant', 'Increases uniformly', 'Changes direction continuously'], answer: 'Remains constant', explanation: 'Newton’s second law gives net force as the rate of change of momentum.' },
    'Work, Energy and Power': { prompt: 'The work done by the net force on a particle equals the change in its:', choices: ['Momentum', 'Kinetic energy', 'Potential energy only', 'Mass'], answer: 'Kinetic energy', explanation: 'The work–energy theorem states that net work equals the change in kinetic energy.' },
    'Centre of Mass': { prompt: 'For two particles on a line, the centre of mass is closer to the particle with:', choices: ['Greater mass', 'Greater speed', 'Greater acceleration', 'Smaller momentum'], answer: 'Greater mass', explanation: 'The centre of mass is the mass-weighted average of the particles’ positions.' },
    Gravitation: { prompt: 'If the distance between two point masses doubles, the gravitational force becomes:', choices: ['Twice as large', 'Half as large', 'One quarter as large', 'Four times as large'], answer: 'One quarter as large', explanation: 'Newton’s law of gravitation follows an inverse-square distance relation.' },
    Thermodynamics: { prompt: 'For a system using the convention that work is done by the system, the first law is:', choices: ['ΔQ = ΔU + W', 'ΔQ = ΔU − W', 'ΔU = ΔQ + W', 'W = ΔQ + ΔU'], answer: 'ΔQ = ΔU + W', explanation: 'Heat supplied changes internal energy and may also be used to do work.' },
    'Oscillations and Waves': { prompt: 'In simple harmonic motion, acceleration is:', choices: ['Proportional to displacement and in the same direction', 'Proportional to displacement and opposite in direction', 'Constant', 'Always zero'], answer: 'Proportional to displacement and opposite in direction', explanation: 'For SHM, a = −ω²x, so acceleration points toward equilibrium.' },
    Electrostatics: { prompt: 'If the separation between two point charges doubles, the magnitude of their force becomes:', choices: ['2F', 'F/2', 'F/4', '4F'], answer: 'F/4', explanation: 'Coulomb’s law gives an inverse-square dependence on separation.' },
    'Current Electricity': { prompt: 'For an ohmic conductor at constant temperature, the current is:', choices: ['Proportional to voltage', 'Inversely proportional to voltage', 'Independent of voltage', 'Proportional to voltage squared'], answer: 'Proportional to voltage', explanation: 'Ohm’s law states V = IR when resistance is constant.' },
    Magnetism: { prompt: 'The magnetic force on a moving charge is zero when its velocity is:', choices: ['Perpendicular to the field', 'Parallel to the field', 'At 45° to the field', 'Changing in magnitude'], answer: 'Parallel to the field', explanation: 'The magnetic force magnitude is qvB sin θ, which is zero when θ = 0°.' },
    Optics: { prompt: 'The power of a lens with focal length 0.5 m is:', choices: ['0.5 D', '1 D', '2 D', '5 D'], answer: '2 D', explanation: 'Lens power in dioptres is P = 1/f when f is measured in metres.' },
    'Modern Physics': { prompt: 'In the photoelectric effect, the maximum kinetic energy of emitted electrons depends on:', choices: ['Light frequency', 'Light intensity only', 'Emitter area', 'Exposure time only'], answer: 'Light frequency', explanation: 'The photon energy hf determines the maximum kinetic energy after overcoming the work function.' },
  },
  chemistry: {
    'Some Basic Concepts of Chemistry': { prompt: 'The number of moles in 18 g of water (molar mass 18 g mol⁻¹) is:', choices: ['0.5 mol', '1 mol', '2 mol', '18 mol'], answer: '1 mol', explanation: 'The amount in moles is mass divided by molar mass: 18/18 = 1 mol.' },
    'Atomic Structure': { prompt: 'The maximum number of electrons in the n = 2 shell is:', choices: ['2', '8', '18', '32'], answer: '8', explanation: 'The shell capacity is 2n², giving 2 × 2² = 8.' },
    'Chemical Bonding': { prompt: 'The molecular geometry of CH₄ is:', choices: ['Linear', 'Trigonal planar', 'Tetrahedral', 'Square planar'], answer: 'Tetrahedral', explanation: 'Four bonding pairs around carbon arrange tetrahedrally.' },
    'Chemical Thermodynamics': { prompt: 'At constant temperature and pressure, a spontaneous process has:', choices: ['ΔG < 0', 'ΔG > 0', 'ΔG = ΔH always', 'ΔS = 0 always'], answer: 'ΔG < 0', explanation: 'A negative Gibbs free-energy change is the spontaneity criterion at constant T and P.' },
    'Chemical Equilibrium': { prompt: 'At equilibrium, the forward and reverse reaction rates are:', choices: ['Both zero', 'Equal', 'Opposite in magnitude', 'Always equal to one'], answer: 'Equal', explanation: 'Dynamic equilibrium occurs when the forward and reverse rates are equal.' },
    'Ionic Equilibrium': { prompt: 'For an aqueous solution at 25°C, pH is defined as:', choices: ['log₁₀[H⁺]', '−log₁₀[H⁺]', '1/[H⁺]', '[OH⁻]'], answer: '−log₁₀[H⁺]', explanation: 'By definition, pH = −log₁₀ of the hydrogen-ion concentration.' },
    Solutions: { prompt: 'Molarity is the number of moles of solute per:', choices: ['Kilogram of solvent', 'Litre of solution', 'Litre of solvent', 'Mole of solvent'], answer: 'Litre of solution', explanation: 'Molarity is defined as moles of solute per litre of solution.' },
    'Coordination Compounds': { prompt: 'The coordination number of cobalt in [Co(NH₃)₆]Cl₃ is:', choices: ['3', '4', '6', '9'], answer: '6', explanation: 'Six ammonia ligands are directly coordinated to the cobalt centre.' },
    'General Organic Chemistry (GOC)': { prompt: 'An electron-withdrawing inductive group generally stabilises a nearby:', choices: ['Carbocation', 'Carbanion', 'Neutral alkane only', 'Free proton only'], answer: 'Carbanion', explanation: 'Electron-withdrawing groups can disperse and stabilise negative charge through the sigma framework.' },
    Hydrocarbons: { prompt: 'Hydrogenation of an alkene typically produces an:', choices: ['Alkane', 'Alkyne', 'Alcohol', 'Aldehyde'], answer: 'Alkane', explanation: 'Hydrogen adds across the carbon–carbon double bond to form a saturated alkane.' },
    'Aldehydes, Ketones and Carboxylic Acids': { prompt: 'Aldehydes and ketones commonly undergo nucleophilic addition at the:', choices: ['Carbonyl carbon', 'Oxygen atom only', 'Alkyl hydrogen', 'C–C single bond'], answer: 'Carbonyl carbon', explanation: 'The carbonyl carbon is electrophilic because the C=O bond is polarised.' },
  },
  mathematics: {
    'Sets, Relations and Functions': { prompt: 'A function assigns each element of its domain to:', choices: ['Exactly one codomain element', 'At least two codomain elements', 'No codomain elements', 'Any number of domain elements'], answer: 'Exactly one codomain element', explanation: 'A function associates every domain element with exactly one output.' },
    Trigonometry: { prompt: 'For every real θ, sin²θ + cos²θ equals:', choices: ['0', '1', 'sin θ', 'cos θ'], answer: '1', explanation: 'This is the fundamental Pythagorean trigonometric identity.' },
    'Complex Numbers': { prompt: 'The value of i² is:', choices: ['1', '−1', 'i', '−i'], answer: '−1', explanation: 'The imaginary unit is defined by i² = −1.' },
    'Quadratic Equations': { prompt: 'For ax² + bx + c = 0, the discriminant is:', choices: ['b² − 4ac', 'b² + 4ac', 'a² − 4bc', '4ac − b'], answer: 'b² − 4ac', explanation: 'The discriminant b² − 4ac determines the nature of the roots.' },
    'Sequences and Series': { prompt: 'The nth term of an arithmetic progression with first term a and common difference d is:', choices: ['a + (n−1)d', 'a + nd', 'adⁿ', 'a(n−1)d'], answer: 'a + (n−1)d', explanation: 'Each step adds one common difference, so the nth term is a + (n−1)d.' },
    'Permutations and Combinations': { prompt: 'The number of ways to arrange r distinct objects selected from n distinct objects is:', choices: ['nCr', 'nPr', 'rⁿ', 'n! + r!'], answer: 'nPr', explanation: 'A permutation counts ordered selections: nPr = n!/(n−r)!.' },
    'Binomial Theorem': { prompt: 'The coefficient of x in the expansion of (1 + x)⁵ is:', choices: ['1', '5', '10', '25'], answer: '5', explanation: 'The x term has coefficient ⁵C₁ = 5.' },
    'Limits, Continuity and Differentiability': { prompt: 'The limit limₓ→₀ (sin x)/x, with x in radians, is:', choices: ['0', '1', '−1', 'Does not exist'], answer: '1', explanation: 'This is a standard fundamental trigonometric limit.' },
    'Applications of Derivatives': { prompt: 'At an interior differentiable local extremum, a necessary condition is:', choices: ['f′(x) = 0', 'f(x) = 0', 'f″(x) = 0 always', 'f′(x) = 1'], answer: 'f′(x) = 0', explanation: 'Fermat’s theorem gives a zero first derivative at an interior differentiable extremum.' },
    'Indefinite Integration': { prompt: 'An antiderivative of x² is:', choices: ['2x', 'x³/3 + C', 'x²/2 + C', '3x² + C'], answer: 'x³/3 + C', explanation: 'Integrating x² increases the power by one and divides by the new power.' },
    'Definite Integration': { prompt: 'The value of ∫₀¹ 2x dx is:', choices: ['0', '1', '2', '4'], answer: '1', explanation: 'An antiderivative is x², so the value is 1² − 0² = 1.' },
    'Area Under the Curve': { prompt: 'The area under y = x from x = 0 to x = 2 is:', choices: ['1', '2', '3', '4'], answer: '2', explanation: 'The area is ∫₀² x dx = [x²/2]₀² = 2.' },
    'Differential Equations': { prompt: 'The order of d²y/dx² + 3dy/dx + y = 0 is:', choices: ['1', '2', '3', '0'], answer: '2', explanation: 'The highest derivative present is the second derivative.' },
    'Matrices and Determinants': { prompt: 'The determinant of [[a, b], [c, d]] is:', choices: ['ad − bc', 'ac − bd', 'ab − cd', 'ad + bc'], answer: 'ad − bc', explanation: 'The determinant of a 2×2 matrix is the product of the main diagonal minus the other diagonal.' },
    Probability: { prompt: 'For mutually exclusive events A and B, P(A ∪ B) equals:', choices: ['P(A) + P(B)', 'P(A)P(B)', 'P(A) − P(B)', '1 − P(A)'], answer: 'P(A) + P(B)', explanation: 'Mutually exclusive events have no overlap, so their probabilities add.' },
    'Vectors and 3D Geometry': { prompt: 'If two nonzero vectors are perpendicular, their dot product is:', choices: ['−1', '0', '1', 'Their magnitudes multiplied'], answer: '0', explanation: 'The dot product is |a||b|cos θ; at 90°, cos θ = 0.' },
    'Coordinate Geometry': { prompt: 'The slope of the line through (x₁, y₁) and (x₂, y₂) is:', choices: ['(y₂−y₁)/(x₂−x₁)', '(x₂−x₁)/(y₂−y₁)', 'x₁ + y₁', 'x₂ − x₁'], answer: '(y₂−y₁)/(x₂−x₁)', explanation: 'Slope is the change in y divided by the change in x.' },
  },
}

const chapterForProblem: Record<string, { subject: JeeSubjectId; chapter: string }> = {
  'PHY-001': { subject: 'physics', chapter: 'Rotational Motion' }, 'PHY-002': { subject: 'physics', chapter: 'Rotational Motion' },
  'PHY-003': { subject: 'physics', chapter: 'Rotational Motion' }, 'PHY-004': { subject: 'physics', chapter: 'Rotational Motion' },
  'PHY-005': { subject: 'physics', chapter: "Newton's Laws of Motion (NLM)" }, 'PHY-006': { subject: 'physics', chapter: 'Rotational Motion' },
  'PHY-007': { subject: 'physics', chapter: 'Rotational Motion' }, 'PHY-008': { subject: 'physics', chapter: 'Rotational Motion' },
  'PHY-009': { subject: 'physics', chapter: 'Rotational Motion' }, 'PHY-010': { subject: 'physics', chapter: 'Rotational Motion' },
  'CHEM-001': { subject: 'chemistry', chapter: 'Electrochemistry' }, 'CHEM-002': { subject: 'chemistry', chapter: 'Electrochemistry' },
  'CHEM-003': { subject: 'chemistry', chapter: 'Electrochemistry' }, 'CHEM-004': { subject: 'chemistry', chapter: 'Electrochemistry' },
  'CHEM-005': { subject: 'chemistry', chapter: 'Electrochemistry' }, 'CHEM-006': { subject: 'chemistry', chapter: 'Electrochemistry' },
  'CHEM-007': { subject: 'chemistry', chapter: 'Electrochemistry' }, 'DEMO-KIN-001': { subject: 'chemistry', chapter: 'Chemical Kinetics' },
  'MATH-001': { subject: 'mathematics', chapter: 'Definite Integration' }, 'MATH-002': { subject: 'mathematics', chapter: 'Limits, Continuity and Differentiability' },
  'MATH-003': { subject: 'mathematics', chapter: 'Area Under the Curve' }, 'MATH-004': { subject: 'mathematics', chapter: 'Differential Equations' },
  'MATH-005': { subject: 'mathematics', chapter: 'Definite Integration' }, 'MATH-006': { subject: 'mathematics', chapter: 'Limits, Continuity and Differentiability' },
  'MATH-007': { subject: 'mathematics', chapter: 'Definite Integration' },
}

function asQuizQuestion(problem: Problem): QuizQuestion {
  return { id: problem.id, prompt: problem.statement, choices: problem.choices, answer: problem.answer, explanation: problem.explanation }
}

function createMockQuiz(subject: JeeSubjectId, chapter: string): ChapterQuiz {
  const question = mockQuestions[subject]?.[chapter]
  const safeQuestion: MockQuestion = question ?? {
    prompt: `Sample question for ${chapter}: which topic would you review first when approaching a problem from this chapter?`,
    choices: [chapter, 'A topic from another subject', 'An unrelated formula', 'None of these'],
    answer: chapter,
    explanation: `This preview question is labeled mock content for ${chapter}. Replace it with a teacher-reviewed question when chapter content is available.`,
  }
  return {
    id: `mock-${subject}-${chapter.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-quiz-1`, subject, chapter,
    name: 'Quiz 1', questionCount: 1, maxMarks: 4, timeLimitMinutes: 5, difficulty: 'Easy', source: 'mock',
    questions: [{ ...safeQuestion, id: `mock-question-${subject}-${chapter.toLowerCase().replace(/[^a-z0-9]+/g, '-')}` }],
  }
}

function createLocalBankQuizzes(subject: JeeSubjectId, chapter: string, problems: Problem[]): ChapterQuiz[] {
  if (subject === 'physics' && chapter === 'Rotational Motion') {
    const buckets: { difficulty: Difficulty; problems: Problem[] }[] = (['Easy', 'Medium', 'Hard'] as Difficulty[]).map((difficulty) => ({ difficulty, problems: problems.filter((problem) => problem.difficulty === difficulty) })).filter((bucket) => bucket.problems.length > 0)
    return buckets.map((bucket, index) => ({
      id: `local-physics-rotation-quiz-${index + 1}`, subject, chapter, name: `Quiz ${index + 1}`,
      questionCount: bucket.problems.length, maxMarks: bucket.problems.length * 4,
      timeLimitMinutes: Math.max(5, bucket.problems.length * 5), difficulty: bucket.difficulty,
      questions: bucket.problems.map(asQuizQuestion), source: 'local-demo-bank',
    }))
  }
  return [{
    id: `local-${subject}-${chapter.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-quiz-1`, subject, chapter,
    name: 'Quiz 1', questionCount: problems.length, maxMarks: problems.length * 4,
    timeLimitMinutes: Math.max(5, problems.length * 5), difficulty: 'Medium',
    questions: problems.map(asQuizQuestion), source: problems.some((problem) => problem.id.startsWith('DEMO-')) ? 'mock' : 'local-demo-bank',
  }]
}

const byChapter = new Map<string, Problem[]>()
PROBLEMS.forEach((problem) => {
  const chapter = chapterForProblem[problem.id]
  if (!chapter) return
  const key = `${chapter.subject}:${chapter.chapter}`
  byChapter.set(key, [...(byChapter.get(key) ?? []), problem])
})

export const CHAPTER_QUIZZES: ChapterQuiz[] = SUBJECTS.flatMap(({ id: subject }) => CHAPTERS_BY_SUBJECT[subject].flatMap((chapter) => {
  const problems = byChapter.get(`${subject}:${chapter}`) ?? []
  return problems.length ? createLocalBankQuizzes(subject, chapter, problems) : [createMockQuiz(subject, chapter)]
}))

export interface QuizAttempt {
  quizId: string
  status: 'in_progress' | 'completed'
  startedAt: string
  answers: Record<string, string>
  submittedAt?: string
  score?: number
}

export function selectedTopicsMatchQuiz(quiz: ChapterQuiz, selectedKeys: Set<string>): boolean {
  if (selectedKeys.size === 0) return true
  const chapterTopicAliases: Record<string, string[]> = {
    'physics:Rotational Motion': ['Rotational Motion'],
    "physics:Newton's Laws of Motion (NLM)": ['Laws of Motion', 'Newton’s Laws of Motion (NLM)'],
    'physics:Work, Energy and Power': ['Work, Energy and Power'],
    'physics:Kinematics': ['Kinematics'],
    'physics:Centre of Mass': ['Centre of Mass'],
    'physics:Thermodynamics': ['Thermodynamics'],
    'physics:Gravitation': ['Gravitation'],
    'physics:Electrostatics': ['Electrostatics'],
    'physics:Current Electricity': ['Current Electricity'],
    'physics:Magnetism': ['Magnetism'],
    'physics:Optics': ['Optics'],
    'physics:Modern Physics': ['Modern Physics'],
    'physics:Oscillations and Waves': ['Oscillations and Waves'],
    'chemistry:Atomic Structure': ['Atomic Structure'],
    'chemistry:Chemical Bonding': ['Chemical Bonding'],
    'chemistry:Chemical Thermodynamics': ['Thermodynamics'],
    'chemistry:Chemical Equilibrium': ['Chemical Equilibrium'],
    'chemistry:Ionic Equilibrium': ['Ionic Equilibrium'],
    'chemistry:Solutions': ['Solutions'],
    'chemistry:Electrochemistry': ['Electrochemistry'],
    'chemistry:Chemical Kinetics': ['Chemical Kinetics'],
    'chemistry:Coordination Compounds': ['Coordination Compounds'],
    'chemistry:General Organic Chemistry (GOC)': ['GOC', 'Organic Chemistry'],
    'chemistry:Hydrocarbons': ['Hydrocarbons', 'Organic Chemistry'],
    'chemistry:Aldehydes, Ketones and Carboxylic Acids': ['Organic Chemistry'],
    'mathematics:Area Under the Curve': ['Area Under the Curve'],
    'mathematics:Limits, Continuity and Differentiability': ['Limits', 'Continuity and Differentiability'],
    'mathematics:Applications of Derivatives': ['Applications of Derivatives'],
    'mathematics:Indefinite Integration': ['Integration'],
    'mathematics:Definite Integration': ['Integration'],
    'mathematics:Differential Equations': ['Differential Equations'],
    'mathematics:Matrices and Determinants': ['Matrices', 'Determinants'],
    'mathematics:Probability': ['Probability'],
    'mathematics:Vectors and 3D Geometry': ['Vectors', '3D Geometry'],
    'mathematics:Complex Numbers': ['Complex Numbers'],
    'mathematics:Coordinate Geometry': ['Coordinate Geometry'],
    'mathematics:Sequences and Series': ['Sequences and Series'],
    'mathematics:Permutations and Combinations': ['Permutations and Combinations'],
  }
  const keysForQuiz = new Set<string>([
    `${quiz.subject}:${quiz.chapter}`,
    ...(chapterTopicAliases[`${quiz.subject}:${quiz.chapter}`] ?? []).map((topic) => `${quiz.subject}:${topic}`),
  ])
  return [...selectedKeys].some((key) => keysForQuiz.has(key))
}

export function quizAttemptMatchesStatus(quiz: ChapterQuiz, attempts: QuizAttempt[], status: string): boolean {
  if (status === 'All statuses') return true
  const attempt = attempts.find((item) => item.quizId === quiz.id)
  if (status === 'Solved') return attempt?.status === 'completed'
  if (status === 'Attempted') return attempt?.status === 'in_progress'
  return !attempt
}

export function filterChapterQuizzes(quizzes: ChapterQuiz[], options: {
  subject?: JeeSubjectId
  selectedSubjects: Set<JeeSubjectId>
  selectedTopics: Set<string>
  difficulty: string
  status: string
  search: string
  attempts: QuizAttempt[]
  sort?: string
}): ChapterQuiz[] {
  const query = options.search.trim().toLocaleLowerCase()
  const filtered = quizzes.filter((quiz) => {
    if (options.subject && quiz.subject !== options.subject) return false
    if (options.selectedSubjects.size && !options.selectedSubjects.has(quiz.subject)) return false
    if (!selectedTopicsMatchQuiz(quiz, options.selectedTopics)) return false
    if (options.difficulty !== 'All difficulties' && quiz.difficulty !== options.difficulty) return false
    if (!quizAttemptMatchesStatus(quiz, options.attempts, options.status)) return false
    if (query && !`${quiz.name} ${quiz.chapter} ${quiz.questions.map((question) => question.prompt).join(' ')}`.toLocaleLowerCase().includes(query)) return false
    return true
  })
  const difficultyOrder: Record<Difficulty, number> = { Easy: 0, Medium: 1, Hard: 2 }
  const statusOrder = (quiz: ChapterQuiz) => {
    const attempt = options.attempts.find((item) => item.quizId === quiz.id)
    return attempt?.status === 'completed' ? 0 : attempt?.status === 'in_progress' ? 1 : 2
  }
  if (options.sort === 'Difficulty: Easy first') filtered.sort((a, b) => difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty] || a.chapter.localeCompare(b.chapter))
  if (options.sort === 'Status') filtered.sort((a, b) => statusOrder(a) - statusOrder(b) || a.chapter.localeCompare(b.chapter))
  if (options.sort === 'Title A–Z') filtered.sort((a, b) => a.name.localeCompare(b.name) || a.chapter.localeCompare(b.chapter))
  return filtered
}
