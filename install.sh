#!/usr/bin/env bash
set -e
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e .
echo 'installed in .venv (editable)'
