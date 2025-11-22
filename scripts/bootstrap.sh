#!/usr/bin/env bash
set -euo pipefail

# Bootstrap script for Ubuntu 24.04 droplets.
# Installs prerequisites, prepares directories, writes /etc/weather/.env, and
# optionally runs the admin user setup. Re-runnable with confirmations on
# destructive steps.

CONFIG_DIR="/etc/weather"
REPO_DIR="/srv/weather"
ENV_FILE="${CONFIG_DIR}/.env"
NGINX_SITE="/etc/nginx/sites-available/weather"
NGINX_LINK="/etc/nginx/sites-enabled/weather"

ASTRONOMY_API_ID=""
ASTRONOMY_API_SECRET=""
DB_PATH=""
PORT=""

function log() {
  echo "[bootstrap] $*"
}

function confirm() {
  local prompt="${1:?}"
  local reply
  while true; do
    read -rp "$prompt (y/n): " reply
    case "${reply,,}" in
      y|yes) return 0 ;;
      n|no) return 1 ;;
      *) echo "Please type y or n." ;;
    esac
  done
}

function require_root() {
  if [[ "$EUID" -ne 0 ]]; then
    echo "This script must be run as root (sudo)." >&2
    exit 1
  fi
}

function ensure_package() {
  local pkg="$1"
  if ! dpkg -s "$pkg" &> /dev/null; then
    log "Installing $pkg"
    apt-get install -y "$pkg"
  else
    log "$pkg already installed"
  fi
}

function ensure_dir() {
  local dir="$1"
  if [[ ! -d "$dir" ]]; then
    log "Creating directory $dir"
    mkdir -p "$dir"
  fi
}

function prompt_env_value() {
  local key="$1"
  local default="${2:-}"
  local current=""
  if [[ -f "$ENV_FILE" ]]; then
    current=$(grep -E "^${key}=" "$ENV_FILE" || true)
    current="${current#${key}=}"
  fi

  if [[ -n "$current" ]]; then
    read -rp "Value for ${key}? [current: ${current}] " input
  else
    read -rp "Value for ${key}?${default:+ [default: ${default}]} " input
  fi

  if [[ -z "$input" ]]; then
    if [[ -n "$current" ]]; then
      echo "$current"
    else
      echo "${default:-}"
    fi
  else
    echo "$input"
  fi
}

function write_env_file() {
  log "Configuring ${ENV_FILE}"
  ensure_dir "$CONFIG_DIR"
  if [[ -f "$ENV_FILE" ]]; then
    if ! confirm "Overwrite existing ${ENV_FILE}?"; then
      log "Keeping existing environment file"
      return
    fi
  fi

  local temp
  temp="$(mktemp)"
  {
    echo "# Weather API configuration"
    echo "DB_PATH=${DB_PATH:-${CONFIG_DIR}/weather_display.db}"
    echo "PORT=${PORT:-8000}"
    echo "ASTRONOMY_API_ID=${ASTRONOMY_API_ID}"
    echo "ASTRONOMY_API_SECRET=${ASTRONOMY_API_SECRET}"
  } > "$temp"

  install -o root -g root -m 600 "$temp" "$ENV_FILE"
  rm -f "$temp"
}

function gather_secrets() {
  log "Collecting secrets for .env"
  export ASTRONOMY_API_ID
  export ASTRONOMY_API_SECRET
  export DB_PATH
  export PORT

  ASTRONOMY_API_ID=$(prompt_env_value "ASTRONOMY_API_ID")
  if [[ -z "$ASTRONOMY_API_ID" ]]; then
    echo "ASTRONOMY_API_ID is required." >&2
    exit 1
  fi

  ASTRONOMY_API_SECRET=$(prompt_env_value "ASTRONOMY_API_SECRET")
  if [[ -z "$ASTRONOMY_API_SECRET" ]]; then
    echo "ASTRONOMY_API_SECRET is required." >&2
    exit 1
  fi

  DB_PATH=$(prompt_env_value "DB_PATH" "${CONFIG_DIR}/weather_display.db")
  PORT=$(prompt_env_value "PORT" "8000")
}

function setup_repo() {
  local repo_url

  if [[ -d "${REPO_DIR}/.git" ]]; then
    log "Updating existing repository at ${REPO_DIR}"
    if confirm "Run git pull in ${REPO_DIR}?"; then
      git -C "$REPO_DIR" pull
    fi
    return
  fi

  read -rp "Git repository URL to clone: " repo_url
  if [[ -z "$repo_url" ]]; then
    echo "Repository URL is required to clone the project." >&2
    exit 1
  fi

  git clone "$repo_url" "$REPO_DIR"
}

function install_python_dependencies() {
  log "Installing Python dependencies"

  log "Ensuring pip is up to date"
  python3 -m pip install --upgrade pip setuptools wheel

  if [[ -f "${REPO_DIR}/requirements.txt" ]]; then
    python3 -m pip install -r "${REPO_DIR}/requirements.txt"
  else
    log "No requirements.txt found in ${REPO_DIR}"
  fi
}

function run_create_admin() {
  if ! confirm "Would you like to run create_admin.py now?"; then
    return
  fi

  read -rp "Admin username: " admin_user
  read -rp "Admin password (min 6 chars): " admin_password
  if (( ${#admin_password} < 6 )); then
    echo "Password must be at least 6 characters." >&2
    return
  fi

  log "Running create_admin.py"
  python3 "${REPO_DIR}/create_admin.py" "$admin_user" "$admin_password"
}

function setup_nginx() {
  log "Configuring nginx"
  cat <<'EOF' > "$NGINX_SITE"
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

  ln -sf "$NGINX_SITE" "$NGINX_LINK"
  nginx -t
  systemctl restart nginx
}

function main() {
  require_root

  log "Preparing system"
  apt-get update
  ensure_package git
  ensure_package curl
  ensure_package docker.io
  ensure_package nginx
  ensure_package python3
  ensure_package python3-pip

  systemctl enable --now docker

  ensure_dir "$CONFIG_DIR"
  ensure_dir "$REPO_DIR"

  gather_secrets
  write_env_file

  setup_repo

  install_python_dependencies

  run_create_admin

  setup_nginx

  log "Bootstrap complete. Run scripts/deploy.sh when ready."
}

main "$@"

