FROM python:3.14-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc libc6-dev && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.11.18 /uv /uvx /usr/local/bin/
ENV UV_LINK_MODE=copy

# uv workspace: root manifest + this member's + its workspace-source dep
# (mcp-sdk) first, so the dependency layer stays cached across source edits.
COPY pyproject.toml uv.lock ./
COPY backend/pyproject.toml backend/pyproject.toml
COPY mcp-sdk mcp-sdk
RUN uv sync --frozen --package backend --no-install-project

COPY backend backend
RUN uv sync --frozen --package backend

COPY scripts/sync_content.py /app/backend/scripts/sync_content.py
COPY frontend/content /app/content
ENV CONTENT_DIR=/app/content
ENV PATH="/app/.venv/bin:${PATH}"
WORKDIR /app/backend
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000 --no-access-log"]
