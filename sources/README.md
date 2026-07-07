# Sources

Third-party reference works (textbook PDFs, lecture notes, plain-text
documents) that course modules can embed as cited excerpts.

- Files anywhere under this directory can be registered via
  `POST /sources/` with a path relative to this directory.
- Excerpts embed an exact, 1-indexed inclusive page range (line range for
  `text` sources) into a module, always rendered with a full citation and a
  numbered entry in the course's References section.
- PDF excerpts render as page images (`GET /sources/{id}/pages/{n}`), so
  figures, diagrams, and typeset equations appear exactly as printed; the
  extracted text is kept as a searchable fallback.
- Use the `source-mining` skill (`.claude/skills/source-mining/`) and
  `python -m backend.scripts.mine_source` to locate citable content via a
  text's table of contents, index, and full-text search.

Only add material you have the right to redistribute to your students.
