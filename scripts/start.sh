#!/usr/bin/env sh
set -eu

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$REPO_ROOT"

if [ ! -f .env ]; then
  app_secret=$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')
  database_secret=$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')
  awk -v app_secret="$app_secret" -v database_secret="$database_secret" '
    /^POSTGRES_PASSWORD=/ { print "POSTGRES_PASSWORD=" database_secret; next }
    /^ADAPTED_SECRET_KEY=/ { print "ADAPTED_SECRET_KEY=" app_secret; next }
    { print }
  ' .env.example > .env
  echo "Created .env with machine-local secrets. Keep it private."
fi

docker compose up --build -d
echo "AdaptEd is starting. Open http://localhost:${ADAPTED_WEB_PORT:-5173}"
echo "API health: http://localhost:${ADAPTED_API_PORT:-8000}/api/v1/health"
