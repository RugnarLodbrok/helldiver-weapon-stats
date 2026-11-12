#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
file_args=()
if [[ $# -gt 0 && "$1" != -* ]]; then
    file_args=(--file "$1")
    shift
fi

exec python3 "$script_dir/scripts/stats.py" split "${file_args[@]}" "$@"
