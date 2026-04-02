#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env.prod}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "env file not found: $ENV_FILE" >&2
  echo "copy deploy/vps.env.example to $ENV_FILE and fill real values first" >&2
  exit 1
fi

BT_BIND_HOST="${BT_BIND_HOST:-127.0.0.1}"
BT_BIND_PORT="${BT_BIND_PORT:-18000}"

ENV_FILE="$ENV_FILE" \
BT_BIND_HOST="$BT_BIND_HOST" \
BT_BIND_PORT="$BT_BIND_PORT" \
docker compose \
  --env-file "$ENV_FILE" \
  -f docker-compose.prod.yml \
  -f docker-compose.bt.yml \
  up -d --build api worker scheduler listener mysql redis

echo
echo "baota/nginx stack started"
echo "api is bound to ${BT_BIND_HOST}:${BT_BIND_PORT}"
echo "health check: curl http://${BT_BIND_HOST}:${BT_BIND_PORT}/v1/health"
echo "status: docker compose --env-file $ENV_FILE -f docker-compose.prod.yml -f docker-compose.bt.yml ps"
echo "logs: docker compose --env-file $ENV_FILE -f docker-compose.prod.yml -f docker-compose.bt.yml logs -f api worker listener"
