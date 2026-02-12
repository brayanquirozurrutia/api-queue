#!/usr/bin/env sh
set -e
.venv/bin/python manage.py migrate --noinput
if [ ! -f scoring/ml/attendance_model.joblib ]; then
  .venv/bin/python manage.py train_model
fi
exec .venv/bin/gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4 --threads 4 --timeout 60
