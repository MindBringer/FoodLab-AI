#!/usr/bin/env bash
set -euo pipefail

if ! groups "$USER" | grep -q docker; then
  sudo usermod -aG docker "$USER"
  exec newgrp docker <<EOF
  echo "Docker group activated"
  docker info
  bash "$0" "$@"
EOF
  exit 0
fi

ROLE=${1:-""}

if [[ "$ROLE" != "svc" && "$ROLE" != "gpu" ]]; then
  echo "Usage: ./setup-stack.sh [svc|gpu]"
  exit 1
fi

BASE_DIR="/opt/FoodLab-AI"
SVC_DIR="/srv/foodlab"
GPU_DIR="/srv/ai-gpu"

echo "=== FoodLab Setup ($ROLE) ==="

# --- Netzwerk ---
docker network inspect foodlab-svc-bridge >/dev/null 2>&1 || \
  docker network create foodlab-svc-bridge

if [ "$ROLE" = "svc" ]; then
  echo "Setting up Service Node..."

  sudo mkdir -p "$SVC_DIR"
  sudo chown $USER:$USER "$SVC_DIR"

  rsync -av --delete \
    "$BASE_DIR/services/" \
    "$SVC_DIR/services/"

  cp "$BASE_DIR/docker-compose.svc.yml" "$SVC_DIR/docker-compose.yml"
  cp "$BASE_DIR/.env" "$SVC_DIR/"

  cd "$SVC_DIR"

  docker compose config
  docker compose down || true
  
  sudo mkdir -p /srv/foodlab/n8n/data
  sudo mkdir -p /srv/foodlab/n8n/files
  sudo mkdir -p /srv/foodlab/n8n/flows
  sudo chown -R 1000:1000 /srv/foodlab/n8n
  
  docker compose up -d --build

  echo "Service node started."

elif [ "$ROLE" = "gpu" ]; then
  echo "Setting up GPU Node..."

  sudo mkdir -p "$GPU_DIR"
  sudo chown $USER:$USER "$GPU_DIR"

  rsync -av \
    "$BASE_DIR/services/llm-router" \
    "$GPU_DIR/services/"

  rsync -av \
    "$BASE_DIR/services/audio-api" \
    "$GPU_DIR/services/"

  cp "$BASE_DIR/docker-compose.ai.yml" "$GPU_DIR/docker-compose.yml"
  cp "$BASE_DIR/.env" "$GPU_DIR/"

  GPU_PROFILE="${GPU_BACKEND:-nvidia}"

  cd "$GPU_DIR"

  docker compose --profile "$GPU_PROFILE" config
  docker compose --profile "$GPU_PROFILE" down || true
  docker compose --profile "$GPU_PROFILE" up -d --build

  echo "GPU node started."
fi

echo "=== Done ==="
