# AI-Driven Course Platform

A Next.js LMS platform optimized for speed and low cost by maximizing deterministic (code-based) grading and strictly routing AI tasks. Complex generative tasks use flagship models, while high-volume, repetitive subjective grading and rescores are routed to ultra-fast, cheap models (e.g., Llama 3 8B via Groq or local vLLM).

### Development Steps
1. Scaffold `Next.js` and a database schema for curriculums, student submissions, and rescore workflows.
2. Build a grading pipeline prioritizing deterministic code execution and regex-based parsing before falling back to AI evaluation.
3. Implement an LLM routing layer utilizing Vercel AI SDK to direct complex tasks to flagship models and simple subjective rubrics to fast/local models (e.g., Llama 3 8B, Qwen 2.5 7B).
4. Enforce strict JSON output schemas (via Zod or `generateObject`) for fast LLMs to map subjective rubrics into calculated partial-credit percentages.
5. Create a Web UI for students to view failed criteria, read sanitized hints, and request rescores (protected by rate limits).
6. Provide an instructor dashboard to author rubrics, review disputed AI scores, and perform manual overrides.

### Project Configuration & AI Environment Setup
Create an optimized developer environment utilizing Model Context Protocol (MCP) servers and centralized AI instructions. We are using GitHub Copilot with Gemini 3.1 Pro (Preview). This empowers the AI agent to understand our architectural decisions, query our test database autonomously, and avoid hallucinating framework-specific patterns.

#### Decoupled Architecture: React + Strict Python (FastAPI)
For long-term AI-assisted maintainability, specifically for complex LMS orchestration (like container provisioning and grading pipelines), we are utilizing a **decoupled architecture (Vite/React frontend + FastAPI Python backend)**. Explicit API contracts (OpenAPI) and native AI/data ecosystem integration (Python) significantly lower the AI's cognitive load.

**Strict Code Quality & Testing (Python):**
Because Python natively lacks compile-time safety, we will leverage the AI's patience to parse and fix pedantic errors by enforcing maximum strictness:
*   **Typing:** Use strictly typed Python (`mypy --strict`). Avoid `Any` types.
*   **Linting & Formatting:** Use `Ruff` with aggressive rules enabled (e.g., catching unused imports, complexity thresholds, docstring requirements).
*   **Testing Requirement:** **Always create tests.** Every feature, endpoint, or grading function must have accompanying `pytest` unit/integration tests out-of-the-box. The AI should write the test file immediately alongside every implementation to ensure high-quality, regression-free code.

**PR-First AI Development Workflow & Self-Hosted CI:**
We are adopting a "PR-First" proactive approach. Pull Requests are created *before* code is written. The PR serves as an isolated, high-context workspace for the AI agent, providing it with a target branch and specific requirements.
1.  **Contextual PR Templates:** When a feature starts, an empty PR is opened containing instructions, context links, and mandatory MCP servers. The AI agent uses this PR as its blueprint.
2.  **Proactive Local Testing:** Developers run the test/linting pipeline continuously on their local machines. 
3.  **Self-Hosted Verification:** Instead of using GitHub cloud minutes, we use **GitHub Self-Hosted Runners** running on our local hardware. When a commit is pushed to the PR branch, the GitHub Action simply pings the local runner to verify the test suite passes for that specific commit hash.
4.  **Semantic AI Reviewer:** We will integrate an AI PR Agent triggered by a GitHub Action. The AI reads the diffs locally, leaves inline contextual comments, and flags logic or security bugs in the PR.
5.  **Branch Protection:** `main` is locked. A PR cannot be merged until the self-hosted CI confirms local tests passed **and** the AI reviewer approves the architecture.

#### Setup Steps
1. Create a `.github/copilot-instructions.md` file detailing our Tech Stack: React frontend and a strictly-typed FastAPI Python backend. Include prompt-injection defense strategies (XML delimiters, instruction capping), and mandate Pytest creation for every new file. 
2. Create a `.github/PULL_REQUEST_TEMPLATE.md` to prompt for necessary AI context (links, MCP servers, exact feature description) before work begins.
3. Define the architectural rules in the markdown file: enforcing explicit API contracts (OpenAPI via FastAPI), `mypy --strict`, aggressive `Ruff` linting, and 100% test-driven generation.
4. Scaffold the GitHub Actions workflows (`ci.yml` and `ai-reviewer.yml`) using `runs-on: self-hosted` to enforce the strict code review pipeline with zero cloud costs.
5. Install the `@modelcontextprotocol/server-postgres` MCP server to allow the AI to autonomously query and validate the LMS database schema during development.
4. Install the `@modelcontextprotocol/server-memory` MCP server to maintain a persistent knowledge graph of our grading rubrics and design decisions.
5. Setup the `Tavily MCP` (Web Search) or `puppeteer-mcp` so the AI can look up the latest ecosystem documentation to prevent syntax hallucinations.

#### Architectural Principles & Prompts
* **Zero Client-Side LLM Access:** The browser must never communicate directly with the LLM. Server-Side Assembled Context is strictly enforced.
* **Prompt Defenses:** Isolate user submissions using XML limits (e.g., `<student_submission>`) and utilize strong system instructions capped *after* the untrusted text.
* **Git-based DevContainers:** Provision Git repositories bundled with DevContainers and opaque test suites. Integrates Git provider APIs to dynamically fork course repositories for individual students upon enrollment.
