# mdformat-pyproject

[![Build Status][ci-badge]][ci-link] [![codecov.io][cov-badge]][cov-link]
[![PyPI version][pypi-badge]][pypi-link]

An [mdformat] plugin to read configuration from `pyproject.toml`.

> ⚠️ WARNING: it has been detected that some native `mdformat` options like `end_of_line` or
> `exclude` are currently being ignored when included in the `pyproject.toml` file. The issue is
> being worked on right now. You can read more here in
> [issue #4](https://github.com/csala/mdformat-pyproject/issues/4)

## Install

Install with:

```bash
pip install mdformat-pyproject
```

## Usage

After installing this plugin, the [mdformat configuration][mdformat-configuration] can be added in
a new `[tool.mdformat]` section inside the `pyproject.toml` file.

```toml
[tool.mdformat]
wrap = "keep"       # possible values: {"keep", "no", INTEGER}
number = false      # possible values: {false, true}
end_of_line = "lf"  # possible values: {"lf", "crlf", "keep"}
```

## Usage as a [pre-commit] hook

Add the following to your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/executablebooks/mdformat
  rev: 1.0.0  # Use the ref you want to point at
  hooks:
    - id: mdformat
      additional_dependencies:
        - mdformat-pyproject
```

[ci-badge]: https://github.com/csala/mdformat-pyproject/actions/workflows/ci.yml/badge.svg
[ci-link]: https://github.com/csala/mdformat-pyproject/actions/workflows/ci.yml
[cov-badge]: https://codecov.io/gh/csala/mdformat-pyproject/branch/master/graph/badge.svg
[cov-link]: https://codecov.io/gh/csala/mdformat-pyproject
[mdformat]: https://github.com/executablebooks/mdformat
[mdformat-configuration]: https://mdformat.readthedocs.io/en/stable/users/configuration_file.html
[pre-commit]: https://pre-commit.com
[pypi-badge]: https://img.shields.io/pypi/v/mdformat-pyproject.svg
[pypi-link]: https://pypi.org/project/mdformat-pyproject
