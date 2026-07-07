"""Execute router — proxies milestone C++ sources to the compile service.

The compiler container (emscripten) turns student code into a single-file
ES6/WASM module; the browser runs it in a Web Worker, so this service never
executes student code — it only compiles it. When an ``assignment_id`` is
supplied, that assignment's fixed test harness is appended server-side, so
the tests a milestone is judged by are never sent to (or editable in) the
client.
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.models.assignment import Assignment

router = APIRouter(prefix="/execute", tags=["execute"])

MAX_SOURCE_CHARS = 100_000


class CppCompileRequest(BaseModel):
    """Student C++ source to compile to a WASM module."""

    source: str = Field(min_length=1, max_length=MAX_SOURCE_CHARS)
    # When set, the assignment's fixed test harness is appended before
    # compilation (the harness itself stays server-side).
    assignment_id: str | None = None


class CppCompileResponse(BaseModel):
    """Compile outcome: a runnable ES6 module, or compiler diagnostics."""

    ok: bool
    js: str = ""
    diagnostics: str = ""


@router.post("/cpp", response_model=CppCompileResponse)
async def compile_cpp(
    payload: CppCompileRequest,
    db: AsyncSession = Depends(get_db),
) -> CppCompileResponse:
    """Compile C++ to a single-file WASM ES6 module via the compiler service."""
    source = payload.source
    if payload.assignment_id is not None:
        assignment = await db.get(Assignment, payload.assignment_id)
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment {payload.assignment_id} not found",
            )
        source = source + "\n" + assignment.test_code

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{settings.COMPILER_URL}/compile", json={"source": source}
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="compile service unavailable",
        ) from exc
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"compile service error ({resp.status_code})",
        )
    return CppCompileResponse.model_validate(resp.json())
