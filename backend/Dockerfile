FROM python:3.14-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc libc6-dev && rm -rf /var/lib/apt/lists/*
RUN pip install poetry && poetry config virtualenvs.create false
COPY mcp-sdk /mcp-sdk
COPY backend/pyproject.toml backend/poetry.lock* ./
RUN poetry install --no-interaction --no-root
COPY backend/ .
RUN poetry install --no-interaction
COPY scripts/sync_content.py /app/scripts/sync_content.py
COPY frontend/content /app/content
ENV CONTENT_DIR=/app/content
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
