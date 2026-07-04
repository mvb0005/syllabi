# Sources

Third-party reference works (textbook PDFs, lecture notes, plain-text
documents) that course modules can embed as cited excerpts.

**Files placed under this directory are not committed to git** (see
`.gitignore` — only this README is tracked). Copyrighted textbooks have no
business in version control. In the devcontainer the repo root is
bind-mounted into the container, so a PDF dropped locally under `sources/`
is immediately visible to the backend without ever touching git history.
Each environment (your machine, a teammate's, a deployed instance)
provisions its own copy of `sources/` independently.

- Files anywhere under this directory can be registered via
  `POST /sources/` with a path relative to this directory.
- Excerpts embed an exact, 1-indexed inclusive page range (line range for
  `text` sources) into a module, always rendered with a full citation and a
  numbered entry in the course's References section.
- Use the `source-mining` skill (`.claude/skills/source-mining/`) and
  `python -m backend.scripts.mine_source` to locate citable content via a
  text's table of contents, index, and full-text search.

Only add material you have the right to redistribute to your students.
