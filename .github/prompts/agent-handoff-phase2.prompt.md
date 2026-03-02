# Agent Handoff — Phase 2: Backend & Frontend Scaffolding

## Your Mission

You are a senior full-stack engineer on the AI LMS platform. Infrastructure is fully operational. Your
job is to scaffold the backend and frontend from scratch, establish the database schema, and ensure
every quality gate passes before considering any phase complete.

**Work autonomously. Do not ask for permission between steps. Make decisions, implement them, validate
them, and move on.**

---

## Context Recovery (Do This First)

Before writing any code:

1. Read the `lms-mcp-memory` knowledge graph to recover any stored architectural decisions.
2. Read `/workspace/.github/copilot-instructions.md` for all coding rules (22 rules — know them cold).
3. Read `/workspace/pyproject.toml` to understand the exact ruff/mypy/pytest configuration in force.
4. Read `/workspace/.devcontainer/docker-compose.yml` to understand available services and the
   `lms-network` topology (postgres is at host `db`, port `5432`).
5. Read `/workspace/.github/PULL_REQUEST_TEMPLATE.md` — this is the contract format for every PR.

Store a summary of what you learn back into `lms-mcp-memory` under entity `"Phase2-Context"` so future
agents can resume from here.

---

## Phase 2A — Git Repository Initialization

1. Run `git init` inside `/workspace` if `.git` does not already exist.
2. Add a `.gitattributes` file with standard line-ending normalization:
   ```
   * text=auto eol=lf
   *.ps1 text eol=crlf
   ```
3. Run `git add -A && git commit -m "chore: initial infrastructure scaffolding"` to commit all
   existing files (the entire Phase 1 output).
4. If the remote `origin` is not yet set, note it in a `TODO.md` at workspace root and continue —
   do not block on it.

---

## Phase 2B — FastAPI Backend Scaffold

### Directory Structure to Create

```
/workspace/backend/
├── __init__.py
├── main.py                  # FastAPI app factory, lifespan, CORS
├── config.py                # Settings via pydantic-settings (reads from env)
├── database.py              # Async SQLAlchemy engine + session factory
├── exceptions.py            # Typed custom exception hierarchy
├── dependencies.py          # FastAPI Depends: get_db, get_current_user
├── models/
│   ├── __init__.py
│   ├── base.py              # DeclarativeBase, TimestampMixin
│   ├── user.py              # User model
│   ├── course.py            # Course, Module models
│   ├── assignment.py        # Assignment, TestCase models
│   └── submission.py        # Submission, GradeRecord models
├── schemas/
│   ├── __init__.py
│   ├── user.py
│   ├── course.py
│   ├── assignment.py
│   └── submission.py
├── routers/
│   ├── __init__.py
│   ├── health.py            # GET /health — always first, no auth
│   ├── users.py
│   ├── courses.py
│   ├── assignments.py
│   └── submissions.py
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   ├── course_service.py
│   └── submission_service.py
└── tests/
    ├── __init__.py
    ├── conftest.py           # pytest fixtures: async engine, test client, seed data
    ├── test_health.py
    ├── models/
    │   └── test_user.py
    ├── routers/
    │   ├── test_users.py
    │   └── test_courses.py
    └── services/
        └── test_user_service.py
```

### Core Data Models

Implement these SQLAlchemy 2.0 models with full `Mapped[T]` / `mapped_column()` type annotations.
All PKs are `uuid.uuid4` strings.

**User**
- `id: uuid` (PK)
- `email: str` (unique, indexed)
- `hashed_password: str`
- `full_name: str`
- `role: enum('student', 'instructor', 'admin')`
- `is_active: bool` (default True)
- `created_at`, `updated_at` timestamps

**Course**
- `id: uuid` (PK)
- `title: str`
- `description: str`
- `instructor_id: uuid` (FK → user)
- `is_published: bool` (default False)
- timestamps

**Module**
- `id: uuid` (PK)
- `course_id: uuid` (FK → course, cascade delete)
- `title: str`
- `order_index: int`
- `content_md: str` (lesson content in Markdown)
- timestamps

**Assignment**
- `id: uuid` (PK)
- `module_id: uuid` (FK → module, cascade delete)
- `title: str`
- `description_md: str`
- `grading_type: enum('deterministic', 'llm_rubric', 'hybrid')`
- `max_score: int` (default 100)
- `due_at: datetime | None`
- timestamps

**TestCase**
- `id: uuid` (PK)
- `assignment_id: uuid` (FK → assignment, cascade delete)
- `name: str` (visible to student)
- `code: str` (**OPAQUE** — never returned to student via API)
- `weight: float` (default 1.0)
- `is_hidden: bool` (default True)

**Submission**
- `id: uuid` (PK)
- `assignment_id: uuid` (FK → assignment)
- `student_id: uuid` (FK → user)
- `content: str` (student's submitted code / text)
- `status: enum('pending', 'grading', 'graded', 'error')`
- `submitted_at: datetime`
- timestamps

**GradeRecord**
- `id: uuid` (PK)
- `submission_id: uuid` (FK → submission, unique — one grade per submission)
- `raw_score: float`
- `max_score: float`
- `percentage: float` (computed: `raw_score / max_score * 100`)
- `public_feedback: str` (shown to student)
- `private_reasoning: str` (server-side only, **NEVER** in API response schemas)
- `graded_by: enum('deterministic', 'llm', 'instructor_override')`
- `graded_at: datetime`

### Implementation Rules

- All route handlers: `async def`
- All DB calls: via `AsyncSession`
- All request/response bodies: Pydantic `BaseModel` subclasses in `schemas/`
- `private_reasoning` MUST be excluded from all Pydantic response schemas — use a dedicated
  `GradeRecordPublic` schema that omits it
- `TestCase.code` MUST be excluded from all student-facing schemas — separate `TestCasePublic`
  (name, weight, is_hidden) from `TestCaseFull` (instructor only)
- `config.py` must load: `DATABASE_URL`, `SECRET_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY`,
  `ENVIRONMENT` (`development` | `production`), `CORS_ORIGINS`
- `main.py` must include CORS middleware permitting `http://localhost:5173` in development

### Alembic Setup

```bash
pip install alembic
cd /workspace
alembic init backend/alembic
```

- Set `sqlalchemy.url` in `alembic.ini` to read from `DATABASE_URL` env var
- Edit `env.py` to import `Base` from `backend.models.base` and use async engine
  (use the `run_sync` / `run_async_middleware` pattern for async Alembic)
- Generate first migration: `alembic revision --autogenerate -m "initial schema"`
- Apply migration: `alembic upgrade head`
- Verify via `lms-mcp-postgres`:
  `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';`

### Requirements File

Create `/workspace/backend/requirements.txt`:
```
fastapi>=0.115
uvicorn[standard]>=0.34
sqlalchemy[asyncio]>=2.0
alembic>=1.14
asyncpg>=0.30
pydantic>=2.10
pydantic-settings>=2.7
python-jose[cryptography]>=3.4
passlib[bcrypt]>=1.7
httpx>=0.28
pytest>=8.3
pytest-asyncio>=0.25
ruff>=0.9
mypy>=1.14
openai>=1.65
```

Install: `pip install -r /workspace/backend/requirements.txt`

### Quality Gate — Backend

Run and fix ALL issues before proceeding:

```bash
cd /workspace
ruff check backend/
ruff format --check backend/
mypy --strict backend/
pytest backend/tests/ -v
```

Zero errors. Zero warnings. All tests green.

---

## Phase 2C — Vite/React Frontend Scaffold

### Bootstrap

```bash
cd /workspace
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

### Tailwind CSS

```bash
npm install -D tailwindcss @tailwindcss/vite
```

Use the Tailwind v4 Vite plugin: add `@import "tailwindcss"` to `src/index.css` and register the
plugin in `vite.config.ts`.

### Shadcn UI

```bash
npx shadcn@latest init
```

Accept defaults: Default style, Slate base color, CSS variables: Yes.

Add starter components:
```bash
npx shadcn@latest add button card input label badge table tabs
```

### Directory Structure

```
/workspace/frontend/src/
├── api/
│   └── client.ts            # Axios instance, withCredentials: true
├── components/
│   ├── ui/                  # Shadcn components (auto-generated, do not edit)
│   └── layout/
│       ├── AppShell.tsx
│       └── PageHeader.tsx
├── pages/
│   ├── DashboardPage.tsx
│   ├── CoursesPage.tsx
│   └── LoginPage.tsx
├── hooks/
│   └── useAuth.ts           # Auth state via httpOnly cookie (no localStorage)
├── lib/
│   └── utils.ts             # shadcn cn() util
├── App.tsx                  # React Router routes
└── main.tsx
```

### API Client Rule

`src/api/client.ts` must use `axios` with `withCredentials: true`. Never use `localStorage` for tokens.

```typescript
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  withCredentials: true,
});
```

### Quality Gate — Frontend

```bash
cd /workspace/frontend
npx tsc --noEmit
npm run lint
npm run build
```

Zero TypeScript errors. Zero ESLint errors. Build succeeds.

---

## Phase 2D — Wiring & Smoke Test

1. Start the backend: `uvicorn backend.main:app --reload --port 8000`
2. Confirm `GET http://localhost:8000/health` → `{"status": "ok"}`
3. Start the frontend: `cd /workspace/frontend && npm run dev`
4. Confirm `http://localhost:5173` renders without console errors
5. `GET http://localhost:8000/openapi.json` → valid OpenAPI 3.x document with health, users,
   courses, assignments, and submissions paths
6. Query `lms-mcp-postgres` to confirm all 7 tables exist:
   `users`, `courses`, `modules`, `assignments`, `test_cases`, `submissions`, `grade_records`

---

## Phase 2E — Memory Persistence

After all quality gates pass, store into `lms-mcp-memory`:

- Entity `"Backend-Schema-v1"` — table names, PK types, non-obvious FK relationships
- Entity `"Frontend-Structure-v1"` — page routes, API client base URL strategy, cookie-based auth
- Entity `"QualityGates-Baseline"` — first clean ruff/mypy/pytest/tsc run outputs as evidence of
  a green baseline
- Relation: `"Phase2-Context" → implements → "Backend-Schema-v1"`
- Relation: `"Phase2-Context" → implements → "Frontend-Structure-v1"`

---

## Completion Criteria

You are done with Phase 2 when ALL of the following are true — verify each explicitly:

- [ ] `git log --oneline` shows at least one commit with all Phase 1 infrastructure files
- [ ] `/workspace/backend/` exists with all directories and files listed above
- [ ] `/workspace/frontend/` exists with Vite + Tailwind + Shadcn bootstrapped
- [ ] `ruff check backend/` → 0 errors
- [ ] `mypy --strict backend/` → 0 errors
- [ ] `pytest backend/tests/ -v` → all tests pass
- [ ] `npx tsc --noEmit` (in `/workspace/frontend`) → 0 errors
- [ ] `alembic upgrade head` ran successfully and all 7 tables exist in PostgreSQL
- [ ] `GET /health` returns 200
- [ ] `lms-mcp-memory` updated with Phase 2 entities

**Do not summarize or hand back to the user until every box above is checked.**

---

## If You Get Stuck

- **DB schema state**: query `lms-mcp-postgres` — `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';`
- **Container health**: use `lms-mcp-docker` to inspect logs for the `db` or `app` container
- **File reads**: use `lms-mcp-filesystem` to re-read any `/workspace` file
- **Alembic async**: use the `run_sync` pattern in `env.py` — `connection.run_sync(do_run_migrations)`
- **mypy + SQLAlchemy 2.0**: use `Mapped[type]` annotations with `mapped_column()` — fully
  strict-compatible

---

## Phase 3 Preview (Do NOT start yet)

After Phase 2 is fully green:
- JWT authentication: login endpoint → set httpOnly cookie → `/users/me`
- Student submission endpoint with background grading (`FastAPI BackgroundTasks`)
- Deterministic grader: subprocess sandbox, stdout comparison vs expected
- First LLM rubric grader with full prompt-injection defenses (XML delimiters, instruction capping)
- GitHub repository initialization and first real CI run on the self-hosted runner
