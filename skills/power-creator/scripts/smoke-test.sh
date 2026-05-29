#!/usr/bin/env bash
# Full pipeline smoke test against examples/sample-power.
# Runs the eval, the loop (1 iteration), and packages the sample.
# Uses the mock backend so it doesn't need network access.
#
# Usage: scripts/smoke-test.sh

set -euo pipefail

POWER_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$POWER_ROOT"

export KIRO_POWER_RUNTIME=mock
export PYTHONPATH="$POWER_ROOT:${PYTHONPATH:-}"

TMPDIR_OVERRIDE=$(mktemp -d)
trap 'rm -rf "$TMPDIR_OVERRIDE"' EXIT

echo "==> run_eval"
python3 -m scripts.run_eval \
    --eval-set examples/eval-set-sample.json \
    --power-path examples/sample-power \
    --runs-per-query 1 --num-workers 2 --timeout 5 \
    --verbose > "$TMPDIR_OVERRIDE/eval_results.json"

echo "==> run_loop (1 iteration, mock model)"
python3 -m scripts.run_loop \
    --eval-set examples/eval-set-sample.json \
    --power-path examples/sample-power \
    --model mock-model \
    --max-iterations 1 \
    --holdout 0 \
    --runs-per-query 1 --num-workers 2 --timeout 5 \
    --report none \
    --verbose > "$TMPDIR_OVERRIDE/loop_results.json"

echo "==> package_power"
python3 -m scripts.package_power examples/sample-power "$TMPDIR_OVERRIDE"
test -f "$TMPDIR_OVERRIDE/sample-power.power" || { echo "FAIL: package output missing"; exit 1; }

echo "==> All smoke-test checks passed."
echo "Outputs: $TMPDIR_OVERRIDE"
