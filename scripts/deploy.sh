#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/srv/weather"
ENV_FILE="/etc/weather/.env"
DB_FILE="/etc/weather/weather_display.db"
CONTAINER_NAME="weather-api"
IMAGE_NAME="weather-api:latest"

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

function build_image() {
  log "Building Docker image"
  docker build -t "$IMAGE_NAME" "$REPO_DIR"
}

function stop_container() {
  if docker ps -q --filter "name=$CONTAINER_NAME" | grep -q .; then
    log "Stopping existing container"
    docker rm -f "$CONTAINER_NAME"
  fi
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

function run_container() {
  log "Starting container with env file"
  mkdir -p "$(dirname "$DB_FILE")"
  docker run -d \
    --name "$CONTAINER_NAME" \
    --env-file "$ENV_FILE" \
    -v "$DB_FILE:/app/weather_display.db" \
    -p 8000:8000 \
    --restart unless-stopped \
    "$IMAGE_NAME"
}

function migrate_db() {
  local python_bin="$REPO_DIR/.venv/bin/python"
  if [[ ! -x "$python_bin" ]]; then
    python_bin="python3"
  fi

  log "Applying database migrations (if any)"
  "$python_bin" "$REPO_DIR/app/database/db.py" --migrate || true
}

function main() {
  require_root
  ensure_repo
  ensure_env
  ensure_db_file
  update_code
  build_image
  stop_container
  run_container
  log "Deploy complete."
}

main "$@"

