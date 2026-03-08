.PHONY: install serve serve-mcp serve-service \
       test test-mcp test-service test-e2e test-mcp-e2e test-service-e2e \
       lint gns3-up gns3-down clean

MCP_DIR = mcp-server
SERVICE_DIR = gns3-service

# ── Development ──────────────────────────────────────────────
install:
	cd $(MCP_DIR) && poetry install
	cd $(SERVICE_DIR) && poetry install

serve: serve-service

serve-mcp:
	cd $(MCP_DIR) && poetry run python -m src.main

serve-service:
	cd $(SERVICE_DIR) && poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8101

# ── Testing ──────────────────────────────────────────────────
test: test-mcp test-service

test-mcp:
	cd $(MCP_DIR) && poetry run python -m pytest -m "not e2e" -v

test-service:
	cd $(SERVICE_DIR) && poetry run python -m pytest -m "not e2e" -v

test-e2e: gns3-up
	cd $(MCP_DIR) && poetry run python -m pytest -m e2e -v
	cd $(SERVICE_DIR) && poetry run python -m pytest -m e2e -v

test-mcp-e2e: gns3-up
	cd $(MCP_DIR) && poetry run python -m pytest -m e2e -v

test-service-e2e: gns3-up
	cd $(SERVICE_DIR) && poetry run python -m pytest -m e2e -v

# ── Code Quality ─────────────────────────────────────────────
lint:
	cd $(MCP_DIR) && poetry run ruff check src/ tests/
	cd $(SERVICE_DIR) && poetry run ruff check src/ tests/

# ── Docker ───────────────────────────────────────────────────
gns3-up:
	cd $(SERVICE_DIR) && docker compose up -d --wait

gns3-down:
	cd $(SERVICE_DIR) && docker compose down

# ── Cleanup ──────────────────────────────────────────────────
clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
