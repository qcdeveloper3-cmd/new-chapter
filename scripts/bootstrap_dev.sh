#!/usr/bin/env bash
set -euo pipefail

INSTALL_OPTIONAL_ENGINES="${INSTALL_OPTIONAL_ENGINES:-0}"
FORCE_SKILL_OVERWRITE="${FORCE_SKILL_OVERWRITE:-0}"

cd "$(dirname "$0")/.."

if [[ ! -x ".venv/bin/python" ]]; then
  python3 -m venv .venv
fi

PYTHON=".venv/bin/python"

# Avoid local proxy issues during package installation unless explicitly needed.
export HTTP_PROXY=""
export HTTPS_PROXY=""

"$PYTHON" -m pip install --upgrade pip setuptools wheel
"$PYTHON" -m pip install -e ".[dev]"
if [[ "$INSTALL_OPTIONAL_ENGINES" == "1" ]]; then
  "$PYTHON" -m pip install -e ".[analysis,fallback]"
fi

"$PYTHON" -m pre_commit install

if [[ "$FORCE_SKILL_OVERWRITE" == "1" ]]; then
  "$PYTHON" scripts/install_repo_skills.py --force
else
  "$PYTHON" scripts/install_repo_skills.py
fi

echo "Bootstrap complete."
