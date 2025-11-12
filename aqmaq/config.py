from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "aqmaq-data"


class Settings(BaseModel):
    """Strongly-typed settings shared across the demo stack."""

    model_config = ConfigDict(frozen=True)

    source: str = Field(default="0", description="Video source (index/path/RTSP)")
    line_y: int = Field(default=300, ge=0, description="Horizontal line for crossing detection")
    api_url: AnyHttpUrl = Field(
        default="http://localhost:8000/incidents", description="Incident ingestion endpoint"
    )
    data_dir: Path = Field(default=_DEFAULT_DATA_DIR, description="Root directory for demo artifacts")
    no_motion_seconds: float = Field(default=5, gt=0, description="Inactivity timeout")
    opencv_ffmpeg_capture_options: str | None = Field(
        default="rtsp_transport;tcp",
        description="Options forced for OpenCV FFmpeg backend",
    )
    zone_config_path: Path | None = Field(
        default=None, description="Optional path to zone configuration JSON"
    )
    zone_model_path: Path | None = Field(
        default=None, description="Optional path to a trained zone interaction model"
    )

    @property
    def thumbs_dir(self) -> Path:
        return self.data_dir / "thumbs"

    @property
    def db_dir(self) -> Path:
        return self.data_dir / "db"

    @property
    def incidents_path(self) -> Path:
        return self.db_dir / "incidents.jsonl"

    @property
    def is_rtsp_source(self) -> bool:
        return self.source.startswith(("rtsp://", "rtsps://"))

    @property
    def faces_dir(self) -> Path:
        return self.data_dir / "faces"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once, respecting .env overrides."""

    load_dotenv()

    data_dir_raw = os.getenv("AQMAQ_DATA_DIR")
    data_dir = Path(data_dir_raw) if data_dir_raw else _DEFAULT_DATA_DIR

    zone_config_env = os.getenv("ZONE_CONFIG_PATH")
    zone_model_env = os.getenv("ZONE_MODEL_PATH")

    return Settings(
        source=os.getenv("SOURCE", "0"),
        line_y=int(os.getenv("LINE_Y", "300")),
        api_url=os.getenv("API_URL", "http://localhost:8000/incidents"),
        data_dir=data_dir,
        no_motion_seconds=float(os.getenv("NO_MOTION_SECONDS", "5")),
        opencv_ffmpeg_capture_options=os.getenv(
            "OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp"
        ),
        zone_config_path=Path(zone_config_env) if zone_config_env else None,
        zone_model_path=Path(zone_model_env) if zone_model_env else None,
    )
