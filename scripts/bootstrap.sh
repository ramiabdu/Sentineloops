#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
  echo "Created backend/.env from backend/.env.example"
else
  echo "backend/.env already exists"
fi

echo "SentinelOps bootstrap complete"
