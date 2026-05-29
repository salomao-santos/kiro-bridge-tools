---
name: skill-creator
description: Create new Kiro skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit or optimize an existing skill, run evals to test a skill's trigger accuracy, benchmark skill performance, or optimize a skill's description for better triggering. Eval runtime uses Kiro CLI / Kiro IDE terminal by default (falls back to claude CLI if kiro not found). Auto-trigger on phrases like "create a skill", "create kiro skill", "write a skill", "write kiro skill", "improve this skill", "test my skill", "run skill evals", "optimize skill description", "benchmark skill", or any mention of SKILL.md authoring.
metadata:
  source: https://github.com/anthropics/skills/tree/main/skills/skill-creator
  adapted_for: Kiro CLI + Kiro IDE terminal (runtime-backends.md)
---

# Skill Creator

A skill for creating new Kiro skills and iteratively improving them.
Adapted from Anthropic's `skill-creator`. All `claude -p` eval calls are replaced by
`scripts/runtime.py`, which routes to **Kiro CLI**, **Kiro IDE (terminal)**,
**Kiro IDE (prompt API)**, or legacy **Claude CLI** — auto-selected at runtime.

## Skill vs. Power — what's different here

| Claude Code Skill | Kiro Power |
|---|---|
| `SKILL.md` (required) | `POWER.md` (required) |
| Lives in `.claude/commands/` | Lives in `.kiro/powers/` |
| Triggered via Claude's `available_skills` | Triggered via Kiro's description routing |
| Eval subprocess was `claude -p` | Eval subprocess is `runtime.py` (kiro or claude) |

This skill helps you author **Kiro skills (SKILL.md)**. The eval runner still uses whatever runtime is configured — typically Kiro CLI.

## High-level workflow

1. **Capture intent.** What should the skill do? When should it trigger? What test cases?
2. **Draft `SKILL.md`.** Frontmatter (`name`, `description`) + imperative-form body.
3. **Author bundled resources** (only what helps): `agents/`, `scripts/`, `references/`, `assets/`.
4. **Run trigger evals.** `scripts/run_eval.py` — tests whether the description triggers correctly via `runtime.py`.
5. **Review with the user.** Use `eval-viewer/generate_review.py` to show results in-browser.
6. **Iterate.** `scripts/run_loop.py` auto-improves the description across iterations with train/test split.
7. **Package.** `scripts/package_skill.py` creates a distributable `.skill` zip.

Your job: figure out which stage the user is at and jump in from there.

## Runtime backends (the adaptation)

Eval scripts invoke a model to test triggering. Original `skill-creator` shells out to `claude -p`. This version routes through `scripts/runtime.py`:

| Backend | Selector | Invocation |
|---|---|---|
| `kiro_cli` | `KIRO_POWER_RUNTIME=kiro_cli` or `which kiro` | `kiro -p "<query>" --output-format stream-json` |
| `kiro_ide_terminal` | `KIRO_POWER_RUNTIME=kiro_ide_terminal` | shells to `$KIRO_IDE_BIN` with IDE session env |
| `kiro_ide_prompt` | `KIRO_POWER_RUNTIME=kiro_ide_prompt` | writes prompt to `$KIRO_IDE_PROMPT_FIFO` |
| `claude_cli` | `KIRO_POWER_RUNTIME=claude_cli` or `which claude` (fallback) | legacy `claude -p` |
| `mock` | `KIRO_POWER_RUNTIME=mock` | deterministic, no network |

**Auto-detection order:** `kiro_cli` → `claude_cli` → `mock`.

**Env vars** (all optional):
- `KIRO_POWER_RUNTIME` — force a backend
- `KIRO_BIN` — path to Kiro CLI binary (default: `kiro`)
- `KIRO_PROMPT_FLAG` — prompt flag (default: `-p`)
- `KIRO_OUTPUT_FORMAT_FLAG` — stream flag (default: `--output-format stream-json`)
- `KIRO_IDE_PROMPT_FIFO` — for `kiro_ide_prompt` backend

Trampoline skill files are written to `.claude/commands/` so Claude Code can discover them during trigger testing. If you're using a Kiro backend that also reads `.claude/commands/`, this works transparently.

## Authoring a SKILL.md

Frontmatter is YAML between `---` markers.

```yaml
---
name: my-skill        # kebab-case, ≤64 chars
description: One declarative sentence that names the user intent and lists trigger contexts.
---
```

**Description tips:**
- Imperative voice: "Use this skill for…" not "This skill does…"
- Focus on user intent, not implementation details
- ≤1024 characters (hard limit — descriptions over this are truncated)
- The description competes with other skills; make it distinctive

## Eval workflow details

### Writing eval sets

Create `evals/trigger-evals.json`:

```json
[
  {"query": "create a skill for summarizing PDFs", "should_trigger": true},
  {"query": "fix the bug in my Python script",     "should_trigger": false}
]
```

### Running evals

```bash
# From the skill-creator directory:
python -m scripts.run_eval \
  --eval-set path/to/trigger-evals.json \
  --skill-path path/to/your-skill \
  --verbose
```

The backend is auto-selected. Override with `KIRO_POWER_RUNTIME=kiro_cli python -m scripts.run_eval ...`.

### Optimization loop

```bash
python -m scripts.run_loop \
  --eval-set path/to/trigger-evals.json \
  --skill-path path/to/your-skill \
  --model claude-sonnet-4-5 \
  --max-iterations 5 \
  --verbose
```

This runs eval → improve → eval in a loop, opens a live HTML report, and prints the best description at the end.

## Agents

The `agents/` directory has three sub-agents used in the full benchmark workflow:

| Agent | Role |
|---|---|
| `agents/analyzer.md` | Post-hoc analysis: why did the winner win? |
| `agents/comparator.md` | Blind comparison of two outputs |
| `agents/grader.md` | Grades expectations against a transcript |

See `references/schemas.md` for the JSON schemas each agent produces.

## Scripts reference

| Script | Purpose |
|---|---|
| `scripts/runtime.py` | Backend adapter (kiro/claude/mock) |
| `scripts/utils.py` | `parse_skill_md()` helper |
| `scripts/run_eval.py` | Single eval run — trigger accuracy |
| `scripts/improve_description.py` | Rewrite description based on eval failures |
| `scripts/run_loop.py` | Eval + improve loop |
| `scripts/aggregate_benchmark.py` | Aggregate multiple benchmark runs |
| `scripts/generate_report.py` | Generate HTML report from loop results |
| `scripts/quick_validate.py` | Validate SKILL.md structure |
| `scripts/package_skill.py` | Package skill into `.skill` zip |
| `eval-viewer/generate_review.py` | Serve interactive eval review page |
