"""Data model for a single check finding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

SEVERITIES = ("error", "warning", "info")


@dataclass
class Issue:
    """One rule violation found in a drawing.

    ``location`` is an ``(x, y)`` pair in drawing units when the finding is
    tied to a graphical entity; table-level findings (text styles, linetype
    definitions) have no location.
    """

    rule_id: str
    severity: str
    message: str
    handle: Optional[str] = None
    entity_type: Optional[str] = None
    location: Optional[Tuple[float, float]] = None

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "handle": self.handle,
            "entity_type": self.entity_type,
            "location": list(self.location) if self.location is not None else None,
        }
