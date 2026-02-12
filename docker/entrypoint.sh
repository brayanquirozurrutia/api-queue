#!/usr/bin/env sh
set -e
uv run python manage.py migrate --noinput
if [ ! -f scoring/ml/attendance_model.joblib ]; then
  uv run python manage.py train_model
fi
exec uv run gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4 --threads 4 --timeout 60
