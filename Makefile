.PHONY: help install serve dev up up-db down logs ps psql \
        migrate migrate-create migrate-rollback \
        test lint format check \
        encrypt decrypt clean sync-content seed-lab-templates openclaw

# ── Paths ────────────────────────────────────────────────────
BE := backend
FE := frontend
SDK := mcp-sdk
ENV ?= local
ENV_FILE := ../deployment/$(ENV)/backend.env
DC := docker compose -f deployment/local/compose.yaml
OPENCLAW_PORT ?= 18789
OPENCLAW_AUTH ?= none
OPENCLAW_BIND ?= loopback

# ── Colors ───────────────────────────────────────────────────
B := \033[0;34m
G := \033[0;32m
Y := \033[1;33m
D := \033[2m
N := \033[0m

.DEFAULT_GOAL := help

# ── Help ─────────────────────────────────────────────────────
help:
	@printf "$(B)══════════════════════════════════════════$(N)\n"
	@printf "$(G)  onlinetlabs$(N)\n"
	@printf "$(B)══════════════════════════════════════════$(N)\n"
	@printf "\n  $(B)Development$(N)\n"
	@printf "  $(Y)%-20s$(N) %s\n" "install"            "Install all dependencies (poetry + pnpm)"
	@printf "  $(Y)%-20s$(N) %s\n" "serve"              "Backend API (ENV=local|dev|prod)"
	@printf "  $(Y)%-20s$(N) %s\n" "dev"                "Frontend dev server (next dev)"
	@printf "  $(Y)%-20s$(N) %s\n" "openclaw"           "OpenClaw Gateway (OPENCLAW_PORT=18789)"
	@printf "\n  $(B)Docker$(N)\n"
	@printf "  $(Y)%-20s$(N) %s\n" "up"                 "Start all services"
	@printf "  $(Y)%-20s$(N) %s\n" "up-db"              "Start database only"
	@printf "  $(Y)%-20s$(N) %s\n" "down"               "Stop all services"
	@printf "  $(Y)%-20s$(N) %s\n" "logs"               "Service logs (svc= filter)"
	@printf "  $(Y)%-20s$(N) %s\n" "ps"                 "Service status"
	@printf "  $(Y)%-20s$(N) %s\n" "psql"               "PostgreSQL console"
	@printf "\n  $(B)Migrations$(N)\n"
	@printf "  $(Y)%-20s$(N) %s\n" "migrate"            "Run migrations"
	@printf "  $(Y)%-20s$(N) %s\n" "migrate-create"     "Create migration (msg=\"description\")"
	@printf "  $(Y)%-20s$(N) %s\n" "migrate-rollback"   "Rollback last migration"
	@printf "\n  $(B)Testing$(N)\n"
	@printf "  $(Y)%-20s$(N) %s\n" "test"               "Run all tests (backend + SDK)"
	@printf "\n  $(B)Code Quality$(N)\n"
	@printf "  $(Y)%-20s$(N) %s\n" "lint"               "Lint (ruff + biome)"
	@printf "  $(Y)%-20s$(N) %s\n" "format"             "Format (ruff + biome)"
	@printf "  $(Y)%-20s$(N) %s\n" "check"              "All checks (CI)"
	@printf "\n  $(B)Utility$(N)\n"
	@printf "  $(Y)%-20s$(N) %s\n" "encrypt"            "Encrypt .env file"
	@printf "  $(Y)%-20s$(N) %s\n" "decrypt"            "Decrypt .env.aes file"
	@printf "  $(Y)%-20s$(N) %s\n" "clean"              "Remove caches"
	@printf "  $(Y)%-20s$(N) %s\n" "sync-content"       "Sync MDX frontmatter into DB"
	@echo ""

# ── Development ──────────────────────────────────────────────
install:
	cd $(BE) && poetry install
	cd $(FE) && pnpm install
	cd $(SDK) && poetry install

serve:
	cd $(BE) && ENV_FILE=$(ENV_FILE) poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev:
	cd $(FE) && ln -sf ../deployment/$(ENV)/frontend.env .env && pnpm dev

openclaw:
	openclaw gateway run --auth $(OPENCLAW_AUTH) --bind $(OPENCLAW_BIND) --port $(OPENCLAW_PORT) --force --allow-unconfigured

# ── Docker ───────────────────────────────────────────────────
up:
	$(DC) up -d --wait

up-db:
	$(DC) up -d db redis

down:
	$(DC) down

logs:
	$(DC) logs -f $(svc)

ps:
	$(DC) ps

psql:
	$(DC) exec db psql -U postgres -d onlinetlabs

# ── Migrations ───────────────────────────────────────────────
migrate:
	cd $(BE) && ENV_FILE=$(ENV_FILE) poetry run alembic upgrade head

migrate-create:
	cd $(BE) && ENV_FILE=$(ENV_FILE) poetry run alembic revision --autogenerate -m "$(msg)"

migrate-rollback:
	cd $(BE) && ENV_FILE=$(ENV_FILE) poetry run alembic downgrade -1

# ── Testing ──────────────────────────────────────────────────
test:
	cd $(BE) && PYTHONPATH=. pytest -v tests/
	cd $(SDK) && PYTHONPATH=src poetry run pytest -v tests/

# ── Code Quality ─────────────────────────────────────────────
lint:
	cd $(BE) && poetry run ruff check . --fix
	cd $(FE) && pnpm lint:fix
	cd $(SDK) && poetry run ruff check src/ tests/ --fix

format:
	cd $(BE) && poetry run ruff format .
	cd $(FE) && pnpm format
	cd $(SDK) && poetry run ruff format src/ tests/

check:
	cd $(BE) && poetry run ruff check .
	cd $(BE) && poetry run ruff format --check .
	cd $(FE) && pnpm lint
	cd $(FE) && pnpm typecheck
	cd $(SDK) && poetry run ruff check src/ tests/
	cd $(SDK) && poetry run ruff format --check src/ tests/

# ── Encryption ───────────────────────────────────────────────
# Все env стека лежат в deployment/<tier>/ и шифруются двумя командами. Ключ в
# CONFIG_PASSWORD (в CI берётся из секретов раннера, в репозитории его нет).
# gns3 шифруется отдельно (gns3/Makefile) — это отдельный сервис.
encrypt:
	@test -n "$(CONFIG_PASSWORD)" || { echo "CONFIG_PASSWORD не задан"; exit 1; }
	@find deployment -name '*.env' | while read -r f; do \
		openssl enc -aes-256-cbc -salt -pbkdf2 -in "$$f" -out "$$f.aes" -pass pass:$(CONFIG_PASSWORD) && echo "  encrypted $$f"; \
	done

decrypt:
	@test -n "$(CONFIG_PASSWORD)" || { echo "CONFIG_PASSWORD не задан"; exit 1; }
	@find deployment -name '*.env.aes' | while read -r f; do \
		openssl enc -aes-256-cbc -d -salt -pbkdf2 -in "$$f" -out "$${f%.aes}" -pass pass:$(CONFIG_PASSWORD) && echo "  decrypted $${f%.aes}"; \
	done

# ── Content Sync ─────────────────────────────────────────────
sync-content:
	cd $(BE) && ENV_FILE=$(ENV_FILE) PYTHONPATH=.. poetry run python -m scripts.sync_content

seed-lab-templates:
	cd $(BE) && ENV_FILE=$(ENV_FILE) PYTHONPATH=.. poetry run python -m scripts.seed_lab_templates

export-cohort:
	cd $(BE) && ENV_FILE=$(ENV_FILE) PYTHONPATH=.. poetry run python -m scripts.export_cohort_metrics

eval-identifier:
	cd $(BE) && ENV_FILE=$(ENV_FILE) PYTHONPATH=.. poetry run python -m scripts.eval_identifier

# ── Cleanup ──────────────────────────────────────────────────
clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf htmlcov/ .coverage
