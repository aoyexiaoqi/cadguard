"""CADGuard — rule-based checker for DXF engineering drawings."""

from .checker import check_document, check_file, run_checks
from .config import DEFAULT_CONFIG, load_config
from .models import Issue

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_CONFIG",
    "Issue",
    "__version__",
    "check_document",
    "check_file",
    "load_config",
    "run_checks",
]
