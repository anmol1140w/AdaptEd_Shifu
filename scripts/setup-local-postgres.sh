#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$repo_root/backend/.env"
if [[ ! -f "$env_file" ]]; then
  echo "Missing backend/.env. Copy backend/.env.example to backend/.env first." >&2
  exit 1
fi

# Load only the local application's environment; do not enable shell tracing.
set -a
# shellcheck disable=SC1090
source "$env_file"
set +a
: "${ADAPTED_DATABASE_PASSWORD:?Set ADAPTED_DATABASE_PASSWORD in backend/.env}"

sudo -u postgres psql --no-psqlrc -v ON_ERROR_STOP=1 \
  -v app_password="$ADAPTED_DATABASE_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE adapted_user LOGIN PASSWORD %L', :'app_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'adapted_user')
\gexec
ALTER ROLE adapted_user WITH LOGIN PASSWORD :'app_password';
SELECT 'CREATE DATABASE adapted OWNER adapted_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'adapted')
\gexec
SQL

echo "Local PostgreSQL role and database are ready."
