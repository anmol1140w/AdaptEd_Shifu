# PS-22 Hackathon Preparation Pack

This workspace contains the round-one presentation plan for:

> **PS-22 — AI-Powered Adaptive Learning & Skill Gap Identification Platform**

## Start here

1. **[PS22_Hackathon_PPT_Blueprint.md](docs/pitch/PS22_Hackathon_PPT_Blueprint.md)**
   The complete 13-slide deck plan, exact slide copy, speaker guidance, design system, judge questions, MVP scope and selection checklist.

2. **[PS22_Research_and_Citations.md](docs/research/PS22_Research_and_Citations.md)**
   Research thesis, existing-solution comparison, source notes, safe wording, citations, pilot metrics and claim-verification checklist.

3. **[PS22_Diagrams_and_Product_Assets.md](docs/architecture/PS22_Diagrams_and_Product_Assets.md)**
   Mermaid diagrams, concept graph, technical architecture, database entities, adaptive pseudocode, RAG contract and mock UI copy.

4. **[PS22_Pitch_Script_and_Rehearsal.md](docs/pitch/PS22_Pitch_Script_and_Rehearsal.md)**
   Five-minute and seven-minute scripts, 90-second demo runbook, team roles, scoring rubric and rehearsal plan.

## Recommended product direction

- Project name: **AdaptEd**
- Tagline: **From marks to mastery**
- Pilot: **Class 9 Mathematics — Algebra and Linear Equations**
- Main differentiator: **an explainable closed loop from evidence → concept mastery → next best action → re-assessment**
- MVP users: **learner and teacher**

## Subject-wise and concept-wise learning analysis

AdaptEd will expose learning gaps at two connected levels:

- **Subject-wise view:** summarizes a learner's overall progress and estimated mastery for a subject, such as Mathematics.
- **Concept-wise view:** drills into the concepts and prerequisites that make up the subject, such as Variables, Distributive Property and Two-step Equations.

The subject view is an aggregation of concept-level evidence; it must not hide the concepts that produced the summary. A teacher should be able to select a subject and then see the underlying concept mastery, confidence, misconceptions, evidence and recommended actions.

The MVP demonstrates one subject—Class 9 Mathematics—but the data model and API should retain subject identifiers so additional subjects can be added without changing the learning loop.

## Minimum round-one deliverables

- A 13-slide deck, or the compressed 8-slide version if the event has a limit.
- One learner journey showing a real adaptive change.
- One teacher dashboard showing a concept-level intervention queue.
- A subject-level summary that drills down into concept-level mastery and gaps.
- One process flow and one architecture diagram.
- A source-backed context slide with no invented statistics.
- A working or seeded demo plus a recorded fallback.
- A clear MVP boundary and measurable pilot metrics.

## Important honesty rules

- Label synthetic learners and simulated outcomes as demo data.
- Do not claim a universal solution when the prototype covers one subject.
- Do not present “we use an LLM” as the innovation.
- Do not claim that RAG guarantees factual correctness; describe it as a risk-reduction and grounding design.
- Keep real student data, credentials and API keys out of this workspace.

## Engineering scaffold

The repository now includes a prose-first scaffold for the future implementation:

- `backend/` — backend, learning-domain and AI integration boundaries.
- `frontend/` — learner and teacher product surfaces.
- `contracts/` — shared integration contracts between frontend and backend.
- `content/` — concepts, questions, lessons and synthetic demo scenarios.
- `docs/` — product, architecture, research and pitch documentation.
- `infra/` — future local and deployment support.
- `scripts/` — future repeatable project utilities.
- `docs/team/` — team ownership, task division and integration responsibilities.

Only the repository structure and documentation are being established at this stage. No application source code has been added yet.
