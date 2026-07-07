"""Source service — registering sources and extracting cited excerpts."""

import io
import threading
from pathlib import Path

import pypdfium2 as pdfium
from pypdf import PdfReader, PdfWriter
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.exceptions import ConflictError, NotFoundError, ValidationError
from backend.models.course import Module
from backend.models.source import Source, SourceExcerpt, SourceKind
from backend.schemas.source import SourceCreate, SourceExcerptCreate


def _sources_root() -> Path:
    """Return the resolved root directory for source files."""
    return Path(settings.SOURCES_DIR).resolve()


def resolve_source_path(relative_path: str) -> Path:
    """Resolve a source-relative path, refusing escapes from the sources root.

    Raises:
        ValidationError: If the path is absolute or resolves outside the
            sources directory, or the file does not exist.
    """
    if Path(relative_path).is_absolute():
        raise ValidationError("Source path must be relative to the sources directory")
    root = _sources_root()
    resolved = (root / relative_path).resolve()
    if not resolved.is_relative_to(root):
        raise ValidationError("Source path escapes the sources directory")
    if not resolved.is_file():
        raise ValidationError(f"Source file '{relative_path}' not found")
    return resolved


def validate_source_kind(file_path: Path, kind: SourceKind) -> None:
    """Verify a source file's actual content matches its declared kind.

    Raises:
        ValidationError: If a ``pdf`` source doesn't start with the PDF
            magic bytes, or a ``text`` source isn't valid UTF-8 text.
    """
    if kind is SourceKind.pdf:
        with file_path.open("rb") as fh:
            magic = fh.read(5)
        if magic != b"%PDF-":
            raise ValidationError(f"'{file_path.name}' is not a PDF file (kind=pdf)")
    else:
        try:
            file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError(
                f"'{file_path.name}' is not valid UTF-8 text (kind=text)"
            ) from exc


def extract_page_range(source: Source, page_start: int, page_end: int) -> str:
    """Extract text for an inclusive, 1-indexed page range of a source.

    PDF sources use pypdf page extraction; ``text`` sources interpret the
    range as line numbers.

    Raises:
        ValidationError: If the range exceeds the document.
    """
    file_path = resolve_source_path(source.path)
    if source.kind is SourceKind.pdf:
        reader = PdfReader(file_path)
        total = len(reader.pages)
        if page_end > total:
            raise ValidationError(f"page_end {page_end} exceeds document length ({total} pages)")
        pages = reader.pages[page_start - 1 : page_end]
        return "\n\n".join(page.extract_text() or "" for page in pages).rstrip()

    lines = file_path.read_text(encoding="utf-8").splitlines()
    total = len(lines)
    if page_end > total:
        raise ValidationError(f"page_end {page_end} exceeds document length ({total} lines)")
    return "\n".join(lines[page_start - 1 : page_end]).rstrip()


# Rasterization scale for page images: 2.0 x 72 dpi = 144 dpi, sharp enough
# for textbook figures and equations without producing multi-MB pages.
PAGE_IMAGE_SCALE = 2.0

# PDFium is not thread-safe: concurrent calls from worker threads corrupt
# its global state ("Data format error" on document open). All pdfium work
# must be serialized through this lock.
_PDFIUM_LOCK = threading.Lock()


def render_page_png(source: Source, page_number: int) -> bytes:
    """Rasterize one 1-indexed page of a PDF source to PNG bytes.

    Raises:
        ValidationError: If the source is not a PDF or the page is out of
            range.
    """
    if source.kind is not SourceKind.pdf:
        raise ValidationError("Page images are only available for PDF sources")
    file_path = resolve_source_path(source.path)
    with _PDFIUM_LOCK:
        pdf = pdfium.PdfDocument(file_path)
        try:
            total = len(pdf)
            if not 1 <= page_number <= total:
                raise ValidationError(
                    f"page {page_number} out of range (document has {total} pages)"
                )
            bitmap = pdf[page_number - 1].render(scale=PAGE_IMAGE_SCALE)
            image = bitmap.to_pil()
        finally:
            pdf.close()
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def slice_pdf_pages(source: Source, page_start: int, page_end: int) -> bytes:
    """Extract an inclusive, 1-indexed page range of a PDF source as PDF bytes.

    Raises:
        ValidationError: If the source is not a PDF or the range exceeds the
            document.
    """
    if source.kind is not SourceKind.pdf:
        raise ValidationError("PDF slices are only available for PDF sources")
    file_path = resolve_source_path(source.path)
    reader = PdfReader(file_path)
    if page_end > len(reader.pages):
        raise ValidationError(
            f"page_end {page_end} exceeds document length ({len(reader.pages)} pages)"
        )
    writer = PdfWriter()
    for page in reader.pages[page_start - 1 : page_end]:
        writer.add_page(page)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


class SourceService:
    """Handles source registration and excerpt creation/lookup."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialise with an async database session."""
        self._db = db

    async def create_source(self, payload: SourceCreate) -> Source:
        """Register a source file for citation.

        Raises:
            ValidationError: If the file is missing, the path is unsafe, or
                the file's actual content doesn't match the declared kind.
            ConflictError: If the bibkey is already registered.
        """
        resolved = resolve_source_path(payload.path)
        validate_source_kind(resolved, payload.kind)
        existing = await self._db.scalar(select(Source).where(Source.bibkey == payload.bibkey))
        if existing is not None:
            raise ConflictError(f"Source with bibkey '{payload.bibkey}' already exists")

        source = Source(
            bibkey=payload.bibkey,
            title=payload.title,
            authors=payload.authors,
            edition=payload.edition,
            publisher=payload.publisher,
            year=payload.year,
            kind=payload.kind,
            path=payload.path,
            page_offset=payload.page_offset,
        )
        self._db.add(source)
        try:
            await self._db.commit()
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(f"Source with bibkey '{payload.bibkey}' already exists") from exc
        await self._db.refresh(source)
        return source

    async def get_source(self, source_id: str) -> Source:
        """Retrieve a source by primary key.

        Raises:
            NotFoundError: If no source with that ID exists.
        """
        source = await self._db.get(Source, source_id)
        if source is None:
            raise NotFoundError("Source", source_id)
        return source

    async def list_sources(self) -> list[Source]:
        """Return all registered sources ordered by bibkey."""
        result = await self._db.scalars(select(Source).order_by(Source.bibkey))
        return list(result)

    async def create_excerpt(self, source_id: str, payload: SourceExcerptCreate) -> SourceExcerpt:
        """Embed a page range of a source into a module.

        Text for the range is extracted immediately and cached on the
        excerpt row.

        Raises:
            NotFoundError: If the source or module does not exist.
            ValidationError: If the range is invalid for the document.
            ConflictError: If the identical span is already embedded.
        """
        source = await self.get_source(source_id)
        if await self._db.get(Module, payload.module_id) is None:
            raise NotFoundError("Module", payload.module_id)

        content_text = extract_page_range(source, payload.page_start, payload.page_end)

        excerpt = SourceExcerpt(
            source_id=source_id,
            module_id=payload.module_id,
            page_start=payload.page_start,
            page_end=payload.page_end,
            topic=payload.topic,
            context_md=payload.context_md,
            order_index=payload.order_index,
            content_text=content_text,
        )
        self._db.add(excerpt)
        try:
            await self._db.commit()
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(
                "This span of the source is already embedded in the module"
            ) from exc
        await self._db.refresh(excerpt, attribute_names=["source"])
        return excerpt

    async def get_excerpt(self, excerpt_id: str) -> SourceExcerpt:
        """Retrieve an excerpt with its source eagerly loaded.

        Raises:
            NotFoundError: If no excerpt with that ID exists.
        """
        excerpt = await self._db.scalar(
            select(SourceExcerpt)
            .where(SourceExcerpt.id == excerpt_id)
            .options(selectinload(SourceExcerpt.source))
        )
        if excerpt is None:
            raise NotFoundError("SourceExcerpt", excerpt_id)
        return excerpt

    async def list_excerpts_for_course(self, course_id: str) -> list[SourceExcerpt]:
        """Return all excerpts across a course's modules, in module order.

        The related ``source`` is eagerly loaded for citation rendering.
        """
        result = await self._db.scalars(
            select(SourceExcerpt)
            .join(Module, SourceExcerpt.module_id == Module.id)
            .where(Module.course_id == course_id)
            .order_by(Module.order_index, SourceExcerpt.order_index, SourceExcerpt.page_start)
            .options(selectinload(SourceExcerpt.source))
        )
        return list(result)
