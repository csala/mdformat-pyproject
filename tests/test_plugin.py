"""Tests for the mdformat_pyproject.plugin module."""

import copy
import pathlib
import unittest.mock

import markdown_it
import pytest

from mdformat_pyproject import plugin

THIS_MODULE_PATH = pathlib.Path(__file__)
THIS_MODULE_PARENT = THIS_MODULE_PATH.parent
PYPROJECT_PATH = THIS_MODULE_PARENT.parent / "pyproject.toml"


def setup_function():
    """Clear the cache of all the functions inside the plugin module."""
    for _, obj in vars(plugin).items():
        if hasattr(obj, "cache_clear"):
            obj.cache_clear()


@pytest.fixture
def nonexistent_path():
    fake_parent = "/fake"
    while pathlib.Path(fake_parent).exists():
        fake_parent += "e"

    return pathlib.Path(fake_parent) / "path" / "to" / "a" / "file.md"


def test__find_pyproject_toml_path_directory_inside_project():
    """Test _find_pyproject_toml_path when search_path points at a directory within the project.

    Input:
        - search_path=THIS_MODULE_PATH -> directory is inside the project
    Expected output:
        - pyproject.toml of this project.
    """
    returned = plugin._find_pyproject_toml_path(THIS_MODULE_PARENT)
    assert returned == PYPROJECT_PATH


def test__find_pyproject_toml_path_directory_outside_project(nonexistent_path):
    """Test _find_pyproject_toml_path when search_path points at a directory within the project.

    Input:
        - search_path=nonexistent_path.parent -> directory is outside the project
    Expected output:
        - pyproject.toml of this project.
    """
    returned = plugin._find_pyproject_toml_path(nonexistent_path.parent)
    assert returned is None


def test__find_pyproject_toml_path_file_inside_project():
    """Test _find_pyproject_toml_path when search_path points at a file within the project.

    Input:
        - search_path="__file__" -> file is inside the project
    Expected output:
        - pyproject.toml of this project.
    """
    returned = plugin._find_pyproject_toml_path(THIS_MODULE_PATH)
    assert returned == PYPROJECT_PATH


def test__find_pyproject_toml_path_file_outside_of_project(nonexistent_path):
    """Test _find_pyproject_toml_path when search_path points at a file outside of a project.

    Input:
        - search_path="/fake/folder/path" -> A madeup path to an nonexistent folder.
    Expected output:
        - None
    """
    returned = plugin._find_pyproject_toml_path(nonexistent_path)
    assert returned is None


def test_read_toml_opts_with_pyproject():
    """Test read_toml_opts when there is a pyproject.toml file.

    Input:
        - conf_dir pointing to this module's folder
    Expected Output:
        - Tuple containing:
          - Dict with the mdformat options from pyproject.toml
          - Path to the pyproject.toml file
    """
    # run
    opts, path = plugin.read_toml_opts(THIS_MODULE_PATH)

    # assert
    assert opts == {"wrap": 99, "number": True, "exclude": [".tox/**", ".venv/**"]}
    assert path == PYPROJECT_PATH


def test_read_toml_opts_without_pyproject(nonexistent_path):
    """Test read_toml_opts when there is no pyproject.toml file.

    Input:
        - conf_dir pointing to a non-existent folder
    Expected Output:
        - Tuple containing:
          - Empty dict
          - None
    """
    # run
    opts, path = plugin.read_toml_opts(nonexistent_path)

    # assert
    assert opts == {}
    assert path is None


def test_update_mdit_no_config():
    """Test update_mdit which is now a no-op.

    Input:
        - mdit with arbitrary configuration
    Expected Side Effect:
        - mdit options should remain untouched
    """
    filename = "/some/file/name.toml"
    mdformat_options = {
        "check": False,
        "end_of_line": "lf",
        "filename": filename,
        "number": False,
        "paths": [filename],
        "wrap": 80,
    }
    mdit = unittest.mock.Mock(spec_set=markdown_it.MarkdownIt())
    mdit.options = {"mdformat": mdformat_options}

    expected_options = copy.deepcopy(mdformat_options)

    plugin.update_mdit(mdit)

    assert mdit.options["mdformat"] == expected_options
