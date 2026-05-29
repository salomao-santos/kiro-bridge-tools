#!/usr/bin/env bash
# check.sh <file> — verify file passes black + isort without changes.
set -euo pipefail
FILE="$1"
black --check "$FILE" && isort --check-only "$FILE"
