"""Tests for the /sources router and excerpt extraction."""

import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient
from pypdf import PdfWriter

from backend.config import settings

TEXT_LINES = [f"Line {n}: the quick brown antenna steers beam {n}." for n in range(1, 21)]


@pytest.fixture(autouse=True)
def sources_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point SOURCES_DIR at a temp directory holding one text and one PDF source."""
    (tmp_path / "notes.txt").write_text("\n".join(TEXT_LINES), encoding="utf-8")

    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=612, height=792)
    with (tmp_path / "blank.pdf").open("wb") as fh:
        writer.write(fh)

    monkeypatch.setattr(settings, "SOURCES_DIR", str(tmp_path))
    return tmp_path


async def _login_instructor(client: AsyncClient) -> None:
    """Create and log in an instructor."""
    email = f"instructor-{uuid.uuid4()}@sources-test.com"
    resp = await client.post(
        "/users/",
        json={
            "email": email,
            "full_name": "Instructor",
            "role": "instructor",
            "password": "pass",
        },
    )
    assert resp.status_code == 201
    login = await client.post("/auth/login", json={"email": email, "password": "pass"})
    assert login.status_code == 200


async def _make_module(client: AsyncClient) -> tuple[str, str]:
    """Create a course and module; return (course_id, module_id)."""
    course_resp = await client.post("/courses/", json={"title": "Cited Course"})
    assert course_resp.status_code == 201
    course_id = str(course_resp.json()["id"])
    module_resp = await client.post(f"/courses/{course_id}/modules", json={"title": "Module"})
    assert module_resp.status_code == 201
    return course_id, str(module_resp.json()["id"])


def _text_source_payload() -> dict[str, str | int]:
    """Return a valid SourceCreate payload for the text fixture."""
    return {
        "bibkey": f"notes{uuid.uuid4().hex[:8]}",
        "title": "Antenna Notes",
        "authors": "A. Author",
        "edition": "2nd ed.",
        "publisher": "Test Press",
        "year": 2020,
        "kind": "text",
        "path": "notes.txt",
    }


@pytest.mark.asyncio
async def test_create_source_and_list(client: AsyncClient) -> None:
    """POST /sources/ registers a source; GET /sources/ returns it."""
    await _login_instructor(client)
    payload = _text_source_payload()
    resp = await client.post("/sources/", json=payload)
    assert resp.status_code == 201
    assert resp.json()["bibkey"] == payload["bibkey"]

    listing = await client.get("/sources/")
    assert listing.status_code == 200
    assert payload["bibkey"] in [s["bibkey"] for s in listing.json()]


@pytest.mark.asyncio
async def test_create_source_missing_file(client: AsyncClient) -> None:
    """POST /sources/ rejects paths that do not exist."""
    await _login_instructor(client)
    payload = _text_source_payload() | {"path": "does-not-exist.pdf"}
    resp = await client.post("/sources/", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_source_path_traversal_rejected(client: AsyncClient) -> None:
    """POST /sources/ rejects traversal outside the sources directory."""
    await _login_instructor(client)
    payload = _text_source_payload() | {"path": "../pyproject.toml"}
    resp = await client.post("/sources/", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_source_kind_mismatch_text_as_pdf(client: AsyncClient) -> None:
    """POST /sources/ rejects a plain-text file registered as kind=pdf."""
    await _login_instructor(client)
    payload = _text_source_payload() | {"kind": "pdf", "path": "notes.txt"}
    resp = await client.post("/sources/", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_source_kind_mismatch_pdf_as_text(client: AsyncClient) -> None:
    """POST /sources/ rejects a PDF file registered as kind=text."""
    await _login_instructor(client)
    payload = _text_source_payload() | {
        "bibkey": f"pdf{uuid.uuid4().hex[:8]}",
        "kind": "text",
        "path": "blank.pdf",
    }
    resp = await client.post("/sources/", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_excerpt_extracts_text_range(client: AsyncClient) -> None:
    """POST /sources/{id}/excerpts caches the extracted line range."""
    await _login_instructor(client)
    _course_id, module_id = await _make_module(client)
    source_resp = await client.post("/sources/", json=_text_source_payload())
    source_id = source_resp.json()["id"]

    resp = await client.post(
        f"/sources/{source_id}/excerpts",
        json={
            "module_id": module_id,
            "page_start": 3,
            "page_end": 5,
            "topic": "Beam steering",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["content_text"] == "\n".join(TEXT_LINES[2:5])
    assert body["source"]["title"] == "Antenna Notes"


@pytest.mark.asyncio
async def test_create_excerpt_range_beyond_document(client: AsyncClient) -> None:
    """POST /sources/{id}/excerpts rejects ranges past the end of the document."""
    await _login_instructor(client)
    _course_id, module_id = await _make_module(client)

    pdf_payload = _text_source_payload() | {
        "bibkey": f"pdf{uuid.uuid4().hex[:8]}",
        "kind": "pdf",
        "path": "blank.pdf",
    }
    source_resp = await client.post("/sources/", json=pdf_payload)
    source_id = source_resp.json()["id"]

    resp = await client.post(
        f"/sources/{source_id}/excerpts",
        json={
            "module_id": module_id,
            "page_start": 4,
            "page_end": 9,
            "topic": "Out of range",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_course_excerpts(client: AsyncClient) -> None:
    """GET /courses/{id}/excerpts returns excerpts with embedded sources."""
    await _login_instructor(client)
    course_id, module_id = await _make_module(client)
    source_resp = await client.post("/sources/", json=_text_source_payload())
    source_id = source_resp.json()["id"]

    create = await client.post(
        f"/sources/{source_id}/excerpts",
        json={
            "module_id": module_id,
            "page_start": 1,
            "page_end": 2,
            "topic": "Introduction",
        },
    )
    assert create.status_code == 201

    resp = await client.get(f"/courses/{course_id}/excerpts")
    assert resp.status_code == 200
    excerpts = resp.json()
    assert len(excerpts) == 1
    assert excerpts[0]["topic"] == "Introduction"
    assert excerpts[0]["source"]["authors"] == "A. Author"


@pytest.mark.asyncio
async def test_list_course_excerpts_course_not_found(client: AsyncClient) -> None:
    """GET /courses/{id}/excerpts returns 404 for an unknown course."""
    resp = await client.get("/courses/does-not-exist/excerpts")
    assert resp.status_code == 404


async def _make_pdf_source(client: AsyncClient) -> str:
    """Register the blank.pdf fixture as a source; return its ID."""
    payload = _text_source_payload() | {
        "bibkey": f"pdf{uuid.uuid4().hex[:8]}",
        "kind": "pdf",
        "path": "blank.pdf",
    }
    resp = await client.post("/sources/", json=payload)
    assert resp.status_code == 201
    return str(resp.json()["id"])


@pytest.mark.asyncio
async def test_get_source_page_image(client: AsyncClient) -> None:
    """GET /sources/{id}/pages/{n} renders the page as a cacheable PNG."""
    await _login_instructor(client)
    source_id = await _make_pdf_source(client)

    resp = await client.get(f"/sources/{source_id}/pages/1")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert "immutable" in resp.headers["cache-control"]
    assert resp.content.startswith(b"\x89PNG\r\n")


@pytest.mark.asyncio
async def test_get_source_page_image_out_of_range(client: AsyncClient) -> None:
    """GET /sources/{id}/pages/{n} rejects pages beyond the document."""
    await _login_instructor(client)
    source_id = await _make_pdf_source(client)

    for bad_page in (0, 6):
        resp = await client.get(f"/sources/{source_id}/pages/{bad_page}")
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_source_page_image_text_source(client: AsyncClient) -> None:
    """GET /sources/{id}/pages/{n} rejects non-PDF sources."""
    await _login_instructor(client)
    resp = await client.post("/sources/", json=_text_source_payload())
    source_id = resp.json()["id"]

    resp = await client.get(f"/sources/{source_id}/pages/1")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_source_page_image_source_not_found(client: AsyncClient) -> None:
    """GET /sources/{id}/pages/{n} returns 404 for an unknown source."""
    resp = await client.get("/sources/does-not-exist/pages/1")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_source_page_images_concurrent(client: AsyncClient) -> None:
    """Parallel page renders must all succeed (PDFium is not thread-safe)."""
    import asyncio

    await _login_instructor(client)
    source_id = await _make_pdf_source(client)

    responses = await asyncio.gather(
        *(client.get(f"/sources/{source_id}/pages/{page}") for page in (1, 2, 3, 4, 5))
    )
    assert all(resp.status_code == 200 for resp in responses)
    assert all(resp.content.startswith(b"\x89PNG\r\n") for resp in responses)


@pytest.mark.asyncio
async def test_get_excerpt_pdf(client: AsyncClient) -> None:
    """GET /sources/excerpts/{id}/pdf serves the embedded range as a PDF."""
    await _login_instructor(client)
    _course_id, module_id = await _make_module(client)
    source_id = await _make_pdf_source(client)

    create = await client.post(
        f"/sources/{source_id}/excerpts",
        json={
            "module_id": module_id,
            "page_start": 2,
            "page_end": 4,
            "topic": "Slice",
        },
    )
    assert create.status_code == 201
    excerpt_id = create.json()["id"]

    resp = await client.get(f"/sources/excerpts/{excerpt_id}/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "immutable" in resp.headers["cache-control"]
    assert resp.content.startswith(b"%PDF-")

    import io

    from pypdf import PdfReader

    assert len(PdfReader(io.BytesIO(resp.content)).pages) == 3


@pytest.mark.asyncio
async def test_get_excerpt_pdf_not_found(client: AsyncClient) -> None:
    """GET /sources/excerpts/{id}/pdf returns 404 for an unknown excerpt."""
    resp = await client.get("/sources/excerpts/does-not-exist/pdf")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_source_page_offset_roundtrip(client: AsyncClient) -> None:
    """POST /sources/ persists page_offset; it defaults to 0 when omitted."""
    await _login_instructor(client)
    resp = await client.post("/sources/", json=_text_source_payload() | {"page_offset": 19})
    assert resp.status_code == 201
    assert resp.json()["page_offset"] == 19

    resp = await client.post("/sources/", json=_text_source_payload())
    assert resp.json()["page_offset"] == 0
