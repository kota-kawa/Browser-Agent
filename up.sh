#!/usr/bin/env bash
set -euo pipefail

NETWORK_NAME="${MULTI_AGENT_NETWORK:-multi_agent_platform_net}"

if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  echo "Creating Docker network: $NETWORK_NAME"
  docker network create "$NETWORK_NAME" >/dev/null
fi

docker compose up --build "$@"
