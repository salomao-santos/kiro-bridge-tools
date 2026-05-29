# Skill ↔ Power — Migration Toolkit (EN)

[← Back to main README](./README.md) · [🇧🇷 PT-BR](./README-ptbr.md) · [🇪🇸 ES](./README-es.md)

## Overview

This project is built on top of **official documentation** and **public examples** from the Claude Code (Anthropic) and Kiro (AWS) ecosystems. It ships three meta-tools that cover the full migration cycle between **Claude Code Skills** and **Kiro Powers**.

| Tool | Direction | Purpose |
|------|-----------|---------|
| [`skills/skill-to-power/`](./skills/skill-to-power/) | Skill → Power | Convert a Claude Code Skill into a Kiro Power |
| [`skills/skill-creator/`](./skills/skill-creator/) | — | Author, evaluate, and optimize Kiro Skills (SKILL.md) |
| [`skills/power-creator/`](./skills/power-creator/) | — | Author, evaluate, and optimize Kiro Powers from scratch |

## Who is this for?

Anyone using another AI tool — **Claude Code, Antigravity, Cursor, Codex, GitHub Copilot** — who wants to migrate to **Kiro IDE** or **Kiro CLI**, or the reverse direction.

- **Coming from Claude Code into Kiro?** Use `skill-to-power` (if you already have Skills) or `power-creator` (from scratch).
- **Staying in Claude Code?** Use `skill-creator` to author and improve Kiro-compatible Skills.

## Skill structure (Claude Code)

```
my-skill/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories
```

## Kiro Power structure

```
my-power/
├── POWER.md                # self-sufficient
├── steering/               # deep-dives only
├── hooks/                  # 3 manual hooks
├── scripts/                # runtime.py + 9 adapted + 2 validators
├── eval-viewer/            # optional viewer
├── examples/               # toy power + eval-set
└── references/             # merged into steering/
```

## Skill ↔ Power mapping

| Claude Skill | Kiro Power | Purpose |
|--------------|------------|---------|
| `SKILL.md` | `POWER.md` | Core documentation (always loaded) |
| `references/*.md` | `steering/*.md` | Deep-dive content (loaded on-demand) |
| `.claude-plugin/marketplace.json` | `POWER.md` frontmatter | Metadata (name, description, keywords) |
| `CLAUDE.md` | `steering/contributing-guidelines.md` or `steering/development-guide.md` or `steering/maintenance-notes.md` | Contributor docs (optional) |
| `README.md` | Not needed | User-facing docs (handled by Powers UI) |
| `scripts/` | `scripts/` | Executable scripts (copied verbatim) |
| `examples/` | `examples/` | Usage examples (copied verbatim) |
| `.mcp.json` | `mcp.json` | MCP server configuration |
| `.claude/commands/` | `hooks/` (Manual Trigger) | Slash commands → manual hooks |
| Triggering via Claude's `available_skills` | Kiro's description-based routing | Activation mechanism |
| `claude -p` subagent | `scripts/runtime.py` (Kiro CLI / IDE adapter) | Eval execution backend |

## Kiro hook types

Hooks trigger automations at specific points:

- **Prompt Submit** — when the user submits a prompt (access via `USER_PROMPT`)
- **Agent Stop** — when the agent finishes its response
- **Pre Tool Use** / **Post Tool Use** — before/after a tool invocation (filters: `read`, `write`, `shell`, `web`, `spec`, `*`, `@mcp`, `@powers`, `@builtin`)
- **File Create** / **File Save** / **File Delete** — by file pattern
- **Pre/Post Task Execution** — before/after a spec task
- **Manual Trigger** — on-demand execution

## References

- [A Guide for Migrating Claude Code Skills to Kiro Powers — AWS Builder](https://builder.aws.com/content/39DLiJ3W2dTp53IqbWNxsJYgcHB/a-guide-for-migrating-claude-code-skills-to-kiro-powers)
- [Anthropic Skills repository](https://github.com/anthropics/skills)
- [Anthropic `skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
- [Anthropic `internal-comms`](https://github.com/anthropics/skills/tree/main/skills/internal-comms)
- [AWS sample Power with scripts (`aidlc_power`)](https://github.com/aws-samples/sample-power-aidlc-all/tree/main/aidlc_power)
