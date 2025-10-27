"""Main plugin module."""

import pathlib
import sys
from functools import cache
from typing import TYPE_CHECKING, MutableMapping, Optional, Sequence, Tuple, Union

import markdown_it
import mdformat

if TYPE_CHECKING:
    from mdformat.renderer.typing import Render

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


_ConfigOptions = MutableMapping[str, Union[int, str, Sequence[str]]]


@cache
def _find_pyproject_toml_path(search_path: pathlib.Path) -> Optional[pathlib.Path]:
    """Find the pyproject.toml file that applies to the search path.

    The search is done ascending through the folders tree until a pyproject.toml
    file is found in the same folder. If the root '/' is reached, None is returned.
    """
    if search_path.is_file():
        search_path = search_path.parent

    for parent in (search_path, *search_path.parents):
        candidate = parent / "pyproject.toml"
        if candidate.is_file():
            return candidate

    return None


@cache
def _parse_pyproject(pyproject_path: pathlib.Path) -> Optional[_ConfigOptions]:
    """Extract and validate the mdformat options from the pyproject.toml file.

    The options are searched inside a [tool.mdformat] key within the toml file,
    and they are validated using the default functions from `mdformat._conf`.
    """
    with pyproject_path.open(mode="rb") as pyproject_file:
        content = tomllib.load(pyproject_file)

    options = content.get("tool", {}).get("mdformat")
    if options is not None:
        mdformat._conf._validate_keys(options, pyproject_path)
        mdformat._conf._validate_values(options, pyproject_path)

    return options


@cache
def read_toml_opts(conf_dir: pathlib.Path) -> Tuple[MutableMapping, Optional[pathlib.Path]]:
    """Alternative read_toml_opts that reads from pyproject.toml instead of .mdformat.toml.

    Notice that if `.mdformat.toml` exists it is ignored.
    """
    pyproject_path = _find_pyproject_toml_path(conf_dir)
    if pyproject_path:
        pyproject_opts = _parse_pyproject(pyproject_path)
    else:
        pyproject_opts = {}

    return pyproject_opts, pyproject_path


def update_mdit(mdit: markdown_it.MarkdownIt) -> None:
    """No-op, since this plugin only monkey patches and does not modify mdit."""
    pass


RENDERERS: MutableMapping[str, "Render"] = {}

# Monkey patch mdformat._conf to use our own read_toml_opts version
mdformat._conf.read_toml_opts = read_toml_opts
