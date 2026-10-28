"""Granular, original JEE practice taxonomy and starter questions."""

import re

from psycopg.types.json import Json

TOPICS: dict[str, tuple[str, ...]] = {
    "physics": (
        "Units and Dimensions", "Vectors", "Motion in One Dimension", "Projectile Motion", "Newton's Laws",
        "Friction", "Work Energy and Power", "Centre of Mass", "Linear Momentum and Collisions", "Circular Motion",
        "Rotational Kinematics", "Torque", "Angular Impulse", "Angular Momentum", "Rolling Motion", "Gravitation",
        "Simple Harmonic Motion", "Waves", "Thermodynamics", "Kinetic Theory", "Electrostatics", "Capacitance",
        "Current Electricity", "Magnetic Force", "Electromagnetic Induction", "Alternating Current", "Ray Optics",
        "Wave Optics", "Dual Nature", "Atoms and Nuclei", "Semiconductor Electronics",
    ),
    "chemistry": (
        "Mole Concept", "Atomic Structure", "Periodic Properties", "Chemical Bonding", "States of Matter",
        "Thermodynamics", "Chemical Equilibrium", "Ionic Equilibrium", "Redox Reactions", "Electrochemistry",
        "Chemical Kinetics", "Solutions", "Solid State", "Surface Chemistry", "s-Block Elements", "p-Block Elements",
        "d- and f-Block Elements", "Coordination Compounds", "General Organic Chemistry", "Isomerism", "Hydrocarbons",
        "Haloalkanes", "Alcohols Phenols and Ethers", "Aldehydes and Ketones", "Amines", "Biomolecules and Polymers",
    ),
    "mathematics": (
        "Sets and Relations", "Functions", "Complex Numbers", "Quadratic Equations", "Sequences and Series",
        "Permutations and Combinations", "Binomial Theorem", "Matrices", "Determinants", "Trigonometric Equations",
        "Straight Lines", "Circles", "Parabola", "Ellipse and Hyperbola", "Limits", "Continuity and Differentiability",
        "Applications of Derivatives", "Indefinite Integration", "Definite Integration", "Area Under Curves",
        "Differential Equations", "Vectors", "Three Dimensional Geometry", "Statistics", "Probability",
    ),
}

VERSION = "granular-topics-v3-bloom-levels"


def slugify(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")


def seed_granular_content(connection) -> None:
    marker = connection.execute("SELECT value FROM content_seed_meta WHERE key = 'jee_content'").fetchone()
    if marker and marker["value"] == VERSION:
        return

    # Upgrade the existing starter catalog in place. This keeps learner attempts
    # while replacing the old database default (BT2 for every question) with
    # explicit Bloom levels for the two static checks per topic.
    if marker:
        connection.execute("UPDATE jee_problems SET bloom_level = 'remember' WHERE id LIKE 'jee-%-1'")
        connection.execute("UPDATE jee_problems SET bloom_level = 'apply' WHERE id LIKE 'jee-%-2'")
        connection.execute(
            """INSERT INTO content_seed_meta (key, value) VALUES ('jee_content', %s)
               ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP""",
            (VERSION,),
        )
        return

    # These are generated records from the previous starter catalog only.
    connection.execute("DELETE FROM problem_topics WHERE problem_id LIKE 'jee-%'")
    connection.execute("DELETE FROM jee_problems WHERE id LIKE 'jee-%'")
    connection.execute("DELETE FROM jee_topics WHERE id LIKE 'topic-%'")

    for subject, topic_names in TOPICS.items():
        for topic_name in topic_names:
            slug = f"{subject}-{slugify(topic_name)}"
            topic_id = f"topic-{slug}"
            connection.execute(
                "INSERT INTO jee_topics (id, subject, name, slug) VALUES (%s, %s, %s, %s)",
                (topic_id, subject, topic_name, slug),
            )
            for number in (1, 2):
                problem_id = f"jee-{slug}-{number}"
                choices = [
                    "Begin with the governing definition or law and check its conditions.",
                    "Substitute numbers immediately without identifying the model.",
                    "Assume all quantities are constant without checking the question.",
                    "Use a formula from an unrelated topic.",
                ]
                connection.execute(
                    """INSERT INTO jee_problems
                    (id, title, subject, chapter, statement, question_type, difficulty, bloom_level, choices, answer, explanation, hints, exam_relevance)
                    VALUES (%s, %s, %s, %s, %s, 'MCQ', %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        problem_id,
                        f"{topic_name}: Concept Check {number}",
                        subject,
                        topic_name,
                        f"A JEE aspirant is solving a problem on {topic_name}. Which approach is the soundest first step?",
                        "Easy" if number == 1 else "Medium",
                        "remember" if number == 1 else "apply",
                        Json(choices),
                        choices[0],
                        "Identify the governing idea, write down the given and required quantities, and verify the conditions before applying a relation.",
                        Json(["Write the given and required quantities.", "Check which definition or law governs the situation."]),
                        Json(["JEE Main", "JEE Advanced"]),
                    ),
                )
                connection.execute(
                    "INSERT INTO problem_topics (problem_id, topic_id) VALUES (%s, %s)",
                    (problem_id, topic_id),
                )
    connection.execute(
        """INSERT INTO content_seed_meta (key, value) VALUES ('jee_content', %s)
           ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP""",
        (VERSION,),
    )

