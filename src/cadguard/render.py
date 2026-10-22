"""Optional PNG rendering of a drawing via ezdxf's drawing add-on.

Rendering is a convenience only: it needs matplotlib (the ``render`` extra)
and is *not* required for checking.  :func:`render_png` returns ``False``
instead of raising whenever rendering is unavailable or fails.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union


def render_png(dxf_path: Union[str, Path], png_path: Union[str, Path]) -> bool:
    """Render the model space of ``dxf_path`` to ``png_path``.

    Returns True on success, False when matplotlib/ezdxf-drawing is not
    available or rendering fails for any reason.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from ezdxf.addons.drawing import Frontend, RenderContext
        from ezdxf.addons.drawing.config import Configuration
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

        import ezdxf

        doc = ezdxf.readfile(str(dxf_path))
        fig = plt.figure()
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        backend = MatplotlibBackend(ax)
        Frontend(ctx, backend, config=Configuration()).draw_layout(
            doc.modelspace(), finalize=True
        )
        fig.savefig(str(png_path), dpi=150)
        plt.close(fig)
        return Path(png_path).exists()
    except Exception:
        return False
