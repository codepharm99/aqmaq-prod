# aqmaq-prod

Единый минимальный скелет для демо «линия выхода»: структура проекта, команды запуска, стандартизованные пути данных.

Чек-лист подзадач
- Поднять API и проверить запись инцидентов
- Настроить источник видео (локальная камера или RTSP с Mac)
- Запустить демо `demo_line.py` и убедиться в событиях
- Проверить сохранение миниатюр в `aqmaq-data/thumbs`
- Верифицировать пути и переменные окружения (`.env`)

**Рабочая среда**
- Ubuntu 24 (Python 3.12, OpenCV headless)
- Mac для камеры (MediaMTX + FFmpeg)
- Опционально: Tailscale

Правила и структура
- Все пути repo-relative. По умолчанию: `AQMAQ_DATA_DIR=./aqmaq-data`
- Данные хранятся в `./aqmaq-data`
  - Тяжёлые файлы вне репозитория (внутри — только `.gitkeep` при необходимости)
- Не использовать `~/aqmaq` и `/mnt/d/aqmaq-data`

Содержание репозитория
- `api.py` — FastAPI: `POST /incidents` пишет строки в `aqmaq-data/db/incidents.jsonl`
- `demo_line.py` — демо-скрипт: читает `SOURCE` (RTSP/локальная камера), рисует линию `LINE_Y`, шлёт события `motion_start`/`motion_end`/`cross_line`, сохраняет кадры в `aqmaq-data/thumbs`
- `tools/mac/aqcam.sh` — на Mac поднимает MediaMTX и публикует камеру на `rtsp://<IP>:8554/cam`
- `.env.example` — пример переменных окружения
- `requirements.txt` — зависимости Python

Переменные окружения (.env)
- `SOURCE` — источник видео. Примеры: `0` (локальная камера), `rtsp://<IP>:8554/cam`
- `LINE_Y` — вертикальная позиция линии для детекции, пиксели (по умолчанию 300–360)
- `API_URL` — адрес API для записи инцидентов, по умолчанию `http://localhost:8000/incidents`
- `AQMAQ_DATA_DIR` — корень данных, по умолчанию `./aqmaq-data`
- `NO_MOTION_SECONDS` — таймаут отсутствия движения до события `motion_end`
- `OPENCV_FFMPEG_CAPTURE_OPTIONS` — форс `rtsp_transport;tcp` для RTSP (если не задано — демо задаёт автоматически при `rtsp://`)

Команды: Ubuntu (API и демо)
- Создать и активировать venv, поставить зависимости
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Подготовить конфиг
  - `cp .env.example .env` и при необходимости отредактировать `SOURCE`, `LINE_Y`, `AQMAQ_DATA_DIR`
- Запустить API
  - `uvicorn api:app --host 0.0.0.0 --port 8000 --reload`
  - Проверка: `curl http://localhost:8000/health` ожидается `{ "ok": true, ... }`
- В другом терминале запустить демо
  - `source .venv/bin/activate`
  - `python demo_line.py` или без GUI: `python demo_line.py --no-gui`
- Валидация
  - Появляются строки в `aqmaq-data/db/incidents.jsonl`
  - Миниатюры событий `cross_line` в `aqmaq-data/thumbs/*.jpg`

Команды: Mac (публикация камеры и URL RTSP)
- Переход и запуск
  - `cd tools/mac`
  - `./aqcam.sh devices` — список устройств (AVFoundation)
  - `./aqcam.sh start` — поднимает MediaMTX и публикует камеру
- Опции (env перед командой)
  - `CAM_INDEX` (номер камеры, по умолчанию 0), `SIZE` (напр. `1280x720`), `FPS` (напр. 30), `URL_PATH` (по умолчанию `cam`)
  - Пример: `CAM_INDEX=0 SIZE=1280x720 FPS=30 ./aqcam.sh start`
- RTSP-адреса
  - В выводе будут LAN и, при наличии Tailscale, TS-адрес
  - Формат: `rtsp://<IP>:8554/cam`

Привязка демо к RTSP
- На машине с `demo_line.py` создайте `.env`:
  - `SOURCE=rtsp://<IP>:8554/cam`
  - Убедитесь, что RTSP через TCP: `OPENCV_FFMPEG_CAPTURE_OPTIONS=rtsp_transport;tcp`
- Запустите API и демо как в секции «Ubuntu»

API (FastAPI)
- `GET /health` — состояние и путь к БД: `aqmaq-data/db/incidents.jsonl`
- `POST /incidents` — запись события
  - Тело: `{ "timestamp": float, "event": "motion_start|motion_end|cross_line", "y": int? }`
  - Запись формата JSONL, по одной строке на событие; добавляется поле `iso` (UTC ISO время)

Директории данных
- `aqmaq-data/db` — база событий `incidents.jsonl` (создаётся автоматически)
- `aqmaq-data/thumbs` — миниатюры событий `cross_line` (создаётся автоматически)
- Храните большие файлы вне репозитория, добавляйте `.gitkeep` при необходимости

Типичный сценарий end-to-end
- На Mac: `tools/mac/aqcam.sh start` — получите RTSP URL
- На Ubuntu:
  - Поднимите API: `uvicorn api:app --host 0.0.0.0 --port 8000 --reload`
  - В другом окне: `python demo_line.py --no-gui` (или без флага для окна)
  - Проверьте `aqmaq-data/db/incidents.jsonl` и `aqmaq-data/thumbs`

Замечания по RTSP/TCP и стабильности
- Всегда используйте TCP для RTSP: флаг ffmpeg `-rtsp_transport tcp` и/или переменная `OPENCV_FFMPEG_CAPTURE_OPTIONS=rtsp_transport;tcp`
- `demo_line.py` автоматически пытается переподключиться к RTSP до 5 раз при обрыве

Требования
- Python 3.12
- OpenCV (headless достаточно для `--no-gui`)
- requests, fastapi, uvicorn, python-dotenv
- На Mac: `mediamtx`, `ffmpeg` (и опционально `tailscale`)

Отладка и проверка
- Проверить API: `curl http://localhost:8000/health`
- Искусственно спровоцировать `cross_line`: перемещая объект через линию `LINE_Y` в кадре
- Логи ffmpeg и mediamtx на Mac: `tools/mac/ffmpeg_cam.log`, `tools/mac/mediamtx.log`

Структура команд (кратко)
- Ubuntu
  - `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
  - `uvicorn api:app --host 0.0.0.0 --port 8000 --reload`
  - `python demo_line.py [--no-gui]`
- Mac
  - `cd tools/mac && ./aqcam.sh devices|start`
  - Переменные: `CAM_INDEX`, `SIZE`, `FPS`, `URL_PATH`

Следующие шаги
- При необходимости вынести параметры в `.env`
- Добавить дополнительные эндпоинты (например, `/stats`)
- Включить сохранение клипов по событиям и/или интеграцию face‑pipeline на кадрах инцидента
