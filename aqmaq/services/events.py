from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from numpy.typing import NDArray
import requests

from ..models import Incident

logger = logging.getLogger(__name__)


class IncidentPublisher:
    """HTTP client responsible for pushing incidents into the API."""

    def __init__(self, endpoint: str, timeout: float = 1.0, session: Optional[requests.Session] = None):
        self.endpoint = endpoint
        self.timeout = timeout
        self._session = session or requests.Session()

    def publish(self, incident: Incident) -> None:
        payload = incident.model_dump(exclude_none=True)
        try:
            response = self._session.post(self.endpoint, json=payload, timeout=self.timeout)
            response.raise_for_status()
            logger.info("[EVENT] %s", payload)
        except Exception as exc:  # pragma: no cover - network side effects
            logger.warning("Failed to publish incident to %s: %s", self.endpoint, exc)


class ThumbnailWriter:
    """Utility responsible for persisting thumbnails for cross-line events."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def persist(self, timestamp: float, frame: NDArray[np.uint8]) -> Path:
        filename = f"event_{int(timestamp)}.jpg"
        target = self.directory / filename
        success = cv2.imwrite(str(target), frame)
        if not success:
            logger.warning("Failed to write thumbnail %s", target)
        else:
            logger.info("[THUMB] %s", target)
        return target

