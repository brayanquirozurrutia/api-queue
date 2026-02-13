# API Queue Scoring

Servicio API para clasificar la probabilidad de asistencia real a un concierto versus riesgo de reventa.

## Stack

- Django + Django REST Framework sobre ASGI.
- Gunicorn con workers Uvicorn.
- PostgreSQL.
- Modelo de ML con scikit-learn.
- Dependencias con `uv`.

---

## 1) Requisitos previos

Antes de correr el proyecto, valida estos prerequisitos:

- **Python 3.13+** (alineado con `requires-python = ">=3.13"` en `pyproject.toml`).
- **pip** actualizado.
- **Entorno virtual (`venv`)** disponible.
- **Docker + Docker Compose** (si usarás el flujo en contenedores).
- **PostgreSQL** accesible (si correrás sin Docker).

### 1.1 Verificación rápida

```bash
python3 --version
python3 -m pip --version
python3 -m venv --help
docker --version
docker compose version
```

### 1.2 Error común al crear el venv en Ubuntu/Debian (`ensurepip is not available`)

Si al ejecutar `python3 -m venv .venv` aparece este error:

```text
The virtual environment was not created successfully because ensurepip is not available.
```

instala el paquete `venv` de tu versión de Python y vuelve a crear el entorno:

```bash
sudo apt update
sudo apt install -y python3.13-venv
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
```

> Si tu sistema tiene otra versión de Python instalada (por ejemplo 3.12), usa el paquete equivalente (`python3.12-venv`).

---

## 2) Configuración inicial

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

## 3) Entorno local con venv (recomendado para IDE)

Si quieres evitar errores de intérprete en VS Code/PyCharm y que el IDE detecte librerías correctamente, usa un entorno virtual local (`.venv`) dentro del repo.

### 3.1 Crear y activar el venv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Si todo está bien, tu prompt debería mostrar algo como `(.venv)`.

Para desactivarlo:

```bash
deactivate
```

### 3.2 Instalar dependencias con el venv activado

Con el entorno activo, instala dependencias del proyecto (incluyendo herramientas de test):

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Si quieres usar `uv` (manteniendo el entorno local):

```bash
uv sync --group dev
```

### 3.3 Configurar el intérprete en el IDE

- **VS Code**:
  1. `Ctrl/Cmd + Shift + P`
  2. `Python: Select Interpreter`
  3. Elegir `./.venv/bin/python`

- **PyCharm / IntelliJ** (incluye versiones recientes):
  1. `Settings/Preferences > Project > Python Interpreter`
  2. `Add Interpreter > Existing`
  3. Seleccionar `./.venv/bin/python`
  4. Confirmar que el intérprete sea **Python 3.13+**

Esto evita el clásico error de imports no resueltos cuando ejecutas fuera del entorno.

---

## 4) Levantar en Docker (recomendado para integración)

```bash
docker compose up --build -d
```

> Nota: Postgres queda publicado en `localhost:5435` (contenedor `5432`).
> El backend usa bind-mount del repo y `DEV_RELOAD=true` por defecto, así que reinicia la API cuando cambia código sin rebuild.
> Si quieres modo producción, define `DEV_RELOAD=false`.
> El modelo se guarda en `/app/.data/attendance_model.joblib` (volumen `backend_data`); puedes cambiarlo con `MODEL_PATH_DOCKER`.

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

## 5) Levantar en local (sin Docker)

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

## 6) Entrenar el modelo

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

## 7) Endpoint de scoring

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

## 8) Entrenamiento vía endpoint (opcional, apagado por defecto)

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

## 9) Tests

### 9.1 Tests en local (rapidos, sin Docker)

```bash
./scripts/test.sh local
```

Esto usa SQLite por defecto via `config.test_settings`, ideal para correr rapido en el host.

> Si `pytest` no existe en tu entorno, instala dependencias de desarrollo con:

```bash
python -m pip install -e . --group dev
```

Con `uv`:

```bash
uv run pytest -q
```

### 9.2 Tests con Postgres (contenedor arriba)

1. Levanta servicios:

```bash
docker compose up -d
```

2. Corre tests con Postgres dentro del backend:

```bash
./scripts/test.sh postgres
```

Si cambiaste dependencias (por ejemplo `pyproject.toml`), fuerza rebuild:

```bash
./scripts/test.sh postgres --build
```

3. (Opcional) Si cambiaste esquema/modelos:

```bash
docker compose exec backend python manage.py migrate
```

---

## 10) Conexión a PostgreSQL desde DataGrip / DBeaver / TablePlus

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

## 11) Recomendaciones para un enfoque de ML más senior

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
