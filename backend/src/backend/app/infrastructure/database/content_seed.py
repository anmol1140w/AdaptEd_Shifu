"""Official JEE topic taxonomy used by the practice and quiz catalog."""

from psycopg.types.json import Json

TOPICS: dict[str, tuple[str, ...]] = {
    "physics": (
        "Units and Measurements", "Kinematics", "Newton's Laws of Motion", "Work, Energy and Power",
        "Centre of Mass and Collisions", "Rotational Motion", "Gravitation", "Properties of Solids and Liquids",
        "Thermodynamics", "Kinetic Theory of Gases", "Oscillations", "Waves", "Electrostatics",
        "Current Electricity", "Magnetic Effects of Current", "Magnetism", "Electromagnetic Induction",
        "Alternating Current", "Electromagnetic Waves", "Ray Optics", "Wave Optics", "Dual Nature of Matter",
        "Atoms and Nuclei", "Semiconductor Electronics", "Experimental Skills",
    ),
    "chemistry": (
        "Some Basic Concepts of Chemistry", "Atomic Structure", "Chemical Bonding and Molecular Structure",
        "States of Matter", "Thermodynamics", "Equilibrium", "Redox Reactions", "Electrochemistry",
        "Chemical Kinetics", "Solutions", "Periodic Classification", "p-Block Elements", "d- and f-Block Elements",
        "Coordination Compounds", "General Organic Chemistry", "Hydrocarbons", "Haloalkanes and Haloarenes",
        "Alcohols, Phenols and Ethers", "Aldehydes, Ketones and Carboxylic Acids", "Amines",
        "Biomolecules and Polymers", "Practical Chemistry",
    ),
    "mathematics": (
        "Sets, Relations and Functions", "Complex Numbers", "Quadratic Equations", "Matrices and Determinants",
        "Permutations and Combinations", "Binomial Theorem", "Sequences and Series", "Limits, Continuity and Differentiability",
        "Applications of Derivatives", "Integral Calculus", "Differential Equations", "Coordinate Geometry",
        "Straight Lines", "Circles", "Conic Sections", "Three Dimensional Geometry", "Vector Algebra",
        "Statistics", "Probability", "Trigonometry", "Mathematical Reasoning",
    ),
}


def seed_topics(connection) -> None:
    for subject, names in TOPICS.items():
        for name in names:
            slug = f"{subject}-{name.lower().replace('&', 'and').replace('-', ' ').replace(' ', '-') }"
            slug = '-'.join(part for part in slug.split('-') if part)
            topic_id = f"topic-{slug}"
            connection.execute(
                """INSERT INTO jee_topics (id, subject, name, slug) VALUES (%s, %s, %s, %s)
                   ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name, subject = EXCLUDED.subject""",
                (topic_id, subject, name, slug),
            )

    seed_problems(connection)


def seed_problems(connection) -> None:
    """Seed an original, clearly labelled starter set: seven practice checks per topic."""
    for subject, names in TOPICS.items():
        for name in names:
            slug = f"{subject}-{name.lower().replace('&', 'and').replace('-', ' ').replace(' ', '-') }"
            slug = '-'.join(part for part in slug.split('-') if part)
            topic_id = f"topic-{slug}"
            for index in range(1, 8):
                problem_id = f"jee-{slug}-{index}"
                choices = [
                    "Identify the governing definition/law and the given quantities first.",
                    "Ignore units and substitute numbers before choosing a model.",
                    "Assume every quantity is constant without checking conditions.",
                    "Use an unrelated chapter because it has a shorter formula.",
                ]
                connection.execute(
                    """INSERT INTO jee_problems
                       (id, title, subject, chapter, statement, question_type, difficulty, choices, answer, explanation, hints, exam_relevance)
                       VALUES (%s, %s, %s, %s, %s, 'MCQ', %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (id) DO NOTHING""",
                    (
                        problem_id,
                        f"{name}: JEE Practice Check {index}",
                        subject,
                        name,
                        f"A student is beginning a JEE-style problem from {name}. Which is the most reliable first step?",
                        "Easy" if index <= 2 else "Medium" if index <= 5 else "Hard",
                        Json(choices),
                        choices[0],
                        "A correct solution starts by identifying the governing definition or law, listing the given quantities, and checking the conditions before substituting values.",
                        Json(["Write down what is given and what is asked.", "Check the conditions under which the relevant definition or law applies."]),
                        Json(["JEE Main", "JEE Advanced"] if index >= 6 else ["JEE Main"]),
                    ),
                )
                connection.execute(
                    """INSERT INTO problem_topics (problem_id, topic_id) VALUES (%s, %s)
                       ON CONFLICT DO NOTHING""",
                    (problem_id, topic_id),
                )

