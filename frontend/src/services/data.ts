import type {
  Assessment,
  Concept,
  Problem,
  StudentProfile,
  TeacherIntervention,
  TeacherProfile,
  TeacherStudent,
} from '../types'

export const STUDENT: StudentProfile = {
  id: 'student-aarav',
  name: 'Aarav Sharma',
  role: 'student',
  avatar: 'AS',
  className: 'Class 12 · Section A',
  exam: 'JEE Main',
  subjects: ['physics', 'chemistry', 'mathematics'],
  weeklyGoal: 18,
  streak: 6,
}

export const TEACHER: TeacherProfile = {
  id: 'teacher-priya',
  name: 'Priya Verma',
  role: 'teacher',
  avatar: 'PV',
  subject: 'Physics',
  classes: ['12-A', '12-B'],
}

export const SUBJECT_META = {
  physics: { label: 'Physics', short: 'PHY', accent: '#65b985' },
  chemistry: { label: 'Chemistry', short: 'CHEM', accent: '#d6a756' },
  mathematics: { label: 'Mathematics', short: 'MATH', accent: '#7fb3d5' },
  biology: { label: 'Biology', short: 'BIO', accent: '#b6a5d9' },
} as const

export const CONCEPTS: Concept[] = [
  { id: 'phy-rotational', name: 'Rotational Dynamics', subject: 'physics', chapter: 'Rotational Motion', description: 'Relate torque, angular acceleration and rotational equilibrium in rigid bodies.', prerequisites: ['phy-vectors'], mastery: 38, recentAccuracy: 42, attempts: 12, lastPracticed: '2026-10-22' },
  { id: 'phy-torque', name: 'Torque & Moment Arms', subject: 'physics', chapter: 'Rotational Motion', description: 'Calculate the turning effect of a force around a chosen axis.', prerequisites: ['phy-vectors'], mastery: 44, recentAccuracy: 42, attempts: 9, lastPracticed: '2026-10-23' },
  { id: 'phy-angular', name: 'Angular Momentum', subject: 'physics', chapter: 'Rotational Motion', description: 'Apply conservation of angular momentum to collisions and changing inertia.', prerequisites: ['phy-rotational'], mastery: 54, recentAccuracy: 57, attempts: 8, lastPracticed: '2026-10-18' },
  { id: 'phy-vectors', name: 'Vectors & Equilibrium', subject: 'physics', chapter: 'Mechanics', description: 'Resolve forces and identify equilibrium conditions in two dimensions.', prerequisites: [], mastery: 76, recentAccuracy: 78, attempts: 18, lastPracticed: '2026-10-20' },
  { id: 'chem-electro', name: 'Electrochemistry', subject: 'chemistry', chapter: 'Electrochemistry', description: 'Connect cell potential, concentration and reaction quotient using Nernst equation.', prerequisites: ['chem-redox'], mastery: 46, recentAccuracy: 49, attempts: 11, lastPracticed: '2026-10-21' },
  { id: 'chem-nernst', name: 'Nernst Equation', subject: 'chemistry', chapter: 'Electrochemistry', description: 'Calculate non-standard electrode potentials at 298 K and beyond.', prerequisites: ['chem-electro'], mastery: 41, recentAccuracy: 43, attempts: 7, lastPracticed: '2026-10-21' },
  { id: 'chem-redox', name: 'Redox Reactions', subject: 'chemistry', chapter: 'Electrochemistry', description: 'Balance electron transfer and identify oxidising and reducing agents.', prerequisites: [], mastery: 68, recentAccuracy: 72, attempts: 16, lastPracticed: '2026-10-17' },
  { id: 'math-integrals', name: 'Definite Integrals', subject: 'mathematics', chapter: 'Integral Calculus', description: 'Evaluate definite integrals using properties, substitution and symmetry.', prerequisites: ['math-limits'], mastery: 52, recentAccuracy: 55, attempts: 14, lastPracticed: '2026-10-22' },
  { id: 'math-limits', name: 'Limits & Continuity', subject: 'mathematics', chapter: 'Calculus', description: 'Reason about limiting values, continuity and differentiability at a point.', prerequisites: [], mastery: 73, recentAccuracy: 75, attempts: 17, lastPracticed: '2026-10-16' },
  { id: 'math-differential', name: 'Differential Equations', subject: 'mathematics', chapter: 'Differential Equations', description: 'Form and solve first-order differential equations in exam-style contexts.', prerequisites: ['math-integrals'], mastery: 61, recentAccuracy: 63, attempts: 10, lastPracticed: '2026-10-19' },
  { id: 'bio-genetics', name: 'Mendelian Genetics', subject: 'biology', chapter: 'Principles of Inheritance', description: 'Use inheritance patterns and probability to predict phenotypes.', prerequisites: [], mastery: 64, recentAccuracy: 69, attempts: 12, lastPracticed: '2026-10-14' },
  { id: 'bio-cell', name: 'Cell Cycle', subject: 'biology', chapter: 'Cell Biology', description: 'Sequence the stages of cell division and identify checkpoint events.', prerequisites: [], mastery: 81, recentAccuracy: 84, attempts: 13, lastPracticed: '2026-10-12' },
]

const physicsProblems: Problem[] = [
  { id: 'PHY-001', title: 'Calculate the Net Torque on a Rotating Disc', subject: 'physics', className: 'Class 12', chapter: 'Rotational Motion', conceptIds: ['phy-torque'], tags: ['Physics', 'Class 12', 'Rotational Motion', 'Torque', 'JEE Main'], difficulty: 'Easy', questionType: 'MCQ', examRelevance: ['JEE Main', 'Boards'], estimatedMinutes: 4, statement: 'A 2 N force acts tangentially on a disc at a radius of 0.5 m. What is the magnitude of the torque?', choices: ['0.5 N·m', '1 N·m', '2.5 N·m', '4 N·m'], answer: '1 N·m', explanation: 'For a tangential force, τ = rF. Therefore τ = 0.5 × 2 = 1 N·m.', formula: 'τ = rF sin θ', hints: ['Identify the angle between radius and force.', 'A tangential force is perpendicular to the radius.'], prerequisiteConcepts: ['phy-vectors'] },
  { id: 'PHY-002', title: 'Angular Momentum Conservation', subject: 'physics', className: 'Class 12', chapter: 'Rotational Motion', conceptIds: ['phy-angular'], tags: ['Physics', 'Angular Momentum', 'JEE Main'], difficulty: 'Medium', questionType: 'MCQ', examRelevance: ['JEE Main', 'JEE Advanced'], estimatedMinutes: 6, statement: 'A skater pulls their arms inward while spinning. Which quantity remains conserved if external torque is negligible?', choices: ['Angular velocity', 'Moment of inertia', 'Angular momentum', 'Rotational kinetic energy'], answer: 'Angular momentum', explanation: 'With negligible external torque, angular momentum L = Iω remains conserved while I and ω change.', formula: 'τ_ext = dL/dt', hints: ['Think about the condition of negligible external torque.'] },
  { id: 'PHY-003', title: 'Moment of Inertia of a Ring', subject: 'physics', className: 'Class 12', chapter: 'Rotational Motion', conceptIds: ['phy-rotational'], tags: ['Physics', 'Moment of Inertia', 'Rotational Motion'], difficulty: 'Medium', questionType: 'Numerical', examRelevance: ['JEE Main'], estimatedMinutes: 5, statement: 'A thin ring of mass 2 kg and radius 0.4 m rotates about its central axis. Find its moment of inertia in kg·m².', answer: '0.32', explanation: 'For a thin ring about its central axis, I = MR² = 2 × (0.4)² = 0.32 kg·m².', formula: 'I = MR²', hints: ['Use the standard expression for a thin ring.'] },
  { id: 'PHY-004', title: 'Rolling Without Slipping', subject: 'physics', className: 'Class 11', chapter: 'System of Particles', conceptIds: ['phy-rotational'], tags: ['Physics', 'Rolling Motion', 'JEE Main'], difficulty: 'Hard', questionType: 'MCQ', examRelevance: ['JEE Main', 'JEE Advanced'], estimatedMinutes: 8, statement: 'For a wheel rolling without slipping, which relation connects the centre-of-mass speed v and angular speed ω?', choices: ['v = ω/R', 'v = Rω', 'v = R/ω', 'v = ω²R'], answer: 'v = Rω', explanation: 'The point of contact is instantaneously at rest, giving v = Rω for pure rolling.', formula: 'v = Rω' },
  { id: 'PHY-005', title: 'Equilibrium of a Suspended Beam', subject: 'physics', className: 'Class 11', chapter: 'Mechanics', conceptIds: ['phy-vectors'], tags: ['Physics', 'Equilibrium', 'Forces'], difficulty: 'Easy', questionType: 'MCQ', examRelevance: ['Boards', 'JEE Main'], estimatedMinutes: 4, statement: 'A body is in translational equilibrium when the vector sum of all external forces is:', choices: ['Maximum', 'Zero', 'Equal to its weight', 'Constant but non-zero'], answer: 'Zero', explanation: 'Translational equilibrium requires ΣF = 0, so the centre of mass has no acceleration.' },
  { id: 'PHY-006', title: 'Couple and Turning Effect', subject: 'physics', className: 'Class 12', chapter: 'Rotational Motion', conceptIds: ['phy-torque'], tags: ['Physics', 'Couple', 'Torque'], difficulty: 'Medium', questionType: 'Numerical', examRelevance: ['JEE Main'], estimatedMinutes: 6, statement: 'Two equal and opposite 5 N forces act 0.6 m apart. Find the moment of the couple in N·m.', answer: '3', explanation: 'The moment of a couple is Fd = 5 × 0.6 = 3 N·m.', formula: 'τ = Fd' },
  { id: 'PHY-007', title: 'Radius of Gyration', subject: 'physics', className: 'Class 12', chapter: 'Rotational Motion', conceptIds: ['phy-rotational'], tags: ['Physics', 'Radius of Gyration'], difficulty: 'Hard', questionType: 'MCQ', examRelevance: ['JEE Advanced'], estimatedMinutes: 7, statement: 'If a body has moment of inertia I and mass M, its radius of gyration k is defined by:', choices: ['I = Mk', 'I = Mk²', 'I = M²k', 'I = k/M'], answer: 'I = Mk²', explanation: 'By definition I = Mk², where k is the distance at which the whole mass may be assumed concentrated.' },
  { id: 'PHY-008', title: 'Angular Impulse', subject: 'physics', className: 'Class 12', chapter: 'Rotational Motion', conceptIds: ['phy-angular'], tags: ['Physics', 'Angular Impulse'], difficulty: 'Hard', questionType: 'Numerical', examRelevance: ['JEE Advanced'], estimatedMinutes: 8, statement: 'A constant torque of 4 N·m acts for 3 s. Find the angular impulse in N·m·s.', answer: '12', explanation: 'Angular impulse equals torque multiplied by time: 4 × 3 = 12 N·m·s.', formula: 'J = τΔt' },
  { id: 'PHY-009', title: 'Torque from an Angled Force', subject: 'physics', className: 'Class 12', chapter: 'Rotational Motion', conceptIds: ['phy-torque'], tags: ['Physics', 'Torque', 'Perpendicular Component'], difficulty: 'Medium', questionType: 'Numerical', examRelevance: ['JEE Main', 'Boards'], estimatedMinutes: 6, statement: 'A 10 N force acts at 0.2 m from an axis at 30° to the radius. Find the torque magnitude in N·m.', answer: '1', explanation: 'Use τ = rF sin θ = 0.2 × 10 × sin 30° = 1 N·m.', formula: 'τ = rF sin θ', hints: ['Only the perpendicular component of force contributes.', 'sin 30° = 0.5.'] },
  { id: 'PHY-010', title: 'Rotational Kinetic Energy', subject: 'physics', className: 'Class 12', chapter: 'Rotational Motion', conceptIds: ['phy-rotational'], tags: ['Physics', 'Rotational Energy', 'JEE Main'], difficulty: 'Easy', questionType: 'MCQ', examRelevance: ['JEE Main', 'JEE Advanced'], estimatedMinutes: 4, statement: 'The rotational kinetic energy of a rigid body rotating with angular speed ω is:', choices: ['Iω', 'Iω²', '½Iω²', '2Iω²'], answer: '½Iω²', explanation: 'Rotational kinetic energy is K = ½Iω², analogous to translational kinetic energy ½mv².', formula: 'K = ½Iω²' },
]

const chemistryProblems: Problem[] = [
  { id: 'CHEM-001', title: 'Nernst Equation Application', subject: 'chemistry', className: 'Class 12', chapter: 'Electrochemistry', conceptIds: ['chem-nernst'], tags: ['Chemistry', 'Class 12', 'Electrochemistry', 'Nernst Equation', 'JEE Main'], difficulty: 'Medium', questionType: 'Numerical', examRelevance: ['JEE Main', 'Boards'], estimatedMinutes: 7, statement: 'At 298 K, a cell has E° = 1.10 V and Q = 10. Estimate E using E = E° − 0.0591 log Q / n for n = 2.', answer: '1.07', explanation: 'E = 1.10 − (0.0591/2)log10(10) ≈ 1.07 V.', formula: 'E = E° − (0.0591/n)log Q', hints: ['log10(10) = 1.', 'Keep three significant figures.'] },
  { id: 'CHEM-002', title: 'Identify the Oxidising Agent', subject: 'chemistry', className: 'Class 11', chapter: 'Electrochemistry', conceptIds: ['chem-redox'], tags: ['Chemistry', 'Redox', 'Oxidising Agent'], difficulty: 'Easy', questionType: 'MCQ', examRelevance: ['JEE Main', 'NEET'], estimatedMinutes: 3, statement: 'In the reaction Zn + Cu²⁺ → Zn²⁺ + Cu, which species is reduced?', choices: ['Zn', 'Cu²⁺', 'Zn²⁺', 'Electrons'], answer: 'Cu²⁺', explanation: 'Cu²⁺ gains electrons to form Cu, so it is reduced and acts as the oxidising agent.' },
  { id: 'CHEM-003', title: 'Cell Potential from Half Cells', subject: 'chemistry', className: 'Class 12', chapter: 'Electrochemistry', conceptIds: ['chem-electro'], tags: ['Chemistry', 'Cell Potential', 'Electrochemistry'], difficulty: 'Medium', questionType: 'Numerical', examRelevance: ['JEE Main'], estimatedMinutes: 6, statement: 'If E°cathode = 0.80 V and E°anode = −0.76 V, find E°cell in volts.', answer: '1.56', explanation: 'E°cell = E°cathode − E°anode = 0.80 − (−0.76) = 1.56 V.', formula: 'E°cell = E°cathode − E°anode' },
  { id: 'CHEM-004', title: 'Faraday Constant and Charge', subject: 'chemistry', className: 'Class 12', chapter: 'Electrochemistry', conceptIds: ['chem-electro'], tags: ['Chemistry', 'Faraday Laws'], difficulty: 'Easy', questionType: 'MCQ', examRelevance: ['Boards', 'JEE Main'], estimatedMinutes: 4, statement: 'One mole of electrons carries approximately which charge?', choices: ['9.65 × 10⁴ C', '9.65 × 10² C', '6.02 × 10²³ C', '1.60 × 10⁻¹⁹ C'], answer: '9.65 × 10⁴ C', explanation: 'The Faraday constant is approximately 96485 C per mole of electrons.' },
  { id: 'CHEM-005', title: 'Balance a Redox Reaction', subject: 'chemistry', className: 'Class 11', chapter: 'Electrochemistry', conceptIds: ['chem-redox'], tags: ['Chemistry', 'Redox', 'Balancing'], difficulty: 'Hard', questionType: 'MCQ', examRelevance: ['JEE Main', 'JEE Advanced'], estimatedMinutes: 9, statement: 'In acidic medium, how many electrons are transferred when MnO₄⁻ is reduced to Mn²⁺?', choices: ['1', '3', '5', '7'], answer: '5', explanation: 'Manganese changes from +7 in MnO₄⁻ to +2 in Mn²⁺, gaining five electrons.' },
  { id: 'CHEM-006', title: 'Concentration Cell Direction', subject: 'chemistry', className: 'Class 12', chapter: 'Electrochemistry', conceptIds: ['chem-nernst'], tags: ['Chemistry', 'Concentration Cell'], difficulty: 'Hard', questionType: 'MCQ', examRelevance: ['JEE Advanced'], estimatedMinutes: 8, statement: 'In a metal-ion concentration cell, oxidation occurs at the electrode with:', choices: ['Higher ion concentration', 'Lower ion concentration', 'Equal ion concentration', 'The salt bridge'], answer: 'Lower ion concentration', explanation: 'The dilute electrode dissolves to increase its ion concentration; oxidation occurs at the lower concentration side.' },
  { id: 'CHEM-007', title: 'Spontaneous Cell Reaction', subject: 'chemistry', className: 'Class 12', chapter: 'Electrochemistry', conceptIds: ['chem-electro'], tags: ['Chemistry', 'Cell Potential', 'Spontaneity'], difficulty: 'Easy', questionType: 'MCQ', examRelevance: ['JEE Main', 'Boards'], estimatedMinutes: 4, statement: 'A galvanic cell reaction is spontaneous under standard conditions when E°cell is:', choices: ['Negative', 'Zero', 'Positive', 'Infinite'], answer: 'Positive', explanation: 'A positive standard cell potential corresponds to a negative standard Gibbs energy change and a spontaneous reaction.' },
]

const mathematicsProblems: Problem[] = [
  { id: 'MATH-001', title: 'Definite Integral Evaluation', subject: 'mathematics', className: 'Class 12', chapter: 'Integral Calculus', conceptIds: ['math-integrals'], tags: ['Mathematics', 'Class 12', 'Definite Integrals', 'JEE Main'], difficulty: 'Easy', questionType: 'Numerical', examRelevance: ['JEE Main', 'Boards'], estimatedMinutes: 5, statement: 'Evaluate ∫₀¹ 2x dx.', answer: '1', explanation: 'The antiderivative is x², so [x²]₀¹ = 1.', formula: '∫ 2x dx = x²' },
  { id: 'MATH-002', title: 'Limits and Continuity', subject: 'mathematics', className: 'Class 12', chapter: 'Calculus', conceptIds: ['math-limits'], tags: ['Mathematics', 'Limits', 'Continuity'], difficulty: 'Medium', questionType: 'MCQ', examRelevance: ['JEE Main', 'Boards'], estimatedMinutes: 5, statement: 'For f(x) = (x² − 1)/(x − 1), what is lim x→1 f(x)?', choices: ['0', '1', '2', 'Does not exist'], answer: '2', explanation: 'Factor x² − 1 = (x − 1)(x + 1), then the limit becomes lim x→1 (x + 1) = 2.' },
  { id: 'MATH-003', title: 'Area Under a Parabola', subject: 'mathematics', className: 'Class 12', chapter: 'Integral Calculus', conceptIds: ['math-integrals'], tags: ['Mathematics', 'Area', 'Definite Integrals'], difficulty: 'Medium', questionType: 'Numerical', examRelevance: ['JEE Main'], estimatedMinutes: 7, statement: 'Find the area under y = x² from x = 0 to x = 2.', answer: '2.67', explanation: 'Area = ∫₀² x² dx = [x³/3]₀² = 8/3 ≈ 2.67 square units.' },
  { id: 'MATH-004', title: 'Differential Equation Order', subject: 'mathematics', className: 'Class 12', chapter: 'Differential Equations', conceptIds: ['math-differential'], tags: ['Mathematics', 'Differential Equations'], difficulty: 'Easy', questionType: 'MCQ', examRelevance: ['JEE Main', 'Boards'], estimatedMinutes: 3, statement: 'What is the order of d²y/dx² + 3dy/dx + y = 0?', choices: ['0', '1', '2', '3'], answer: '2', explanation: 'The highest derivative present is the second derivative, so the order is 2.' },
  { id: 'MATH-005', title: 'Property of Symmetric Integrals', subject: 'mathematics', className: 'Class 12', chapter: 'Integral Calculus', conceptIds: ['math-integrals'], tags: ['Mathematics', 'Symmetry', 'Integration'], difficulty: 'Hard', questionType: 'MCQ', examRelevance: ['JEE Advanced'], estimatedMinutes: 8, statement: 'If f(x) is odd, what is ∫₋aᵃ f(x) dx?', choices: ['2∫₀ᵃ f(x)dx', '0', 'a', 'Depends on f'], answer: '0', explanation: 'The areas cancel by symmetry for any integrable odd function over [−a, a].' },
  { id: 'MATH-006', title: 'Continuity at a Point', subject: 'mathematics', className: 'Class 12', chapter: 'Calculus', conceptIds: ['math-limits'], tags: ['Mathematics', 'Continuity', 'Piecewise Functions'], difficulty: 'Hard', questionType: 'Numerical', examRelevance: ['JEE Main', 'JEE Advanced'], estimatedMinutes: 8, statement: 'For f(x) = (x² − 4)/(x − 2) when x ≠ 2 and f(2) = k, find k for continuity at x = 2.', answer: '4', explanation: 'The simplified expression is x + 2, whose limit at x = 2 is 4. Thus k = 4.' },
  { id: 'MATH-007', title: 'Fundamental Theorem Check', subject: 'mathematics', className: 'Class 12', chapter: 'Integral Calculus', conceptIds: ['math-integrals'], tags: ['Mathematics', 'Definite Integrals', 'Fundamental Theorem'], difficulty: 'Medium', questionType: 'MCQ', examRelevance: ['JEE Main', 'Boards'], estimatedMinutes: 5, statement: 'If F′(x) = f(x), then ∫ₐᵇ f(x) dx equals:', choices: ['F(a) + F(b)', 'F(b) − F(a)', 'f(b) − f(a)', 'F(a)F(b)'], answer: 'F(b) − F(a)', explanation: 'The fundamental theorem of calculus evaluates the definite integral as F(b) − F(a).' },
]

const biologyProblems: Problem[] = [
  { id: 'BIO-001', title: 'Mendelian Dihybrid Cross', subject: 'biology', className: 'Class 12', chapter: 'Principles of Inheritance', conceptIds: ['bio-genetics'], tags: ['Biology', 'Genetics', 'Mendelian Inheritance', 'NEET'], difficulty: 'Medium', questionType: 'MCQ', examRelevance: ['NEET'], estimatedMinutes: 5, statement: 'In a classic dihybrid cross between two heterozygotes, what is the expected phenotypic ratio?', choices: ['3:1', '1:1', '9:3:3:1', '1:2:1'], answer: '9:3:3:1', explanation: 'Independent assortment of two heterozygous pairs produces the 9:3:3:1 phenotypic ratio.' },
  { id: 'BIO-002', title: 'Cell Cycle Checkpoint', subject: 'biology', className: 'Class 11', chapter: 'Cell Biology', conceptIds: ['bio-cell'], tags: ['Biology', 'Cell Cycle', 'NEET'], difficulty: 'Easy', questionType: 'MCQ', examRelevance: ['NEET', 'Boards'], estimatedMinutes: 3, statement: 'Which checkpoint ensures DNA replication is complete before mitosis?', choices: ['G1 checkpoint', 'G2 checkpoint', 'Spindle checkpoint', 'Restriction enzyme'], answer: 'G2 checkpoint', explanation: 'The G2 checkpoint verifies replication and DNA integrity before the cell enters mitosis.' },
  { id: 'BIO-003', title: 'Test Cross Probability', subject: 'biology', className: 'Class 12', chapter: 'Principles of Inheritance', conceptIds: ['bio-genetics'], tags: ['Biology', 'Test Cross', 'Probability'], difficulty: 'Medium', questionType: 'Numerical', examRelevance: ['NEET'], estimatedMinutes: 6, statement: 'In a test cross Aa × aa, what percentage of offspring are expected to show the recessive phenotype?', answer: '50', explanation: 'Half the gametes from Aa carry a and all gametes from aa carry a, so 50% are aa.' },
  { id: 'BIO-004', title: 'Metaphase Alignment', subject: 'biology', className: 'Class 11', chapter: 'Cell Biology', conceptIds: ['bio-cell'], tags: ['Biology', 'Mitosis', 'Cell Cycle'], difficulty: 'Easy', questionType: 'MCQ', examRelevance: ['NEET', 'Boards'], estimatedMinutes: 3, statement: 'During which phase do chromosomes align at the equatorial plate?', choices: ['Prophase', 'Metaphase', 'Anaphase', 'Telophase'], answer: 'Metaphase', explanation: 'Spindle fibres align chromosomes at the cell equator during metaphase.' },
  { id: 'BIO-005', title: 'Incomplete Dominance', subject: 'biology', className: 'Class 12', chapter: 'Principles of Inheritance', conceptIds: ['bio-genetics'], tags: ['Biology', 'Incomplete Dominance', 'NEET'], difficulty: 'Hard', questionType: 'MCQ', examRelevance: ['NEET'], estimatedMinutes: 7, statement: 'In incomplete dominance, the heterozygous phenotype is:', choices: ['Always dominant', 'Always recessive', 'Intermediate', 'Lethal'], answer: 'Intermediate', explanation: 'Neither allele fully masks the other, producing an intermediate phenotype in heterozygotes.' },
  { id: 'BIO-006', title: 'S Phase Activity', subject: 'biology', className: 'Class 11', chapter: 'Cell Biology', conceptIds: ['bio-cell'], tags: ['Biology', 'DNA Replication', 'Cell Cycle'], difficulty: 'Medium', questionType: 'MCQ', examRelevance: ['NEET', 'Boards'], estimatedMinutes: 4, statement: 'What major event occurs during S phase of the cell cycle?', choices: ['Cytokinesis', 'DNA replication', 'Chromosome separation', 'Nuclear envelope breakdown'], answer: 'DNA replication', explanation: 'S phase is the synthesis phase during which the cell duplicates its DNA.' },
  { id: 'BIO-007', title: 'Monohybrid Genotypic Ratio', subject: 'biology', className: 'Class 12', chapter: 'Principles of Inheritance', conceptIds: ['bio-genetics'], tags: ['Biology', 'Genetics', 'Monohybrid Cross'], difficulty: 'Easy', questionType: 'MCQ', examRelevance: ['NEET', 'Boards'], estimatedMinutes: 4, statement: 'The genotypic ratio from a monohybrid cross Aa × Aa is:', choices: ['3:1', '1:1', '1:2:1', '9:3:3:1'], answer: '1:2:1', explanation: 'The offspring genotypes are AA, Aa and aa in the ratio 1:2:1.' },
]

export const PROBLEMS = [...physicsProblems, ...chemistryProblems, ...mathematicsProblems, ...biologyProblems]

export const ASSESSMENTS: Assessment[] = [
  { id: 'assessment-diagnostic', title: 'JEE Main diagnostic · Mechanics', type: 'Diagnostic test', subject: 'physics', chapter: 'Rotational Motion', questionIds: ['PHY-001', 'PHY-002', 'PHY-003', 'PHY-005'], questionCount: 4, duration: 12, difficulty: 'Medium', examRelevance: 'JEE Main', adaptive: true, description: 'A short baseline that estimates your rotational motion starting point and selects the right next practice.' },
  { id: 'assessment-electro', title: 'Electrochemistry checkpoint', type: 'Chapter quiz', subject: 'chemistry', chapter: 'Electrochemistry', questionIds: ['CHEM-001', 'CHEM-002', 'CHEM-003', 'CHEM-005'], questionCount: 4, duration: 15, difficulty: 'Medium', examRelevance: 'JEE Main', adaptive: true, description: 'Check the calculation and redox foundations behind cell potential questions.' },
  { id: 'assessment-calculus', title: 'Calculus mixed practice', type: 'Exam-style practice', subject: 'mathematics', chapter: 'Calculus', questionIds: ['MATH-001', 'MATH-002', 'MATH-004', 'MATH-005'], questionCount: 4, duration: 14, difficulty: 'Hard', examRelevance: 'JEE Main', adaptive: false, description: 'A timed set spanning limits, continuity, integrals and differential equations.' },
  { id: 'assessment-revision', title: 'Weak concept revision sprint', type: 'Personalized assessment', subject: 'physics', chapter: 'Rotational Motion', questionIds: ['PHY-001', 'PHY-003', 'PHY-006', 'PHY-007'], questionCount: 4, duration: 14, difficulty: 'Easy', examRelevance: 'JEE Main', adaptive: true, description: 'Generated from your recent torque and moment-of-inertia evidence.' },
]

const names = ['Riya Kapoor', 'Arjun Mehta', 'Meera Iyer', 'Kabir Singh', 'Ananya Rao', 'Vivaan Shah', 'Ishita Nair', 'Reyansh Gupta', 'Aditi Joshi', 'Dev Malhotra', 'Saanvi Das', 'Aarav Bhat', 'Myra Kulkarni', 'Yash Thakur', 'Tara Menon', 'Neil Khanna', 'Kiara Bose', 'Rohan Verma', 'Siya Jain', 'Atharv Roy']
const weakConceptNames = ['Rotational Dynamics', 'Nernst Equation', 'Definite Integrals', 'Torque & Moment Arms', 'Electrochemistry']

export const TEACHER_STUDENTS: TeacherStudent[] = names.map((name, index) => {
  const overall = 54 + ((index * 13) % 40)
  const status: TeacherStudent['interventionStatus'] = overall < 62 ? 'Intervention Suggested' : overall < 72 ? 'Needs Attention' : 'On Track'
  return {
    id: `class-student-${index + 1}`,
    name,
    className: 'Class 12',
    section: index % 2 === 0 ? 'A' : 'B',
    overallMastery: overall,
    latestAssessment: Math.min(96, overall + 7 - (index % 4) * 3),
    recentActivity: `${2 + (index % 6)} activities this week`,
    weakestConcept: weakConceptNames[index % weakConceptNames.length],
    interventionStatus: status,
    trend: [overall - 12, overall - 9, overall - 6, overall - 3, overall],
    subjectScores: { Physics: overall - 3 + (index % 5), Chemistry: overall + 4 - (index % 4), Mathematics: overall - 1 + (index % 3) },
    conceptScores: { 'Rotational Dynamics': Math.max(32, overall - 17 + (index % 8)), 'Nernst Equation': Math.max(35, overall - 12 + (index % 7)), 'Definite Integrals': Math.max(42, overall - 8 + (index % 6)), 'Vectors & Equilibrium': Math.min(94, overall + 12) },
    mistakes: index % 3 === 0 ? ['Used rF without checking the perpendicular component', 'Lost the negative sign in a concentration quotient'] : index % 3 === 1 ? ['Confused moment of inertia with angular momentum'] : ['Applied the definite-integral property to a non-symmetric function'],
  }
})

export const BASE_INTERVENTIONS: TeacherIntervention[] = [
  { id: 'intervention-rotational', conceptId: 'phy-rotational', conceptName: 'Rotational Dynamics', affectedStudents: TEACHER_STUDENTS.filter((s) => s.conceptScores['Rotational Dynamics'] < 58).map((s) => s.id), severity: 'High', reason: 'The class median is 51% with a repeated torque-versus-angular-momentum misconception.', recommendation: 'Run a 20-minute torque and moment-arm revision, then assign the adaptive rotational motion checkpoint.', status: 'Open', createdAt: '2026-10-23' },
  { id: 'intervention-nernst', conceptId: 'chem-nernst', conceptName: 'Nernst Equation', affectedStudents: TEACHER_STUDENTS.filter((s) => s.conceptScores['Nernst Equation'] < 55).map((s) => s.id), severity: 'Medium', reason: 'Students are accurate on standard potentials but lose marks when concentration changes.', recommendation: 'Use a worked example on Q and a two-question targeted practice set.', status: 'Open', createdAt: '2026-10-21' },
  { id: 'intervention-integrals', conceptId: 'math-integrals', conceptName: 'Definite Integrals', affectedStudents: TEACHER_STUDENTS.filter((s) => s.conceptScores['Definite Integrals'] < 57).map((s) => s.id), severity: 'Medium', reason: 'Recent attempts show errors choosing symmetry properties before evaluating the integral.', recommendation: 'Assign a small-group session on odd/even functions and property selection.', status: 'Reviewed', createdAt: '2026-10-18' },
]

export function getProblem(id: string) {
  return PROBLEMS.find((problem) => problem.id === id)
}

export function getConcept(id: string) {
  return CONCEPTS.find((concept) => concept.id === id)
}

export function getAssessment(id: string) {
  return ASSESSMENTS.find((assessment) => assessment.id === id)
}

export function subjectLabel(subject: string) {
  return SUBJECT_META[subject as keyof typeof SUBJECT_META]?.label ?? subject
}
