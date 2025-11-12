#!/usr/bin/env bash
set -euo pipefail
sudo apt update
sudo apt install -y libgtk-3-0 libglib2.0-0 libsm6 libxext6 libxrender1 libgl1 xauth
echo "OK: GUI runtime deps installed."

