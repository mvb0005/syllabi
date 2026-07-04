"""Sources router — third-party reference works and cited excerpts."""

from fastapi import APIRouter, Depends, HTTPException, status
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
from backend.services.source_service import SourceService

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
