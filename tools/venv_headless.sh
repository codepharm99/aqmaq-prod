#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."  # в корень репо
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
echo "OK: .venv (headless) готово."

