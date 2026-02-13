#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-local}"
BUILD_FLAG="${2:-}"

cd "$ROOT_DIR"

case "$MODE" in
  local)
    if [[ ! -x ".venv/bin/python" ]]; then
      echo "Missing .venv. Create it with: python3 -m venv .venv" >&2
      exit 1
    fi
    exec .venv/bin/python -m pytest -q
    ;;
  postgres)
    if ! command -v docker >/dev/null 2>&1; then
      echo "docker is required for postgres mode." >&2
      exit 1
    fi
    if [[ "$BUILD_FLAG" == "--build" ]]; then
      docker compose up -d --build backend
    else
      docker compose up -d backend
    fi
    exec docker compose exec -T -e USE_POSTGRES_FOR_TESTS=1 backend pytest -q -o cache_dir=/tmp/pytest_cache
    ;;
  *)
    echo "Usage: scripts/test.sh [local|postgres]" >&2
    exit 2
    ;;
esac
