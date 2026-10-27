# PS-22 Research, Evidence and Citation Pack

This file supports the round-one PPT. It is deliberately conservative: it separates verified source claims, product observations and claims that the team should validate through a small pilot. Use the source links in speaker notes or an appendix rather than filling the visible slides with URLs.

**Prepared:** 15 October 2026  
**Recommended pilot:** Class 9 Mathematics — Algebra and Linear Equations  
**Product name:** AdaptEd

---

## 1. Research thesis

The argument for PS-22 should not be “AI is popular, therefore education needs AI.” The stronger research thesis is:

> Learners produce observable interaction evidence; a platform can use that evidence to estimate concept-level knowledge, choose an appropriate next action and support teachers with a prioritised intervention view. Generative AI is useful for explanations and item drafts, but educational reliability requires grounding, guardrails and human oversight.

For PS-22, AdaptEd should report learning at two connected levels: a subject-wise summary for overall progress and a concept-wise drill-down that identifies the prerequisite, misconception and evidence behind that summary. The pilot is intentionally limited to Class 9 Mathematics, while the subject-aware model remains extensible to additional subjects.

This gives the deck four layers of evidence:

1. **Education context:** learning is heterogeneous and technology must serve a clear educational purpose.
2. **Learning science / educational AI:** knowledge tracing and adaptive tutoring are established research directions.
3. **Current product landscape:** LMSs, practice platforms and AI tutors each solve useful parts of the workflow.
4. **Your validation plan:** a bounded pilot will test whether the closed loop improves mastery and teacher efficiency.

---

## 2. Sources to cite in the deck

### Source A — UNESCO guidance on generative AI in education

**Source:** UNESCO, *Guidance for Generative AI in Education and Research* (2023).  
**Stable landing page:** <https://unesdoc.unesco.org/ark:/48223/pf0000386693>

**Use this source for:**

- The need for a human-centred approach to generative AI in education.
- Data privacy, inclusion, age-appropriateness and human agency.
- The principle that AI should support educational goals rather than replace educators.

**Safe wording for the slide:**

> UNESCO’s guidance frames generative AI in education as a human-centred opportunity that requires privacy, inclusion, age-appropriate use and human oversight.

**Do not write:** “UNESCO says AI will solve the learning gap.” That is not a defensible interpretation.

**Place in deck:** Slide 3 context; Slide 11 responsible AI.

---

### Source B — UNESCO Global Education Monitoring Report

**Source:** UNESCO GEM Report 2023, *Technology in education: A tool on whose terms?*  
**Landing page:** <https://gem-report-2023.unesco.org/>

**Use this source for:**

- Technology should be evaluated against educational objectives, not novelty.
- Access, governance, evidence and teacher capability matter.
- Technology can support learning but is not automatically beneficial merely because it is digital.

**Safe wording for the slide:**

> The case for educational technology is strongest when it is evidence-led, accessible and aligned to a clear learning goal.

**Place in deck:** Slide 3 context; Slide 12 feasibility and impact.

---

### Source C — Deep Knowledge Tracing

**Source:** Piech et al., *Deep Knowledge Tracing* (2015).  
**Stable page:** <https://arxiv.org/abs/1506.05908>

**What the paper contributes:**

- Knowledge tracing models the learner’s knowledge as it changes through interactions with coursework.
- The paper explores recurrent neural networks for predicting future student performance.
- It connects learner-state modelling with intelligent curriculum design.

**How to use it honestly:**

> Educational AI research has explored knowledge tracing: modelling a learner’s evolving knowledge from interaction sequences. AdaptEd uses a transparent, smaller hybrid mastery model for the MVP and treats advanced knowledge tracing as a later calibration path.

**Do not claim:** that your prototype reproduces the paper’s results, or that deep learning is necessary for the first version.

**Place in deck:** Slide 3 research; Slide 7 working mechanism.

---

### Source D — Khan Academy / Khanmigo

**Primary product pages to verify before submission:**

- <https://www.khanmigo.ai/>
- <https://www.khanacademy.org/khan-labs>

**Product category observation:**

- Khan Academy demonstrates how a large educational content ecosystem can add AI tutoring and educator support.
- It is a useful benchmark for conversational guidance, hints and teacher-facing support.

**Safe wording:**

> AI tutoring products show the value of conversational, guided help inside a structured learning ecosystem. AdaptEd focuses specifically on the diagnostic-to-intervention loop and exposes subject summaries with concept-level evidence to teachers.

**Do not claim:** that a benchmark product has no adaptive or analytics features. Product capabilities change; describe the gap as your focus, not an absolute criticism.

**Place in deck:** Slide 4 existing solutions; Slide 6 innovation.

---

### Source E — Duolingo Max

**Source accessed for this blueprint:** Duolingo, “Introducing Duolingo Max, a learning experience powered by GPT-4,” 14 March 2023.  
**URL:** <https://blog.duolingo.com/duolingo-max/>

**Product category observation:**

- The article describes AI-powered conversational features such as Video Call and Roleplay.
- It describes feedback after the interaction and human involvement in scenario design and content review.

**Safe wording:**

> Domain-focused products demonstrate that generative AI can support practice, roleplay and feedback when the experience is constrained by curriculum design and human review.

**Why it helps your argument:**

It is a concrete example of “AI inside a learning experience,” while your product differentiates around concept mastery, adaptive assessment and teacher intervention.

**Place in deck:** Slide 4 existing solutions; Slide 11 human review.

---

### Source F — Moodle / LMS category

**Product source to verify before submission:** <https://moodle.org/>  
**Documentation:** <https://docs.moodle.org/>

**Category observation:**

- LMSs organize courses, learning materials, activities, submissions and grades.
- They are important integration points, not competitors to dismiss.

**Safe wording:**

> An LMS provides the course and assessment workflow. AdaptEd can sit as an intelligence layer that interprets interaction evidence and recommends the next learning action.

**Place in deck:** Slide 4 existing solutions; Slide 11 architecture.

---

## 3. Research-to-slide map

| Slide | Claim | Evidence / support | How to say it safely |
|---:|---|---|---|
| 2 | Marks alone hide concept-level gaps | Product problem framing; validate with a small pilot | “A score compresses multiple concepts into one number.” |
| 5, 9 | Subject-wise summaries should lead to concept-wise diagnosis | Proposed product design; validate through teacher review | “The subject view summarizes progress, while the concept view shows the evidence and next action behind it.” |
| 3 | Educational AI must be human-centred | UNESCO guidance and GEM Report | “AI is useful when aligned to learning goals and safeguards.” |
| 3 | Learner knowledge can be modelled from interaction histories | Knowledge-tracing research | “Research has explored…” not “our model is proven.” |
| 4 | Existing products solve parts of the journey | Product documentation and official product pages | “Our focus is the missing connection,” not “others cannot do this.” |
| 5–7 | Closed-loop evidence → action → re-check | Your product design | Label as proposed mechanism / MVP design. |
| 11 | RAG and teacher approval reduce unsupported generation | Architecture and evaluation plan | “Designed to reduce risk,” not “guarantees correctness.” |
| 12 | Impact can be measured | Defined pilot metrics | “We will evaluate…” not “we already improved…” |

---

## 4. Existing-solution landscape for the comparison slide

Use categories instead of a long competitor list. A panel will care more about the gap and your scope than about a superficial market survey.

### Category 1 — Learning management systems

**Examples:** Moodle, Google Classroom, Canvas and institution-specific portals.

**Strengths:**

- Course and assignment organization.
- Submission and grade collection.
- Teacher / learner account workflows.
- Institution familiarity.

**Potential gap for this problem:**

- A gradebook does not automatically explain the prerequisite concept behind a response.
- Data may remain in reports rather than a next-best-action loop.
- Teacher has to interpret and prioritize manually.

### Category 2 — Practice and tutoring platforms

**Examples:** Khan Academy, domain-specific practice apps and coaching platforms.

**Strengths:**

- Structured content and large item banks.
- Immediate hints or feedback.
- Practice routines and learner engagement.

**Potential gap for this problem:**

- Institutions may not get a unified, teacher-controlled intervention queue.
- A learner may see recommendations without a clear explanation of the evidence behind them.
- Content ecosystems and curricula differ across schools.

### Category 3 — Generative AI assistants

**Examples:** General chat assistants, AI tutors and educational copilots.

**Strengths:**

- Natural-language explanations.
- Multiple explanation styles.
- Conversational practice.
- Low friction for asking questions.

**Potential gap for this problem:**

- A conversation alone is not a reliable mastery estimate.
- Ungrounded answers can be incorrect or too advanced.
- The assistant can over-help, causing answer copying instead of learning.
- Teachers may not know which interactions indicate a wider gap.

### Category 4 — Assessment and quiz generators

**Strengths:**

- Quick item creation.
- Automated grading for objective questions.
- Reports by test or topic.

**Potential gap for this problem:**

- A generated quiz may not be tied to a prerequisite graph or a verified misconception.
- “More questions” does not necessarily mean “better next question.”
- Quality control and source traceability are essential.

### Your positioning

> AdaptEd is the connective intelligence layer: it links assessment evidence, subject summaries, concept mastery, grounded support, personalised practice and teacher intervention.

---

## 5. Research questions for your own validation

These questions can become a mini-pilot or appendix. They also make the plan look like a real educational product rather than a demo-only app.

### Learner questions

- Can learners identify their weak concept after seeing the map?
- Do they understand why a question was selected?
- Does hint-first support increase independent attempts?
- Is the language understandable at the selected grade level?
- Does the targeted re-check measure transfer, not recall of an identical item?

### Teacher questions

- Does the dashboard reduce time spent identifying who needs help?
- Are the recommended interventions actionable in a real class period?
- Does the teacher trust the evidence and confidence indicator?
- Which controls are necessary before assigning a learner a new path?
- What kinds of false positives or false negatives are unacceptable?

### Technical questions

- Does retrieval return the correct approved concept chunk?
- How often does the answer schema fail validation?
- Does the adaptive policy produce meaningfully different paths?
- Is the mastery estimate stable when one answer is noisy?
- Can the system function with low bandwidth or a temporary LLM outage?

### Ethical and access questions

- Are explanations accessible to learners with reading or visual needs?
- What data is truly necessary?
- Can a learner see and challenge an incorrect gap classification?
- Are any signals unfairly influenced by device speed, language or connectivity?
- Can a teacher override the model without hidden consequences?

---

## 6. Metrics and experimental design

### Minimum viable pilot

Use a small, transparent pilot. For example:

- 10–20 volunteer learners or synthetic seeded profiles for a prototype demonstration.
- 5–10 concepts in algebra.
- 30–50 teacher-reviewed items.
- A baseline diagnostic, targeted practice and transfer re-check.
- 1–3 teachers or mentors reviewing recommendations.

If you do not have real learners, say **“prototype simulation using seeded learner profiles”**. Do not present synthetic results as classroom outcomes.

### Core measures

#### 1. Concept mastery gain

```text
post-recheck mastery − baseline mastery
```

Report per concept, not only one class average.

#### 2. Transfer accuracy

Give a new question with the same underlying concept but different numbers, wording or representation.

#### 3. Recommendation precision

Ask a teacher to label whether the recommended next action was appropriate. Compare the recommendation to teacher judgment.

#### 4. Explanation rubric

Score each explanation from 0–2 on:

- Correctness.
- Grounding in approved content.
- Age-appropriate language.
- Hint-first / non-spoiler behaviour.
- Actionable next step.

#### 5. Teacher efficiency

Compare:

```text
manual time to identify an intervention group
versus
time using the dashboard
```

This is a prototype usability measure, not a universal productivity claim.

#### 6. Equity and access

Break down completion and learning gain by language, device type and connectivity condition when ethically and legally appropriate. Do not collect sensitive attributes merely to make a chart.

### Evaluation table for the appendix

| Hypothesis | Test | Success signal | Limitation |
|---|---|---|---|
| Adaptive items are more relevant than fixed order | Compare fixed vs policy-selected sequence in a simulation | Higher transfer accuracy or fewer unproductive attempts | Synthetic profiles are not a classroom trial |
| Grounded explanations are more trustworthy | Teacher rubric on generated responses | Higher correctness / grounding score | Small reviewer sample |
| Intervention queue is useful | Teacher ranks top actions | Agreement with teacher priority | Teacher expertise varies |
| Learners understand the path | Short usability interview | Learners can explain why next item was chosen | Self-report bias |

---

## 7. Citation style for the visible PPT

Put small numbered references in the lower-right corner of slides 3, 4 and 11:

```text
[1] UNESCO, 2023   [2] UNESCO GEM Report, 2023   [3] Piech et al., 2015
```

Use a final appendix slide or speaker notes for full URLs. If the hackathon requires inline citations, use short footnotes and readable text, not long links.

### Suggested appendix references

1. UNESCO. *Guidance for Generative AI in Education and Research.* 2023. <https://unesdoc.unesco.org/ark:/48223/pf0000386693>
2. UNESCO Global Education Monitoring Report. *Technology in education: A tool on whose terms?* 2023. <https://gem-report-2023.unesco.org/>
3. Piech, C. et al. *Deep Knowledge Tracing.* arXiv:1506.05908, 2015. <https://arxiv.org/abs/1506.05908>
4. Khan Academy. *Khanmigo / Khan Labs.* Verify current product page before submission. <https://www.khanmigo.ai/>
5. Duolingo Team. “Introducing Duolingo Max, a learning experience powered by GPT-4.” 14 March 2023. <https://blog.duolingo.com/duolingo-max/>
6. Moodle. Official platform and documentation pages. Verify current feature descriptions before submission. <https://moodle.org/>

---

## 8. Claims to avoid or rewrite

| Risky claim | Better replacement |
|---|---|
| “Our AI understands every learner.” | “Our prototype estimates concept mastery from selected evidence and shows confidence.” |
| “We eliminate teachers’ workload.” | “We reduce manual diagnosis and give teachers a prioritised intervention view.” |
| “Our model guarantees correct answers.” | “Grounding, structured validation and human review are designed to reduce unsupported answers.” |
| “Personalised learning increases scores by 40%.” | “We will measure concept mastery gain and transfer accuracy in a pilot.” |
| “We cover all subjects.” | “We start with Class 9 algebra and design for extensibility.” |
| “We use advanced deep learning.” | “We use a transparent hybrid mastery policy in the MVP and can calibrate it with data.” |
| “Students are weak in algebra.” | “The learner shows a gap in a specific prerequisite concept.” |

---

## 9. Final source-verification checklist

Before sending the PPT, the team should:

- [ ] Open every URL and confirm it still resolves.
- [ ] Confirm the publication date and exact title.
- [ ] Verify current features of named products.
- [ ] Replace every placeholder statistic with a cited, checked number—or remove it.
- [ ] Add access date if your event expects it.
- [ ] Keep a copy of all sources in a private team research folder or appendix.
- [ ] Mark prototype simulation results as simulation.
- [ ] Never expose learner names, personal data, API keys or private classroom records in screenshots.
