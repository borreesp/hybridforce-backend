#!/usr/bin/env sh
set -euo pipefail

echo "[entrypoint] Running migrations..."
alembic upgrade head

echo "[entrypoint] Starting API..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
