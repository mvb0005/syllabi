# LMS Platform — Development Roadmap

## ✅ Phase 1 — Infrastructure
- Docker Compose dev environment (`lms-mothership`) with PostgreSQL, FastAPI, Vite containers
- `lms-network` bridge; MCP servers (postgres, memory, filesystem, github, docker)
- GitHub repo (`mvb0005/syllabi`), branch protection, self-hosted CI runner

## ✅ Phase 2 — Core Scaffold (merged 2026-03-02)
| PR | Branch | Contents |
|---|---|---|
| #2 | `feat/phase2-backend-core` | FastAPI app, SQLAlchemy 2.0 async, Pydantic v2, 5 routers, 3 services, 16 tests, pre-commit |
| #3 | `feat/phase2-alembic` | Alembic async env, 7-table initial migration applied to PostgreSQL |
| #4 | `feat/phase2-frontend` | Vite 7 + React 19 + TypeScript + Tailwind v4 + Shadcn UI |

**Known stubs on `main` (deferred to Phase 3):**
- `get_current_user` raises `NotImplementedError` — no real auth yet
- `instructor_id` sourced from request body (`# TODO(phase3)`)
- `client.ts` uses handwritten helpers pending `openapi-typescript` codegen

---

## 🔜 Phase 3 — Authentication & Access Control

### 3A — JWT Authentication  `feat/phase3-auth`
- [ ] `POST /auth/login` — verify bcrypt password, issue JWT in `httpOnly` cookie
- [ ] `POST /auth/logout` — clear cookie
- [ ] `GET /auth/me` — return `UserPublic` for the bearer
- [ ] Implement `get_current_user` dependency (decode JWT → load User from DB)
- [ ] Wire `instructor_id` on `POST /courses/` to `current_user.id`; remove from `CourseCreate`
- [ ] Role guards: `instructor_required`, `student_required` dependency helpers
- [ ] Tests: login/logout flow, protected endpoint rejection (401/403), cookie handling

### 3B — Enrollment & Scoped Access  `feat/phase3-enrollment`
- [ ] `enrollments` table (student ↔ course many-to-many) + Alembic migration
- [ ] `POST /courses/{id}/enroll` — student self-enroll (or instructor adds)
- [ ] Scope `POST /submissions/` to enrolled students only
- [ ] Scope `GET /submissions/{id}/grade` to submitter or course instructor

### 3C — Grading Pipeline  `feat/phase3-grading`
- [ ] Deterministic grader: run student code against `TestCase.code` in isolated subprocess; set `Submission.status`
- [ ] LLM rubric grader: Groq `llama3-8b-8192` for cheap parsing; GPT-4o for semantic evaluation
  - Wrap student input in `<student_submission>` XML tags
  - Structured Pydantic output: `private_reasoning` (server-only) + `public_feedback`
  - Decompose rubric into boolean criteria array; `score = passed / total`
- [ ] `POST /submissions/{id}/grade` — trigger grading pipeline
- [ ] Rate limiting: max 3 rescore attempts per hour per student per assignment
- [ ] Never expose `private_reasoning` to clients (enforced by `GradeRecordPublic` schema)

### 3D — Frontend Auth Shell  `feat/phase3-frontend-auth`
- [ ] Login page → `POST /api/auth/login`
- [ ] `useCurrentUser()` hook → `GET /api/auth/me`
- [ ] Route guard: redirect to `/login` if unauthenticated
- [ ] Replace `client.ts` handwritten helpers with `openapi-typescript` codegen from FastAPI OpenAPI spec

---

## 🔮 Phase 4 — AI Course Generation (future)
- Instructor defines curriculum in YAML/markdown
- LLM generates full course content, assignment descriptions, test cases
- DevContainers per student (Git-based, Docker-in-Docker)
- CI pipeline per student submission

---

## 🔮 Phase 5 — Interactive Visuals Powered by Student Code (design, 2026-07-05)

**Goal:** a lesson embeds a live visual (e.g. Phase V beam-pattern explorer
with steering-angle slider) whose curves are computed by the *student's own*
submitted implementation, not a canned animation.

**Architecture decision: compile student C++ → WebAssembly, run in-browser.**
- Each exercise ships a fixed `extern "C"` harness header defining a narrow
  export ABI (e.g. `float array_gain(int n, float theta_steer, float theta)`)
  wrapping the student's TODO functions; Eigen is header-only and works
  under Emscripten.
- Interactivity is client-side at 60 fps (sliders call WASM exports per
  frame); zero server compute after the one-time compile; the browser's WASM
  sandbox means student code never touches the DOM or network.
- Rejected: server-side execution per interaction (round-trip latency, per-
  interaction sandbox burden); rewriting exercises in JS/Pyodide (curriculum
  is deliberately C++).

**Pipeline:**
1. `POST /submissions/` (existing) → compile service: Emscripten in a locked
   container (`--network=none`, 512 MB, 1 CPU, 30 s, read-only rootfs, tmpfs
   build dir); surface compiler stderr to the student on failure.
2. Store `.wasm` artifact keyed by submission; serve like excerpt PDFs
   (immutable cache headers).
3. Frontend `InteractiveVisual` component + per-exercise **visual manifest**
   (JSON on the assignment: exports to call, slider params + ranges, plot
   type). Phase V manifest: polar/cartesian array factor, sliders θ_steer
   and N.
4. Later: unify grading onto the same artifact — run the wasm under
   `wasmtime` against the test harness server-side, so the visual and the
   grade come from one compile (kills toolchain drift between grader and
   visual).

**Incremental delivery:**
- **v0** ✅ (2026-07-05) — visual component + fenced-block registry
  (`sampling-explorer`, `iq-mixer`, `inner-product-probe` in Phase I),
  reference implementations in TS.
- **v0.5** ✅ (2026-07-06) — **in-browser code milestones**: `compiler/`
  service (emsdk image + stdlib HTTP wrapper, Eigen baked in) compiles the
  student's whole exercise to a single-file WASM ES6 module;
  `POST /execute/cpp` proxies to it; `CodeMilestone` (CodeMirror editor,
  seeded from the new `assignments.starter_code` column) runs the module in
  a Web Worker with a 15 s watchdog and greps for the stub's own
  "all tests passed" line. Live on Phase I (dft/fir) and Phase V
  (steering/beamform, via Eigen).
- **v1** ✅ (2026-07-06) — **scopes drawn by student code**: `CodeMilestone`
  appends a per-exercise `extern "C"` harness (EMSCRIPTEN_KEEPALIVE exports,
  results read from HEAPF32) to the source on the same compile that runs the
  tests, then re-instantiates the artifact with `noInitialRun` to power a
  scope panel — Phase I spectrum via the student's `dft()`, Phase V beam
  pattern via `steering_vector()`/`beamform()`
  (`frontend/src/components/MilestoneScopes.tsx`).
- **v2** — grading unified on the WASM artifact via wasmtime; lesson-body
  visuals (sampling explorer et al.) switch from TS reference to the
  student's latest compiled module.

**Open questions:** compile queue depth (start serial); artifact retention
policy; whether the manifest lives on Assignment or a new table; double vs
float ABI (stubs use float — keep float).
