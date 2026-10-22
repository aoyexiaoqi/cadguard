"""Sample drawings: a clean reference drawing and a demo drawing with
deliberately planted violations (used by ``cadguard --demo`` and the tests).

Planted violations in the demo drawing, one per rule:

1. a LINE on the non-standard layer ``SCRATCH``        -> layer.nonstandard
2. text style ``FANCY`` using font ``papyrus.ttf``     -> text_style.nonstandard_font
3. custom linetype ``MYLINE`` loaded and used          -> linetype.nonstandard
4. a DIMENSION whose text is overridden to ``999``     -> dimension.text_override
5. two identical LINEs                                  -> geometry.duplicate
6. no title block anywhere                              -> title_block.missing
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import ezdxf


def _add_title_block(doc) -> None:
    block = doc.blocks.new(name="TITLE_BLOCK")
    block.add_lwpolyline(
        [(0, 0), (180, 0), (180, 40), (0, 40)], close=True,
        dxfattribs={"layer": "0"},
    )
    block.add_text("图号 DWG NO: DEMO-001", dxfattribs={"layer": "0"}).set_placement((5, 10))
    msp = doc.modelspace()
    msp.add_blockref("TITLE_BLOCK", (0, -60), dxfattribs={"layer": "TITLE"})


def _add_clean_dimension(msp) -> None:
    dim = msp.add_linear_dim(base=(0, 30), p1=(0, 0), p2=(50, 0),
                             dxfattribs={"layer": "DIM"})
    dim.render()


def build_clean_drawing(path: Union[str, Path]) -> Path:
    """A drawing that passes every default rule."""
    doc = ezdxf.new("R2010")
    for layer in ("OUTLINE", "DIM", "TEXT", "TITLE"):
        if not doc.layers.has_entry(layer):
            doc.layers.add(layer)
    msp = doc.modelspace()
    # outline rectangle + a circle, all distinct geometry
    msp.add_line((0, 0), (50, 0), dxfattribs={"layer": "OUTLINE"})
    msp.add_line((50, 0), (50, 30), dxfattribs={"layer": "OUTLINE"})
    msp.add_line((50, 30), (0, 30), dxfattribs={"layer": "OUTLINE"})
    msp.add_line((0, 30), (0, 0), dxfattribs={"layer": "OUTLINE"})
    msp.add_circle((25, 15), 8, dxfattribs={"layer": "OUTLINE"})
    msp.add_text("PART-01", dxfattribs={"layer": "TEXT"}).set_placement((5, 35))
    _add_clean_dimension(msp)
    _add_title_block(doc)
    doc.saveas(str(path))
    return Path(path)


def build_demo_drawing(path: Union[str, Path]) -> Path:
    """A drawing with one planted violation per rule (see module docstring)."""
    doc = ezdxf.new("R2010")
    for layer in ("OUTLINE", "DIM", "TEXT", "SCRATCH"):
        if not doc.layers.has_entry(layer):
            doc.layers.add(layer)
    msp = doc.modelspace()

    # some clean geometry for contrast
    msp.add_line((0, 0), (50, 0), dxfattribs={"layer": "OUTLINE"})
    msp.add_circle((25, 15), 8, dxfattribs={"layer": "OUTLINE"})

    # 1. non-standard layer
    msp.add_line((0, 50), (50, 50), dxfattribs={"layer": "SCRATCH"})

    # 2. non-standard font (text style definition)
    doc.styles.add("FANCY", font="papyrus.ttf")
    msp.add_text(
        "fancy note", dxfattribs={"layer": "TEXT", "style": "FANCY"}
    ).set_placement((5, 55))

    # 3. non-standard linetype, loaded and used
    if not doc.linetypes.has_entry("MYLINE"):
        doc.linetypes.add("MYLINE", pattern=[0.6, 0.4, -0.2])
    msp.add_line(
        (0, 60), (50, 60), dxfattribs={"layer": "OUTLINE", "linetype": "MYLINE"}
    )

    # 4. dimension with manually overridden text
    dim = msp.add_linear_dim(base=(0, -10), p1=(0, 0), p2=(50, 0),
                             dxfattribs={"layer": "DIM"})
    dim.render()
    for entity in msp.query("DIMENSION"):
        entity.dxf.text = "999"

    # 5. duplicate geometry: two identical lines
    msp.add_line((0, 70), (50, 70), dxfattribs={"layer": "OUTLINE"})
    msp.add_line((0, 70), (50, 70), dxfattribs={"layer": "OUTLINE"})

    # 6. (no title block is added on purpose)

    doc.saveas(str(path))
    return Path(path)
