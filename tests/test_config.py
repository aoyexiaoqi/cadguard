import json

import pytest

from cadguard.config import DEFAULT_CONFIG, load_config, merged_config


def test_defaults_returned_without_path():
    cfg = load_config()
    assert cfg["layers"]["severity"] == "error"
    assert "OUTLINE" in cfg["layers"]["allowed"]


def test_defaults_are_isolated_copies():
    cfg = load_config()
    cfg["layers"]["allowed"].append("HACK")
    assert "HACK" not in DEFAULT_CONFIG["layers"]["allowed"]


def test_yaml_override_merges(tmp_path):
    path = tmp_path / "rules.yaml"
    path.write_text(
        "layers:\n  severity: warning\n  allowed: [ONLY_THIS]\n", encoding="utf-8"
    )
    cfg = load_config(path)
    assert cfg["layers"]["severity"] == "warning"
    assert cfg["layers"]["allowed"] == ["ONLY_THIS"]
    # untouched sections keep defaults
    assert cfg["title_block"]["block_names"] == DEFAULT_CONFIG["title_block"]["block_names"]


def test_json_override(tmp_path):
    path = tmp_path / "rules.json"
    path.write_text(
        json.dumps({"duplicate_geometry": {"enabled": False}}), encoding="utf-8"
    )
    cfg = load_config(path)
    assert cfg["duplicate_geometry"]["enabled"] is False


def test_invalid_severity_rejected():
    with pytest.raises(ValueError):
        merged_config({"layers": {"severity": "fatal"}})


def test_missing_file_raises(tmp_path):
    with pytest.raises(OSError):
        load_config(tmp_path / "nope.yaml")
