FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/app/.venv/bin:/root/.local/bin:${PATH}"

COPY pyproject.toml README.md ./
RUN uv sync --dev --no-install-project

COPY . .

RUN chmod +x docker/entrypoint.sh \
    && mkdir -p /app/.data \
    && groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["./docker/entrypoint.sh"]
