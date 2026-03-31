#!/usr/bin/env bash
set -euo pipefail

echo "=== FoodLab Base Installation ==="

# --- System Update ---
sudo apt-get update
sudo apt-get upgrade -y

# --- Basic Tools ---
sudo apt-get install -y \
  git \
  curl \
  wget \
  jq \
  rsync \
  htop \
  net-tools \
  ca-certificates \
  gnupg \
  lsb-release

# --- Docker installieren (offiziell) ---
if ! command -v docker &> /dev/null; then
  echo "Installing Docker..."

  sudo mkdir -p /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) \
    signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# --- Docker User Setup ---
sudo usermod -aG docker $USER

# --- NVIDIA Setup optional ---
if lspci | grep -i nvidia > /dev/null; then
  echo "NVIDIA GPU detected – installing toolkit..."

  sudo apt-get install -y nvidia-driver-535 || true

  distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
  curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit.gpg

  curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

  sudo apt-get update
  sudo apt-get install -y nvidia-container-toolkit

  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
fi

echo "=== Base Installation complete ==="
echo "Re-login recommended (docker group)."
