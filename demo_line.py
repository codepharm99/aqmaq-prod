import os
import cv2
import time
import requests
from dotenv import load_dotenv
from pathlib import Path
import argparse

# -------- env --------
load_dotenv()

SOURCE = os.getenv("SOURCE", "0")
LINE_Y = int(os.getenv("LINE_Y", "300"))
API_URL = os.getenv("API_URL", "http://localhost:8000/incidents")
NO_MOTION_SECONDS = float(os.getenv("NO_MOTION_SECONDS", "5"))

# Базовый каталог данных: по умолчанию ./aqmaq-data внутри репо
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("AQMAQ_DATA_DIR", str(BASE_DIR / "aqmaq-data")))
THUMBS_DIR = DATA_DIR / "thumbs"

# Форсируем TCP для RTSP (если не задано снаружи)
if SOURCE.startswith(("rtsp://", "rtsps://")):
    os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")

# -------- CLI --------
parser = argparse.ArgumentParser()
parser.add_argument("--no-gui", action="store_true", help="Запуск без окна")
args = parser.parse_args()
NO_GUI = args.no_gui

# -------- ensure dirs --------
THUMBS_DIR.mkdir(parents=True, exist_ok=True)

# -------- helpers --------
def open_capture(src: str):
    if src == "0":
        cap = cv2.VideoCapture(0)
    else:
        if src.startswith(("rtsp://", "rtsps://")):
            cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        else:
            cap = cv2.VideoCapture(src)
    return cap

def post_event(event: str, y: int | None = None, frame=None):
    ts = time.time()
    data = {"timestamp": ts, "event": event}
    if y is not None:
        data["y"] = y
    try:
        requests.post(API_URL, json=data, timeout=1)
        print(f"[EVENT] {event}" + (f" y={y}" if y is not None else ""))
        if event == "cross_line" and frame is not None:
            thumb_path = THUMBS_DIR / f"event_{int(ts)}.jpg"
            cv2.imwrite(str(thumb_path), frame)
    except Exception as e:
        print("[ERROR] POST failed:", e)

# -------- init --------
cap = open_capture(SOURCE)
fgbg = cv2.createBackgroundSubtractorMOG2()

print(f"[INFO] Starting demo_line... Source={SOURCE}, Line_Y={LINE_Y}, no_gui={NO_GUI}")
print(f"[INFO] DATA_DIR={DATA_DIR}")
print(f"[INFO] OPENCV_FFMPEG_CAPTURE_OPTIONS={os.getenv('OPENCV_FFMPEG_CAPTURE_OPTIONS')}")
print(f"[INFO] NO_MOTION_SECONDS={NO_MOTION_SECONDS}")

frame_count = 0
reopen_attempts = 0

presence = False
last_motion_ts = time.time()
AREA_MIN = 500

while True:
    ret, frame = cap.read()
    if not ret:
        if SOURCE.startswith(("rtsp://", "rtsps://")) and reopen_attempts < 5:
            reopen_attempts += 1
            print(f"[WARN] Read failed. Reopening RTSP (attempt {reopen_attempts}/5)...")
            cap.release()
            time.sleep(0.5)
            cap = open_capture(SOURCE)
            continue
        print("[INFO] Video ended or camera disconnected.")
        break

    reopen_attempts = 0
    frame_count += 1

    mask = fgbg.apply(frame)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    any_motion = False
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w * h > AREA_MIN:
            any_motion = True
            cy = y + h // 2
            if abs(cy - LINE_Y) < 5:
                post_event("cross_line", y=cy, frame=frame)

    now = time.time()
    if any_motion:
        last_motion_ts = now
        if not presence:
            presence = True
            post_event("motion_start")
    else:
        if presence and (now - last_motion_ts) > NO_MOTION_SECONDS:
            presence = False
            post_event("motion_end")

    if not NO_GUI:
        cv2.line(frame, (0, LINE_Y), (frame.shape[1], LINE_Y), (0, 0, 255), 2)
        cv2.imshow("Line Demo", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
if not NO_GUI:
    cv2.destroyAllWindows()

print("[INFO] Finished.")
