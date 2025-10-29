"""Tests for the mdformat_pyproject.plugin module."""

import copy
import pathlib
from unittest import mock

import markdown_it
import pytest

from mdformat_pyproject import plugin

THIS_MODULE_PATH = pathlib.Path(__file__)
THIS_MODULE_PARENT = THIS_MODULE_PATH.parent
PYPROJECT_PATH = THIS_MODULE_PARENT.parent / "pyproject.toml"
PYPROJECT_OPTIONS = {"wrap": 99, "number": True, "exclude": [".tox/**", ".venv/**"]}
MDFORMAT_TOML_PATH = THIS_MODULE_PARENT / ".mdformat.toml"
MDFORMAT_TOML_OPTIONS = {"wrap": 80, "number": False}


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


def test__parse_pyproject_invalid_toml(tmp_path):
    """Test _parse_pyproject when the given file is not a valid toml.

    Input:
        - pyproject_path pointing to an invalid toml file
    Expected outcome:
        - raise an mdformat._conf.InvalidConfError
    """
    invalid_pyproject_path = tmp_path / "pyproject.toml"
    invalid_pyproject_path.write_text("This is not a valid toml")
    with pytest.raises(plugin.mdformat._conf.InvalidConfError):
        plugin._parse_pyproject(invalid_pyproject_path)


def test__parse_pyproject_no_options(tmp_path):
    """Test _parse_pyproject when the given file has no tool.mdformat section.

    Input:
        - pyproject_path pointing at a pyproject.toml with no mdformat options.
    Expected output:
        - None
    """
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text('name = "mdformat-pyproject-testing"')
    options = plugin._parse_pyproject(pyproject_path)
    assert options is None


@mock.patch("mdformat_pyproject.plugin.mdformat._conf")
def test__parse_pyproject_with_options(_conf_patch):
    """Test _parse_pyproject when the given file has tool.mdformat options.

    Input:
        - pyproject_path pointing at this project's pyproject.toml
    Expected output:
        - Current options
    Expected outcome:
        - mdformat._conf._validate_keys has been called
        - mdformat._conf._validate_values has been called
    """
    options = plugin._parse_pyproject(PYPROJECT_PATH)
    assert options == PYPROJECT_OPTIONS
    _conf_patch._validate_keys.assert_called_once_with(PYPROJECT_OPTIONS, PYPROJECT_PATH)
    _conf_patch._validate_values.assert_called_once_with(PYPROJECT_OPTIONS, PYPROJECT_PATH)


def test_patched_read_toml_opts_without_configuration(nonexistent_path):
    """Test read_toml_opts when there is no pyproject.toml or .mdformat.toml file.

    Input:
        - search_path pointing to a non-existent folder
    Expected Output:
        - Tuple containing:
          - Empty dict
          - None
    """
    # run
    options, path = plugin.patched_read_toml_opts(nonexistent_path)

    # assert
    assert options == {}
    assert path is None


def test_patched_read_toml_opts_with_only_mdformat():
    """Test read_toml_opts when there is only an .mdformat.toml file.

    Input:
        - search_path pointing to the current file, which has an .mdformat.toml alongside it
    Expected Output:
        - Tuple containing:
          - mdformat options
          - mdformat path
    """
    # run
    options, path = plugin.patched_read_toml_opts(THIS_MODULE_PATH)

    # assert
    assert options == MDFORMAT_TOML_OPTIONS
    assert path == MDFORMAT_TOML_PATH


def test_patched_read_toml_opts_with_only_pyproject():
    """Test read_toml_opts when there is only a .pyproject.toml file.

    Input:
        - search_path pointing to a folder with a pyproject.toml
    Expected Output:
        - Tuple containing:
          - pyproject options
          - pyproject path
    """
    # run
    options, path = plugin.patched_read_toml_opts(PYPROJECT_PATH.parent)

    # assert
    assert options == PYPROJECT_OPTIONS
    assert path == PYPROJECT_PATH


@mock.patch("mdformat_pyproject.plugin.print_paragraphs")
def test_patched_read_toml_opts_with_both_no_mdformat_options(pp_patch, tmp_path):
    """Test read_toml_opts when both files exist, but pyproject has no options.

    Input:
        - search_path pointing to a folder with both pyproject.toml and .mdformat.toml, but
          pyproject.toml has no mdformat options.
    Expected Output:
        - Tuple containing:
          - mdformat options
          - mdformat path
    Expected Outcome:
        - print_paragraphs has not been called
    """
    # setup
    mdformat_toml_path = tmp_path / ".mdformat.toml"
    mdformat_toml_path.write_text(MDFORMAT_TOML_PATH.read_text())
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text('name = "mdformat-pyproject-testing"')

    # run
    options, path = plugin.patched_read_toml_opts(tmp_path)

    # assert
    assert options == MDFORMAT_TOML_OPTIONS
    assert path == mdformat_toml_path
    pp_patch.assert_not_called()


@mock.patch("mdformat_pyproject.plugin.print_paragraphs")
def test_patched_read_toml_opts_with_both(pp_patch, tmp_path):
    """Test read_toml_opts when both files exist and have options.

    Input:
        - search_path pointing to a folder with both pyproject.toml and .mdformat.toml, both with
          options.
    Expected Output:
        - Tuple containing:
          - mdformat options
          - mdformat path
    Expected Outcome:
        - print_paragraphs has been called to warn the user
    """
    # setup
    mdformat_toml_path = tmp_path / ".mdformat.toml"
    mdformat_toml_path.write_text(MDFORMAT_TOML_PATH.read_text())
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(PYPROJECT_PATH.read_text())

    # run
    options, path = plugin.patched_read_toml_opts(tmp_path)

    # assert
    assert options == MDFORMAT_TOML_OPTIONS
    assert path == mdformat_toml_path
    pp_patch.assert_called()


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
    mdit = mock.Mock(spec_set=markdown_it.MarkdownIt())
    mdit.options = {"mdformat": mdformat_options}

    expected_options = copy.deepcopy(mdformat_options)

    plugin.update_mdit(mdit)

    assert mdit.options["mdformat"] == expected_options
