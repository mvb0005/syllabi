---
name: source-mining
description: Mine a third-party text (textbook PDF, notes) for citable content and embed page-range excerpts into LMS course modules with full citations. Use when asked to add a source, find supporting reading for a topic, embed textbook pages in a course, or build a module's references from a PDF's table of contents, index, or citations.
---

# Source Mining — find and embed cited textbook content

A **source** is a third-party reference work stored under `sources/` in the
repo. A **source excerpt** embeds an exact, 1-indexed inclusive page range of
a source into a course module, always rendered with a LaTeX-style citation
(`[n, pp. a–b]` in the text, numbered entry in the course's References
section). Excerpt text is extracted once at creation time and cached in the
database.

The workflow has four steps: **register → explore → verify → embed**.

## 0. Prerequisites

- The file must live under `sources/` (any subdirectory). Paths passed to the
  API and tools are always *relative to* `sources/` — absolute paths and
  `..` traversal are rejected.
- Supported kinds: `pdf` (page ranges) and `text` (the range is interpreted
  as line numbers).
- Backend running (`uvicorn backend.main:app`) and an instructor login for
  the write endpoints.

## 1. Register the source

```bash
curl -s -X POST http://localhost:8000/sources/ \
  -H 'Content-Type: application/json' -b cookies.txt \
  -d '{
    "bibkey": "proakis2008",
    "title": "Digital Communications",
    "authors": "J. G. Proakis and M. Salehi",
    "edition": "5th ed.",
    "publisher": "McGraw-Hill",
    "year": 2008,
    "kind": "pdf",
    "path": "proakis/digital-communications-5e.pdf"
  }'
```

Bibliographic fields drive the rendered citation
(`Authors, *Title*, edition. Publisher, year.`), so fill them the way a
bibliography entry should read. `bibkey` follows the LaTeX convention
(`firstauthorYEAR`).

## 2. Explore: find where the topic lives

Use the mining tool (paths relative to `sources/`):

```bash
# Page count + embedded metadata
python -m backend.scripts.mine_source book.pdf --info

# Table of contents from the PDF outline, with page numbers
python -m backend.scripts.mine_source book.pdf --toc

# Full-text search: which pages mention the topic?
python -m backend.scripts.mine_source book.pdf --search "beamforming"
```

Strategy, in order of reliability:

1. **Outline/ToC** (`--toc`): chapter and section titles with their start
   pages bound the candidate range. If no outline is embedded, find the
   printed contents pages: `--search "Contents"` near the front, then
   `--pages` to read them.
2. **Index**: textbooks put it on the last pages. Read it with `--pages`
   (e.g. the final 10 pages) and look up the topic — index entries give
   exact page numbers, often distinguishing definitions (bold) from
   mentions.
3. **Full-text search** (`--search`): confirms density — a genuine
   treatment of the topic shows a run of consecutive hits; scattered
   single hits are passing mentions. Search synonyms too (e.g.
   "array factor" as well as "beamforming").
4. **Citations**: if the course content already cites a work
   (e.g. "Van Trees, ch. 2"), start from that chapter via the ToC.

## 3. Verify before embedding

Never embed a range you haven't read. Extract it and check that it actually
supports the topic, starts and ends at sensible boundaries (section starts,
not mid-paragraph), and is self-contained:

```bash
python -m backend.scripts.mine_source book.pdf --pages 161-170
```

Trim the range to the tightest span that covers the topic — excerpts are
quoted readings, not chapter dumps. A good excerpt is 1–10 pages.

## 4. Embed the excerpt

```bash
curl -s -X POST http://localhost:8000/sources/<source_id>/excerpts \
  -H 'Content-Type: application/json' -b cookies.txt \
  -d '{
    "module_id": "<module_id>",
    "page_start": 161,
    "page_end": 170,
    "topic": "Optimum receivers for AWGN channels",
    "context_md": "Why this reading matters for the phase, in one or two sentences.",
    "order_index": 0
  }'
```

- `topic` is the short label shown in the reading block — name the concept,
  not the book.
- `context_md` (optional, markdown + TeX math) introduces the reading in the
  course's voice.
- The API re-extracts and caches the text; a 422 means the range exceeds the
  document, a 409 means that exact span is already embedded in the module.

Verify the result end-to-end: `GET /courses/{course_id}/excerpts` should
include the excerpt with its `source`, and the course page will render the
reading block plus a numbered References entry.

## Module IDs

Find the target module via the API:

```bash
curl -s http://localhost:8000/courses/ | jq '.[] | {id, title}'
curl -s http://localhost:8000/courses/<course_id>/modules | jq '.[] | {id, title}'
```
