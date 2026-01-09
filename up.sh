#!/usr/bin/env bash
set -euo pipefail

# Create docker network if it doesn't exist
docker network create minecraft_network 2>/dev/null || true

# Build and start the stack
DOCKER_BUILDKIT=1 docker compose up --build -d

echo "App running at http://localhost:5090"