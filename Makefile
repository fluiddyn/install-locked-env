
sync:
	pdm sync

lock:
	pdm lock

format:
	.venv/bin/ruff format

.PHONY: test
test:
	pdm run pytest test -v

.PHONY: test-all
test-all:
	pdm run pytest test -v --run-slow
