# Description Optimization

The `description` in POWER.md frontmatter is the **only** signal Kiro uses to decide whether to consult a Power. Optimizing it is the highest-leverage improvement after the body itself is reasonable.

## When to run optimization

After the Power body is in good shape and the user is satisfied with the outputs. Description tuning is downstream of correctness — don't optimize the description of a Power that doesn't work yet.

## Step 1: Generate trigger eval queries

20 queries: 8–10 should-trigger, 8–10 should-not-trigger.

```json
[
  {"query": "...", "should_trigger": true},
  {"query": "...", "should_trigger": false}
]
```

Queries must be **realistic** — what a real Kiro IDE or Kiro CLI user types. Include:
- File paths with realistic names (`~/Downloads/Q4 sales final FINAL v2.xlsx`)
- Personal context, company names, column names
- Mixed lengths, casing, typos, abbreviations
- Edge cases > clear-cut cases

**Bad**: `"Format this data"`, `"Create a chart"` — too abstract.

**Good**: `"ok so my boss just sent me this xlsx file (in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column for profit margin as a percent. Revenue is in column C and costs are in column D i think"`

For **should-not-trigger** queries, the valuable ones are near-misses — share keywords with the Power but actually need something different. "Write a fibonacci function" as a negative for a PDF Power is too easy.

## Step 2: Review queries with the user

Open `assets/eval_review.html` in Kiro IDE's preview. Replace placeholders:
- `__EVAL_DATA_PLACEHOLDER__` → JSON array (no quotes, raw JS assignment)
- `__POWER_NAME_PLACEHOLDER__` → Power name
- `__POWER_DESCRIPTION_PLACEHOLDER__` → current description

The user edits queries, toggles `should_trigger`, then clicks "Export Eval Set". File downloads to `~/Downloads/eval_set.json`. Watch for `(1)`, `(2)` suffixes from re-exports.

## Step 3: Run the optimization loop

```bash
python -m scripts.run_loop \
  --eval-set <eval.json> \
  --power-path <path> \
  --model <model-id> \
  --max-iterations 5 \
  --holdout 0.4 \
  --verbose
```

What it does:
1. Splits the eval set 60/40 (train/test), stratified by `should_trigger`.
2. Evaluates current description against the full set (3 runs/query for noise reduction).
3. If anything fails, calls the model via `runtime.invoke()` to propose an improved description.
4. Re-evaluates, repeats up to `--max-iterations`.
5. Picks `best_description` by **test** score (not train) to avoid overfitting.

The model that proposes improvements sees train results only — test scores are blinded so it can't fit to them.

`--report auto` opens an auto-refreshing HTML in the user's browser so they can watch progress.

## Step 4: Apply the result

Take `best_description` from JSON output, paste into POWER.md frontmatter, show before/after scores to the user.

## How triggering works in Kiro

Kiro routes queries based on the Power's description. Simple, one-step queries may not consult any Power — Kiro handles them directly. Complex, multi-step, or specialized queries reliably trigger when the description matches.

This means: **trivial queries are poor test cases**. "read file X" won't trigger a Power regardless of description quality.

## Common description failures

| Failure mode | Symptom | Fix |
|---|---|---|
| Too narrow | low recall on should-trigger | broaden phrasing, add intent variants |
| Too broad | high false-trigger rate | add a disambiguating clause (`use this Power for X, *not* for Y`) |
| Implementation-focused | misses intent-driven queries | rewrite around user goals, not internals |
| Passive voice | low overall trigger rate | switch to imperative ("Use this Power when...") |

## Character limit

Hard limit: 1024 chars. `improve_description.py` retries with a shortening prompt if the model exceeds it. `quick_validate.py` fails the Power if the final description is over the limit.
