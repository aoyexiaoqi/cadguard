import json

from cadguard.cli import main


def test_check_demo_drawing_exit_1_and_report(demo_path, tmp_path):
    out = tmp_path / "report.md"
    code = main(["check", str(demo_path), "--out", str(out)])
    assert code == 1  # error-severity findings exist
    text = out.read_text(encoding="utf-8")
    assert "dimension.text_override" in text
    assert "title_block.missing" in text


def test_check_clean_drawing_exit_0(clean_path, capsys):
    code = main(["check", str(clean_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "0 issue(s)" in out


def test_check_json_output(clean_path, tmp_path):
    out = tmp_path / "report.json"
    code = main(["check", str(clean_path), "--out", str(out)])
    assert code == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["summary"]["total"] == 0


def test_check_missing_file_exit_2(tmp_path):
    assert main(["check", str(tmp_path / "missing.dxf")]) == 2


def test_check_bad_rules_exit_2(clean_path, tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("layers:\n  severity: fatal\n", encoding="utf-8")
    assert main(["check", str(clean_path), "--rules", str(bad)]) == 2


def test_demo_command(tmp_path):
    dxf_out = tmp_path / "demo.dxf"
    report_out = tmp_path / "demo_report.md"
    code = main(["--demo", "--dxf-out", str(dxf_out), "--out", str(report_out)])
    assert code == 0
    assert dxf_out.exists()
    text = report_out.read_text(encoding="utf-8")
    for rule_id in (
        "layer.nonstandard",
        "text_style.nonstandard_font",
        "linetype.nonstandard",
        "dimension.text_override",
        "geometry.duplicate",
        "title_block.missing",
    ):
        assert rule_id in text


def test_demo_subcommand(tmp_path):
    dxf_out = tmp_path / "demo2.dxf"
    report_out = tmp_path / "demo2.json"
    code = main(["demo", "--dxf-out", str(dxf_out), "--out", str(report_out)])
    assert code == 0
    assert json.loads(report_out.read_text(encoding="utf-8"))["summary"]["total"] >= 7


def test_no_command_shows_help(capsys):
    assert main([]) == 2
    assert "cadguard" in capsys.readouterr().out
