
sync:
	pdm sync

lock:
	pdm lock

format:
	.venv/bin/ruff format

.PHONY: test
test:
	pdm run pytest test -v
