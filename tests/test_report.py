import json

from cadguard.checker import check_document, check_file
from cadguard.models import Issue
from cadguard.report import CheckReport, write_report


def test_check_document_and_counts(demo_doc, default_config):
    report = check_document(demo_doc, default_config)
    assert report.total >= 7
    sev = report.count_by_severity()
    assert sev["error"] >= 3  # layer, dimension override, title block
    assert report.error_count == sev["error"]
    assert report.count_by_rule()["geometry.duplicate"] == 1


def test_check_file_sets_source(demo_path, default_config):
    report = check_file(demo_path, default_config)
    assert report.source == str(demo_path)


def test_markdown_report_contents(demo_doc, default_config):
    report = check_document(demo_doc, default_config)
    md = report.to_markdown()
    assert "CADGuard" in md
    assert "dimension.text_override" in md
    assert "layer.nonstandard" in md
    assert "999" in md


def test_json_report_roundtrip(demo_doc, default_config):
    report = check_document(demo_doc, default_config)
    data = json.loads(report.to_json())
    assert data["summary"]["total"] == report.total
    assert data["summary"]["by_rule"]["title_block.missing"] == 1
    issue = next(i for i in data["issues"] if i["rule_id"] == "layer.nonstandard")
    assert issue["entity_type"] == "LINE"
    assert issue["location"] == [0.0, 50.0]
    assert issue["handle"]


def test_empty_report_renders():
    report = CheckReport(source="empty.dxf", issues=[])
    assert report.total == 0
    assert "No issues found" in report.to_markdown()
    assert json.loads(report.to_json())["issues"] == []


def test_write_report_infers_format(tmp_path, demo_doc, default_config):
    report = check_document(demo_doc, default_config)
    md_path = tmp_path / "r.md"
    json_path = tmp_path / "r.json"
    assert write_report(report, md_path) == "md"
    assert write_report(report, json_path) == "json"
    assert json.loads(json_path.read_text(encoding="utf-8"))["summary"]["total"] == report.total
    assert "CADGuard" in md_path.read_text(encoding="utf-8")


def test_issue_to_dict_location_none():
    issue = Issue(rule_id="title_block.missing", severity="error", message="x")
    assert issue.to_dict()["location"] is None
