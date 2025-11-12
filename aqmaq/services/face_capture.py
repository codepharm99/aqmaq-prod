from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import List

import cv2
import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class FaceCaptureService:
    """Detects faces in frames and persists crops for auditing."""

    def __init__(self, output_dir: Path, cascade_path: str | None = None):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        cascade = cascade_path or (cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.detector = cv2.CascadeClassifier(cascade)
        if self.detector.empty():
            raise RuntimeError(f"Failed to load face cascade at {cascade}")

    def capture(self, frame: NDArray[np.uint8], zone: str) -> List[Path]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(80, 80))

        saved: List[Path] = []
        timestamp = int(time.time())
        for idx, (x, y, w, h) in enumerate(faces):
            crop = frame[y : y + h, x : x + w]
            filename = f"face_{zone}_{timestamp}_{idx}.jpg"
            target = self.output_dir / filename
            if cv2.imwrite(str(target), crop):
                saved.append(target)
                logger.info("[FACE] %s", target)
            else:
                logger.warning("Failed to save face crop %s", target)
        return saved
