# Test file

This repository contains 2 separate configuration files with contradictory settings:

1. The `tests/mdformat_toml/.mdformat.toml`, which defines a `wrap` length of 80 and sets `number`
   to `false`, meaning that numbered lists would be written starting with `1.` on all the rows.
2. The `pyproject.toml`, which should be used after the `mdformat-pyproject` plugin is installed,
   and which defines wrap length of 99 and sets `number` to `true`, meaning that numbered lists
   would be written starting with consecutive numbers.

This file is written according to the rules specified in the `pyproject.toml` file and serves as a
valid test to see if the plugin is working as expected.
