FROM python:3.14-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.11.18 /uv /uvx /usr/local/bin/
ENV UV_LINK_MODE=copy

# uv workspace: root manifest + this member's + its workspace-source dep
# (mcp-sdk) first, so the dependency layer stays cached across source edits.
COPY pyproject.toml uv.lock ./
COPY gns3/gns3-mcp/pyproject.toml gns3/gns3-mcp/pyproject.toml
COPY mcp-sdk mcp-sdk
RUN uv sync --frozen --package gns3-mcp-server --no-install-project

COPY gns3/gns3-mcp gns3/gns3-mcp
RUN uv sync --frozen --package gns3-mcp-server

ENV PATH="/app/.venv/bin:${PATH}"
WORKDIR /app/gns3/gns3-mcp
EXPOSE 8100
CMD ["python", "-m", "src.main"]
