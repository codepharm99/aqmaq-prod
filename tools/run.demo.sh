#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-headless}"   # headless|gui
SRC="${2:-rtsp://100.106.150.77:8554/cam}"
LINE="${3:-360}"

cd "$(dirname "$0")/.."  # в корень репо

export AQMAQ_DATA_DIR=./aqmaq-data
export OPENCV_FFMPEG_CAPTURE_OPTIONS=rtsp_transport;tcp

case "$MODE" in
  headless)
    source .venv/bin/activate
    python demo_line.py --source "$SRC" --line-y "$LINE" --no-gui
    ;;
  gui)
    source .venv-gui/bin/activate
    # Проверка DISPLAY — если пусто, окно не откроется
    if [ -z "${DISPLAY:-}" ]; then
      echo "[WARN] \$DISPLAY пуст. Если вы по SSH, подключайтесь с X11 форвардингом: ssh -X user@host"
    fi
    python - <<'PY'
import cv2, numpy as np
img=np.zeros((120,320,3),np.uint8); cv2.putText(img,'HighGUI check', (10,70),
    cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2,cv2.LINE_AA)
try:
    cv2.imshow('cv2 test', img); cv2.waitKey(500); cv2.destroyAllWindows()
    print('[OK] cv2.imshow работает')
except cv2.error as e:
    print('[ERR] cv2.imshow недоступно:', e); exit(1)
PY
    python demo_line.py --source "$SRC" --line-y "$LINE"
    ;;
  *)
    echo "Usage: tools/run_demo.sh [headless|gui] [RTSP_URL] [LINE_Y]"
    exit 2
    ;;
esac

