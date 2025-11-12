from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class ZoneClassifier:
    """Wraps an optional ML model to estimate interaction probability per zone."""

    def __init__(
        self,
        model_path: Path | None,
        input_size: Tuple[int, int] = (224, 224),
        threshold: float = 0.6,
    ):
        self.model_path = model_path
        self.input_size = input_size
        self.threshold = threshold
        self._interpreter = None
        self._input_details = None
        self._output_details = None

        if model_path and model_path.exists():
            try:
                from tensorflow import lite as tflite  # type: ignore

                self._interpreter = tflite.Interpreter(model_path=str(model_path))
                self._interpreter.allocate_tensors()
                self._input_details = self._interpreter.get_input_details()
                self._output_details = self._interpreter.get_output_details()
                logger.info("Loaded TFLite model from %s", model_path)
            except Exception as exc:  # pragma: no cover - optional dependency
                logger.warning("Failed to load TFLite model %s: %s", model_path, exc)

    def predict_proba(self, roi: NDArray[np.uint8]) -> float:
        if roi.size == 0:
            return 0.0

        if self._interpreter is None:
            return self._heuristic_score(roi)

        resized = cv2.resize(roi, self.input_size)
        tensor = resized.astype(np.float32) / 255.0
        tensor = np.expand_dims(tensor, axis=0)

        self._interpreter.set_tensor(self._input_details[0]["index"], tensor)
        self._interpreter.invoke()
        output = self._interpreter.get_tensor(self._output_details[0]["index"])
        return float(output.flatten()[0])

    def _heuristic_score(self, roi: NDArray[np.uint8]) -> float:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        norm = np.sum(edges) / (edges.size * 255.0)
        return float(norm)
