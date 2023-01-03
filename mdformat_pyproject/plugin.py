"""Main plugin module."""

import functools
import pathlib
import sys
from typing import Mapping, NoReturn, Optional

import markdown_it
import mdformat
from mdformat.renderer.typing import Render

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@functools.lru_cache()
def _find_pyproject_toml_path(search_path: str) -> Optional[pathlib.Path]:
    """Find the pyproject.toml file that corresponds to the search path.

    The search is done ascending through the folders tree until a pyproject.toml
    file is found in the same folder. If the root '/' is reached, None is returned.

    The special path "-" used for stdin inputs is replaced with the current working
    directory.
    """
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
    """Extract and validate the mdformat options from the pyproject.toml file.

    The options are searched inside a [tool.mdformat] key within the toml file,
    and they are validated using the default functions from `mdformat._conf`.
    """
    content = tomllib.loads(pyproject_path.read_text())
    options = content.get("tool", {}).get("mdformat")
    if options is not None:
        mdformat._conf._validate_keys(options, pyproject_path)
        mdformat._conf._validate_values(options, pyproject_path)
        return options


@functools.lru_cache()
def _reload_cli_opts() -> Mapping:
    """Re-parse the sys.argv array to deduce which arguments were used in the CLI.

    If unknown arguments are found, we deduce that mdformat is being called as a
    python library and therefore no mdofrmat command line arguments were passed.

    Notice that the strategy above does not fully close the door to situations
    with colliding arguments with different meanings, but the rarity of the
    situation and the complexity of a possible solution makes the risk worth taking.
    """
    import mdformat._cli

    enabled_parserplugins = mdformat.plugins.PARSER_EXTENSIONS
    enabled_codeformatters = mdformat.plugins.CODEFORMATTERS
    arg_parser = mdformat._cli.make_arg_parser(enabled_parserplugins, enabled_codeformatters)
    args, unknown = arg_parser.parse_known_args(sys.argv[1:])
    if unknown:
        return {}

    return {key: value for key, value in vars(args).items() if value is not None}


def update_mdit(mdit: markdown_it.MarkdownIt) -> NoReturn:
    """Read the pyproject.toml file and re-create the mdformat options."""
    mdformat_options = mdit.options["mdformat"]
    file_path = mdformat_options.get("filename", "-")
    pyproject_path = _find_pyproject_toml_path(file_path)
    if pyproject_path:
        pyproject_opts = _parse_pyproject(pyproject_path)
        if pyproject_opts is not None:
            cli_opts = _reload_cli_opts()
            new_options: Mapping = {**pyproject_opts, **cli_opts}
            mdformat_options.update(new_options)


RENDERERS: Mapping[str, Render] = {}
