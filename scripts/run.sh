#!/bin/sh
set -e

python - <<'PY'
import os
import time
import psycopg

url = os.environ.get("DATABASE_URL")
if not url:
    raise SystemExit("DATABASE_URL is not set")

# psycopg accepts URIs without SQLAlchemy driver prefix
psycopg_url = url.replace("postgresql+psycopg://", "postgresql://", 1)

for i in range(30):
    try:
        conn = psycopg.connect(psycopg_url)
        conn.close()
        print("DB is ready")
        break
    except Exception as exc:
        print("DB not ready, retrying...", exc)
        time.sleep(2)
else:
    raise SystemExit("Database not reachable after retries")
PY

alembic upgrade head
uvicorn main:app --host 0.0.0.0 --port 8000
