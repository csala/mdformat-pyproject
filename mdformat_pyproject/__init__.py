"""An mdformat plugin for reading configuration from ``pyproject.toml`` files."""

__version__ = "0.1.1"

from .plugin import RENDERERS, update_mdit  # noqa: F401
