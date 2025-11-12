from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ZoneDefinition:
    """Declarative description of a product zone."""

    name: str
    x: float  # left, normalized 0-1
    y: float  # top, normalized 0-1
    width: float
    height: float

    def clamp(self) -> "ZoneDefinition":
        def _clamp(value: float) -> float:
            return min(max(value, 0.0), 1.0)

        return ZoneDefinition(
            name=self.name,
            x=_clamp(self.x),
            y=_clamp(self.y),
            width=_clamp(self.width),
            height=_clamp(self.height),
        )

    def as_pixels(self, frame_shape: tuple[int, int, int]) -> tuple[int, int, int, int]:
        h, w = frame_shape[:2]
        x1 = int(self.x * w)
        y1 = int(self.y * h)
        x2 = int(min((self.x + self.width) * w, w))
        y2 = int(min((self.y + self.height) * h, h))
        return x1, y1, x2, y2

    def extract_roi(self, frame: NDArray[np.uint8]) -> NDArray[np.uint8]:
        x1, y1, x2, y2 = self.as_pixels(frame.shape)
        return frame[y1:y2, x1:x2]


def load_zones(path: Path | None) -> List[ZoneDefinition]:
    """Load zone definitions from JSON; fallback to a default zone covering the frame."""

    if path is None or not path.exists():
        return [ZoneDefinition(name="default", x=0.25, y=0.3, width=0.5, height=0.4)]

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    zones: List[ZoneDefinition] = []
    for entry in payload:
        zone = ZoneDefinition(
            name=entry["name"],
            x=float(entry["x"]),
            y=float(entry["y"]),
            width=float(entry["width"]),
            height=float(entry["height"]),
        ).clamp()
        zones.append(zone)
    return zones
