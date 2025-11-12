from __future__ import annotations

import argparse
import logging
import os

from aqmaq import Settings, get_settings
from aqmaq.services import IncidentPublisher, ThumbnailWriter
from aqmaq.vision import LineDemoRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Aqmaq line-crossing demo")
    parser.add_argument("--no-gui", action="store_true", help="Disable OpenCV window output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    settings = get_settings()
    _configure_rtsp_transport(settings)

    settings.data_dir.mkdir(parents=True, exist_ok=True)

    publisher = IncidentPublisher(settings.api_url)
    thumbnails = ThumbnailWriter(settings.thumbs_dir)
    runner = LineDemoRunner(settings, publisher, thumbnails)
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
