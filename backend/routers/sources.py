"""Sources router — third-party reference works and cited excerpts."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import instructor_required
from backend.exceptions import ConflictError, NotFoundError, ValidationError
from backend.models.user import User
from backend.schemas.source import (
    SourceCreate,
    SourceExcerptCreate,
    SourceExcerptPublic,
    SourcePublic,
)
from backend.services.source_service import SourceService, render_page_png, slice_pdf_pages

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("/", response_model=SourcePublic, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: SourceCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(instructor_required),
) -> SourcePublic:
    """Register a source file for citation (instructor only)."""
    try:
        source = await SourceService(db).create_source(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.detail
        ) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail) from exc
    return SourcePublic.model_validate(source)


@router.get("/", response_model=list[SourcePublic])
async def list_sources(
    db: AsyncSession = Depends(get_db),
) -> list[SourcePublic]:
    """List all registered sources."""
    sources = await SourceService(db).list_sources()
    return [SourcePublic.model_validate(source) for source in sources]


@router.get("/{source_id}", response_model=SourcePublic)
async def get_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
) -> SourcePublic:
    """Retrieve a source by ID."""
    try:
        source = await SourceService(db).get_source(source_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SourcePublic.model_validate(source)


@router.get("/{source_id}/pages/{page_number}", response_class=Response)
async def get_source_page_image(
    source_id: str,
    page_number: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Render one page of a PDF source as a PNG image.

    Serves the figures, equations, and layout that plain-text extraction
    loses; excerpt readings embed these images page by page.
    """
    try:
        source = await SourceService(db).get_source(source_id)
        # Rasterization is CPU-bound; keep it off the event loop.
        png = await asyncio.to_thread(render_page_png, source, page_number)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.detail
        ) from exc
    return Response(
        content=png,
        media_type="image/png",
        # Pages of a registered source never change; let browsers cache hard.
        headers={"Cache-Control": "public, max-age=86400, immutable"},
    )


@router.get("/excerpts/{excerpt_id}/pdf", response_class=Response)
async def get_excerpt_pdf(
    excerpt_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Serve an excerpt's embedded page range as a standalone PDF.

    Only spans already embedded in a module are servable, keeping exposure
    scoped to cited excerpts; the frontend renders this slice with PDF.js.
    """
    try:
        excerpt = await SourceService(db).get_excerpt(excerpt_id)
        # pypdf slicing is CPU-bound (pure Python, thread-safe).
        pdf_bytes = await asyncio.to_thread(
            slice_pdf_pages, excerpt.source, excerpt.page_start, excerpt.page_end
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.detail
        ) from exc
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Cache-Control": "public, max-age=86400, immutable",
            "Content-Disposition": "inline",
        },
    )


@router.post(
    "/{source_id}/excerpts",
    response_model=SourceExcerptPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_excerpt(
    source_id: str,
    payload: SourceExcerptCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(instructor_required),
) -> SourceExcerptPublic:
    """Embed a page range of a source into a module (instructor only)."""
    try:
        excerpt = await SourceService(db).create_excerpt(source_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.detail
        ) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail) from exc
    return SourceExcerptPublic.model_validate(excerpt)
