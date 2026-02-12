FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

COPY pyproject.toml README.md ./
RUN uv sync --no-dev --no-install-project

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 8000

CMD ["./docker/entrypoint.sh"]
