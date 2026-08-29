.PHONY: test test-unit test-cov lint

test:
	uv run --package backend pytest tests -v

test-unit:
	uv run --package backend pytest tests/unit -v

test-cov:
	uv run --package backend pytest tests --cov=. --cov-report=term-missing

lint:
	uv run --package backend ruff check .
