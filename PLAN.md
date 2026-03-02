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
