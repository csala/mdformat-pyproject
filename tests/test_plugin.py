"""Tests for the mdformat_pyproject.plugin module."""

import copy
import pathlib
import unittest.mock

import markdown_it
import pytest
from mdformat._conf import InvalidConfError

from mdformat_pyproject import plugin

THIS_MODULE_PATH = pathlib.Path(__file__).parent


def setup_function():
    """Clear the cache of all the functions inside the plugin module."""
    for _, obj in vars(plugin).items():
        if hasattr(obj, "cache_clear"):
            obj.cache_clear()


@pytest.fixture
def fake_filename():
    fake_parent = "/fake"
    while pathlib.Path(fake_parent).exists():
        fake_parent += "e"

    return str(pathlib.Path(fake_parent) / "path" / "to" / "a" / "file.md")


@unittest.mock.patch("mdformat_pyproject.plugin.pathlib.Path.cwd", lambda: THIS_MODULE_PATH)
def test__find_pyproject_toml_path_cwd():
    """Test _find_pyproject_toml_path when search_path is `-`.

    Setup:
        - Patch Path.cwd to return the path of this module, to ensure
          that the `cwd` points at a subfolder of the project regardless
          of where the `pytest` command was executed.
    Input:
        - search_path="-"
    Expected output:
        - pyproject.toml of this project.
    """
    returned = plugin._find_pyproject_toml_path("-")
    assert returned == THIS_MODULE_PATH.parent / "pyproject.toml"


def test__find_pyproject_toml_path_file_inside_project():
    """Test _find_pyproject_toml_path when search_path points at a file within the project.

    Input:
        - search_path="__file__" -> file is inside the project
    Expected output:
        - pyproject.toml of this project.
    """
    returned = plugin._find_pyproject_toml_path(__file__)
    assert returned == THIS_MODULE_PATH.parent / "pyproject.toml"


def test__find_pyproject_toml_path_file_outside_of_project(fake_filename):
    """Test _find_pyproject_toml_path when search_path points at a file outside of a project.

    Input:
        - search_path="/fake/folder/path" -> A madeup path to an inexisting folder.
    Expected output:
        - None
    """
    returned = plugin._find_pyproject_toml_path(fake_filename)
    assert returned is None


def get_mdit(filename, **kwargs):
    mdit = unittest.mock.Mock(spec_set=markdown_it.MarkdownIt())
    mdformat_options = {
        "check": False,
        "end_of_line": "lf",
        "filename": str(pathlib.Path(filename).resolve()),
        "number": False,
        "paths": [filename],
        "wrap": 80,
    }
    mdit.options = {"mdformat": {**mdformat_options, **kwargs}}
    return mdit


def test_update_mdit_no_config(fake_filename):
    """Test update_mdit when there is no pyproject.toml.

    Input:
        - mdit with the default opts and a filename located inside a fake folder
    Excepted Side Effect:
        - mdit options should remain untouched
    """
    mdit = get_mdit(fake_filename)
    expected_options = copy.deepcopy(mdit.options["mdformat"])

    plugin.update_mdit(mdit)

    assert mdit.options["mdformat"] == expected_options


def test_update_mdit_pyproject():
    """Test update_mdit when there is configuration inside the pyproject.toml file.

    Input:
        - mdit with the default opts and a filename located inside the current project.
    Excepted Side Effect:
        - mdit options should be updated to the pyproject values
    """
    mdit = get_mdit(__file__)

    plugin.update_mdit(mdit)

    mdformat_options = mdit.options["mdformat"]
    assert mdformat_options["wrap"] == 99
    assert mdformat_options["number"] is True
    assert mdformat_options["end_of_line"] == "lf"


_BROKEN_OPTS = {"tool": {"mdformat": {"invalid": "option"}}}


@unittest.mock.patch("mdformat_pyproject.plugin.tomllib.load", lambda _: _BROKEN_OPTS)
def test_update_mdit_invalid_pyproject():
    """Test update_mdit when there are invlid options inside the pyproject.toml file.

    Setup:
        - Mock tomllib.load to return an invalid pyproject.toml file.
        - Also ensure that the load cache is clear
    Input:
        - mdit with the default opts and a filename located inside the current project.
    Excepted Side Effect:
        - _validate_keys should raise an exception.

    """
    mdit = get_mdit(__file__)

    with pytest.raises(InvalidConfError):
        plugin.update_mdit(mdit)


@unittest.mock.patch("mdformat_pyproject.plugin.sys.argv", ["mdformat", "--wrap", "70", __file__])
def test_update_mdit_pyproject_and_cli():
    """Test update_mdit when there are conflicting pyproject.toml configuration and cli argumnents.

    Setup:
        - Patch sys.argv to inject cli options different than the pyproject.toml.
    Input:
        - mdit with the default opts and a filename located inside the current project.
    Excepted Side Effect:
        - mdit options should be updated, with the cli options having priority over the
          pyproject ones.
    """
    mdit = get_mdit(__file__)
    expected_options = copy.deepcopy(mdit.options["mdformat"])

    plugin.update_mdit(mdit)

    expected_options["wrap"] = 70
    expected_options["number"] = True
    assert mdit.options["mdformat"] == expected_options


@unittest.mock.patch("mdformat_pyproject.plugin.sys.argv", ["fake", "--wrap", "70", "--unknown"])
def test_update_mdit_unknown_cli_arguments():
    """Test update_mdit when there are unknown arguments passed in the command line.

    Setup:
        - Mock sys.argv to inject unknown cli options.
    Input:
        - mdit with the default opts and a filename located inside the current project.
    Excepted Side Effect:
        - The CLI arguments are discarded and only the pyproject.toml options are
          injected into the mdit options.
    """
    mdit = get_mdit(__file__)
    expected_options = copy.deepcopy(mdit.options["mdformat"])

    plugin.update_mdit(mdit)

    expected_options["wrap"] = 99  # Still from pyproject
    expected_options["number"] = True
    assert mdit.options["mdformat"] == expected_options
