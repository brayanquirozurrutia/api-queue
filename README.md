# API Queue Scoring

Servicio API para clasificar la probabilidad de asistencia real a un concierto versus riesgo de reventa.

## Stack

- Django + Django REST Framework sobre ASGI.
- Gunicorn con workers Uvicorn.
- PostgreSQL.
- Modelo de ML con scikit-learn.
- Dependencias con `uv`.

---

## 1) Configuración inicial

```bash
cp .env.example .env
```

Variables clave en `.env`:

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` (interno: `5432`; si usas Docker Compose, host publicado: `5435`)
- `DB_CONN_MAX_AGE`
- `MODEL_PATH`
- `ENABLE_MODEL_TRAIN_ENDPOINT` (default recomendado: `false`)
- `MODEL_TRAIN_TOKEN` (obligatorio si se habilita entrenamiento por endpoint)

---

## 2) Entorno local con venv (recomendado para IDE)

Si quieres evitar errores de intérprete en VS Code/PyCharm y que el IDE detecte librerías correctamente, usa un entorno virtual local (`.venv`) dentro del repo.

### 2.1 Crear y activar el venv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Si todo está bien, tu prompt debería mostrar algo como `(.venv)`.

Para desactivarlo:

```bash
deactivate
```

### 2.2 Instalar dependencias con el venv activado

Con el entorno activo, instala dependencias del proyecto:

```bash
pip install -e .
```

Si quieres usar `uv` (manteniendo el entorno local):

```bash
uv sync
```

### 2.3 Configurar el intérprete en el IDE

- **VS Code**:
  1. `Ctrl/Cmd + Shift + P`
  2. `Python: Select Interpreter`
  3. Elegir `./.venv/bin/python`

- **PyCharm / IntelliJ**:
  1. `Settings/Preferences > Project > Python Interpreter`
  2. `Add Interpreter > Existing`
  3. Seleccionar `./.venv/bin/python`

Esto evita el clásico error de imports no resueltos cuando ejecutas fuera del entorno.

---

## 3) Levantar en Docker (recomendado para integración)

```bash
docker compose up --build -d
```

> Nota: Postgres queda publicado en `localhost:5435` (contenedor `5432`).

Aplicar migraciones y entrenar modelo dentro del contenedor backend:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py train_model
```

API disponible en: `http://localhost:8000/api/v1/`

Documentación OpenAPI/Swagger:

- Schema OpenAPI (JSON): `http://localhost:8000/api/schema/`
- Swagger UI: `http://localhost:8000/api/docs/`

Para apagar todo:

```bash
docker compose down
```

---

## 4) Levantar en local (sin Docker)

### Opción A (usando venv + pip)

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py train_model
python -m uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

### Opción B (usando uv)

```bash
uv sync --frozen
uv run python manage.py migrate
uv run python manage.py train_model
uv run uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

---

## 5) Entrenar el modelo

Forma recomendada (operativa):

```bash
python manage.py train_model
```

Por defecto se generan **120.000 registros mock** para entrenar el modelo. También puedes ajustar volumen y semilla:

```bash
python manage.py train_model --size 300000 --seed 123
```

El artefacto se guarda en la ruta configurada por `MODEL_PATH`.

---

## 6) Endpoint de scoring

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

---

## 7) Entrenamiento vía endpoint (opcional, apagado por defecto)

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

---

## 8) Tests

### 8.1 Tests en local

Con venv activo:

```bash
pytest -q
```

Con `uv`:

```bash
uv run pytest -q
```

### 8.2 Tests con contenedor arriba

1. Levanta servicios:

```bash
docker compose up -d
```

2. Corre tests dentro del backend:

```bash
docker compose exec backend pytest -q
```

3. (Opcional) Si cambiaste esquema/modelos:

```bash
docker compose exec backend python manage.py migrate
```

---

## 9) Conexión a PostgreSQL desde DataGrip / DBeaver / TablePlus

Cuando corres con Docker Compose, usa estos datos:

- **Host:** `127.0.0.1`
- **Port:** `5435`
- **Database:** valor de `POSTGRES_DB` en `.env`
- **User:** valor de `POSTGRES_USER` en `.env`
- **Password:** valor de `POSTGRES_PASSWORD` en `.env`

### Configuración rápida en DataGrip

1. `+` > `Data Source` > `PostgreSQL`
2. Completa Host/Port/DB/User/Password
3. `Test Connection`
4. Si pide driver, aceptar descarga automática

> Si no conecta, revisa: `docker compose ps` y que el contenedor `postgres` esté `Up`.

---

## 10) Recomendaciones para un enfoque de ML más senior

Para endurecer el ciclo de vida del modelo y acercarlo a prácticas de ML Engineering senior:

1. **Versionado de modelos y datasets**
   - Guardar artefactos con versión semántica (`v1`, `v1.1`, etc.) y metadatos de entrenamiento.
   - Registrar hash de datos/features para trazabilidad.

2. **Separar entrenamiento y serving**
   - Evitar entrenar en runtime del API.
   - Mover entrenamiento a jobs programados (Airflow, GitHub Actions, Argo, etc.).

3. **Evaluación robusta**
   - Añadir métricas de clasificación: AUC-ROC, precision/recall, F1 por clase y calibration.
   - Definir umbrales por costo de negocio (falsos positivos de reventa vs falsos negativos).

4. **Monitoreo en producción**
   - Trackear drift de features y drift de predicciones.
   - Alertas cuando distribución cambie más allá de umbral.

5. **Gobernanza y seguridad**
   - Validar esquema de entrada de features de forma estricta.
   - Firmar/versionar artefactos y restringir endpoint de entrenamiento.

6. **Reproducibilidad**
   - Fijar seeds y versiones de librerías.
   - Guardar config de entrenamiento junto con el modelo.

Estas mejoras pueden incorporarse iterativamente sin romper la API actual.
