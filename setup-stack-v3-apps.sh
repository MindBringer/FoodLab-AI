#!/usr/bin/env bash
set -Eeuo pipefail

ROLE="${ROLE:-}"
BASE_SVC="${BASE_SVC:-/srv/foodlab}"
BASE_GPU="${BASE_GPU:-/srv/ai-gpu}"
ENV_FILE="${ENV_FILE:-}"
GPU_BACKEND="${GPU_BACKEND:-auto}"
BUNDLE_DIR="${BUNDLE_DIR:-$(cd "$(dirname "$0")" && pwd)}"

usage() {
  cat <<USAGE
setup-stack-v3-apps.sh
Usage:
  sudo ./setup-stack-v3-apps.sh --role svc
  sudo ./setup-stack-v3-apps.sh --role gpu --gpu-backend nvidia
  sudo ENV_FILE=/root/foodlab.env ./setup-stack-v3-apps.sh --role svc

Flags:
  --role svc|gpu
  --gpu-backend auto|nvidia|amd|cpu
  --env-file PATH
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --role) ROLE="$2"; shift ;;
    --gpu-backend) GPU_BACKEND="$2"; shift ;;
    --env-file) ENV_FILE="$2"; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

[[ $EUID -eq 0 ]] || { echo "Run as root"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "docker missing"; exit 1; }

copy_env() {
  local target="$1"
  mkdir -p "$target"
  if [[ -n "$ENV_FILE" ]]; then
    install -m 600 "$ENV_FILE" "$target/.env"
  elif [[ ! -f "$target/.env" ]]; then
    install -m 600 "$BUNDLE_DIR/.env.example" "$target/.env"
  fi
}

if [[ "$ROLE" == "svc" ]]; then
  mkdir -p "$BASE_SVC"/{compose,env,services}
  mkdir -p "$BASE_SVC"/data/{inbox,raw,results,ocr}
  mkdir -p "$BASE_SVC"/{postgres,qdrant,redis,n8n/data,n8n/files,n8n/flows}
  rsync -a --delete "$BUNDLE_DIR/services/" "$BASE_SVC/services/"
  install -m 644 "$BUNDLE_DIR/docker-compose.svc.yml" "$BASE_SVC/compose/docker-compose.yml"
  copy_env "$BASE_SVC/env"
  docker network inspect foodlab-svc-bridge >/dev/null 2>&1 || docker network create foodlab-svc-bridge
  docker compose --env-file "$BASE_SVC/env/.env" -f "$BASE_SVC/compose/docker-compose.yml" up -d --build
elif [[ "$ROLE" == "gpu" ]]; then
  mkdir -p "$BASE_GPU"/{compose,env,services,models/ollama,cache/huggingface,audio}
  rsync -a --delete "$BUNDLE_DIR/services/llm-router/" "$BASE_GPU/services/llm-router/"
  rsync -a --delete "$BUNDLE_DIR/services/audio-api/" "$BASE_GPU/services/audio-api/"
  install -m 644 "$BUNDLE_DIR/docker-compose.ai.yml" "$BASE_GPU/compose/docker-compose.yml"
  copy_env "$BASE_GPU/env"
  sed -i "s/^GPU_BACKEND=.*/GPU_BACKEND=${GPU_BACKEND}/" "$BASE_GPU/env/.env" || true
  docker network inspect foodlab-svc-bridge >/dev/null 2>&1 || docker network create foodlab-svc-bridge
  profile="$GPU_BACKEND"; [[ "$profile" == "auto" ]] && profile="cpu"
  COMPOSE_PROFILES="$profile" docker compose --env-file "$BASE_GPU/env/.env" -f "$BASE_GPU/compose/docker-compose.yml" up -d --build
else
  usage
  exit 2
fi
