.PHONY: help install serve serve-mcp \
       test lint up down gns3-up \
       up-db psql \
       migrate migrate-create migrate-rollback \
       encrypt decrypt clean

# ── Paths ────────────────────────────────────────────────────
MCP_DIR = gns3-mcp
SERVICE_DIR = gns3-service
ENV ?= local
ENV_FILE := $(ENV).env

DC = docker compose

# ── Colors ───────────────────────────────────────────────────
B := \033[0;34m
G := \033[0;32m
Y := \033[1;33m
N := \033[0m

.DEFAULT_GOAL := help

# ── Help ─────────────────────────────────────────────────────
help:
	@printf "$(B)══════════════════════════════════════════$(N)\n"
	@printf "$(G)  gns3$(N)\n"
	@printf "$(B)══════════════════════════════════════════$(N)\n"
	@printf "\n  $(B)Development$(N)\n"
	@printf "  $(Y)%-20s$(N) %s\n" "install"            "Install dependencies (gns3-mcp + gns3-service)"
	@printf "  $(Y)%-20s$(N) %s\n" "serve"              "Start gns3-service (ENV=local|dev|prod)"
	@printf "  $(Y)%-20s$(N) %s\n" "serve-mcp"          "Start MCP server"
	@printf "\n  $(B)Testing$(N)\n"
	@printf "  $(Y)%-20s$(N) %s\n" "test"               "Run gns3-mcp unit tests"
	@printf "\n  $(B)Code Quality$(N)\n"
	@printf "  $(Y)%-20s$(N) %s\n" "lint"               "Lint both services with ruff"
	@printf "\n  $(B)Docker$(N)\n"
	@printf "  $(Y)%-20s$(N) %s\n" "up"                 "Start full plugin stack (Docker)"
	@printf "  $(Y)%-20s$(N) %s\n" "down"               "Stop all containers"
	@printf "  $(Y)%-20s$(N) %s\n" "gns3-up"            "Start GNS3 server only"
	@printf "  $(Y)%-20s$(N) %s\n" "up-db"              "Start PostgreSQL only"
	@printf "  $(Y)%-20s$(N) %s\n" "psql"               "PostgreSQL console"
	@printf "\n  $(B)Migrations$(N)\n"
	@printf "  $(Y)%-20s$(N) %s\n" "migrate"            "Run migrations"
	@printf "  $(Y)%-20s$(N) %s\n" "migrate-create"     "Create migration (msg=\"description\")"
	@printf "  $(Y)%-20s$(N) %s\n" "migrate-rollback"   "Rollback last migration"
	@printf "\n  $(B)Utility$(N)\n"
	@printf "  $(Y)%-20s$(N) %s\n" "encrypt"            "Encrypt .env file"
	@printf "  $(Y)%-20s$(N) %s\n" "decrypt"            "Decrypt .env.aes file"
	@printf "  $(Y)%-20s$(N) %s\n" "clean"              "Remove caches"
	@echo ""

# ── Development ──────────────────────────────────────────────
install:
	cd $(MCP_DIR) && poetry install
	cd $(SERVICE_DIR) && poetry install

serve:
	cd $(SERVICE_DIR) && ENV_FILE=$(ENV_FILE) poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8101

serve-mcp:
	cd $(MCP_DIR) && ENV_FILE=$(ENV_FILE) poetry run python -m src.main

# ── Testing ──────────────────────────────────────────────────
test:
	cd $(MCP_DIR) && poetry run python -m pytest -v

# ── Code Quality ─────────────────────────────────────────────
lint:
	cd $(MCP_DIR) && poetry run ruff check src/ tests/
	cd $(SERVICE_DIR) && poetry run ruff check src/ tests/

# ── Docker ───────────────────────────────────────────────────
up:
	$(DC) up -d --wait

down:
	$(DC) down

gns3-up:
	$(DC) up -d gns3-server --wait

up-db:
	$(DC) up -d postgres --wait

psql:
	$(DC) exec postgres psql -U gns3test -d gns3_service_test

# ── Migrations ──────────────────────────────────────────────
migrate:
	cd $(SERVICE_DIR) && ENV_FILE=$(ENV_FILE) poetry run alembic upgrade head

migrate-create:
	cd $(SERVICE_DIR) && ENV_FILE=$(ENV_FILE) poetry run alembic revision --autogenerate -m "$(msg)"

migrate-rollback:
	cd $(SERVICE_DIR) && ENV_FILE=$(ENV_FILE) poetry run alembic downgrade -1

# ── Encryption ───────────────────────────────────────────────
encrypt:
	openssl enc -aes-256-cbc -salt -pbkdf2 -in $(file) -out $(file).aes -pass pass:$(CONFIG_PASSWORD)

decrypt:
	openssl enc -aes-256-cbc -d -salt -pbkdf2 -in $(file) -out $$(echo $(file) | sed 's/.aes$$//') -pass pass:$(CONFIG_PASSWORD)

# ── Cleanup ──────────────────────────────────────────────────
clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
