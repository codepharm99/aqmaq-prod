from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


EventName = Literal[
    "motion_start",
    "motion_end",
    "cross_line",
    "interaction_start",
    "interaction_end",
    "face_capture",
]


class Incident(BaseModel):
    """Canonical representation of an incident within the demo domain."""

    timestamp: float = Field(ge=0)
    event: EventName
    y: int | None = None
    zone: str | None = None
    metadata: dict[str, Any] | None = None
    iso: str | None = None
