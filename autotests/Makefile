ENV ?= local
ENV_FILE := settings/configuration/$(ENV).env

.PHONY: test encrypt decrypt

test:
	PYTHONPATH=.. poetry run pytest -v --rootdir=. --envFile $(ENV_FILE) .

encrypt:
	openssl enc -aes-256-cbc -salt -pbkdf2 -in $(file) -out $(file).aes -pass pass:$(CONFIG_PASSWORD)

decrypt:
	openssl enc -aes-256-cbc -d -salt -pbkdf2 -in $(file) -out $$(echo $(file) | sed 's/.aes$$//') -pass pass:$(CONFIG_PASSWORD)
