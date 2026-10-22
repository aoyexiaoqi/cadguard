import pytest

pytest.importorskip("matplotlib")

from cadguard.render import render_png  # noqa: E402


def test_render_png_success(clean_path, tmp_path):
    out = tmp_path / "preview.png"
    assert render_png(clean_path, out) is True
    assert out.exists() and out.stat().st_size > 0


def test_render_png_missing_input_returns_false(tmp_path):
    out = tmp_path / "preview.png"
    assert render_png(tmp_path / "missing.dxf", out) is False
    assert not out.exists()
