---
name: sample-power
description: Use this Power when the user wants to test a sample Kiro Power end-to-end — it does nothing useful and exists solely as a smoke-test fixture for power-creator's eval pipeline. Triggers on phrases like "sample power", "smoke test power", "test fixture", or any mention of running validate-eval.sh.
keywords: [sample, smoke-test, fixture]
---

# Sample Power

Minimal fixture used by `scripts/validate-eval.sh` and `scripts/smoke-test.sh`. The mock backend in `scripts/runtime.py` checks whether the Power's directory name (`sample-power`) appears in the test query and synthesizes a `tool_use` event accordingly.

Real Powers would have steering files, hooks, scripts, etc. This one is intentionally bare.
