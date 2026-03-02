## 🤖 AI Agent PR Context
*This PR is opened BEFORE development begins. The AI will use this document as its blueprint and working context.*

### 🎯 Feature Explanation
<!-- Provide a clear, concise description of the feature or bug fix to be implemented on this branch. -->
- 

### 🔗 Context Links
<!-- Link to relevant external documentation, Figma mocks, OpenAPI specs, or existing files in the repo necessary for the AI to understand the task. -->
- [Target File 1](...)
- [Doc Link](...)

### 🔌 Required MCP Servers
<!-- Check all Model Context Protocol servers the AI should ensure are running to complete this work accurately. -->
- [ ] `@modelcontextprotocol/server-postgres` (For database / schema queries)
- [ ] `@modelcontextprotocol/server-memory` (For adhering to project rules)
- [ ] `puppeteer-mcp` / `browser-use` (For UI testing/scraping)
- [ ] Other: 

### ✅ Implementation Checklist (For the AI)
- [ ] Implement the feature exactly as described above.
- [ ] Ensure Python code strictly passes `mypy --strict`.
- [ ] Ensure Python code passes aggressive `ruff` linting and formatting.
- [ ] Write accompanying `pytest` unit/integration tests for any new logic.
- [ ] Run the local self-hosted test suite proactively to verify the state before pushing.

---

### 🚦 CI Status (Self-Hosted)
This repository relies on proactive, self-hosted CI. Once the AI commits work to this branch, the GitHub Action will ping the local runner to verify the test suite passes against the latest commit hash.