# API Queue Scoring

Servicio API para clasificar la probabilidad de asistencia real a un concierto versus riesgo de reventa.

## Stack elegido

- Django + Django REST Framework sobre ASGI.
- Uvicorn workers administrados por Gunicorn.
- PostgreSQL.
- Modelo de ML con scikit-learn entrenado con mock data.
- Gestión de dependencias con `uv` y lockfile reproducible.
- Python 3.13.

## Diseño de escalabilidad

- Endpoint async con ORM asíncrono (`aupdate_or_create`, `acreate`).
- Proceso CPU-bound del modelo aislado con `asyncio.to_thread`.
- Gunicorn con múltiples workers Uvicorn para concurrencia horizontal.
- Conexiones persistentes a Postgres (`CONN_MAX_AGE`).
- Listo para escalar en Kubernetes con múltiples réplicas de backend.

## Entrenamiento de modelo

```bash
uv run python manage.py train_model
```

## Desarrollo local

```bash
uv sync --frozen
uv run python manage.py migrate
uv run python manage.py train_model
uv run uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

## Endpoint

`POST /api/v1/score/`

Ejemplo de payload:

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

## Docker

```bash
docker compose up --build
```
