#!/usr/bin/env sh
set -eu

destination="${1:-data/raw/accepted_2007_to_2018Q4.csv}"
expected_sha256="3eae03c28fd9d2e8a076ebeb73507e8d4d0f44d90500decdb0936e0933d1f36a"
source_url="https://huggingface.co/datasets/codesignal/lending-club-loan-accepted/resolve/main/accepted_2007_to_2018Q4.csv?download=true"

mkdir -p "$(dirname "$destination")"
curl -L --fail --retry 3 --progress-bar -o "$destination" "$source_url"
printf '%s  %s\n' "$expected_sha256" "$destination" | sha256sum --check
