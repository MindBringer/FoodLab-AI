#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/MindBringer/FoodLab-AI.git"
TARGET_DIR="/opt/FoodLab-AI"

echo "=== FoodLab Bootstrap ==="

# --- Clone oder Update ---
if [ -d "$TARGET_DIR/.git" ]; then
  echo "Repo exists → pulling latest"
  cd "$TARGET_DIR"
  git pull
else
  echo "Cloning repo..."
  sudo mkdir -p /opt
  sudo chown $USER:$USER /opt
  git clone "$REPO_URL" "$TARGET_DIR"
fi

cd "$TARGET_DIR"

# --- ENV Setup ---
if [ ! -f ".env" ]; then
  echo "Creating .env from template"
  cp .env.example .env
fi

echo "Edit .env if needed:"
echo "nano $TARGET_DIR/.env"

echo "=== Bootstrap complete ==="
