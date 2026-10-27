# PS-22 Hackathon PPT Blueprint

## Working product identity

Use the project name instead of presenting a generic “AI learning platform.” The project name is:

> **AdaptEd — From marks to mastery**

AdaptEd is the project name for the PS-22 platform. The positioning and slide content should consistently use this name.

### One-line pitch

> AdaptEd converts every learner response into a concept-level mastery map, then delivers the next best question, explanation and practice plan—while giving teachers an actionable intervention queue.

### 30-second pitch

> Today, a score tells a student that they are behind, but not what to learn next. AdaptEd starts with a short diagnostic, maps the learner’s mastery across concepts, adapts question difficulty in real time and explains mistakes using teacher-approved learning material. It creates a personal recovery path for the learner and highlights only the students and concepts that need teacher intervention. We will demonstrate the first version for Class 9 mathematics, focused on algebra and linear equations, so the solution is measurable, feasible and ready to scale.

### Tagline options

1. **From marks to mastery.** — recommended
2. **Every answer reveals a better next step.**
3. **Find the gap. Fix the foundation. Move forward.**
4. **One learner. One learning path.**

---

## What the selection panel must believe

Round-one evaluators usually have limited time. They should be able to answer “yes” to these questions after seeing your deck:

| Judge question                     | What your PPT must prove                                                                                                                                               |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Is the problem real?               | Marks and completion rates do not reveal which prerequisite concept is missing. Learners receive generic remediation; teachers cannot manually diagnose every learner. |
| Is the proposed product different? | It closes the loop: diagnosis → concept map → adaptive practice → grounded explanation → teacher action → re-assessment.                                               |
| Is it buildable?                   | The MVP is deliberately bounded to one grade, one subject and a small concept graph. A hybrid rules + ML + LLM design avoids requiring a huge training dataset.        |
| Is AI being used meaningfully?     | AI is used for mastery inference, question selection, explanation and quiz generation—not as a decorative chatbot.                                                     |
| Is it safe for education?          | Retrieval-grounded answers, source references, hint-first tutoring, age-appropriate guardrails, teacher override and privacy-by-design are explicit.                   |
| Can impact be measured?            | You define metrics such as concept mastery gain, time-to-mastery, retention, recommendation acceptance and teacher intervention efficiency.                            |
| Can the team demo it?              | The story is shown through one learner journey and one teacher dashboard, not a list of disconnected features.                                                         |

### The strongest strategic decision

Do **not** pitch “an AI tutor for every subject and every student” in round one. Pitch a credible wedge:

> **Pilot: Class 9 Mathematics — Algebra and Linear Equations**

Why this is a good wedge:

- The subject has a clear prerequisite graph.
- Question correctness can be evaluated objectively.
- Misconceptions can be represented explicitly.
- Adaptive difficulty is easy to show visually.
- The team can create a small teacher-approved content bank for the demo.
- The same architecture can later expand to science, languages and vocational skills.

If the team has a stronger domain dataset, substitute it, but keep the same scope discipline: one learner segment, one subject, five to ten concepts, one measurable outcome.

---

## Recommended deck structure

Use a **13-slide main deck** for a 5–7 minute round-one pitch. If the event has a strict page limit, use the compressed 8-slide version later in this file.

| Slide | Job of the slide | Target time |
|---:|---|---:|
| 1 | Create a memorable opening and state the promise | 20 sec |
| 2 | Make the problem specific and human | 30 sec |
| 3 | Show context and research-backed urgency | 30 sec |
| 4 | Explain why existing solutions are insufficient | 30 sec |
| 5 | State the insight and proposed solution | 35 sec |
| 6 | Show the product through the learner experience | 35 sec |
| 7 | Explain the adaptive working mechanism | 45 sec |
| 8 | Show the teacher experience and intervention loop | 30 sec |
| 9 | Show the end-to-end process flow | 30 sec |
| 10 | Prove the technical architecture and responsible AI | 35 sec |
| 11 | Show feasibility, MVP and execution plan | 35 sec |
| 12 | Define impact, metrics and future scope | 30 sec |
| 13 | Close with differentiation and a clear ask | 20 sec |

Keep the visible slide text short. Put explanations in speaker notes or present them verbally. A panel should never need to read a paragraph to understand a slide.

---

# Slide-by-slide content specification

## Slide 1 — Title: From marks to mastery

### Purpose

Make the panel immediately understand that your solution is not another content library or generic chatbot.

### Put this on the slide

**AdaptEd**
**From marks to mastery**

> An AI-powered adaptive learning and skill-gap identification platform

**Pilot:** Class 9 Mathematics | Algebra + Linear Equations  
**SDG 4:** Quality Education

At the bottom, show team name, member names and a small “PS-22” label.

### Visual direction

Use a split visual:

- Left: a red/orange “Score: 42%” card that stops at the score.
- Right: a green/blue “Next best step: solve two-step equations” card with a tiny concept graph.
- An arrow between them labelled **score → insight → action**.

Avoid stock images of smiling students. A clean product-style visual communicates seriousness and technical capability.

### Speaker script

> A score can tell us that a learner is struggling, but it does not tell the learner or the teacher what to do next. AdaptEd turns every response into a concept-level learning signal and converts that signal into the next best question, explanation and intervention.

### What makes this selection-worthy

The first slide establishes the central contrast: **measurement alone versus actionable mastery**.

---

## Slide 2 — Problem statement: The score hides the gap

### Purpose

Move from a broad education problem to a precise operational problem.

### Put this on the slide

**The problem is not a lack of content. It is a lack of diagnosis.**

Three short cards:

1. **Learner**  
   “I know my score, but not which concept I should fix first.”
2. **Teacher**  
   “I see 40 scores, but not 40 individual misconceptions.”
3. **Institution**  
   “We intervene after failure instead of preventing it earlier.”

Bottom statement:

> Standard assessments compress a multi-concept learning profile into one number.

### Optional problem framing

Show a sample learner result:

```text
Mathematics: 42%
What the score hides:
✓ Variables: strong
△ One-step equations: developing
✕ Two-step equations: weak
✕ Word problems: weak because of the prerequisite gap
```

### Speaker script

> A learner who gets three algebra questions wrong may have three very different causes: a notation issue, a missing prerequisite or a difficulty translating words into equations. A percentage cannot separate these causes. Teachers then spend time guessing, and learners are often given the same worksheet regardless of the gap.

### Visual direction

Use a funnel or compression visual: **multiple concepts and responses → one percentage**. Use red only for the hidden gap; do not make the learner look like the problem.

### Important wording

Say **“the system does not expose the gap”**, not **“weak students cannot learn.”** This is more respectful, more accurate and more compelling.

---

## Slide 3 — Problem context and research: Why now?

### Purpose

Demonstrate that the team did research without drowning the panel in statistics.

### Put this on the slide

**Three signals make adaptive learning urgent:**

**1. Learning is heterogeneous**  
Learners differ in prior knowledge, pace, language, confidence and misconceptions.

**2. Technology is moving from content delivery to learning support**  
Knowledge tracing and intelligent tutoring research show that interaction histories can be used to estimate evolving mastery.

**3. Generative AI lowers the cost of personalised support—but introduces trust risk**  
Explanations must be grounded, age-appropriate and reviewable by teachers.

Use a small source strip at the bottom, not large URLs:

- UNESCO, *Guidance for Generative AI in Education and Research* (2023)
- UNESCO Global Education Monitoring Report, *Technology in education: A tool on whose terms?* (2023)
- Piech et al., *Deep Knowledge Tracing* (2015)
- Khan Academy, Khanmigo product materials
- Duolingo, *Introducing Duolingo Max* (2023)

### Research message to say aloud

> The research does not say “put a chatbot in the classroom and the problem disappears.” It points to a more disciplined opportunity: model the learner’s changing knowledge state, use technology on clear educational terms and keep humans in the loop.

### If you want a number

Use only a number that you can verify from a primary or reputable source before submission. Good candidates include:

- A local baseline from a partner school or a short team-run diagnostic.
- A published learning-outcome or foundational-literacy statistic from an official government, UNESCO, UNICEF or OECD report.
- A pilot baseline such as “8 of 12 test learners could solve a one-step equation but failed a two-step equation.”

Do **not** invent a global percentage to make the slide look stronger. A small, transparent pilot observation is more credible than an unverified viral statistic.

### Visual direction

Create a three-step “then → now → responsible next” timeline:

```text
Marks only  →  Digital content  →  Adaptive, explainable learning loop
```

---

## Slide 4 — Existing solutions and identified gaps

### Purpose

Show awareness of the market and explain the gap your product fills. Do not insult existing products; position them as valuable but incomplete for this use case.

### Put this on the slide

**Existing tools solve parts of the journey. The learner still has to connect the parts.**

| Category | What it does well | Gap for PS-22 |
|---|---|---|
| LMS / classroom tools | Distribute work, collect submissions, show grades | Usually not concept-level diagnosis or next-best learning action |
| Practice platforms | Deliver large question banks and hints | Personalisation may be bounded to platform content; teacher intervention may remain separate |
| AI tutors | Explain or converse on demand | May not maintain a reliable mastery model; hallucination and over-helping risks |
| Assessment tools | Produce tests and reports | Often measure performance after the fact instead of adapting the next item |
| Teacher expertise | Understands context and learner behaviour | Time does not scale to manually inspect every response |

Bottom callout:

> **Identified gap:** An explainable, closed-loop system that links assessment evidence to concept mastery, personalised practice and a teacher action queue.

### Examples you can mention verbally

- Moodle or an LMS: strong course management and assessment workflow.
- Khan Academy / Khanmigo: strong practice and AI-supported tutoring experiences.
- Duolingo Max: strong AI-powered conversational practice and feedback in a focused domain.
- Google Classroom or similar tools: useful distribution and assignment visibility.

Use product names only to explain categories. Do not claim a product lacks a feature unless you have verified the current version.

### Visual direction

Use four blocks around an empty centre:

```text
[Content] [Assessment] [AI explanation] [Teacher reports]
                         ↓
               missing closed loop
```

The empty centre is the opening for AdaptEd.

### Speaker script

> We are not trying to replace an LMS, a teacher or a content platform. We are adding the intelligence layer that connects evidence to the next action, while preserving teacher control.

---

## Slide 5 — Proposed solution: The AdaptEd learning loop

### Purpose

Present the solution in one visual before listing features.

### Put this on the slide

**One learning loop. Two interfaces. One shared mastery model.**

```text
Diagnose → Map the gap → Teach / explain → Practice → Re-check → Improve
                 ↑                                  ↓
              Teacher intervention ← Progress evidence
```

Short definition:

> AdaptEd builds a live concept-level mastery map from learner interactions and uses it to recommend the next best learning action.

### The five product modules

1. **Adaptive assessment** — selects the next item using current mastery and difficulty.
2. **Skill-gap map** — shows subject, concept and prerequisite-level gaps.
3. **Personalised path** — orders micro-lessons, examples and practice by need.
4. **Grounded AI learning assistant** — explains, hints, asks a check question and cites approved sources.
5. **Teacher intervention dashboard** — prioritises students and concepts for human support.

### Subject-wise to concept-wise visibility

AdaptEd must present the same learning state at two levels:

```text
Subject summary: Mathematics
  ↓
Concept detail: Algebra
  ├── Variables and expressions — secure
  ├── Distributive property — developing
  ├── Two-step equations — needs support
  └── Word problems — not enough evidence
```

The subject-level summary should aggregate the underlying concept evidence and provide an entry point for drill-down. The concept-level view is where the platform identifies prerequisites, misconceptions, confidence and the next best action. The MVP uses one subject, but the subject identifier must remain part of the data model and API so the same structure can support additional subjects later.

### Speaker script

> The differentiator is not any one feature. It is the shared mastery model. The same evidence that changes the learner’s next question also powers the teacher’s intervention queue.

### Visual direction

Make the mastery map the centre of the slide. Place the learner app on the left, the teacher dashboard on the right and the map between them. This visually communicates that both users see different views of the same learning state.

---

## Slide 6 — Key features and innovation

### Purpose

Translate the solution into concrete product behaviour and make the innovation legible.

### Put this on the slide

**What the learner gets**

- 5-minute diagnostic instead of a one-size-fits-all test.
- Next question changes with evidence of mastery.
- Concept-level explanation of mistakes.
- Hint-first tutoring rather than answer dumping.
- Weak-area quiz generated from approved concepts.
- Visible “why this next?” explanation for every recommendation.

**What the teacher gets**

- Student mastery heatmap by concept.
- Confidence / evidence indicator for each estimate.
- “Intervene now” queue with reason and suggested action.
- Progress and re-assessment view.
- Ability to approve, edit, hide or replace AI-generated material.

### Innovation statement

> **Explainable closed-loop adaptation:** every recommendation is linked to evidence, every AI explanation is grounded in approved content, and every high-risk decision can be reviewed by a teacher.

### Distinguish innovation from implementation

Your innovation is not “we use an LLM.” The LLM is an implementation component. The innovation is the **evidence → mastery → action → re-check loop** with teacher oversight.

### Visual direction

Use two mock phone/browser panels, but show only one action per panel:

- Learner: “You missed the prerequisite: distributing a negative sign. Let’s try a hint.”
- Teacher: “12 learners are blocked at two-step equations. Suggested intervention: 10-minute mini-lesson + 3-question re-check.”

Keep mock screens large enough to read. Do not show six tiny screenshots.

---

## Slide 7 — Proposed workflow / working mechanism

### Purpose

Prove that the idea is technically coherent, not a collection of buzzwords.

### Put this on the slide

**How one learner response becomes one personalised next step**

```text
1. Learner answers item
             ↓
2. Capture evidence
   correctness · difficulty · time · hint use · misconception tag
             ↓
3. Update concept mastery
   prerequisite-aware score + confidence + recent trend
             ↓
4. Select next best action
   practice · micro-lesson · hint · AI explanation · teacher support
             ↓
5. Re-check and record learning gain
```

### The MVP mastery model

For a first demo, use a transparent hybrid score rather than pretending to have a production-grade deep model:

```text
mastery(concept) =
  0.50 × recent correctness
+ 0.20 × difficulty-adjusted correctness
+ 0.15 × retention / repeat performance
+ 0.10 × independence (fewer hints)
+ 0.05 × response confidence
```

Then apply prerequisite rules:

- If a prerequisite concept is below threshold, recommend that concept first.
- If mastery is high and confidence is high, increase difficulty.
- If correctness is high but hint use is high, label the concept “fragile.”
- If response time is long and errors repeat, recommend a worked example or teacher review.

The coefficients are illustrative for the prototype. State that they will be calibrated with pilot data.

### Adaptive item policy

```text
Start: medium difficulty baseline
If correct twice with low support: move up one difficulty level
If incorrect: serve a targeted hint or prerequisite check
If incorrect twice: pause adaptation, explain, then re-check
If mastery is stable: mix retrieval practice from older concepts
```

### AI assistant policy

1. Identify the learner’s concept and current attempt.
2. Retrieve approved lesson chunks and worked examples.
3. Generate a short explanation at the learner’s level.
4. Ask a leading check question.
5. Do not reveal the full answer before the learner attempts the next step.
6. Show the source / lesson reference.
7. Log feedback for teacher review.

### Speaker script

> We use deterministic rules where the decision must be explainable, a mastery model for learner-state estimation, and a language model only where language generation adds value. This separation makes the MVP feasible and makes the system safer than letting a chatbot decide the whole learning path.

---

## Slide 8 — User journey: One learner, one gap, one recovery path

### Purpose

Make the product emotionally and operationally understandable.

### Persona

**Riya, Class 9**  
She scores 42% in algebra. She can solve one-step equations but repeatedly fails when a negative sign must be distributed in a two-step equation. She has limited time and is embarrassed to ask the same question in class.

### Put this journey on the slide

```text
1. Baseline
   Riya takes 5 adaptive questions.

2. Diagnosis
   AdaptEd identifies a likely gap in “distributive property”.

3. Explanation
   The assistant gives a visual explanation and asks a one-step check question.

4. Targeted practice
   Riya receives three questions that isolate the misconception.

5. Re-check
   A new item tests transfer, not memorisation of the same question.

6. Confidence
   Her mastery map changes from “needs support” to “developing”.
```

### Product copy for the demo

Show these exact example messages in the learner mock-up:

> **Why this next?** You are comfortable with one-step equations. We are practising distributing a negative sign before moving to two-step equations.

> **Hint 1:** What happens to every term inside the bracket when you multiply by −2?

> **Try again:** Solve −2(x + 3) = 8. First expand the bracket; do not move terms yet.

### Speaker script

> Riya is not sent back to the entire algebra chapter. The platform isolates the bottleneck, gives a hint before an answer, and checks whether the skill transfers to a new problem. This is the difference between personalised learning and simply serving more content.

### Visual direction

Use a horizontal six-step journey with a small mastery meter under each step. Highlight the moment where the generic score becomes an actionable concept.

---

## Slide 9 — Teacher dashboard and intervention loop

### Purpose

Show that the platform serves teachers rather than trying to remove them.

### Put this on the slide

**Teacher view: from 40 scores to 3 high-value actions**

Dashboard cards:

- **Class mastery:** 64% average across the selected concept cluster.
- **Most common gap:** distributing signs — 11 learners.
- **At-risk trend:** 5 learners have repeated the same misconception twice.
- **Suggested action:** 10-minute mini-lesson + 3-question re-check.

The dashboard should support a clear drill-down:

```text
Subject summary: Mathematics
    → Concept detail: Distributive property
    → Evidence: repeated negative-sign misconception
    → Action: mini-lesson and re-check
```

The subject summary gives the teacher a high-level view of progress. The concept detail explains the reason behind that summary and provides the evidence for intervention.

Intervention queue example:

| Priority | Learner / group | Evidence | Recommended action |
|---|---|---|---|
| High | Riya | 2 repeated errors, high hint use | Review worked example, then re-check |
| Medium | Group B | Correct answers but slow response | Retrieval practice set |
| Low | Group C | Stable mastery | Mixed challenge quiz |

### Teacher control points

- Approve or edit AI explanations.
- Lock a prerequisite before the learner moves forward.
- Assign a class-level mini-lesson.
- Override a recommendation.
- Export a progress report.

### Speaker script

> The dashboard is not another wall of analytics. It is an intervention queue. It tells a teacher which concept is blocking how many learners, why the system is concerned and what small action is recommended. The teacher remains the decision-maker.

### Visual direction

Use a heatmap on the left and a three-row action queue on the right. Use only three colours with a legend: green = secure, amber = developing, red = needs support. Add a confidence badge so the teacher can distinguish “well-supported signal” from “needs more evidence.”

---

## Slide 10 — Process flow diagram

### Purpose

Give the panel a single end-to-end picture that joins the learner, AI and teacher paths.

### Put this on the slide

```text
                 ┌──────────────────────────┐
                 │ Teacher-approved content │
                 │ concepts, examples, rubrics│
                 └──────────────┬───────────┘
                                │ indexed for retrieval
                                ▼
┌───────────────┐       ┌────────────────────┐       ┌──────────────────────┐
│ Learner starts │──────▶│ Adaptive assessment│──────▶│ Evidence store       │
│ baseline       │       │ item selection     │       │ answers, time, hints  │
└───────────────┘       └──────────┬─────────┘       └──────────┬───────────┘
                                   │                            │
                                   ▼                            ▼
                         ┌────────────────────┐       ┌──────────────────────┐
                         │ Mastery + gap map  │──────▶│ Recommendation engine │
                         │ concept graph      │       │ next best action      │
                         └──────────┬─────────┘       └──────────┬───────────┘
                                    │                            │
                       ┌────────────┴────────────┐               │
                       ▼                         ▼               ▼
              ┌────────────────┐       ┌────────────────┐  ┌──────────────┐
              │ Learner path   │       │ Grounded AI    │  │ Teacher queue│
              │ practice/quiz  │       │ hints/explain  │  │ intervene    │
              └───────┬────────┘       └───────┬────────┘  └──────┬───────┘
                      └──────────────┬────────┘                    │
                                     ▼                             │
                              ┌──────────────┐                      │
                              │ Re-assess    │◀─────────────────────┘
                              │ measure gain │
                              └──────────────┘
```

### Key label to add

Place a loop arrow around **evidence → mastery map → recommendation → re-assessment**. That loop is your product’s core.

### Presenter explanation

> Content is curated and indexed before the learner interacts. The learner’s responses update an evidence store and mastery map. The recommendation engine decides the next action. The learner gets a path and a grounded explanation; the teacher gets an intervention queue. Re-assessment closes the loop.

---

## Slide 11 — Proposed technology stack and responsible AI

### Purpose

Show a realistic architecture and explain why each technology exists.

### Put this on the slide

**Prototype stack**

| Layer | Suggested choice | Reason |
|---|---|---|
| Frontend | React + TypeScript + Tailwind or Material UI | Fast role-based learner and teacher views |
| API | Python + FastAPI | Typed, lightweight, easy to demo and integrate with ML/LLM services |
| Mastery engine | Python service with rule-based policy + Bayesian / logistic baseline | Transparent decision path; works with limited pilot data |
| LLM layer | Approved LLM API or local open model | Generate explanations, hints and quiz drafts; not the final authority on mastery |
| RAG | Embeddings + vector store such as pgvector or Chroma | Restrict explanations to teacher-approved content |
| Database | PostgreSQL | Learners, attempts, concepts, recommendations, audit history |
| Auth | JWT / session-based role access | Separate learner and teacher data paths |
| Deployment | Docker + a simple cloud service | Reproducible demo and easy handoff |

### Architecture principle

```text
Rules decide safety-critical learning actions.
ML estimates mastery from evidence.
LLM generates language within retrieved content.
Teacher approves high-impact interventions.
```

### Responsible AI guardrails

- Retrieval-grounded answers with lesson citations.
- Age-appropriate language and no open-ended medical, legal or mental-health advice.
- Hint-first mode; the assistant should encourage thinking.
- “I’m not sure” fallback when retrieval confidence is low.
- Teacher review and override.
- Audit log of generated content, source chunks and model version.
- Collect only necessary learner data; use pseudonymous IDs in the prototype.
- No automated high-stakes grading or promotion decisions.
- Accessibility: keyboard navigation, readable contrast, text alternatives and low-bandwidth fallback.

### Speaker script

> The architecture intentionally separates prediction from generation. The model estimates a learning state; the language model communicates a safe explanation using approved material. This improves reproducibility, explainability and trust.

---

## Slide 12 — Feasibility and execution plan

### Purpose

Prove that the team can deliver the expected functional demo.

### Put this on the slide

**MVP scope: one subject, one concept graph, two roles, one closed loop**

### Suggested 4-phase plan

| Phase | Deliverable | Evidence of completion |
|---|---|---|
| 1. Design + content | Concept graph, item bank, misconception tags, user flows | 5–10 concepts and 30–50 teacher-reviewed questions |
| 2. Core intelligence | Adaptive item selector, mastery update, recommendation rules | A test script shows different next questions for different responses |
| 3. Product surfaces | Learner assessment/path and teacher dashboard | End-to-end role-based flow works with seeded data |
| 4. AI + validation | Grounded assistant, quiz generation, guardrails, metrics | Explanation cites source; re-check shows mastery change; edge cases handled |

### Team role split

- **Product / research:** learner personas, concept graph, success metrics, pitch.
- **Frontend:** learner and teacher screens, visual progress map.
- **Backend:** API, database schema, authentication, event logging.
- **AI / data:** mastery estimator, retrieval, prompt templates, evaluation set.
- **QA / demo owner:** scripted scenarios, failure states, rehearsal, backup video.

### What to build versus what to defer

**Build for the hackathon**

- One grade + subject pilot.
- 5–10 concepts with prerequisite edges.
- Seeded learner profiles.
- Adaptive diagnostic and three-level difficulty.
- Gap map and recommendation cards.
- Grounded hint / explanation assistant.
- Weak-area quiz generation using a controlled schema.
- Teacher dashboard with intervention queue.

**Defer to future scope**

- All subjects and boards.
- Voice tutor and emotion detection.
- Fully automatic curriculum authoring.
- High-stakes certification.
- Large-scale predictive dropout scoring.
- Fully autonomous teacher interventions.

### Feasibility proof to show

Include a small “prototype truth” box:

> **In our demo,** two learners answer the same first question but receive different next questions because their mastery evidence differs. A teacher sees the concept cluster behind both outcomes and receives an intervention suggestion.

This is stronger than claiming the platform works for every learner.

---

## Slide 13 — Expected impact, future scope and close

### Purpose

Finish with measurable impact, not a generic “AI will transform education” statement.

### Put this on the slide

**Near-term impact**

- Learners know what to learn next, not just what they scored.
- Teachers prioritise intervention by concept and evidence.
- Institutions can see whether remediation changed mastery.

**Pilot success metrics**

| Metric | Definition |
|---|---|
| Concept mastery gain | Change in mastery estimate between diagnostic and re-check |
| Transfer accuracy | Performance on a new item testing the same concept |
| Time-to-mastery | Attempts or minutes needed to cross the mastery threshold |
| Recommendation usefulness | Learner / teacher rating and acceptance rate |
| Teacher efficiency | Time saved identifying a small intervention group |
| Explanation quality | Rubric score for correctness, grounding and age appropriateness |
| Equity / access | Performance and completion differences across language, device and connectivity groups |

**Future scope**

- More subjects through reusable concept graphs.
- Multilingual explanations and regional curricula.
- Spaced repetition and long-term retention modelling.
- Teacher authoring and collaborative lesson feedback.
- Offline / low-bandwidth mode.
- School-level analytics with privacy-preserving aggregation.
- Research evaluation with controlled pilots and teacher feedback.

### Final close

> **AdaptEd does not replace the teacher. It gives every learner a next step—and gives every teacher the evidence to make that step count.**

End with a QR code or short demo URL only if it works reliably. Add the team contact and a one-line ask:

> **We are looking for a pilot classroom / mentor to validate the mastery loop.**

### Speaker script

> Our first success is not a perfect prediction model. It is a learner who can identify and improve a real concept gap, and a teacher who can act earlier with less manual diagnosis. We start narrow, measure the loop and scale only after the evidence is trustworthy.

---

# Compressed 8-slide version

Use this if the submission portal allows only a small number of slides.

| Slide | Combine |
|---:|---|
| 1 | Title + one-line pitch |
| 2 | Problem statement + learner/teacher pain |
| 3 | Context, research and existing-solution gaps |
| 4 | Proposed solution + innovation |
| 5 | User journey + product screens |
| 6 | Working mechanism + process flow |
| 7 | Tech stack + feasibility + responsible AI |
| 8 | Impact metrics + future scope + close |

For a one-page executive summary, use the following copy:

> **AdaptEd is an explainable adaptive learning platform for Class 9 mathematics.** It diagnoses concept-level gaps from learner responses, selects the next best question, explains mistakes from teacher-approved content and gives teachers an intervention queue. Unlike a score-only assessment or a stand-alone chatbot, AdaptEd connects subject summaries, concept evidence, mastery, action and re-assessment in one closed loop. The MVP uses React, FastAPI, PostgreSQL, a prerequisite-aware mastery engine and RAG-grounded LLM explanations. We will measure concept mastery gain, transfer accuracy, time-to-mastery, explanation quality and teacher intervention efficiency.

---

# What to actually demo in round one

## The ideal 90-second demo story

Seed two learner profiles so the adaptive behaviour is visible:

### Learner A — foundation gap

- Strong in variables.
- Weak in distributing negative signs.
- Uses hints repeatedly.
- Receives prerequisite explanation and easier targeted items.

### Learner B — ready for challenge

- Strong in one- and two-step equations.
- Low hint use.
- Receives a word-problem transfer item and a higher difficulty question.

### Demo sequence

1. Open the learner assessment.
2. Answer one item correctly and one item incorrectly.
3. Show the mastery map changing.
4. Ask the assistant “Why did I get this wrong?”
5. Show a grounded hint with a source label.
6. Take the targeted quiz.
7. Switch to the teacher view.
8. Show the concept heatmap and the intervention queue.
9. Re-check the learner and show improvement.

## Demo fallback plan

Prepare three layers of backup:

1. Live deployed demo.
2. Local demo with seeded data and a mock LLM response.
3. 60–90 second screen recording embedded in the deck.

Do not let an API timeout make the team appear unprepared. Put a small “demo mode” label on any seeded or cached response.

---

# Design system for the PPT

## Visual theme

Use a calm, trustworthy education aesthetic rather than a neon “AI startup” look.

### Palette

- **Ink:** `#172033` — body text and headings.
- **Deep blue:** `#2457A6` — trust, navigation and primary actions.
- **Teal:** `#18A999` — growth and confirmed mastery.
- **Amber:** `#F4B942` — developing / needs attention.
- **Coral:** `#E76F51` — risk or error, used sparingly.
- **Mist:** `#F4F7FB` — slide background.
- **White:** `#FFFFFF` — cards and screenshots.

### Typography

- Heading: Inter, Manrope or Aptos Display, bold.
- Body: Inter, Aptos or Source Sans 3.
- Use a maximum of two typefaces.
- Headings 32–44 pt; body 18–24 pt; footnotes 10–12 pt.
- Use sentence case, not all caps, except for small labels.

### Layout rules

- 16:9 widescreen.
- One message per slide.
- 60% visual, 40% text maximum.
- Keep margins generous; align cards to a clear grid.
- Use the same top-left title position on every slide.
- Use a small progress marker such as `01 / 13` in the footer.
- Use a single illustration style and one icon family.

### Diagram rules

- Arrows should have one direction and a short verb label.
- Never connect every object to every other object.
- Use colour to indicate state, not to decorate.
- Add a legend when using red / amber / green.
- Put the conclusion next to the diagram, not several slides later.

## What not to do visually

- Do not put a wall of text on the slide.
- Do not use more than one large statistic without its source.
- Do not show an unreadable architecture diagram with 20 tools.
- Do not use fake product screenshots that look like a finished enterprise product if it is a prototype; label mock-ups honestly.
- Do not use a chatbot screen as the only proof of innovation.
- Do not use red for “weak student”; use it for a learning state that can change.

---

# Submission-quality checklist

## Content checklist

- [ ] The title names PS-22 and the product promise.
- [ ] The problem is framed as a diagnostic and intervention gap.
- [ ] A focused pilot segment is named.
- [ ] Existing solution categories are acknowledged fairly.
- [ ] The differentiator is a closed-loop mastery model.
- [ ] Adaptive assessment is explained with a concrete policy.
- [ ] Concept-level gap identification is visible.
- [ ] Personalised recommendation is shown, not just claimed.
- [ ] The AI assistant is grounded and hint-first.
- [ ] Weak-area quiz generation is included.
- [ ] The teacher dashboard contains an action queue.
- [ ] User journey and process flow are present.
- [ ] Tech stack maps to actual responsibilities.
- [ ] MVP scope and execution plan are credible.
- [ ] Impact metrics are measurable.
- [ ] Future scope does not overwhelm the MVP.
- [ ] SDG 4 is connected to the actual product outcome.

## Credibility checklist

- [ ] Every statistic has a source and retrieval date.
- [ ] Product capabilities are not exaggerated.
- [ ] The team can explain what is rule-based, ML-based and LLM-based.
- [ ] The team can show one real end-to-end flow.
- [ ] The demo has a fallback.
- [ ] Privacy, accessibility and teacher control are mentioned.
- [ ] Mock data and prototype assumptions are labelled.

## Rehearsal checklist

- [ ] The complete pitch fits the time limit with 20% buffer.
- [ ] Each speaker has a clear handoff line.
- [ ] No speaker reads the slide word-for-word.
- [ ] The team can answer “What happens when the AI is wrong?”
- [ ] The team can answer “What is your actual novelty?”
- [ ] The team can answer “How will you evaluate improvement?”
- [ ] The team can answer “Why not just use an LMS or ChatGPT?”

---

# Likely judge questions and strong answers

## “Why not just use ChatGPT?”

> A general chatbot can explain a concept, but it does not reliably maintain a prerequisite-aware mastery model, choose the next assessment item, measure transfer or create a teacher intervention queue. AdaptEd uses an LLM only for grounded communication inside a larger evidence and assessment loop.

## “How do you know a learner has a skill gap?”

> We do not infer it from one wrong answer. We combine repeated evidence: correctness, item difficulty, prerequisite relationships, hint use, response trend and re-check performance. The system also exposes confidence and requests more evidence when the signal is uncertain.

## “What if the AI gives a wrong explanation?”

> Explanations are generated from teacher-approved retrieved content, checked against a structured response format and shown with a source. Low-retrieval-confidence cases fall back to a curated explanation or teacher review. The assistant is not allowed to make high-stakes decisions autonomously.

## “How is this feasible with limited data?”

> The MVP uses a small, explicitly designed concept graph, teacher-reviewed items and a transparent hybrid mastery policy. We can demonstrate adaptive behaviour without claiming to have trained a large model. Pilot interaction data can calibrate the model later.

## “How will you prevent students from gaming the system?”

> We use varied item templates, transfer questions, response-time and hint-use signals, periodic re-checks and teacher review. We treat speed as a supporting signal, not as a standalone judgment.

## “What is the business or adoption model?”

> The initial model is institution-led: a school or coaching centre pilots a subject pack and teacher dashboard. The product can later support curriculum publishers, district programs and learner subscriptions, but adoption begins with a measurable classroom workflow.

## “How will you handle privacy?”

> We collect the minimum data needed for learning recommendations, use role-based access and pseudonymous identifiers in the prototype, separate analytics from identity where possible and retain an audit trail for generated content and recommendations.

## “How does this support SDG 4?”

> It supports more inclusive, equitable quality education by making targeted support available beyond the few learners a teacher can manually diagnose in a large class. Accessibility, multilingual delivery and low-bandwidth support are part of the scale-up plan.

---

# Final positioning statement

If the panel remembers only one idea, make it this:

> **AdaptEd is not a chatbot added to a classroom. It is a closed-loop learning system that turns evidence into mastery insight, mastery insight into a personalised action and that action into measurable improvement.**
