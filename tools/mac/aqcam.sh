#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CFG="${CFG:-$DIR/mediamtx.yml}"

CAM_INDEX="${CAM_INDEX:-0}"
SIZE="${SIZE:-1280x720}"
FPS="${FPS:-30}"
GOP="${GOP:-60}"
PRESET="${PRESET:-veryfast}"
URL_PATH="${URL_PATH:-cam}"

MTX_LOG="${MTX_LOG:-$DIR/mediamtx.log}"
FFMPEG_LOG="${FFMPEG_LOG:-$DIR/ffmpeg_cam.log}"
FFMPEG_PUB="rtsp://127.0.0.1:8554/${URL_PATH}"

FFMPEG_CMD=(ffmpeg -hide_banner -loglevel warning
  -f avfoundation -framerate "${FPS}" -video_size "${SIZE}" -i "${CAM_INDEX}"
  -pix_fmt yuv420p -c:v libx264 -preset "${PRESET}" -tune zerolatency -g "${GOP}"
  -f rtsp -rtsp_transport tcp "${FFMPEG_PUB}"
)

need_cmd(){ command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' not found"; exit 1; }; }

start_mtx(){
  need_cmd mediamtx
  if pgrep -f "mediamtx .*${CFG}" >/dev/null 2>&1; then
    echo "[mtx] already running"
  else
    echo "[mtx] starting with ${CFG}"
    nohup mediamtx "${CFG}" >> "${MTX_LOG}" 2>&1 &
    for i in {1..30}; do
      nc -z 127.0.0.1 8554 && { echo "[mtx] ready"; break; }
      sleep 0.3
      [[ $i -eq 30 ]] && { echo "ERROR: mediamtx didn't start on :8554"; exit 1; }
    done
  fi
}

start_ffmpeg(){
  need_cmd ffmpeg
  if pgrep -f "ffmpeg .* ${FFMPEG_PUB}" >/dev/null 2>&1; then
    echo "[ffmpeg] publisher already running"
  else
    echo "[ffmpeg] publishing camera index=${CAM_INDEX} ${SIZE}@${FPS} → ${FFMPEG_PUB}"
    nohup "${FFMPEG_CMD[@]}" >> "${FFMPEG_LOG}" 2>&1 &
    sleep 1
    pgrep -f "ffmpeg .* ${FFMPEG_PUB}" >/dev/null || { echo "ERROR: ffmpeg publish failed (see ${FFMPEG_LOG})"; exit 1; }
  fi
}

stop_all(){ pkill -f "ffmpeg .* ${FFMPEG_PUB}" 2>/dev/null || true; pkill -f "mediamtx .*${CFG}" 2>/dev/null || true; echo "[ok] stopped"; }
status(){ pgrep -f "mediamtx .*${CFG}" >/dev/null && echo "[mtx] RUNNING" || echo "[mtx] STOPPED"; pgrep -f "ffmpeg .* ${FFMPEG_PUB}" >/dev/null && echo "[ffmpeg] RUNNING" || echo "[ffmpeg] STOPPED"; echo "[logs] mtx:${MTX_LOG}  ffmpeg:${FFMPEG_LOG}"; }
show_url(){ local TSIP=""; command -v tailscale >/dev/null 2>&1 && TSIP="$(tailscale ip -4 | head -n1 || true)"; local LANIP; LANIP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo 127.0.0.1)"; echo ""; echo "RTSP URLs:"; [[ -n "${TSIP}" ]] && echo "  Tailscale: rtsp://${TSIP}:8554/${URL_PATH}"; echo "  LAN:       rtsp://${LANIP}:8554/${URL_PATH}"; }
devices(){ need_cmd ffmpeg; echo "[devices] AVFoundation:"; ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | sed 's/^/\t/'; }
usage(){ echo "Usage: $(basename "$0") [start|stop|restart|status|devices]"; echo "Env: CAM_INDEX SIZE FPS GOP PRESET URL_PATH CFG"; }

case "${1:-start}" in
  start) start_mtx; start_ffmpeg; status; show_url ;;
  stop) stop_all ;;
  restart) stop_all; start_mtx; start_ffmpeg; status; show_url ;;
  status) status; show_url ;;
  devices) devices ;;
  *) usage; exit 1 ;;
esac

