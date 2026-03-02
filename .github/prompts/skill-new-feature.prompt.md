---
mode: agent
tools: [lms-memory, lms-postgres, lms-filesystem, lms-github]
description: Implement a new LMS platform feature end-to-end (backend + frontend + tests)
---

You are implementing a new feature for the AI LMS platform. Follow `.github/copilot-instructions.md` exactly.

## Task
Implement the feature described in this PR from backend to frontend.

## Steps to Follow

1. **Read this PR's description** for the full feature spec, context links, and required MCP servers.
2. **Query `lms-memory`** for any related architectural patterns or prior decisions.
3. **Inspect `lms-postgres` schema** to understand what tables exist before creating new ones.
4. **Backend first:**
   - Create the SQLAlchemy model in `backend/models/`
   - Create the Pydantic schemas in `backend/schemas/`
   - Create the Alembic migration
   - Create the FastAPI router in `backend/routers/`
   - Create the service layer in `backend/services/`
5. **Write backend tests** in `backend/tests/` mirroring the module structure. Cover happy path, edge cases, and error states.
6. **Run `ruff check`, `ruff format`, `mypy --strict`, and `pytest`** — fix all issues.
7. **Frontend second:**
   - Regenerate the typed API client from the FastAPI OpenAPI spec
   - Create the React component(s) in `frontend/src/components/`
   - Wire to the API client
   - Use Tailwind + Shadcn UI exclusively
8. **Commit to the PR branch** with a clear message following conventional commits format: `feat: <description>`.
9. **Store key decisions in `lms-memory`** before finishing.

## Feature Description
${input:feature_description:Describe the feature to implement}
