"""Rules configuration: built-in defaults plus YAML/JSON overrides.

The configuration is a mapping of rule sections.  Every section accepts:

- ``enabled``  — turn the rule off without deleting its configuration
- ``severity`` — one of ``error`` / ``warning`` / ``info``

plus rule-specific keys documented in ``docs/rules.md``.  A user file only
needs to contain the sections/keys it overrides; everything else falls back
to :data:`DEFAULT_CONFIG`.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .models import SEVERITIES

DEFAULT_CONFIG: Dict[str, Dict[str, Any]] = {
    "layers": {
        "enabled": True,
        "severity": "error",
        # Standard layer names (compared case-insensitively).  When this
        # list is empty, only the naming pattern below is enforced.
        "allowed": [
            "0",
            "OUTLINE",
            "CENTER",
            "CENTERLINE",
            "HIDDEN",
            "DIM",
            "TEXT",
            "TITLE",
            "FRAME",
            "BORDER",
            "HATCH",
        ],
        # Layer names must also match this regular expression when the
        # whitelist is empty; with a whitelist it is reported as a hint.
        "pattern": r"^[A-Za-z0-9_\-]+$",
    },
    "text_styles": {
        "enabled": True,
        "severity": "warning",
        # Font file names (compared case-insensitively, basename only).
        "allowed_fonts": [
            "txt",
            "txt.shx",
            "romans.shx",
            "simplex.shx",
            "isocp.shx",
            "gbenor.shx",
            "gbeitc.shx",
            "simhei.ttf",
            "simsun.ttc",
            "simfang.ttf",
            "arial.ttf",
        ],
    },
    "linetypes": {
        "enabled": True,
        "severity": "warning",
        # ByLayer / ByBlock / Continuous are always allowed.
        "allowed": [
            "CENTER",
            "CENTER2",
            "CENTERX2",
            "HIDDEN",
            "HIDDEN2",
            "HIDDENX2",
            "DASHED",
            "DASHDOT",
            "DOT",
            "PHANTOM",
            "BORDER",
        ],
    },
    "dimension_text_override": {
        "enabled": True,
        "severity": "error",
    },
    "duplicate_geometry": {
        "enabled": True,
        "severity": "warning",
        # Coordinates are rounded to this many decimals before comparison.
        "precision": 6,
    },
    "title_block": {
        "enabled": True,
        "severity": "error",
        # A title block counts as present when a block reference with one of
        # these names exists, or a TEXT/MTEXT contains one of the markers.
        "block_names": ["TITLE_BLOCK", "TITLEBLOCK", "TITLE", "GB_TITLE", "A3_TITLE"],
        "text_markers": ["图号", "DWG NO", "DWG.NO", "图名"],
    },
}


def _validate(cfg: Dict[str, Any]) -> None:
    for section, values in cfg.items():
        if not isinstance(values, dict):
            raise ValueError("config section %r must be a mapping" % section)
        severity = values.get("severity")
        if severity is not None and severity not in SEVERITIES:
            raise ValueError(
                "invalid severity %r in section %r (expected one of %s)"
                % (severity, section, ", ".join(SEVERITIES))
            )


def merged_config(user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return the defaults deep-merged with a user-supplied mapping."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    if user:
        for section, values in user.items():
            if isinstance(values, dict) and isinstance(cfg.get(section), dict):
                cfg[section].update(values)
            else:
                cfg[section] = values
    _validate(cfg)
    return cfg


def load_config(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load rules configuration from a YAML or JSON file (or defaults)."""
    if path is None:
        return merged_config()
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        import yaml

        data = yaml.safe_load(text)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("rules config must be a mapping of rule sections")
    return merged_config(data)
