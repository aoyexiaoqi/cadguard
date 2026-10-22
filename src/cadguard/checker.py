"""Check orchestration: run all enabled rules over a DXF document."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import ezdxf

from .config import merged_config
from .models import Issue
from .rules import RULES


def run_checks(doc, config: Optional[Dict[str, Any]] = None) -> List[Issue]:
    """Run every enabled rule against an ezdxf document."""
    cfg = merged_config(config)
    issues: List[Issue] = []
    for section, rule in RULES.items():
        section_cfg = cfg.get(section) or {}
        if not section_cfg.get("enabled", True):
            continue
        issues.extend(rule(doc, section_cfg))
    issues.sort(key=lambda i: (i.rule_id, i.handle or "", i.message))
    return issues


def check_document(doc, config: Optional[Dict[str, Any]] = None):
    """Run checks and return a :class:`~cadguard.report.CheckReport`."""
    from .report import CheckReport

    return CheckReport(source="<document>", issues=run_checks(doc, config))


def check_file(path: Union[str, Path], config: Optional[Dict[str, Any]] = None):
    """Read a DXF file from disk and return a CheckReport for it."""
    from .report import CheckReport

    doc = ezdxf.readfile(str(path))
    report = check_document(doc, config)
    report.source = str(path)
    return report
