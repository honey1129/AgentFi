#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-git@github.com:honey1129/AgentFi.git}"
APP_DIR="${APP_DIR:-/opt/agentfi}"
BRANCH="${BRANCH:-main}"
ENV_FILE_NAME="${ENV_FILE_NAME:-.env.prod}"
DEFAULT_APP_USER="${SUDO_USER:-${USER:-}}"
if [[ -z "$DEFAULT_APP_USER" ]]; then
  DEFAULT_APP_USER="$(id -un 2>/dev/null || true)"
fi
APP_USER="${APP_USER:-$DEFAULT_APP_USER}"
ENABLE_UFW="${ENABLE_UFW:-false}"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This installer only supports Linux VPS hosts." >&2
  exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This installer currently supports Debian/Ubuntu systems only." >&2
  exit 1
fi

if [[ -z "$APP_USER" ]]; then
  echo "Unable to determine APP_USER." >&2
  exit 1
fi

run_as_root() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

user_home() {
  getent passwd "$APP_USER" | cut -d: -f6
}

APP_USER_HOME="$(user_home)"
if [[ -z "$APP_USER_HOME" ]]; then
  echo "Unable to determine home directory for $APP_USER." >&2
  exit 1
fi

echo "==> Installing base packages"
run_as_root apt-get update
run_as_root apt-get install -y \
  ca-certificates \
  curl \
  git \
  gnupg \
  lsb-release \
  ufw

if ! command -v docker >/dev/null 2>&1; then
  echo "==> Installing Docker Engine and Compose plugin"
  run_as_root install -m 0755 -d /etc/apt/keyrings
  if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | run_as_root gpg --dearmor -o /etc/apt/keyrings/docker.asc
    run_as_root chmod a+r /etc/apt/keyrings/docker.asc
  fi

  CODENAME="$(. /etc/os-release && echo "${VERSION_CODENAME}")"
  ARCH="$(dpkg --print-architecture)"
  echo \
    "deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${CODENAME} stable" \
    | run_as_root tee /etc/apt/sources.list.d/docker.list >/dev/null

  run_as_root apt-get update
  run_as_root apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin
  run_as_root systemctl enable --now docker
else
  echo "==> Docker already installed"
fi

if getent group docker >/dev/null 2>&1; then
  echo "==> Ensuring ${APP_USER} is in docker group"
  run_as_root usermod -aG docker "$APP_USER"
fi

if [[ "$ENABLE_UFW" == "true" ]]; then
  echo "==> Configuring UFW"
  run_as_root ufw allow OpenSSH
  run_as_root ufw allow 80/tcp
  run_as_root ufw allow 443/tcp
  run_as_root ufw --force enable
else
  echo "==> Skipping UFW enable (set ENABLE_UFW=true to enable it)"
fi

echo "==> Preparing application directory at ${APP_DIR}"
run_as_root mkdir -p "$APP_DIR"
run_as_root chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

if [[ -d "${APP_DIR}/.git" ]]; then
  echo "==> Existing git repo found, updating ${BRANCH}"
  git -C "$APP_DIR" fetch origin
  git -C "$APP_DIR" checkout "$BRANCH"
  git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
else
  echo "==> Cloning repository"
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

if [[ ! -f "$ENV_FILE_NAME" ]]; then
  echo "==> Creating ${ENV_FILE_NAME} from deploy/vps.env.example"
  cp deploy/vps.env.example "$ENV_FILE_NAME"
else
  echo "==> ${ENV_FILE_NAME} already exists, keeping current file"
fi

cat <<EOF

Install complete.

Repository: ${APP_DIR}
Branch: ${BRANCH}
Env file: ${APP_DIR}/${ENV_FILE_NAME}

Next steps:
1. Edit ${APP_DIR}/${ENV_FILE_NAME} with real production values.
2. Re-login or run: newgrp docker
3. Start the stack:
   cd ${APP_DIR}
   bash scripts/deploy_vps.sh ${ENV_FILE_NAME}

Useful checks:
  docker --version
  docker compose version
  docker compose --env-file ${ENV_FILE_NAME} -f docker-compose.prod.yml ps
EOF
