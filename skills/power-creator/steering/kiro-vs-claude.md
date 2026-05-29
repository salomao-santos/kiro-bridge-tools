# Kiro vs. Claude — what changed in this Power

This file documents the deltas between Anthropic's `skill-creator` and this `power-creator`. Useful when porting other Skills, or debugging differences.

## File-level renames

| Skill | Power |
|---|---|
| `SKILL.md` | `POWER.md` |
| `skill-creator` (name) | `power-creator` |
| `scripts/package_skill.py` | `scripts/package_power.py` |
| `.skill` (zip extension) | `.power` |
| `--skill-path`, `--skill-name` CLI flags | `--power-path`, `--power-name` |
| `.claude/commands/` (trampoline location) | `.kiro/powers/` (configurable via `$KIRO_POWERS_DIR`) |

## Runtime indirection

Original `skill-creator` does:

```python
subprocess.Popen(["claude", "-p", query, "--output-format", "stream-json", ...])
```

This Power routes through `scripts/runtime.py`:

```python
from scripts.runtime import invoke
for event in invoke(query, power_path=..., model=...):
    if event["type"] == "tool_use" and trampoline_name in event["input"].get("power",""):
        return True
```

Backends: `kiro_cli`, `kiro_ide_terminal`, `kiro_ide_prompt`, `claude_cli` (legacy fallback), `mock` (for CI). See `steering/runtime-backends.md`.

## Optionality matrix

`skill-creator` treated `scripts/`, `references/`, `assets/` as optional but had no concept of `steering/`, `hooks/`, `mcp.json`. Kiro Powers expand the optional surface:

| Dir / file | Skill | Power |
|---|---|---|
| `POWER.md` / `SKILL.md` | required | required |
| `scripts/` | optional | optional |
| `references/` | optional | optional |
| `assets/` | optional | optional |
| `steering/` | n/a | optional |
| `hooks/` | n/a | optional |
| `eval-viewer/` | optional | optional |
| `examples/` | optional | optional |
| `mcp.json` | n/a | optional |
| `agents/` | optional | merged into `steering/agent-*.md` |

## What got dropped

- **Subagent parallelism** — Kiro doesn't have Claude Code's `Task` subagent. `run_eval.py` uses `ProcessPoolExecutor` for parallelism instead. Same wall-clock for trigger evals; not equivalent for full task subagents.
- **Cowork-specific instructions** — replaced with Kiro IDE / Kiro CLI branches in steering files.
- **Claude.ai-specific instructions** — replaced with `kiro_ide_*` backend notes.

## What got added

- `scripts/runtime.py` — backend abstraction.
- `scripts/validate-eval.sh` — end-to-end mock eval smoke test for CI.
- `scripts/smoke-test.sh` — full pipeline against `examples/sample-power/`.
- `hooks/` — three manual hooks (eval-on-demand, improve-on-demand, validate-on-save).
- `steering/runtime-backends.md` — backend matrix + extension guide.

## Things to watch when porting another Skill

1. Anywhere the source Skill spawns `claude -p` — replace with `runtime.invoke()`.
2. Anywhere it reads `SKILL.md` — rename to `POWER.md`.
3. Anywhere it writes to `.claude/commands/` — write to `.kiro/powers/` instead.
4. H2 sections that look like deep dives — move to `steering/`.
5. Phrases like "use proactively", "after every X", "on save" — convert to `.kiro.hook` files.
6. `references/` files — copy into `steering/` with `ref-` prefix to avoid collisions.
