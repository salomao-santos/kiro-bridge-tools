# Eval Process — Deep Dive

This document expands the high-level workflow in POWER.md. Read when actually running an eval.

## Workspace layout

Put results in `<power-name>-workspace/` as a sibling of the Power directory. Organize by iteration:

```
my-power-workspace/
└── iteration-1/
    ├── eval-0-<name>/
    │   ├── with_power/
    │   │   ├── outputs/
    │   │   ├── timing.json
    │   │   └── grading.json
    │   └── without_power/
    │       └── outputs/
    ├── eval-1-<name>/
    │   └── ...
    ├── benchmark.json
    └── benchmark.md
```

Don't create all directories upfront. Make each as the eval runs.

## Step 1: Spawn all runs in one batch

For each test case, kick off two parallel runs: one with the Power loaded, one without (baseline).

- **Creating a new Power**: baseline = no Power at all. Save to `without_power/outputs/`.
- **Improving an existing Power**: baseline = the previous version. Snapshot first (`cp -r <power-path> <workspace>/power-snapshot/`) and point the baseline run at the snapshot. Save to `old_power/outputs/`.

Write `eval_metadata.json` per test case:

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name",
  "prompt": "the user task prompt",
  "assertions": []
}
```

Names matter — they show up in the viewer.

## Step 2: Draft assertions while runs are in flight

Don't idle while waiting. Good assertions are objectively verifiable and named descriptively. Subjective Powers (writing style, design quality) don't get assertions — qualitative review only.

Update `eval_metadata.json` and `evals/evals.json` once drafted.

## Step 3: Capture timing as runs complete

Each run process emits `total_tokens` and `duration_ms`. Save immediately:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

This is the only chance to capture this data.

## Step 4: Grade, aggregate, launch viewer

1. **Grade** — read `steering/agent-grader.md` and evaluate each assertion. Save to `grading.json` with fields `text`, `passed`, `evidence` (exact field names — the viewer depends on them).

2. **Aggregate**:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --power-name <name>
   ```
   Produces `benchmark.json` and `benchmark.md` with mean ± stddev across configurations.

3. **Analyst pass** — see `steering/agent-analyzer.md`. Look for non-discriminating assertions, high-variance evals, time/token tradeoffs.

4. **Launch viewer**:
   ```bash
   python eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --power-name <name> \
     --benchmark <workspace>/iteration-N/benchmark.json
   ```

   **Kiro IDE / headless**: pass `--static <path.html>`. Output is a standalone HTML file; Kiro IDE opens it inline. The viewer's "Submit All Reviews" downloads `feedback.json` — copy it into the workspace for the next iteration.

## Step 5: Read feedback

`feedback.json` shape:

```json
{
  "reviews": [
    {"run_id": "eval-0-with_power", "feedback": "missing axis labels", "timestamp": "..."},
    {"run_id": "eval-1-with_power", "feedback": "", "timestamp": "..."}
  ],
  "status": "complete"
}
```

Empty feedback = user is fine. Focus improvements on entries with actual complaints.

## Iteration loop

1. Apply improvements to the Power
2. Re-run all evals into `iteration-<N+1>/`
3. Launch viewer with `--previous-workspace <workspace>/iteration-<N>`
4. Wait for feedback, repeat

Stop when:
- User says they're happy
- Feedback is uniformly empty
- No meaningful progress

## Common pitfalls

- **Overfitting to N test cases.** A Power must work across millions of queries, not 3. Generalize from feedback to broader user intents, not ever-longer rule lists.
- **Forgetting baseline runs.** Baselines are what make the benchmark meaningful. Without them, you don't know if the Power helps.
- **Skipping the viewer.** Always show outputs to the human before forming your own opinion. Especially in Kiro IDE — generate the HTML first.
- **Tool-name mismatch.** The viewer expects `grading.json` fields `text`/`passed`/`evidence`. Anything else (`name`/`met`/`details`) silently breaks the UI.
