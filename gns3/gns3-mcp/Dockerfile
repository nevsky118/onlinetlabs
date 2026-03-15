FROM python:3.14-slim
WORKDIR /app
RUN pip install poetry && poetry config virtualenvs.create false
COPY mcp-sdk /mcp-sdk
COPY gns3/gns3-mcp/pyproject.toml gns3/gns3-mcp/poetry.lock* ./
RUN poetry install --no-interaction --no-root
COPY gns3/gns3-mcp/ .
RUN poetry install --no-interaction
EXPOSE 8100
CMD ["python", "-m", "src.main"]
