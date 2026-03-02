---
mode: agent
tools: [lms-memory, lms-postgres, lms-filesystem]
description: Scaffold a new FastAPI grading endpoint with an opaque test suite and AI fallback
---

You are building a grading endpoint for the AI LMS platform. Follow the instructions in `.github/copilot-instructions.md` exactly.

## Task
Create a new grading endpoint for the assignment described below.

## Steps to Follow

1. **Check memory first.** Query `lms-memory` for any existing conventions for grading endpoints.
2. **Inspect the database.** Use `lms-postgres` to review the `assignments`, `submissions`, and `test_cases` tables before writing any schema code.
3. **Determine grading strategy:**
   - If the assignment is deterministic (code execution, regex, AST), implement it purely in Python with no LLM call.
   - If the assignment is subjective, decompose the rubric into a Pydantic boolean criteria model and route to the fast LLM (Groq `llama3-8b-8192`).
4. **Implement the endpoint** at `POST /api/v1/grades/{assignment_id}/submit`.
5. **Protect against prompt injection:** Wrap student input in `<student_submission>` tags and append instructions AFTER.
6. **Separate grading output** into `private_reasoning` (server-side only) and `public_feedback` (returned to student).
7. **Add rate limiting** — maximum 3 resubmissions per hour per student per assignment.
8. **Write tests** in `backend/tests/grading/test_{assignment_slug}.py` covering:
   - A correct submission (all criteria pass)
   - A partial submission (some criteria pass — verify percentage math)
   - A prompt injection attempt (all criteria must fail)
   - Rate limit exceeded (429 response)
9. **Run `ruff check`, `ruff format`, and `mypy --strict`** — fix all errors before finishing.
10. **Store the new rubric pattern in `lms-memory`** so future grading endpoints can reference it.

## Assignment Details
${input:assignment_description:Describe the assignment and its grading criteria}
