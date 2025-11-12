#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."  # в корень репо
# 1) GUI зависимости для HighGUI
bash tools/ubuntu/install-gui-deps.sh
# 2) Отдельный venv для GUI
python3 -m venv .venv-gui
source .venv-gui/bin/activate
pip install -U pip
# 3) Локально сгенерировать requirements.gui.txt из базового
sed 's/opencv-python-headless/opencv-python/g' requirements.txt > requirements.gui.txt
pip install -r requirements.gui.txt
echo "OK: .venv-gui (с opencv-python) готово."
