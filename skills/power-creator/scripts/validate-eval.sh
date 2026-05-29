#!/usr/bin/env bash
# End-to-end eval validation using the mock backend.
# Exercises runtime.py + run_eval.py + run_loop.py without hitting a real model.
#
# Usage: scripts/validate-eval.sh
# Returns 0 on full pass, non-zero on failure.

set -euo pipefail

POWER_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$POWER_ROOT"

export KIRO_POWER_RUNTIME=mock
export PYTHONPATH="$POWER_ROOT:${PYTHONPATH:-}"

echo "==> Checking POWER.md exists"
test -f POWER.md || { echo "FAIL: no POWER.md"; exit 1; }

echo "==> Checking runtime.py importable"
python3 -c "from scripts.runtime import invoke, invoke_once, select_backend; print('backend:', select_backend())" \
    || { echo "FAIL: runtime.py import"; exit 2; }

echo "==> Checking quick_validate on this Power"
python3 -m scripts.quick_validate "$POWER_ROOT" \
    || { echo "FAIL: quick_validate"; exit 3; }

echo "==> Checking quick_validate on examples/sample-power"
python3 -m scripts.quick_validate "$POWER_ROOT/examples/sample-power" \
    || { echo "FAIL: sample-power quick_validate"; exit 4; }

echo "==> Running run_eval against examples/sample-power with mock backend"
OUT_FILE=$(mktemp)
ERR_FILE=$(mktemp)
trap 'rm -f "$OUT_FILE" "$ERR_FILE"' EXIT
python3 -m scripts.run_eval \
    --eval-set "$POWER_ROOT/examples/eval-set-sample.json" \
    --power-path "$POWER_ROOT/examples/sample-power" \
    --runs-per-query 1 \
    --num-workers 2 \
    --timeout 5 \
    --verbose > "$OUT_FILE" 2> "$ERR_FILE" || { echo "FAIL: run_eval"; cat "$ERR_FILE"; exit 5; }

python3 -c "
import json, sys
data = json.load(open('$OUT_FILE'))
assert 'summary' in data, 'missing summary'
assert 'results' in data, 'missing results'
print('eval summary:', data['summary'])
print('backend:', data.get('backend'))
" || { echo "FAIL: run_eval output parse"; cat "$OUT_FILE"; exit 6; }

echo "==> Running invoke_once mock rewrite"
python3 -c "
from scripts.runtime import invoke_once
out = invoke_once('rewrite this description', model='mock-model')
assert '<new_description>' in out, f'mock rewrite missing tag: {out!r}'
print('mock rewrite ok')
" || { echo "FAIL: invoke_once mock"; exit 7; }

echo "==> All validate-eval checks passed."
