#!/usr/bin/env sh
set -eu

echo "[entrypoint] Running migrations"
.venv/bin/python manage.py migrate --noinput

if [ ! -f scoring/ml/attendance_model.joblib ]; then
  echo "[entrypoint] Model not found, training initial model"
  .venv/bin/python manage.py train_model
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
