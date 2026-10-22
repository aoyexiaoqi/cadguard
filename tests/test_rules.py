from collections import Counter

import pytest

from cadguard.checker import run_checks
from cadguard.config import merged_config
from cadguard.rules import (
    check_dimension_overrides,
    check_duplicates,
    check_layers,
    check_linetypes,
    check_text_styles,
    check_title_block,
)
from conftest import make_doc

ALL_RULE_IDS = {
    "layer.nonstandard",
    "text_style.nonstandard_font",
    "linetype.nonstandard",
    "dimension.text_override",
    "geometry.duplicate",
    "title_block.missing",
}


def _section(config, name):
    return config[name]


# ---------------------------------------------------------------------------
# whole-document behaviour
# ---------------------------------------------------------------------------

def test_clean_drawing_has_no_issues(clean_doc, default_config):
    assert run_checks(clean_doc, default_config) == []


def test_demo_drawing_fires_every_rule(demo_doc, default_config):
    issues = run_checks(demo_doc, default_config)
    counts = Counter(i.rule_id for i in issues)
    assert set(counts) == ALL_RULE_IDS
    assert counts["layer.nonstandard"] == 1
    assert counts["text_style.nonstandard_font"] == 1
    assert counts["dimension.text_override"] == 1
    assert counts["geometry.duplicate"] == 1
    assert counts["title_block.missing"] == 1
    assert counts["linetype.nonstandard"] >= 1


def test_issues_carry_handle_type_and_location(demo_doc, default_config):
    issues = run_checks(demo_doc, default_config)
    layer_issue = next(i for i in issues if i.rule_id == "layer.nonstandard")
    assert layer_issue.entity_type == "LINE"
    assert layer_issue.handle
    assert layer_issue.location == (0.0, 50.0)
    assert layer_issue.severity == "error"


def test_disabled_rule_is_skipped(demo_doc):
    config = merged_config({"layers": {"enabled": False}})
    rule_ids = {i.rule_id for i in run_checks(demo_doc, config)}
    assert "layer.nonstandard" not in rule_ids
    assert "geometry.duplicate" in rule_ids


def test_severity_override(demo_doc):
    config = merged_config({"duplicate_geometry": {"severity": "error"}})
    dup = next(
        i for i in run_checks(demo_doc, config) if i.rule_id == "geometry.duplicate"
    )
    assert dup.severity == "error"


# ---------------------------------------------------------------------------
# layer rule
# ---------------------------------------------------------------------------

def test_layer_rule_flags_unknown_layer(default_config):
    doc = make_doc()
    doc.modelspace().add_line((0, 0), (1, 1), dxfattribs={"layer": "SCRATCH"})
    issues = check_layers(doc, _section(default_config, "layers"))
    assert len(issues) == 1
    assert "SCRATCH" in issues[0].message


def test_layer_rule_is_case_insensitive(default_config):
    doc = make_doc()
    doc.modelspace().add_line((0, 0), (1, 1), dxfattribs={"layer": "outline"})
    assert check_layers(doc, _section(default_config, "layers")) == []


def test_layer_rule_pattern_only_mode():
    cfg = {"severity": "error", "allowed": [], "pattern": r"^[A-Z0-9_]+$"}
    doc = make_doc()
    msp = doc.modelspace()
    msp.add_line((0, 0), (1, 1), dxfattribs={"layer": "GOOD_NAME"})
    msp.add_line((0, 0), (1, 1), dxfattribs={"layer": "bad name"})
    issues = check_layers(doc, cfg)
    assert len(issues) == 1
    assert "bad name" in issues[0].message


# ---------------------------------------------------------------------------
# text style rule
# ---------------------------------------------------------------------------

def test_text_style_rule(default_config):
    doc = make_doc()
    assert check_text_styles(doc, _section(default_config, "text_styles")) == []
    doc.styles.add("FANCY", font="papyrus.ttf")
    issues = check_text_styles(doc, _section(default_config, "text_styles"))
    assert len(issues) == 1
    assert issues[0].entity_type == "STYLE"
    assert issues[0].location is None


def test_text_style_rule_accepts_font_paths(default_config):
    doc = make_doc()
    doc.styles.add("GB", font=r"C:\fonts\simhei.ttf")
    assert check_text_styles(doc, _section(default_config, "text_styles")) == []


# ---------------------------------------------------------------------------
# linetype rule
# ---------------------------------------------------------------------------

def test_linetype_rule_clean_by_default(default_config):
    doc = make_doc()
    doc.modelspace().add_line((0, 0), (1, 1), dxfattribs={"layer": "OUTLINE"})
    assert check_linetypes(doc, _section(default_config, "linetypes")) == []


def test_linetype_rule_flags_loaded_and_used(default_config):
    doc = make_doc()
    doc.linetypes.add("MYLINE", pattern=[0.6, 0.4, -0.2])
    doc.modelspace().add_line(
        (0, 0), (1, 1), dxfattribs={"layer": "OUTLINE", "linetype": "MYLINE"}
    )
    issues = check_linetypes(doc, _section(default_config, "linetypes"))
    assert len(issues) == 2  # table definition + entity usage
    assert all(i.rule_id == "linetype.nonstandard" for i in issues)


def test_linetype_rule_flags_layer_assignment(default_config):
    doc = make_doc()
    doc.linetypes.add("MYLINE", pattern=[0.6, 0.4, -0.2])
    doc.layers.get("OUTLINE").dxf.linetype = "MYLINE"
    issues = check_linetypes(doc, _section(default_config, "linetypes"))
    assert any(i.entity_type == "LAYER" for i in issues)


# ---------------------------------------------------------------------------
# dimension override rule
# ---------------------------------------------------------------------------

def _add_dimension(doc, text=None):
    msp = doc.modelspace()
    dim = msp.add_linear_dim(base=(0, 15), p1=(0, 0), p2=(10, 0),
                             dxfattribs={"layer": "DIM"})
    dim.render()
    entity = list(msp.query("DIMENSION"))[-1]
    if text is not None:
        entity.dxf.text = text
    return entity


def test_dimension_measured_text_is_silent(default_config):
    doc = make_doc()
    _add_dimension(doc)  # default text is "<>"
    assert check_dimension_overrides(
        doc, _section(default_config, "dimension_text_override")
    ) == []


def test_dimension_manual_override_fires(default_config):
    doc = make_doc()
    _add_dimension(doc, text="999")
    issues = check_dimension_overrides(
        doc, _section(default_config, "dimension_text_override")
    )
    assert len(issues) == 1
    assert "999" in issues[0].message
    assert "measured value" in issues[0].message


def test_dimension_formatted_override_fires(default_config):
    doc = make_doc()
    _add_dimension(doc, text="<> mm")
    issues = check_dimension_overrides(
        doc, _section(default_config, "dimension_text_override")
    )
    assert len(issues) == 1
    assert "extra text" in issues[0].message


# ---------------------------------------------------------------------------
# duplicate geometry rule
# ---------------------------------------------------------------------------

def test_duplicate_lines_fire_once_per_extra_copy(default_config):
    doc = make_doc()
    msp = doc.modelspace()
    for _ in range(3):
        msp.add_line((0, 0), (10, 0), dxfattribs={"layer": "OUTLINE"})
    msp.add_line((0, 5), (10, 5), dxfattribs={"layer": "OUTLINE"})
    issues = check_duplicates(doc, _section(default_config, "duplicate_geometry"))
    assert len(issues) == 2


def test_duplicate_line_reversed_endpoints(default_config):
    doc = make_doc()
    msp = doc.modelspace()
    msp.add_line((0, 0), (10, 0), dxfattribs={"layer": "OUTLINE"})
    msp.add_line((10, 0), (0, 0), dxfattribs={"layer": "OUTLINE"})
    assert len(check_duplicates(doc, _section(default_config, "duplicate_geometry"))) == 1


def test_distinct_geometry_is_silent(default_config):
    doc = make_doc()
    msp = doc.modelspace()
    msp.add_circle((0, 0), 5, dxfattribs={"layer": "OUTLINE"})
    msp.add_circle((0, 0), 6, dxfattribs={"layer": "OUTLINE"})
    assert check_duplicates(doc, _section(default_config, "duplicate_geometry")) == []


def test_duplicate_other_entity_kinds(default_config):
    doc = make_doc()
    msp = doc.modelspace()
    for _ in range(2):
        msp.add_lwpolyline(
            [(0, 0), (5, 0), (5, 5)], dxfattribs={"layer": "OUTLINE"}
        )
        msp.add_arc((0, 0), 5, 0, 90, dxfattribs={"layer": "OUTLINE"})
        msp.add_point((7, 7), dxfattribs={"layer": "OUTLINE"})
        msp.add_text("NOTE", dxfattribs={"layer": "TEXT"}).set_placement((1, 1))
    issues = check_duplicates(doc, _section(default_config, "duplicate_geometry"))
    assert len(issues) == 4  # one extra copy per kind


def test_duplicate_circles_and_inserts(default_config):
    doc = make_doc()
    msp = doc.modelspace()
    msp.add_circle((3, 3), 5, dxfattribs={"layer": "OUTLINE"})
    msp.add_circle((3, 3), 5, dxfattribs={"layer": "OUTLINE"})
    doc.blocks.new(name="BOLT")
    msp.add_blockref("BOLT", (1, 1), dxfattribs={"layer": "OUTLINE"})
    msp.add_blockref("BOLT", (1, 1), dxfattribs={"layer": "OUTLINE"})
    issues = check_duplicates(doc, _section(default_config, "duplicate_geometry"))
    assert len(issues) == 2


# ---------------------------------------------------------------------------
# title block rule
# ---------------------------------------------------------------------------

def test_title_block_missing_fires(default_config):
    doc = make_doc()
    issues = check_title_block(doc, _section(default_config, "title_block"))
    assert len(issues) == 1
    assert issues[0].rule_id == "title_block.missing"


def test_title_block_blockref_satisfies(default_config):
    doc = make_doc()
    doc.blocks.new(name="TITLE_BLOCK")
    doc.modelspace().add_blockref("TITLE_BLOCK", (0, 0))
    assert check_title_block(doc, _section(default_config, "title_block")) == []


def test_title_block_text_marker_satisfies(default_config):
    doc = make_doc()
    doc.modelspace().add_text(
        "图号 A-001", dxfattribs={"layer": "TEXT"}
    ).set_placement((0, 0))
    assert check_title_block(doc, _section(default_config, "title_block")) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
