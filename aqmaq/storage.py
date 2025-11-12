from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from .models import Incident


class IncidentStore(Protocol):
    """Storage protocol for persisting incidents."""

    path: Path

    def append(self, incident: Incident) -> Incident:  # pragma: no cover - protocol
        ...


class JsonlIncidentStore:
    """Simple JSONL-backed store; good enough for demos and tests."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, incident: Incident) -> Incident:
        record = incident.model_copy()
        if record.iso is None:
            record.iso = datetime.now(timezone.utc).isoformat()

        payload = record.model_dump(mode="json", exclude_none=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

        return record

