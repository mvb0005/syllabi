"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers import assignments, courses, health, submissions, users


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown logic."""
    yield


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Returns:
        Fully configured FastAPI instance.
    """
    app = FastAPI(
        title="Syllabi LMS API",
        description="AI-powered Learning Management System",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(users.router)
    app.include_router(courses.router)
    app.include_router(assignments.router)
    app.include_router(submissions.router)

    return app


app = create_app()
