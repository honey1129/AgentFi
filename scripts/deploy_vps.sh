#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env.prod}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "env file not found: $ENV_FILE" >&2
  echo "copy deploy/vps.env.example to $ENV_FILE and fill real values first" >&2
  exit 1
fi

ENV_FILE="$ENV_FILE" docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml up -d --build

echo
echo "production stack started"
echo "health check: docker compose --env-file $ENV_FILE -f docker-compose.prod.yml ps"
echo "logs: docker compose --env-file $ENV_FILE -f docker-compose.prod.yml logs -f caddy api worker"
