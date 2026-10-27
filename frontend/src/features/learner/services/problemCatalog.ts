import { PROBLEMS } from '../../../services/data'
import type { JeeSubjectId, Problem } from '../../../types'

export const SUBJECTS: { id: JeeSubjectId; label: string; short: string }[] = [
  { id: 'physics', label: 'Physics', short: 'PHY' },
  { id: 'chemistry', label: 'Chemistry', short: 'CHEM' },
  { id: 'mathematics', label: 'Mathematics', short: 'MATH' },
]

export const TOPICS_BY_SUBJECT: Record<JeeSubjectId, string[]> = {
  physics: [
    'Rotational Motion', 'Newton’s Laws of Motion (NLM)', 'Work, Energy and Power', 'Kinematics',
    'Laws of Motion', 'Centre of Mass', 'Gravitation', 'Thermodynamics', 'Electrostatics',
    'Current Electricity', 'Magnetism', 'Optics', 'Modern Physics',
  ],
  chemistry: [
    'Chemical Kinetics', 'Chemical Equilibrium', 'Ionic Equilibrium', 'Thermodynamics',
    'Electrochemistry', 'Solutions', 'Atomic Structure', 'Chemical Bonding', 'Coordination Compounds',
    'Organic Chemistry', 'GOC', 'Hydrocarbons',
  ],
  mathematics: [
    'Area Under the Curve', 'Limits', 'Continuity and Differentiability', 'Applications of Derivatives',
    'Integration', 'Differential Equations', 'Matrices', 'Determinants', 'Probability',
    'Permutations and Combinations', 'Vectors', '3D Geometry', 'Complex Numbers',
    'Coordinate Geometry', 'Sequences and Series',
  ],
}

export interface ListedProblem {
  problem: Problem
  topic: string
  isMock: boolean
}

// Existing local question bank plus one clearly labeled sample for Chemical Kinetics,
// which is not represented in the original bank. No API endpoint exists for problems yet.
const supplementalMocks: Problem[] = [
  {
    id: 'DEMO-KIN-001',
    title: 'Determine the Order from Initial Rates',
    subject: 'chemistry',
    className: 'Class 12',
    chapter: 'Chemical Kinetics',
    conceptIds: [],
    tags: ['Chemical Kinetics', 'Rate Law', 'Demo question'],
    difficulty: 'Medium',
    questionType: 'Numerical',
    examRelevance: ['JEE Main'],
    estimatedMinutes: 6,
    statement: 'In a reaction, doubling [A] while keeping [B] constant doubles the rate. Doubling [B] while keeping [A] constant makes the rate four times larger. What is the overall order of the reaction?',
    answer: '3',
    explanation: 'The reaction is first order in A and second order in B, so the overall order is 1 + 2 = 3.',
    hints: ['Compare how the rate changes when each reactant concentration doubles.'],
  },
]

const topicByProblemId: Record<string, string> = {
  'PHY-001': 'Rotational Motion', 'PHY-002': 'Rotational Motion', 'PHY-003': 'Rotational Motion',
  'PHY-004': 'Rotational Motion', 'PHY-005': 'Laws of Motion', 'PHY-006': 'Rotational Motion',
  'PHY-007': 'Rotational Motion', 'PHY-008': 'Rotational Motion', 'PHY-009': 'Rotational Motion',
  'PHY-010': 'Rotational Motion',
  'CHEM-001': 'Electrochemistry', 'CHEM-002': 'Electrochemistry', 'CHEM-003': 'Electrochemistry',
  'CHEM-004': 'Electrochemistry', 'CHEM-005': 'Electrochemistry', 'CHEM-006': 'Electrochemistry',
  'CHEM-007': 'Electrochemistry',
  'MATH-001': 'Integration', 'MATH-002': 'Continuity and Differentiability',
  'MATH-003': 'Area Under the Curve', 'MATH-004': 'Differential Equations',
  'MATH-005': 'Integration', 'MATH-006': 'Continuity and Differentiability',
  'MATH-007': 'Integration',
}

function isJeeSubject(subject: Problem['subject']): subject is JeeSubjectId {
  return subject === 'physics' || subject === 'chemistry' || subject === 'mathematics'
}

const existingProblems: ListedProblem[] = PROBLEMS
  .filter((problem) => isJeeSubject(problem.subject) && topicByProblemId[problem.id])
  .map((problem) => ({ problem, topic: topicByProblemId[problem.id]!, isMock: true }))

const addedProblems: ListedProblem[] = supplementalMocks.map((problem) => ({
  problem,
  topic: 'Chemical Kinetics',
  isMock: true,
}))

export const STUDENT_PROBLEMS: ListedProblem[] = [...existingProblems, ...addedProblems]
