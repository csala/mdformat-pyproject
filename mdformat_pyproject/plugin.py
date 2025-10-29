"""Main plugin module."""

from __future__ import annotations

import sys
from functools import cache
from pathlib import Path

import markdown_it
import mdformat
from mdformat._cli import print_paragraphs

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Sequence

    from mdformat.renderer.typing import Render

    _ConfigOptions = dict[str, int | str | Sequence[str]]

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@cache
def _parse_pyproject(pyproject_path: Path) -> _ConfigOptions | None:
    """Extract and validate the mdformat options from the ``pyproject.toml`` file.

    The options are searched inside a ``[tool.mdformat]`` section within the TOML file,
    and they are validated using the default functions from ``mdformat._conf``.

    If no ``[tool.mdformat]`` section is found, ``None`` is returned.
    """
    with pyproject_path.open(mode="rb") as pyproject_file:
        try:
            content = tomllib.load(pyproject_file)
        except tomllib.TOMLDecodeError as e:
            raise mdformat._conf.InvalidConfError(f"Invalid TOML syntax: {e}")

    options = content.get("tool", {}).get("mdformat")
    if options is None:
        return None

    mdformat._conf._validate_keys(options, pyproject_path)
    mdformat._conf._validate_values(options, pyproject_path)

    return options


_orig_read_toml_opts = mdformat._conf.read_toml_opts


@cache
def patched_read_toml_opts(search_path: Path) -> tuple[dict, Path | None]:
    """Patched version of ``mdformat._conf.read_toml_opts``.

    Search the first ``.mdformat.toml`` or ``pyproject.toml`` file in the provided
    ``search_path`` folder or its parents.

    The search is done ascending through the folders tree until a ``.mdformat.toml`` or a
    ``pyproject.toml`` file is found. If the root ``/`` is reached, ``None`` is returned.

    ``.mdformat.toml`` takes precedence over ``pyproject.toml`` if both are present in the
    same folder. In that case, a warning is logged to inform the user that the
    ``pyproject.toml`` file has been ignored.

    ``pyproject.toml`` files without a ``[tool.mdformat]`` section are ignored.

    This behavior mimics the one from Ruff, as described in `issues#17
    <https://github.com/csala/mdformat-pyproject/issues/17>`_.
    """
    if search_path.is_file():
        search_path = search_path.parent

    for parent in (search_path, *search_path.parents):
        # Try to find a pyproject.toml file first, with a [tool.mdformat] section.
        pyproject_options = None
        pyproject_path = parent / "pyproject.toml"
        if pyproject_path.is_file():
            pyproject_options = _parse_pyproject(pyproject_path)

        # Read options from .mdformat.toml if present.
        mdformat_path = parent / ".mdformat.toml"
        if mdformat_path.is_file():
            # If both pyproject.toml and .mdformat.toml are present, the latter takes
            # precedence, but we warn the user that pyproject.toml is being ignored.
            if pyproject_options is not None:
                print_paragraphs(
                    (
                        f"Warning: ignoring mdformat options from {pyproject_path} "
                        f"since {mdformat_path} is present.",
                    )
                )

            # Return options from .mdformat.toml using the original function, even if
            # they are empty.
            return _orig_read_toml_opts(mdformat_path.parent)

        # Return options from pyproject.toml if .mdformat.toml is not present.
        elif pyproject_options is not None:
            return pyproject_options, pyproject_path

    # No config file found, return empty options.
    return {}, None


def update_mdit(mdit: markdown_it.MarkdownIt) -> None:
    """No-op, since this plugin only monkey patches and does not modify ``mdit``."""
    pass


RENDERERS: dict[str, Render] = {}

# Monkey patch mdformat._conf to use our own read_toml_opts version
mdformat._cli.read_toml_opts = patched_read_toml_opts
