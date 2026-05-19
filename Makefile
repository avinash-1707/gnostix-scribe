.PHONY: dev server client install migrate

PYTHON := server/.venv/bin/python
UVICORN := server/.venv/bin/uvicorn
ALEMBIC := server/.venv/bin/alembic

dev:
	@echo "Starting server (8000) + client (3001). Ctrl-C to stop both."
	@trap 'kill 0' INT TERM EXIT; \
		$(UVICORN) server.main:app --reload --host 127.0.0.1 --port 8000 & \
		(cd client && pnpm dev) & \
		wait

server:
	$(UVICORN) server.main:app --reload --host 127.0.0.1 --port 8000

client:
	cd client && pnpm dev

install:
	uv venv server/.venv --python 3.12
	uv pip install --python $(PYTHON) -r server/requirements.txt
	cd client && pnpm install

migrate:
	cd server && ../$(ALEMBIC) upgrade head
