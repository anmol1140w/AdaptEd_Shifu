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
- Pilot: **Class 11–12 Physics, Chemistry and Mathematics**
- Main differentiator: **an explainable closed loop from evidence → concept mastery → next best action → re-assessment**
- MVP users: **learner and teacher**

## Subject-wise and concept-wise learning analysis

AdaptEd will expose learning gaps at two connected levels:

- **Subject-wise view:** summarizes a learner's overall progress and estimated mastery for a subject, such as Mathematics.
- **Concept-wise view:** drills into the concepts and prerequisites that make up the subject, such as Variables, Distributive Property and Two-step Equations.

The subject view is an aggregation of concept-level evidence; it must not hide the concepts that produced the summary. A teacher should be able to select a subject and then see the underlying concept mastery, confidence, misconceptions, evidence and recommended actions.

The current learning flow supports PCM for Classes 11 and 12. Subject and concept identifiers remain explicit through content, assessments, retrieval and analytics.

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

## Application status and local run

### Start the full app (Windows, macOS, or Linux)

The easiest way to run the complete app is with Docker Desktop (Windows/macOS) or Docker Engine plus the Docker Compose plugin (Linux). No host-installed Python, Node.js, or PostgreSQL is needed.

1. Install and start Docker Desktop / Docker Engine.
2. From the repository folder, run the matching command:

   **Windows PowerShell**
   ```powershell
   .\scripts\start.ps1
   ```

   **Windows Command Prompt**
   ```bat
   scripts\start.bat
   ```

   **macOS / Linux**
   ```sh
   sh scripts/start.sh
   ```

The first start creates an ignored root `.env` with private random database and session-signing secrets, builds the containers, and starts PostgreSQL, the API, and the web app. Open [http://localhost:5173](http://localhost:5173). The API health check is at [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health). The database volume survives app/container restarts and `docker compose down`; `docker compose down --volumes` permanently deletes local database data.

Email/password sign-in and the core app work without external AI credentials. To enable Google sign-in, set `ADAPTED_GOOGLE_CLIENT_ID` and `ADAPTED_GOOGLE_CLIENT_SECRET` in the root `.env`, set `VITE_GOOGLE_OAUTH_ENABLED=true`, confirm the Google OAuth redirect URI matches `ADAPTED_GOOGLE_REDIRECT_URI`, then rebuild with `docker compose up --build -d`. The OAuth client must also allow the app's browser origin. Ollama Cloud and Qdrant are optional: add their credentials to the root `.env` to enable tutor, generated quiz, and retrieval-backed features. Never commit `.env` or share its secret values.

To stop the app while keeping student accounts and learning records, run `docker compose down`. To start it again, run the same platform start command. To inspect startup problems, run `docker compose logs -f backend frontend db`.

By default the app binds to localhost ports 5173 and 8000. If a port is occupied, change `ADAPTED_WEB_PORT` or `ADAPTED_API_PORT` in `.env`; if changing the web origin (for example, to use the app from another device), also update `ADAPTED_FRONTEND_URL`, `ADAPTED_CORS_ORIGINS`, and the Google OAuth allowed origin. If changing the API port, update `ADAPTED_GOOGLE_REDIRECT_URI` and its authorized redirect URI in Google Cloud. A deployment exposed to the public internet needs HTTPS and production secrets/domains configured.

### Manual developer run (without Docker)

The repository contains a connected React and FastAPI application:

- `backend/src/backend/` — FastAPI routes, PostgreSQL persistence, sign-in, adaptive assessments, AI support and teacher review.
- `frontend/src/` — learner adaptive practice and cited tutor flows, JEE practice pages, and teacher question review and analytics.
- `content/concepts/` and `content/items/` — PCM concepts and authored question drafts. New bank items begin unapproved and require teacher review.
- `content/datasets/ncert/` — citation-preserving chunks and the Qdrant Cloud ingestion pipeline.

Run the API from `backend/` after configuring `backend/.env` from `.env.example` and providing a PostgreSQL database:

```bash
cd backend
uv sync
uv run backend
```

For a local PostgreSQL service, copy `backend/.env.example` to `backend/.env`, then run `bash scripts/setup-local-postgres.sh` from the repository root. It creates the app's `adapted_user` role and `adapted` database using the password in the ignored `backend/.env`; `sudo` will ask for your local administrator password. PostgreSQL must be running on `127.0.0.1:5432`.

The API creates its schema and seeds the PCM concept/question catalog on first database access. Register a teacher with the configured invite code, create a classroom, then have student accounts join it. Teachers approve items before student assessments can use them.

Run the web app from `frontend/`:

```bash
npm ci
npm run dev
```

Set `VITE_API_BASE_URL` in `frontend/.env` if the API is not at `http://localhost:8000/api/v1`. Google sign-in requires `ADAPTED_GOOGLE_CLIENT_ID`, `ADAPTED_GOOGLE_CLIENT_SECRET`, and matching redirect settings. Ollama Cloud tutor and quiz generation require `OLLAMA_API_KEY` and a configured model. NCERT grounding also requires Qdrant Cloud credentials and the `ncert_pcm_active` alias to point at an ingested collection. AI routes return a clear service error when those integrations or mapped source chunks are unavailable; they do not silently switch to another model.

For Google sign-in, set the existing Web OAuth client ID and secret in `backend/.env`, register `http://localhost:8000/api/v1/auth/google/callback` as an authorized redirect URI, and set `VITE_GOOGLE_OAUTH_ENABLED=true` in `frontend/.env`. Restart both servers after changing environment files. Keep the client secret only in the ignored backend environment file.

The app code is wired end to end, but a successful live demonstration still depends on a reachable database, teacher-approved questions, and a populated Qdrant collection for grounded AI support.
