#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env.prod}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "env file not found: $ENV_FILE" >&2
  echo "copy deploy/vps.env.example to $ENV_FILE and fill real values first" >&2
  exit 1
fi

HOST_API_PORT="${HOST_API_PORT:-18000}"

ENV_FILE="$ENV_FILE" \
HOST_API_PORT="$HOST_API_PORT" \
docker compose \
  --env-file "$ENV_FILE" \
  -f docker-compose.host-services.yml \
  up -d --build api worker scheduler listener

echo
echo "host-services stack started"
echo "api is bound to 127.0.0.1:${HOST_API_PORT}"
echo "health check: curl http://127.0.0.1:${HOST_API_PORT}/v1/health"
echo "status: docker compose --env-file $ENV_FILE -f docker-compose.host-services.yml ps"
echo "logs: docker compose --env-file $ENV_FILE -f docker-compose.host-services.yml logs -f api worker listener"
