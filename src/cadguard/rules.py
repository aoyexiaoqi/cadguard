"""Individual drawing rules.

Every rule is a function ``(doc, section_config) -> list[Issue]`` where
``doc`` is an ezdxf document.  Rule ids are stable and used in reports:

- ``layer.nonstandard``
- ``text_style.nonstandard_font``
- ``linetype.nonstandard``
- ``dimension.text_override``
- ``geometry.duplicate``
- ``title_block.missing``
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from .models import Issue

# Linetypes that are always acceptable regardless of configuration.
_IMPLICIT_LINETYPES = {"BYLAYER", "BYBLOCK", "CONTINUOUS"}


def entity_location(entity) -> Optional[Tuple[float, float]]:
    """Best-effort (x, y) location of a graphical entity."""
    dxf = entity.dxf
    for attr in ("insert", "start", "center", "defpoint", "location"):
        try:
            value = getattr(dxf, attr)
        except Exception:
            continue
        if value is not None:
            try:
                return (round(float(value[0]), 3), round(float(value[1]), 3))
            except Exception:
                continue
    return None


def _issue(rule_id, severity, message, entity=None, handle=None, entity_type=None):
    if entity is not None:
        return Issue(
            rule_id=rule_id,
            severity=severity,
            message=message,
            handle=entity.dxf.handle,
            entity_type=entity.dxftype(),
            location=entity_location(entity),
        )
    return Issue(
        rule_id=rule_id,
        severity=severity,
        message=message,
        handle=handle,
        entity_type=entity_type,
    )


# ---------------------------------------------------------------------------
# 1. Layer check
# ---------------------------------------------------------------------------

def check_layers(doc, cfg: Dict[str, Any]) -> List[Issue]:
    severity = cfg.get("severity", "error")
    allowed = {str(name).upper() for name in cfg.get("allowed", [])}
    pattern = cfg.get("pattern")
    regex = re.compile(pattern) if pattern else None
    issues = []
    for entity in doc.modelspace():
        layer = str(entity.dxf.layer or "0")
        if allowed:
            if layer.upper() in allowed:
                continue
            message = "entity on non-standard layer %r" % layer
            if regex is not None and not regex.match(layer):
                message += " (also violates layer naming pattern)"
            issues.append(_issue("layer.nonstandard", severity, message, entity))
        elif regex is not None and not regex.match(layer):
            issues.append(
                _issue(
                    "layer.nonstandard",
                    severity,
                    "layer name %r violates naming pattern %r" % (layer, pattern),
                    entity,
                )
            )
    return issues


# ---------------------------------------------------------------------------
# 2. Text style / font check
# ---------------------------------------------------------------------------

def check_text_styles(doc, cfg: Dict[str, Any]) -> List[Issue]:
    severity = cfg.get("severity", "warning")
    allowed = {str(f).lower() for f in cfg.get("allowed_fonts", [])}
    issues = []
    for style in doc.styles:
        font = str(style.dxf.font or "").strip()
        if not font:
            continue
        basename = font.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if basename not in allowed:
            issues.append(
                Issue(
                    rule_id="text_style.nonstandard_font",
                    severity=severity,
                    message="text style %r uses non-standard font %r"
                    % (style.dxf.name, font),
                    handle=style.dxf.handle,
                    entity_type="STYLE",
                )
            )
    return issues


# ---------------------------------------------------------------------------
# 3. Linetype check
# ---------------------------------------------------------------------------

def check_linetypes(doc, cfg: Dict[str, Any]) -> List[Issue]:
    severity = cfg.get("severity", "warning")
    allowed = {str(n).upper() for n in cfg.get("allowed", [])} | _IMPLICIT_LINETYPES
    issues = []

    def bad(name: str) -> bool:
        return bool(name) and name.upper() not in allowed

    for linetype in doc.linetypes:
        name = str(linetype.dxf.name)
        if bad(name):
            issues.append(
                Issue(
                    rule_id="linetype.nonstandard",
                    severity=severity,
                    message="non-standard linetype %r is loaded in the drawing" % name,
                    handle=linetype.dxf.handle,
                    entity_type="LTYPE",
                )
            )
    for layer in doc.layers:
        name = str(layer.dxf.linetype or "")
        if bad(name):
            issues.append(
                Issue(
                    rule_id="linetype.nonstandard",
                    severity=severity,
                    message="layer %r uses non-standard linetype %r"
                    % (layer.dxf.name, name),
                    handle=layer.dxf.handle,
                    entity_type="LAYER",
                )
            )
    for entity in doc.modelspace():
        try:
            name = str(entity.dxf.linetype or "")
        except Exception:
            continue
        if bad(name):
            issues.append(
                _issue(
                    "linetype.nonstandard",
                    severity,
                    "entity uses non-standard linetype %r" % name,
                    entity,
                )
            )
    return issues


# ---------------------------------------------------------------------------
# 4. Dimension text override
# ---------------------------------------------------------------------------

def check_dimension_overrides(doc, cfg: Dict[str, Any]) -> List[Issue]:
    severity = cfg.get("severity", "error")
    issues = []
    for dim in doc.modelspace().query("DIMENSION"):
        text = str(dim.dxf.text or "").strip()
        if text in ("", "<>"):
            continue  # measured value is displayed
        measured = None
        try:
            measured = dim.get_measurement()
        except Exception:
            measured = None
        if "<>" in text:
            message = (
                "dimension text is formatted with extra text %r "
                "instead of the plain measured value" % text
            )
        else:
            message = "dimension text manually overridden to %r" % text
        if measured is not None:
            message += " (measured value: %.3f)" % float(measured)
        issues.append(_issue("dimension.text_override", severity, message, dim))
    return issues


# ---------------------------------------------------------------------------
# 5. Duplicate geometry
# ---------------------------------------------------------------------------

def _point(value, nd: int) -> Tuple[float, float, float]:
    return (
        round(float(value[0]), nd),
        round(float(value[1]), nd),
        round(float(value[2]), nd) if len(value) > 2 else 0.0,
    )


def _geometry_signature(entity, nd: int):
    """A hashable signature of (type, geometry) or None if unsupported."""
    dxf = entity.dxf
    etype = entity.dxftype()
    try:
        if etype == "LINE":
            return (etype, tuple(sorted([_point(dxf.start, nd), _point(dxf.end, nd)])))
        if etype == "CIRCLE":
            return (etype, _point(dxf.center, nd), round(float(dxf.radius), nd))
        if etype == "ARC":
            return (
                etype,
                _point(dxf.center, nd),
                round(float(dxf.radius), nd),
                round(float(dxf.start_angle), nd),
                round(float(dxf.end_angle), nd),
            )
        if etype == "POINT":
            return (etype, _point(dxf.location, nd))
        if etype == "LWPOLYLINE":
            points = tuple(
                (round(float(p[0]), nd), round(float(p[1]), nd))
                for p in entity.get_points("xy")
            )
            return (etype, points, bool(entity.closed))
        if etype == "POLYLINE":
            points = tuple(_point(v.dxf.location, nd) for v in entity.vertices)
            return (etype, points, bool(entity.is_closed))
        if etype == "INSERT":
            return (
                etype,
                str(dxf.name),
                _point(dxf.insert, nd),
                round(float(dxf.rotation or 0.0), nd),
                round(float(dxf.xscale or 1.0), nd),
                round(float(dxf.yscale or 1.0), nd),
            )
        if etype == "TEXT":
            return (etype, _point(dxf.insert, nd), str(dxf.text))
        if etype == "MTEXT":
            return (etype, _point(dxf.insert, nd), str(entity.text))
    except Exception:
        return None
    return None


def check_duplicates(doc, cfg: Dict[str, Any]) -> List[Issue]:
    severity = cfg.get("severity", "warning")
    nd = int(cfg.get("precision", 6))
    seen: Dict[Any, Any] = {}
    issues = []
    for entity in doc.modelspace():
        signature = _geometry_signature(entity, nd)
        if signature is None:
            continue
        first = seen.get(signature)
        if first is None:
            seen[signature] = entity
        else:
            issues.append(
                _issue(
                    "geometry.duplicate",
                    severity,
                    "duplicate of %s entity %s with identical geometry"
                    % (entity.dxftype(), first.dxf.handle),
                    entity,
                )
            )
    return issues


# ---------------------------------------------------------------------------
# 6. Title block presence
# ---------------------------------------------------------------------------

def check_title_block(doc, cfg: Dict[str, Any]) -> List[Issue]:
    severity = cfg.get("severity", "error")
    block_names = {str(n).upper() for n in cfg.get("block_names", [])}
    markers = [str(m) for m in cfg.get("text_markers", [])]

    def layout_has_title_block(layout) -> bool:
        for insert in layout.query("INSERT"):
            if str(insert.dxf.name).upper() in block_names:
                return True
        for etype in ("TEXT", "MTEXT"):
            for entity in layout.query(etype):
                content = str(entity.dxf.text) if etype == "TEXT" else str(entity.text)
                if any(marker in content for marker in markers):
                    return True
        return False

    for layout in doc.layouts:
        if layout_has_title_block(layout):
            return []
    return [
        Issue(
            rule_id="title_block.missing",
            severity=severity,
            message=(
                "no title block found (expected a block reference named one of "
                "%s or a text containing one of %s)"
                % (sorted(block_names), markers)
            ),
        )
    ]


RULES = {
    "layers": check_layers,
    "text_styles": check_text_styles,
    "linetypes": check_linetypes,
    "dimension_text_override": check_dimension_overrides,
    "duplicate_geometry": check_duplicates,
    "title_block": check_title_block,
}
