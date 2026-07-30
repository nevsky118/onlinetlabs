# Env files live in deployment/<tier>/. Encryption uses the shared `make encrypt`/`make decrypt` from the repo root.
ENV ?= local
ENV_FILE := ../deployment/$(ENV)/autotests.env

.PHONY: test
test:
	PYTHONPATH=.. poetry run pytest -v --rootdir=. --envFile $(ENV_FILE) .

.PHONY: test-e2e
test-e2e:
	cd ../backend && PYTHONPATH=.:.. poetry run pytest \
		--rootdir=../autotests \
		--envFile ../deployment/local/autotests.env \
		../autotests/api_tests/e2e/learning_analytics/ -v
