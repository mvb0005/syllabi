# LMS backend — FastAPI + uvicorn, migrations applied on start.
# Build context is the repository root (see .devcontainer/docker-compose.yml).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

# Install pinned dependencies from the canonical pyproject; the source tree
# itself is bind-mounted at runtime so code changes don't require a rebuild.
COPY pyproject.toml ./
COPY backend ./backend
COPY alembic.ini ./
RUN pip install .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
