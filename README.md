# API Queue Scoring

Servicio API para clasificar la probabilidad de asistencia real a un concierto versus riesgo de reventa.

## Stack

- Django + Django REST Framework sobre ASGI.
- Gunicorn con workers Uvicorn.
- PostgreSQL.
- Modelo de ML con scikit-learn.
- Dependencias con `uv`.

## 1) Configuración inicial

```bash
cp .env.example .env
```

Variables clave en `.env`:

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `DB_CONN_MAX_AGE`
- `MODEL_PATH`
- `ENABLE_MODEL_TRAIN_ENDPOINT` (default recomendado: `false`)
- `MODEL_TRAIN_TOKEN` (obligatorio si se habilita entrenamiento por endpoint)

## 2) Levantar en Docker (recomendado)

```bash
docker compose up --build
```

Luego aplica migraciones y entrena el modelo dentro del contenedor backend:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py train_model
```

API disponible en: `http://localhost:8000/api/v1/`

## 3) Levantar en local (sin Docker)

```bash
uv sync --frozen
uv run python manage.py migrate
uv run python manage.py train_model
uv run uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

## 4) Entrenar el modelo

Forma recomendada (operativa):

```bash
python manage.py train_model
```

El artefacto se guarda en la ruta configurada por `MODEL_PATH`.

## 5) Endpoint de scoring

`POST /api/v1/score/`

Payload:

```json
{
  "email": "persona@example.com",
  "age": 29,
  "country": "CL",
  "city": "Santiago",
  "account_age_days": 950,
  "purchases_last_12_months": 8,
  "canceled_orders": 0,
  "tickets_per_order_avg": 1.4,
  "distance_to_venue_km": 12.5,
  "payment_failures_ratio": 0.02,
  "event_affinity_score": 0.91,
  "night_purchase_ratio": 0.12,
  "resale_reports_count": 0,
  "attendance_rate": 0.88
}
```

Respuesta:

```json
{
  "attendance_probability": 0.93,
  "reseller_probability": 0.07,
  "risk_label": "attendee",
  "model_version": "v1"
}
```

## 6) Entrenamiento vía endpoint (opcional, apagado por defecto)

Ruta: `POST /api/v1/model/train/`

Headers requeridos:

- `X-Train-Token: <MODEL_TRAIN_TOKEN>`

Requisitos:

1. `ENABLE_MODEL_TRAIN_ENDPOINT=true`
2. `MODEL_TRAIN_TOKEN` configurado

Recomendación senior:

- Mantener esta ruta deshabilitada en internet pública.
- Usarla solo en red interna/operación controlada.
- Preferir entrenamiento por job asíncrono o pipeline CI/CD de ML para producción.

## 7) Tests

```bash
pytest -q
```
