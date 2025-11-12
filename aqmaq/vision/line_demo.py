from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import cv2
import numpy as np
from numpy.typing import NDArray

from ..config import Settings
from ..models import Incident
from ..services import IncidentPublisher, ThumbnailWriter

logger = logging.getLogger(__name__)


@dataclass
class MotionState:
    presence: bool = False
    last_motion_ts: float = field(default_factory=lambda: time.time())


class LineDemoRunner:
    """Encapsulates the classic line-crossing demo flow."""

    def __init__(
        self,
        settings: Settings,
        publisher: IncidentPublisher,
        thumbnail_writer: ThumbnailWriter,
        area_threshold: int = 500,
        line_tolerance: int = 5,
    ):
        self.settings = settings
        self.publisher = publisher
        self.thumbnail_writer = thumbnail_writer
        self.area_threshold = area_threshold
        self.line_tolerance = line_tolerance
        self._background = cv2.createBackgroundSubtractorMOG2()

    def run(self, *, no_gui: bool) -> None:
        logger.info(
            "Starting demo_line: source=%s line_y=%s no_gui=%s",
            self.settings.source,
            self.settings.line_y,
            no_gui,
        )
        logger.info("DATA_DIR=%s", self.settings.data_dir)

        cap = self._open_capture()
        state = MotionState()
        reopen_attempts = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    if self._should_retry_rtsp(reopen_attempts):
                        reopen_attempts += 1
                        logger.warning("Read failed. Re-opening RTSP (%s/5)...", reopen_attempts)
                        cap.release()
                        time.sleep(0.5)
                        cap = self._open_capture()
                        continue
                    logger.info("Video ended or camera disconnected.")
                    break

                reopen_attempts = 0
                motion_detected = self._process_frame(frame)
                self._update_presence(state, motion_detected)

                if not no_gui:
                    if not self._render_gui(frame):
                        logger.info("ESC pressed. Stopping demo loop.")
                        break
        finally:
            cap.release()
            if not no_gui:
                cv2.destroyAllWindows()
            logger.info("Finished demo run.")

    def _open_capture(self) -> cv2.VideoCapture:
        source = self.settings.source
        if source == "0":
            return cv2.VideoCapture(0)
        if self.settings.is_rtsp_source:
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return cap
        return cv2.VideoCapture(source)

    def _should_retry_rtsp(self, attempts: int) -> bool:
        return self.settings.is_rtsp_source and attempts < 5

    def _process_frame(self, frame: NDArray[np.uint8]) -> bool:
        mask = self._background.apply(frame)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h <= self.area_threshold:
                continue

            motion_detected = True
            cy = y + h // 2
            if abs(cy - self.settings.line_y) <= self.line_tolerance:
                self._handle_cross_line(frame, cy)

        return motion_detected

    def _handle_cross_line(self, frame: NDArray[np.uint8], y: int) -> None:
        timestamp = time.time()
        incident = Incident(timestamp=timestamp, event="cross_line", y=y)
        self.publisher.publish(incident)
        self.thumbnail_writer.persist(timestamp, frame)

    def _update_presence(self, state: MotionState, motion_detected: bool) -> None:
        now = time.time()
        if motion_detected:
            state.last_motion_ts = now
            if not state.presence:
                state.presence = True
                self.publisher.publish(Incident(timestamp=now, event="motion_start"))
        else:
            if state.presence and (now - state.last_motion_ts) > self.settings.no_motion_seconds:
                state.presence = False
                self.publisher.publish(Incident(timestamp=now, event="motion_end"))

    def _render_gui(self, frame: NDArray[np.uint8]) -> bool:
        cv2.line(frame, (0, self.settings.line_y), (frame.shape[1], self.settings.line_y), (0, 0, 255), 2)
        cv2.imshow("Line Demo", frame)
        return not (cv2.waitKey(1) & 0xFF == 27)
