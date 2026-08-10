#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd -- "$script_dir/.." && pwd)"

python3 -m venv "$skill_dir/.venv"
"$skill_dir/.venv/bin/python" -m pip install --upgrade pip
"$skill_dir/.venv/bin/python" -m pip install "deepxiv-sdk==0.3.1"

echo "Standalone runtime ready. Export DEEPXIV_TOKEN in your shell, then run scripts/doctor.py."
