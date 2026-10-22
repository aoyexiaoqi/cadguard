import ezdxf
import pytest

from cadguard.config import load_config
from cadguard.demo import build_clean_drawing, build_demo_drawing


@pytest.fixture()
def default_config():
    return load_config()


@pytest.fixture()
def clean_path(tmp_path):
    return build_clean_drawing(tmp_path / "clean.dxf")


@pytest.fixture()
def demo_path(tmp_path):
    return build_demo_drawing(tmp_path / "demo.dxf")


@pytest.fixture()
def clean_doc(clean_path):
    return ezdxf.readfile(str(clean_path))


@pytest.fixture()
def demo_doc(demo_path):
    return ezdxf.readfile(str(demo_path))


def make_doc():
    """A minimal in-memory document for rule unit tests."""
    doc = ezdxf.new("R2010")
    for layer in ("OUTLINE", "DIM", "TEXT"):
        if not doc.layers.has_entry(layer):
            doc.layers.add(layer)
    return doc
