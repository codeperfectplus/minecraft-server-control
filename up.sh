#!/usr/bin/env bash
set -euo pipefail

# Build and start the stack
DOCKER_BUILDKIT=1 docker compose up --build -d

echo "App running at http://localhost:5090"