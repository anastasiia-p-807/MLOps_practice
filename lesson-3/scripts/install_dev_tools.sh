#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${PROJECT_DIR}/install.log"

exec > >(tee -a "${LOG_FILE}") 2>&1

echo "== MLOps lesson-3 dev tools installer =="
echo "Project: ${PROJECT_DIR}"
echo "Started: $(date -Is)"

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

install_with_apt() {
  if ! command_exists apt-get; then
    echo "apt-get was not found. Install missing tools manually for this OS."
    return 0
  fi

  sudo apt-get update
  sudo apt-get install -y python3 python3-pip python3-venv docker.io docker-compose-plugin
}

ensure_base_tools() {
  local missing=()

  command_exists docker || missing+=("docker")
  command_exists python3 || missing+=("python3")
  command_exists pip3 || missing+=("pip3")

  if ((${#missing[@]} > 0)); then
    echo "Missing tools: ${missing[*]}"
    install_with_apt
  fi
}

print_versions() {
  echo
  echo "== Tool versions =="
  docker --version || true
  docker compose version || true
  python3 --version || true
  pip3 --version || true
}

install_python_dependencies() {
  echo
  echo "== Python dependency install =="
  python3 -m pip install --upgrade pip
  python3 -m pip install -r "${PROJECT_DIR}/requirements.txt"
}

verify_python_dependencies() {
  echo
  echo "== Python dependency verification =="
  python3 - <<'PY'
import torch
import torchvision
from PIL import Image

print(f"torch={torch.__version__}")
print(f"torchvision={torchvision.__version__}")
print(f"pillow={Image.__version__}")
PY
}

ensure_base_tools
print_versions
install_python_dependencies
verify_python_dependencies

echo
echo "Finished: $(date -Is)"
