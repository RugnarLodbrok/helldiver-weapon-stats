#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    printf 'Usage: %s <JSON-file>\n' "$0" >&2
    exit 1
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
target="$script_dir/hellforge-stats.json"
temporary_file="$(mktemp "$script_dir/.hellforge-stats.XXXXXX")"
trap 'rm -f -- "$temporary_file"' EXIT

python3 "$script_dir/merge_json.py" "$target" "$1" > "$temporary_file"
chmod --reference="$target" -- "$temporary_file"
mv -- "$temporary_file" "$target"

printf 'Updated: %s\n' "$target"
