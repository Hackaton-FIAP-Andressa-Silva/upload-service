#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete. Starting server..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8001
