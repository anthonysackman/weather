#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/srv/weather"
ENV_FILE="/etc/weather/.env"
DB_FILE="/etc/weather/weather_display.db"

function log() {
  echo "[deploy] $*"
}

function require_root() {
  if [[ "$EUID" -ne 0 ]]; then
    echo "Deploy script must be run as root (sudo)." >&2
    exit 1
  fi
}

function ensure_repo() {
  if [[ ! -d "$REPO_DIR/.git" ]]; then
    echo "Repository not found at $REPO_DIR. Run bootstrap first." >&2
    exit 1
  fi
}

function update_code() {
  log "Updating repository"
  git -C "$REPO_DIR" pull --ff-only
}

function refresh_compose() {
  log "Rebuilding and restarting docker compose services"
  docker compose -f "$REPO_DIR/compose.yaml" pull --quiet
  docker compose -f "$REPO_DIR/compose.yaml" build
}


function ensure_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Environment file $ENV_FILE missing. Run bootstrap." >&2
    exit 1
  fi
}

function ensure_db_file() {
  mkdir -p "$(dirname "$DB_FILE")"
  if [[ ! -f "$DB_FILE" ]]; then
    touch "$DB_FILE"
  fi
  chmod 660 "$DB_FILE"
}

function run_compose() {
  log "Bringing up docker compose service"
  docker compose -f "$REPO_DIR/compose.yaml" up -d --force-recreate --remove-orphans --quiet-pull
}

function main() {
  require_root
  ensure_repo
  ensure_env
  ensure_db_file
  update_code
  refresh_compose
  run_compose
  log "Deploy complete."
}

main "$@"

