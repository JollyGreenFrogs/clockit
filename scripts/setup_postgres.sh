#!/usr/bin/env bash
set -euo pipefail

# scripts/setup_postgres.sh
# Install PostgreSQL (if missing), start the service, create role and database
# Usage:
#   ./scripts/setup_postgres.sh
# Environment variables (defaults used when not set):
#   POSTGRES_DB (default: clockit)
#   POSTGRES_USER (default: clockit)
#   POSTGRES_PASSWORD (default: clockit_pass)
#   POSTGRES_HOST (default: localhost)
#   POSTGRES_PORT (default: 5432)

BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASEDIR"

# Load .env if present (exports variables)
if [ -f .env ]; then
  # shellcheck disable=SC1091
  set -a
  . .env
  set +a
fi

# Helper to prefer multiple environment variable names (checks each in order)
get_first() {
  for name in "$@"; do
    val="${!name:-}"
    if [ -n "$val" ]; then
      printf "%s" "$val"
      return 0
    fi
  done
  return 1
}

# Prefer values set via POSTGRES_* or DB_* in .env; fall back to defaults
DB_NAME="$(get_first POSTGRES_DB DB_NAME)"
DB_USER="$(get_first POSTGRES_USER DB_USER)"
DB_PASSWORD="$(get_first POSTGRES_PASSWORD DB_PASSWORD)"
DB_HOST="$(get_first POSTGRES_HOST DB_HOST)"
DB_PORT="$(get_first POSTGRES_PORT DB_PORT)"

# Apply sensible defaults
DB_NAME="${DB_NAME:-clockit}"
DB_USER="${DB_USER:-clockit}"
DB_PASSWORD="${DB_PASSWORD:-clockit_pass}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "Postgres setup: DB_NAME=$DB_NAME, DB_USER=$DB_USER, DB_HOST=$DB_HOST, DB_PORT=$DB_PORT"

install_postgres() {
  if command -v psql >/dev/null 2>&1; then
    echo "Postgres appears installed (psql found). Skipping apt install."
    return 0
  fi

  echo "Installing PostgreSQL via apt..."
  sudo apt-get update
  sudo apt-get install -y postgresql postgresql-contrib
}

start_postgres() {
  echo "Starting PostgreSQL service..."
  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl start postgresql || true
  fi

  if sudo service postgresql status >/dev/null 2>&1; then
    sudo service postgresql start || true
  else
    # Try init.d fallback
    if [ -f /etc/init.d/postgresql ]; then
      sudo /etc/init.d/postgresql start || true
    fi
  fi

  # Wait briefly for server to accept connections
  for i in {1..10}; do
    if sudo -u postgres psql -c '\l' >/dev/null 2>&1; then
      echo "Postgres is running"
      return 0
    fi
    sleep 1
  done

  echo "Warning: PostgreSQL may not be running or accepting connections yet."
}

create_role_and_db() {
  echo "Creating role and database (if they don't exist)..."

  # Create role if not exists
  if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1; then
    echo "Role '${DB_USER}' already exists"
  else
    echo "Creating role '${DB_USER}'"
    sudo -u postgres psql -c "CREATE ROLE \"${DB_USER}\" WITH LOGIN PASSWORD '${DB_PASSWORD}';"
  fi

  # Create database if not exists
  if sudo -u postgres psql -lqt | cut -d \| -f 1 | awk '{print $1}' | grep -qw "${DB_NAME}"; then
    echo "Database '${DB_NAME}' already exists"
  else
    echo "Creating database '${DB_NAME}' owned by '${DB_USER}'"
    sudo -u postgres psql -c "CREATE DATABASE \"${DB_NAME}\" OWNER \"${DB_USER}\";"
  fi

  echo "Granting privileges on database '${DB_NAME}' to '${DB_USER}'"
  sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE \"${DB_NAME}\" TO \"${DB_USER}\";"
}

main() {
  install_postgres
  start_postgres
  create_role_and_db

  cat <<EOF

Postgres setup complete.

Add or update these entries in your .env file (or export in your shell):

POSTGRES_HOST=${DB_HOST}
POSTGRES_PORT=${DB_PORT}
POSTGRES_DB=${DB_NAME}
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}

Then run your application with DATABASE_TYPE=postgres set in .env or environment.

EOF
}

main "$@"
