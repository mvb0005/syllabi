---
mode: agent
tools: [lms-memory, lms-filesystem]
description: Author a new subjective rubric for an LMS assignment with LLM-evaluated boolean criteria
---

You are authoring a subjective grading rubric for the AI LMS platform. The rubric will be evaluated by an LLM-as-a-judge. Follow `.github/copilot-instructions.md` exactly.

## Task
Design the rubric for the assignment described below.

## Rules for Rubric Design

1. **Decompose requirements into discrete boolean criteria.** Do NOT ask the LLM to assign a score — always ask for pass/fail per criterion and compute the score programmatically.
2. **Each criterion must have:**
   - A `name`: short, descriptive. Tells the student WHAT is tested, not HOW (e.g., `"contains_five_sentences"` not `"write_exactly_5_sentences: The student must write exactly 5 sentences"`).
   - A `private_check`: the precise instruction for the LLM judge (never shown to student).
   - A `public_hint`: a short AI-generated hint the student sees on failure (no answer revealed).
   - A `model`: `"fast"` (Groq Llama 3 8B) for counting/parsing, `"flagship"` for semantic reasoning.
3. **Prefer deterministic checks.** If a criterion can be solved with `len(sentences)` or regex, mark it `"deterministic": true` and implement it in Python, not via LLM.
4. **Include at least one partial-credit path.** The score formula is always `passed / total`.

## Output Format
Produce a Python `RubricDefinition` Pydantic model instance and the matching `pytest` test cases for the grading logic, saved to:
- `backend/grading/rubrics/{assignment_slug}.py`
- `backend/tests/grading/test_{assignment_slug}.py`

## Assignment Details
${input:assignment_description:Describe the assignment and what a good answer looks like}
