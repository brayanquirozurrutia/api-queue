#!/usr/bin/env sh
set -eu

MODEL_PATH="${MODEL_PATH:-/app/scoring/ml/attendance_model.joblib}"

echo "[entrypoint] Running migrations"
.venv/bin/python manage.py migrate --noinput

if [ ! -f "$MODEL_PATH" ]; then
  echo "[entrypoint] Model not found, training initial model"
  .venv/bin/python manage.py train_model
fi

if [ "${DEV_RELOAD:-false}" = "true" ]; then
  echo "[entrypoint] Starting uvicorn (reload enabled)"
  exec .venv/bin/uvicorn config.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir /app \
    --reload-exclude .venv \
    --reload-exclude .git \
    --reload-exclude .pytest_cache
fi

echo "[entrypoint] Starting gunicorn"
exec .venv/bin/gunicorn config.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-4}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --log-level "${LOG_LEVEL:-info}"
