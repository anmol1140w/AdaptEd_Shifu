# PS-22 Pitch Script, Demo Runbook and Selection Strategy

This is the speaking and rehearsal companion to `PS22_Hackathon_PPT_Blueprint.md`. It assumes a 5–7 minute round-one presentation with a 90-second product demonstration. Adjust the timings if the event gives a different limit.

---

## 1. Winning pitch structure

Use this narrative order:

```text
Pain → Evidence → Gap → Insight → Product → Proof → Feasibility → Impact → Ask
```

The audience should never wonder why a feature appears. Every feature should answer a pain introduced earlier.

### The story in one sentence per act

- **Pain:** A score tells a learner that they are behind but not which concept is blocking progress.
- **Evidence:** Learning technology is most valuable when it is aligned to a clear educational goal and supported by responsible use.
- **Gap:** Current tools often split content, assessment, tutoring and teacher analytics across separate experiences.
- **Insight:** The useful unit of personalisation is not “more content”; it is the next best learning action for a specific concept.
- **Product:** AdaptEd builds a concept-level mastery map and closes the loop from evidence to action to re-check.
- **Proof:** One simulated learner receives prerequisite support while another receives a harder transfer question.
- **Feasibility:** Start with one grade, subject and concept graph; use deterministic rules where explainability matters.
- **Impact:** Measure mastery gain, transfer, explanation quality and teacher intervention efficiency.
- **Ask:** Help us validate the loop with a pilot classroom or mentor.

---

## 2. Five-minute script

The script below is intentionally concise. Do not read every word if the team is comfortable speaking naturally.

### 0:00–0:20 — Slide 1

> A score can tell us that a learner is struggling, but it cannot tell the learner what to learn next or the teacher which concept to address. AdaptEd is an adaptive learning and skill-gap platform built around one promise: **from marks to mastery**. We begin with a focused pilot for Class 9 mathematics, algebra and linear equations.

### 0:20–0:50 — Slide 2

> Today, three people experience the same gap. The learner sees a percentage without a recovery path. The teacher sees many scores without the individual misconception behind them. The institution intervenes after failure instead of identifying the prerequisite gap earlier. A single score compresses many concepts into one number.

### 0:50–1:20 — Slide 3

> This is a good moment for an evidence-led adaptive system, but not for an unsupervised chatbot. UNESCO’s guidance emphasises human-centred, inclusive and safe use of generative AI. Knowledge-tracing research shows that learner interactions can be used to model evolving knowledge. Our design combines that opportunity with teacher approval and measurable re-assessment.

### 1:20–1:50 — Slide 4

> Existing tools are valuable: LMSs organize courses, practice platforms deliver questions, AI tutors explain and assessment tools report scores. The gap is the connection between them. We need one system that can say: this is the likely concept gap, this is the evidence, this is the next action and this is how we will check whether it worked.

### 1:50–2:25 — Slide 5

> AdaptEd closes that loop. It diagnoses, maps the gap, teaches or explains, gives targeted practice, re-checks the concept and then shows progress to the teacher. The shared mastery model is the bridge between the learner experience and the teacher dashboard. We are not replacing a teacher or an LMS; we are adding an evidence-to-action layer.

### 2:25–3:10 — Slide 7 / mechanism

> For every response, we capture correctness, item difficulty, time, hint use and misconception tags. A transparent mastery policy updates the concept state and its confidence. If a prerequisite is weak, the next action is a scaffolded lesson. If the concept is developing, the next action is targeted practice. If it is secure, the learner receives a transfer or higher-difficulty item. The language model generates a hint or explanation only from approved content.

### 3:10–4:10 — Demo

> Let us follow Riya. She gets two questions wrong around distributing a negative sign. The platform does not send her back to the whole algebra chapter. It identifies the specific concept, explains why the next item was selected and gives a hint before showing an answer. After targeted practice, we give her a new transfer question. Now we switch to the teacher view: the dashboard groups the same pattern across learners and recommends a short mini-lesson and re-check. The teacher can approve, edit or override that recommendation.

### 4:10–4:40 — Slides 10–11

> The prototype uses React and FastAPI for the role-based interfaces and API, PostgreSQL for learning evidence, a concept graph and transparent mastery service for adaptation, and retrieval-grounded generation for explanations. Rules decide the learning policy; the model estimates mastery; the LLM communicates within retrieved content; the teacher controls high-impact actions.

### 4:40–5:10 — Slides 12–13

> We keep the MVP buildable: one subject, five to ten concepts, teacher-reviewed items, two user roles and one closed loop. We will measure concept mastery gain, transfer accuracy, time-to-mastery, explanation quality and teacher intervention efficiency. AdaptEd does not replace the teacher. It gives every learner a next step and every teacher the evidence to make that step count.

---

## 3. Seven-minute expanded script

Use the extra time for the user journey, dashboard and impact detail. Do not add more features just to fill time.

### Optional 45 seconds on the user journey

> Riya is a useful example because her score hides the cause of her difficulty. She knows variables and one-step equations, but she repeatedly loses a negative sign when expanding brackets. AdaptEd shows that prerequisite, gives a visual explanation, asks her to attempt the next step and checks transfer with a new question. This makes the learner’s progress visible without labelling her as permanently weak.

### Optional 30 seconds on teacher value

> For a teacher, the important output is not another chart. It is a short intervention queue: which concept is blocking how many learners, how strong the evidence is and what action is suggested. The teacher can group learners for a mini-lesson, edit the content or override the system if classroom context says something different.

### Optional 30 seconds on responsible AI

> We treat educational AI as a high-trust domain. The prototype uses pseudonymous demo data, approved content, retrieval references, age-appropriate prompt rules, a hint-first policy and audit events for generated content. Low-confidence retrieval falls back to a curated response or teacher review. We do not use the system for automated high-stakes promotion or punishment.

---

## 4. Demo runbook

### Before presenting

- Start the local or deployed app before the judges arrive.
- Log in as a demo learner in one browser tab and as a teacher in another.
- Seed both learner profiles and reset their attempts.
- Confirm the LLM response is cached or the demo mode is available.
- Open the source lesson used by the RAG response.
- Keep the backup recording in a separate tab or presentation slide.
- Turn off notifications and close unrelated applications.

### Demo data

Use clearly fictional data:

```text
Class: 9A — Mathematics
Learner 1: Riya — foundation gap in distributive property
Learner 2: Arjun — secure in two-step equations, ready for transfer
Learner 3: Meera — insufficient evidence, needs baseline
Concept cluster: Variables → Distributive property → Two-step equations
```

### Exact click path

1. Open Riya’s learner dashboard.
2. Click **Start diagnostic**.
3. Answer the first item correctly.
4. Answer a distributive-property item incorrectly.
5. Show the Mathematics subject summary, drill down to the concept map and open the “why this next?” panel.
6. Click **I need a hint**.
7. Show the hint, source label and check question.
8. Submit a corrected attempt.
9. Open **Targeted practice**.
10. Answer a transfer item.
11. Switch to the teacher dashboard.
12. Open **Intervention queue**.
13. Show the group count, evidence, confidence and suggested action.
14. Approve or edit the recommendation.
15. Show the mastery trend after the re-check.

### Demo narration: the three “wow” moments

**Wow moment 1 — adaptation**

> The next question is different because the evidence is different. This is not a fixed quiz sequence.

**Wow moment 2 — grounded explanation**

> The assistant explains the exact misconception, gives a hint rather than dumping the answer and points to the approved lesson source.

**Wow moment 3 — teacher action**

> The same learner evidence becomes an actionable teacher queue, not just another analytics chart.

### If the live demo breaks

Say:

> We will switch to our seeded demo mode so the learning logic remains visible without depending on a live model call.

Then show the recording or cached response. Never apologise for ten seconds while the audience watches a spinner.

---

## 5. Team speaking roles

### Team of two

- **Speaker 1:** Slides 1–5 and opening problem story.
- **Speaker 2:** Slides 6–13, demo and technical feasibility.

### Team of three

- **Speaker 1:** Problem, context, existing gaps.
- **Speaker 2:** Product, user journey, live demo.
- **Speaker 3:** Architecture, feasibility, impact and Q&A lead.

### Team of four or more

Keep only three speakers on stage if possible. Assign the remaining members to:

- Demo operations.
- Backup video and deployment.
- Judge Q&A support.
- Evidence and citation verification.

Too many speaker handoffs can make a short pitch feel fragmented.

### Handoff lines

- “Now that we have shown the gap, [Name] will show how AdaptEd closes it.”
- “You have seen the learner path; [Name] will show how the same evidence helps the teacher.”
- “The product idea is clear; [Name] will now prove that the MVP is technically feasible.”

---

## 6. Selection-oriented scoring strategy

Use this internal scoring rubric before submission. Score each row from 1 to 5 and ask a team member who is not building the product to judge the deck.

| Criterion | 1-point failure | 5-point evidence |
|---|---|---|
| Problem clarity | Generic “education is hard” statement | Specific learner, teacher and system pain with a concept-level example |
| Relevance to PS-22 | Only a chatbot or quiz | Adaptive assessment, skill-gap identification, recommendations, assistant, quizzes and teacher analytics are connected |
| Innovation | “We use AI” | Explainable closed-loop mastery model with teacher oversight |
| Feasibility | All subjects, all ages, all languages | One bounded pilot, named data, named modules and build sequence |
| Technical depth | Buzzword stack | Clear separation of policy, mastery, retrieval and generation |
| User value | Feature list | One learner journey and one teacher intervention outcome |
| Responsible AI | No risk plan | Grounding, hint-first, teacher approval, privacy, audit and accessibility |
| Impact | Vague social good | Metrics and evaluation design |
| Presentation | Dense slides | One message per slide, legible visuals, rehearsed demo |
| Team readiness | Cannot answer questions | Clear ownership, backup plan and realistic assumptions |

### Internal target

Aim for at least **40/50** before submitting. A weak problem slide or unconvincing feasibility plan is usually more damaging than a less flashy UI.

---

## 7. Three-day preparation plan

### Day 1 — Story and evidence

- Freeze the pilot scope.
- Finalise product name and tagline.
- Collect and verify four to six sources.
- Write the one-line problem statement.
- Draw the concept graph.
- Draft the 13-slide deck with placeholders, not decoration.
- Decide what is prototype logic versus future scope.

### Day 2 — Product and demo

- Build or polish the learner flow.
- Build the teacher intervention queue.
- Seed two contrasting learner profiles.
- Implement the mastery update and adaptive next-item policy.
- Add RAG source labels or honest simulated source labels.
- Record a fallback demo.

### Day 3 — Polish and rehearse

- Replace paragraphs with diagrams and short copy.
- Check font size from a distance.
- Add source footnotes.
- Time the complete pitch three times.
- Ask an outsider to repeat the product promise after viewing Slide 1.
- Run the judge-question drill.
- Export a PDF and verify that all fonts, diagrams and links render.

---

## 8. Question drill before submission

Each team member should answer these in 20 seconds or less.

### What is the exact problem?

> Learners receive scores without concept-level diagnosis, and teachers cannot manually turn every response into a personalised intervention.

### What is the one-line solution?

> A concept-level mastery loop that selects the next best learning action and gives teachers an evidence-based intervention queue.

### What is new?

> The integration of adaptive assessment, explainable mastery mapping, grounded AI support and teacher action in one closed loop—not the use of an LLM alone.

### What is your MVP?

> Class 9 mathematics, algebra and linear equations, five to ten concepts, teacher-reviewed items, two roles and one end-to-end re-assessment loop.

### How are subject-wise and concept-wise gaps shown?

> AdaptEd gives a subject-level summary first—for example, overall Mathematics progress—then lets the learner or teacher drill down into concept-level mastery, prerequisites, misconceptions, confidence and evidence. The MVP uses one subject, but subject identifiers remain in the model so the same reporting structure can support additional subjects later.

### What happens if the LLM fails?

> The deterministic assessment and mastery path still work; the tutor falls back to a curated explanation or teacher review.

### How do you measure success?

> Concept mastery gain, transfer accuracy, time-to-mastery, explanation quality and teacher intervention efficiency.

### How do you protect learners?

> Minimum data, pseudonymous demo IDs, role-based access, grounded responses, hint-first behaviour, teacher override and no autonomous high-stakes decisions.

### Why will schools adopt it?

> It fits existing course and teacher workflows, starts with a small curriculum pack and reduces the manual effort needed to identify the next intervention.

---

## 9. Final rehearsal checklist

### Story

- [ ] The first 20 seconds contain the problem, product and pilot scope.
- [ ] The team says “concept” or “skill gap” consistently.
- [ ] Existing tools are respected and the gap is specific.
- [ ] The product is presented as a loop, not a feature list.

### Demo

- [ ] The next question visibly changes.
- [ ] The explanation includes a source or clearly labelled demo source.
- [ ] The teacher dashboard shows an action, not only a chart.
- [ ] A transfer question appears after targeted practice.
- [ ] The backup mode is tested.

### Slides

- [ ] No paragraph is smaller than 18 pt in the main deck.
- [ ] Every statistic has a source.
- [ ] Every prototype screen is labelled `prototype` or `demo data` where appropriate.
- [ ] No slide has more than one main conclusion.
- [ ] The final slide repeats the memorable promise.

### Q&A

- [ ] One person owns the technical architecture answer.
- [ ] One person owns the education / impact answer.
- [ ] One person owns privacy and responsible AI.
- [ ] The team can admit what is not yet built without undermining the MVP.
