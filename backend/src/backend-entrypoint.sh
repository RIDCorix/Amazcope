uv run alembic upgrade head
uv run uvicorn core.main:app --host 0.0.0.0 --port 8000 --reload
