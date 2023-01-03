"""Main plugin module."""

import functools
import pathlib
import sys
from typing import Mapping, NoReturn, Optional

from markdown_it import MarkdownIt
import mdformat
from mdformat.renderer.typing import Render

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@functools.lru_cache()
def _find_pyproject_toml_path(search_path: str) -> Optional[pathlib.Path]:
    if search_path == "-":
        search_path = pathlib.Path.cwd()
    else:
        search_path = pathlib.Path(search_path).resolve()

    for parent in (search_path, *search_path.parents):
        candidate = parent / "pyproject.toml"
        if candidate.is_file():
            return candidate

    return None


@functools.lru_cache()
def _parse_pyproject(pyproject_path: pathlib.Path) -> Optional[Mapping]:
    """Parse the pyproject.toml file."""
    content = tomllib.loads(pyproject_path.read_text())
    options = content.get("tool", {}).get("mdformat")
    if options is not None:
        mdformat._conf._validate_keys(options, pyproject_path)
        mdformat._conf._validate_values(options, pyproject_path)
        return options


@functools.lru_cache()
def _reload_cli_opts() -> Mapping:
    enabled_parserplugins = mdformat.plugins.PARSER_EXTENSIONS
    enabled_codeformatters = mdformat.plugins.CODEFORMATTERS
    arg_parser = mdformat._cli.make_arg_parser(
        enabled_parserplugins, enabled_codeformatters
    )
    return {
        key: value
        for key, value in vars(arg_parser.parse_args()).items()
        if value is not None
    }


def update_mdit(mdit: MarkdownIt) -> NoReturn:
    """Read the pyproject.toml file and update the mdformat options."""
    mdformat_options = mdit.options["mdformat"]
    file_path = mdformat_options["filename"]
    pyproject_path = _find_pyproject_toml_path(file_path)
    cli_opts = _reload_cli_opts()
    if pyproject_path:
        pyproject_opts = _parse_pyproject(pyproject_path)
        if pyproject_opts is not None:
            options: Mapping = {
                **mdformat._conf.DEFAULT_OPTS,
                **pyproject_opts,
                **cli_opts,
            }
            mdformat_options.update(options)


RENDERERS: Mapping[str, Render] = {}
