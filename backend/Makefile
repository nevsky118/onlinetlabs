.PHONY: test test-unit test-cov lint

test:
	poetry run pytest tests -v

test-unit:
	poetry run pytest tests/unit -v

test-cov:
	poetry run pytest tests --cov=. --cov-report=term-missing

lint:
	poetry run ruff check .
