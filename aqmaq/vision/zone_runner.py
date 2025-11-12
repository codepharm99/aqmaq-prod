from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List

import cv2
import numpy as np
from numpy.typing import NDArray

from ..config import Settings
from ..models import Incident
from ..services import FaceCaptureService, IncidentPublisher, ZoneClassifier
from ..zones import ZoneDefinition

logger = logging.getLogger(__name__)


@dataclass
class ZoneState:
    active: bool = False
    last_active_ts: float = field(default_factory=lambda: time.time())
    score: float = 0.0


class ZoneRunner:
    """Runs the zone interaction demo pipeline."""

    def __init__(
        self,
        settings: Settings,
        zones: List[ZoneDefinition],
        classifier: ZoneClassifier,
        face_capture: FaceCaptureService,
        publisher: IncidentPublisher,
        activation_threshold: float = 0.6,
        cooldown_seconds: float = 2.0,
    ):
        self.settings = settings
        self.zones = zones
        self.classifier = classifier
        self.face_capture = face_capture
        self.publisher = publisher
        self.activation_threshold = activation_threshold
        self.cooldown_seconds = cooldown_seconds
        self._cap = None
        self._states: Dict[str, ZoneState] = {zone.name: ZoneState() for zone in zones}

    def run(self, *, no_gui: bool) -> None:
        logger.info(
            "Starting zone demo: source=%s zones=%s", self.settings.source, [z.name for z in self.zones]
        )
        self._cap = self._open_capture()

        try:
            while True:
                ret, frame = self._cap.read()
                if not ret:
                    if self.settings.is_rtsp_source:
                        logger.warning("Frame read failed, retrying RTSP...")
                        time.sleep(0.5)
                        self._cap.release()
                        self._cap = self._open_capture()
                        continue
                    break

                self._process_frame(frame)
                if not no_gui:
                    if not self._render_gui(frame):
                        logger.info("ESC pressed, stopping zone demo.")
                        break
        finally:
            if self._cap is not None:
                self._cap.release()
            if not no_gui:
                cv2.destroyAllWindows()
            logger.info("Zone demo finished.")

    def _open_capture(self) -> cv2.VideoCapture:
        if self.settings.source == "0":
            return cv2.VideoCapture(0)
        if self.settings.is_rtsp_source:
            cap = cv2.VideoCapture(self.settings.source, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return cap
        return cv2.VideoCapture(self.settings.source)

    def _process_frame(self, frame: NDArray[np.uint8]) -> None:
        now = time.time()
        for zone in self.zones:
            state = self._states[zone.name]
            roi = zone.extract_roi(frame)
            score = self.classifier.predict_proba(roi)
            state.score = score

            if score >= self.activation_threshold:
                state.last_active_ts = now
                if not state.active:
                    state.active = True
                    self._emit_interaction_event("interaction_start", zone.name, score)
                    self._capture_faces(frame, zone.name)
            else:
                if state.active and (now - state.last_active_ts) > self.cooldown_seconds:
                    state.active = False
                    self._emit_interaction_event("interaction_end", zone.name, score)

    def _emit_interaction_event(self, event: str, zone: str, score: float) -> None:
        incident = Incident(
            timestamp=time.time(),
            event=event,  # type: ignore[arg-type]
            zone=zone,
            metadata={"score": score},
        )
        self.publisher.publish(incident)

    def _capture_faces(self, frame: NDArray[np.uint8], zone: str) -> None:
        faces = self.face_capture.capture(frame, zone)
        for path in faces:
            incident = Incident(
                timestamp=time.time(),
                event="face_capture",
                zone=zone,
                metadata={"path": str(path)},
            )
            self.publisher.publish(incident)

    def _render_gui(self, frame: NDArray[np.uint8]) -> bool:
        overlay = frame.copy()
        for zone in self.zones:
            x1, y1, x2, y2 = zone.as_pixels(frame.shape)
            state = self._states[zone.name]
            color = (0, 200, 0) if state.active else (0, 0, 200)
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
            label = f"{zone.name}: {state.score:.2f}"
            cv2.putText(
                overlay,
                label,
                (x1 + 5, y1 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
                cv2.LINE_AA,
            )

        cv2.imshow("Zone Demo", overlay)
        return not (cv2.waitKey(1) & 0xFF == 27)
