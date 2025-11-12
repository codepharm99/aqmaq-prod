from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from aqmaq import Settings, get_settings
from aqmaq.services import FaceCaptureService, IncidentPublisher, ZoneClassifier
from aqmaq.vision import ZoneRunner
from aqmaq.zones import load_zones


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Aqmaq zone interaction demo")
    parser.add_argument("--no-gui", action="store_true", help="Disable OpenCV window output")
    parser.add_argument("--zones", type=str, default=None, help="Path to zone config JSON")
    parser.add_argument("--model", type=str, default=None, help="Path to TFLite interaction model")
    parser.add_argument(
        "--threshold", type=float, default=0.6, help="Probability threshold for activation"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    settings = get_settings()
    _configure_rtsp_transport(settings)

    zone_path = args.zones or (str(settings.zone_config_path) if settings.zone_config_path else None)
    model_path = args.model or (str(settings.zone_model_path) if settings.zone_model_path else None)

    zone_config = Path(zone_path) if zone_path else settings.zone_config_path
    zones = load_zones(zone_config)

    resolved_model = Path(model_path) if model_path else settings.zone_model_path

    publisher = IncidentPublisher(settings.api_url)
    classifier = ZoneClassifier(resolved_model, threshold=args.threshold)
    face_capture = FaceCaptureService(settings.faces_dir)
    runner = ZoneRunner(
        settings=settings,
        zones=zones,
        classifier=classifier,
        face_capture=face_capture,
        publisher=publisher,
        activation_threshold=args.threshold,
    )
    runner.run(no_gui=args.no_gui)


def _configure_rtsp_transport(settings: Settings) -> None:
    if not settings.is_rtsp_source:
        return

    if settings.opencv_ffmpeg_capture_options:
        os.environ.setdefault(
            "OPENCV_FFMPEG_CAPTURE_OPTIONS", settings.opencv_ffmpeg_capture_options
        )
    logging.info(
        "OPENCV_FFMPEG_CAPTURE_OPTIONS=%s",
        os.getenv("OPENCV_FFMPEG_CAPTURE_OPTIONS", "<not-set>"),
    )


if __name__ == "__main__":
    main()
