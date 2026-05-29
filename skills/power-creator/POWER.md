---
name: power-creator
displayName: "Power Creator"
description: Create new Kiro Powers, modify and improve existing Powers, and measure Power triggering accuracy. Use this Power whenever the user wants to author a Power from scratch, edit an existing Power, run trigger evals against a Power's description, benchmark a Power's behavior with variance analysis, optimize a Power's description for better triggering accuracy, or package a Power for distribution. Auto-trigger on phrases like "create a power", "build a kiro power", "improve this power", "test my power", "evaluate power triggering", "optimize power description", or any mention of POWER.md authoring.
keywords:
  - power
  - kiro-power
  - power-md
  - eval
  - triggering
  - description-optimization
  - benchmark
author: Community
metadata:
  source: https://github.com/anthropics/skills/tree/main/skills/skill-creator
  adapted_for: Kiro IDE + Kiro CLI
---

# Power Creator

A Power for authoring, evaluating, and iteratively improving Kiro Powers. Adapted from Anthropic's `skill-creator` skill. Replaces all `claude -p` calls with a runtime adapter that supports **Kiro CLI**, **Kiro IDE (terminal)**, **Kiro IDE (prompt API)**, and a legacy **Claude CLI** fallback.

## Power vs. Skill — what changed

| Claude Skill | Kiro Power |
|---|---|
| `SKILL.md` (required) | `POWER.md` (required) |
| `scripts/`, `references/`, `assets/` (optional) | `scripts/`, `steering/`, `hooks/`, `eval-viewer/`, `assets/`, `examples/`, `mcp.json` — all optional |
| Triggered via Claude's `available_skills` list | Triggered via Kiro's description-based routing |
| `claude -p` subprocess for eval | `scripts/runtime.py` backend abstraction |
| Subagent parallelism on Claude Code | Process-pool parallelism + Kiro CLI / IDE adapter |

**Only `POWER.md` is required.** Every other directory listed here is optional and Kiro will load it only if present.

## High-level workflow

1. **Capture intent.** What should the Power do? When should it trigger? Output format? Test cases needed?
2. **Draft `POWER.md`.** Frontmatter (`name`, `description`, optional `keywords`) + imperative-form body, < 500 lines.
3. **Author bundled resources** (only what helps): `steering/` for deep-dives, `scripts/` for deterministic helpers, `hooks/` for automation, `assets/` for output templates.
4. **Run trigger evals.** Use `scripts/run_eval.py` to test whether the description triggers correctly. Backend selected automatically via `runtime.py`.
5. **Review with the user.** Generate HTML report via `eval-viewer/generate_review.py` (or `scripts/generate_report.py` for the description loop). Two tabs: Outputs and Benchmark.
6. **Iterate.** Use `scripts/run_loop.py` to auto-improve the description across iterations with train/test split.
7. **Package.** `scripts/package_power.py` produces a `.power` zip the user can install.

Your job: figure out which stage the user is at and pick up from there. The user may say "I have a draft, help me evaluate" — skip straight to step 4. They may say "just vibe with me, no evals" — that's fine too.

## Runtime backends (THE adaptation)

The eval scripts must invoke a model to test triggering. The original `skill-creator` shells out to `claude -p`. Power Creator routes through `scripts/runtime.py`, which selects a backend at runtime:

| Backend | Selector | Invocation |
|---|---|---|
| `kiro_cli` | `KIRO_POWER_RUNTIME=kiro_cli` or `which kiro` | `kiro -p "<query>" --output-format stream-json` *(flags configurable via env)* |
| `kiro_ide_terminal` | `KIRO_POWER_RUNTIME=kiro_ide_terminal` (Kiro IDE built-in terminal) | shells out to `$KIRO_IDE_BIN` with the IDE's session env |
| `kiro_ide_prompt` | `KIRO_POWER_RUNTIME=kiro_ide_prompt` | writes prompt to `$KIRO_IDE_PROMPT_FIFO` or stdin pipe |
| `claude_cli` | `KIRO_POWER_RUNTIME=claude_cli` or `which claude` (fallback) | legacy `claude -p` |
| `mock` | `KIRO_POWER_RUNTIME=mock` | deterministic responses for tests |

**Env vars** (all optional):
- `KIRO_POWER_RUNTIME` — force a backend; otherwise auto-detect (`kiro_cli` > `claude_cli` > `mock`)
- `KIRO_BIN` — path to Kiro CLI binary (default: `kiro`)
- `KIRO_PROMPT_FLAG` — flag the Kiro CLI expects (default: `-p`)
- `KIRO_OUTPUT_FORMAT_FLAG` — stream flag (default: `--output-format stream-json`)
- `KIRO_IDE_PROMPT_FIFO` — for `kiro_ide_prompt` backend

See `steering/runtime-backends.md` for the full matrix, trigger-detection logic, and how to add a new backend.

## Authoring a POWER.md

Frontmatter is YAML between `---` markers. Required keys: `name` (kebab-case, ≤64 chars), `description` (≤1024 chars, no `<` or `>`). Optional: `keywords`, `author`, `metadata`, `compatibility`, `allowed-tools`.

```yaml
---
name: my-power
description: One pushy sentence that names the user intent AND lists trigger contexts.
keywords: [keyword1, keyword2]
---
```

**Description writing tips** (matter because the description is the only triggering signal Kiro sees):
- Imperative voice: "Use this Power for X" not "this Power does X".
- Focus on user *intent*, not implementation.
- Be a little pushy — Kiro under-triggers by default. List concrete contexts/phrases.
- Stay under 1024 chars; `scripts/quick_validate.py` enforces this.

**Body writing tips**:
- < 500 lines; if approaching that, split into `steering/*.md` and reference them.
- Imperative form for instructions.
- Explain the *why* — modern LLMs respond to theory-of-mind, not rigid MUSTs.
- Bundle repeated work as a script and tell the Power to call it.

## Running trigger evals (the core eval loop)

The trigger eval measures whether Kiro consults this Power for a query. Eval set is a JSON array of `{query, should_trigger}` records.

```bash
python -m scripts.run_eval \
  --eval-set examples/eval-set-sample.json \
  --power-path . \
  --runs-per-query 3 \
  --verbose
```

What it does: writes a temporary POWER.md trampoline into `<workspace>/.kiro/powers/<unique>/`, invokes the model via `runtime.invoke(query, power_dir)`, parses the response stream for a tool call that references the trampoline name, aggregates trigger rates, prints JSON.

For the **full optimization loop** (auto-improves the description across iterations):

```bash
python -m scripts.run_loop \
  --eval-set <eval.json> \
  --power-path . \
  --model <model-id> \
  --max-iterations 5 \
  --holdout 0.4 \
  --verbose
```

Train/test split prevents overfitting: 60% train drives improvement, 40% test selects the best iteration. Outputs `best_description` chosen by test score.

## Reviewing results with the user

Always show the user the outputs **before** drawing your own conclusions. Two viewers:

1. **Per-iteration eval viewer** (qualitative + benchmark):
   ```bash
   python eval-viewer/generate_review.py <workspace>/iteration-N \
     --power-name <name> --benchmark <workspace>/iteration-N/benchmark.json
   ```
   In Kiro IDE: prefer `--static <output.html>` so Kiro's built-in browser can open the file directly. In Kiro CLI w/ display: omit `--static` for a live server.

2. **Description-loop report**:
   `scripts/run_loop.py --report auto` writes an auto-refreshing HTML next to the run results. In Kiro IDE, point the IDE preview at the file path.

## Hooks

Three manual hooks ship in `hooks/`. All are `when.type: manual` — Kiro shows them as buttons; the user clicks to fire.

- `eval-on-demand.kiro.hook` — runs `scripts/run_eval.py` against the current Power
- `improve-on-demand.kiro.hook` — runs `scripts/run_loop.py` (long-running)
- `validate-on-save.kiro.hook` — `when.type: fileSave` on `POWER.md`; runs `scripts/quick_validate.py`

Delete any you don't want. None are required for the eval scripts to work.

## Packaging

```bash
python -m scripts.package_power <path/to/power-folder>
```

Produces `<name>.power` (zip) excluding `__pycache__`, `*.pyc`, `.DS_Store`, `node_modules`, and the workspace `evals/` dir.

## File tree (full)

```
power-creator/
├── POWER.md
├── steering/
│   ├── eval-process.md          # viewer details, grading
│   ├── runtime-backends.md      # backend matrix + how to extend
│   ├── description-optimization.md
│   ├── packaging.md
│   ├── agent-grader.md          # from skill-creator agents/
│   ├── agent-comparator.md
│   ├── agent-analyzer.md
│   ├── ref-schemas.md           # from skill-creator references/
│   └── kiro-vs-claude.md
├── hooks/
│   ├── eval-on-demand.kiro.hook
│   ├── improve-on-demand.kiro.hook
│   └── validate-on-save.kiro.hook
├── scripts/
│   ├── __init__.py
│   ├── runtime.py               # NEW backend abstraction
│   ├── run_eval.py              # adapted
│   ├── run_loop.py              # adapted
│   ├── improve_description.py   # adapted (POWER.md aware)
│   ├── aggregate_benchmark.py
│   ├── generate_report.py
│   ├── package_power.py
│   ├── quick_validate.py        # validates POWER.md
│   ├── utils.py
│   ├── validate-eval.sh         # NEW: end-to-end mock eval
│   └── smoke-test.sh            # NEW: full pipeline
├── eval-viewer/
│   └── generate_review.py
├── assets/
│   └── eval_review.html         # HTML template for description-tuning UI
├── examples/
│   ├── sample-power/
│   │   └── POWER.md
│   └── eval-set-sample.json
└── references/                  # merged into steering/ at install time
```

## Final loop, condensed

- Figure out what the Power is about
- Draft / edit `POWER.md`
- Run eval against test prompts via `runtime.invoke()`
- Generate HTML review for the human BEFORE judging yourself
- Run quantitative benchmark
- Improve, repeat until satisfied
- Package the `.power` and hand it to the user
