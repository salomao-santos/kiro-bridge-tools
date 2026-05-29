# Runtime Backends

`scripts/runtime.py` is the abstraction layer between eval scripts and whichever model harness the user has installed. Original `skill-creator` hard-coded `subprocess(["claude","-p",...])`; Power Creator picks a backend at runtime.

## Backend selection order

1. Env var `KIRO_POWER_RUNTIME` (explicit override)
2. `kiro_cli` if `which kiro` succeeds
3. `claude_cli` if `which claude` succeeds (legacy fallback)
4. `mock` (used by `validate-eval.sh` for CI)

If selection fails, `runtime.invoke()` raises `RuntimeError("no backend available")`.

## Backend matrix

| Backend | Subprocess | Streaming | Trigger detection |
|---|---|---|---|
| `kiro_cli` | `$KIRO_BIN $KIRO_PROMPT_FLAG <query>` + `$KIRO_OUTPUT_FORMAT_FLAG` | stream-json line-by-line | tool_use event with Power name in input |
| `kiro_ide_terminal` | same as `kiro_cli` but inherits IDE env (`KIRO_IDE_SESSION`, `KIRO_WORKSPACE`) | same | same |
| `kiro_ide_prompt` | writes query to `$KIRO_IDE_PROMPT_FIFO`; reads response from companion `.out` file | full message | regex on full output |
| `claude_cli` | `claude -p <query> --output-format stream-json --include-partial-messages` | stream-json | content_block_start + delta |
| `mock` | none | none | deterministic — Power name in query string ⇒ trigger |

## Env vars

| Var | Default | Purpose |
|---|---|---|
| `KIRO_POWER_RUNTIME` | (auto) | Force a backend: `kiro_cli`, `kiro_ide_terminal`, `kiro_ide_prompt`, `claude_cli`, `mock` |
| `KIRO_BIN` | `kiro` | Kiro CLI binary path |
| `KIRO_PROMPT_FLAG` | `-p` | Prompt flag (e.g. `--prompt`, `run`) — adjust if Kiro CLI uses different flag |
| `KIRO_OUTPUT_FORMAT_FLAG` | `--output-format stream-json` | Streaming flag (set empty to disable) |
| `KIRO_INCLUDE_PARTIAL_FLAG` | `--include-partial-messages` | Partial-event flag (set empty to disable) |
| `KIRO_MODEL_FLAG` | `--model` | Model selector flag |
| `KIRO_POWERS_DIR` | `.kiro/powers` | Where to write the trampoline POWER.md for trigger eval |
| `KIRO_IDE_BIN` | (unset) | IDE-launched Kiro binary |
| `KIRO_IDE_PROMPT_FIFO` | (unset) | FIFO/pipe for `kiro_ide_prompt` backend |

If you don't know the real Kiro CLI flag names, set these and the runtime adapter will use whatever you give it. The defaults are guesses; the *abstraction* is what's load-bearing.

## Trigger detection logic

`runtime.invoke()` returns an iterator of events. Each event has a `type`:

- `tool_use` — model called a tool. Carries `name` (tool name) and `input` (tool args). Power triggered when `input` references the trampoline Power name.
- `text` — model emitted plain text. Not a trigger signal, but captured for the viewer.
- `done` — final result delimiter.
- `error` — backend error.

`run_eval.py` consumes the iterator and short-circuits on the first `tool_use` matching the trampoline name. If no `tool_use` arrives before `done`, the query is recorded as not-triggered.

## Adding a new backend

1. Add an `if backend == "<name>":` branch to `runtime.invoke()`.
2. Yield event dicts conforming to the schema above.
3. Document the env vars in this file.
4. Add a test case to `scripts/validate-eval.sh` (use `KIRO_POWER_RUNTIME=mock` pattern as a template).

## Why the abstraction matters

The eval loop is otherwise identical to `skill-creator`'s. By isolating the model call to `runtime.invoke()`, the rest of the pipeline (eval aggregation, train/test split, description rewriting, HTML reports) works unchanged. Swapping Kiro CLI for a future Kiro IDE MCP integration is a one-file change.
