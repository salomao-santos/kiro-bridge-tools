# Mapping Rules: Skill → Power

Source-field → target-field map for every known skill frontmatter shape.

## Frontmatter mapping

| Source SKILL.md field | Target POWER.md field | Transformation |
|---|---|---|
| `name` | `name` | passthrough (kebab-case enforce) |
| `name` | `displayName` | Title Case unless `aliases[0]` present |
| `aliases[0]` | `displayName` | passthrough (preferred over titlecased name) |
| `aliases[1..]` | (POWER.md body comment) | Preserve in `<!-- aliases: [...] -->` block at end of body |
| `description` | `description` | Strip routing phrases (`use when...`, `trigger phrases:`, `whenever...`). Keep first clause. |
| `description` | `keywords[]` | Extract 5–8 top nouns/verbs |
| `triggers` (comma-separated) | `keywords[]` | Split on commas, dedupe, append |
| `metadata.author` | `author` | passthrough |
| `metadata.version` | (POWER.md body comment) | `<!-- source-version: X.Y.Z -->` |
| `license` | (POWER.md body footer) | `Licensed under <X>.` line at bottom |
| `model` | (dropped) | Kiro Powers do not pin model; log a note |
| `context` | (dropped) | Skill-only field; log a note |
| `skills[]` (dependency list) | POWER.md body | List under `## Dependencies` |
| `allowed-tools[]` | hook `when` filters | If hook generated, set `when.toolName` patterns |
| `hooks.PreToolUse` | `hooks/*.kiro.hook` | One file per matcher entry |
| `hooks.PostToolUse` | `hooks/*.kiro.hook` | Same as above, `when.type: postToolUse` |

## Body mapping

| Source location | Target | Notes |
|---|---|---|
| First paragraph of body | POWER.md `## Overview` | passthrough |
| H2 sections in body | `steering/<slug>.md` | One file per H2 |
| Zero H2s in body | `steering/workflow.md` | Whole body |
| `scripts/*` | `scripts/*` | Verbatim copy, preserve `+x` |
| `examples/*` | `examples/*` | Verbatim copy |
| `references/*` | `steering/*` | Merged, prefix `ref-` on collision |
| `agents/*.md` | `steering/agent-<name>.md` | Persona → steering |
| `assets/*` | `assets/*` | Verbatim copy |
| `tools/*` | `scripts/*` | Merged (Kiro convention) |
| `.mcp.json` | `mcp.json` | Drop leading dot |
| `.claude/commands/*` | `steering/command-<name>.md` | Add note about routing |
| Top-level sibling `*.md` (e.g. `editing.md`, `pptxgenjs.md` — not SKILL.md/README/LICENSE) | `steering/<name>.md` | Anthropic pptx pattern: SKILL.md body references peer .md files. Move each into steering/. |

## Special cases

- **Negative activation** ("do NOT activate for X") → preserve verbatim in `description`. Kiro's routing handles negation via description content.
- **Bilingual descriptions** (CJK + EN) → UTF-8 pass-through. Keywords include CJK terms unchanged.
- **State-machine skills** with conditional `references/` → each phase reference → `steering/phase-<n>-<name>.md`. POWER.md body documents the phase order.
- **Multi-skill repo** (multiple SKILL.md files under one parent) → produce one Power per skill in `<parent>-powers/<name>-power/`.

## Required POWER.md frontmatter (per Kiro spec)

```yaml
name: string             # kebab-case identifier
displayName: string      # human-readable title
description: string      # routing + summary
keywords: [string]       # 1+ items, used for search/routing
author: string           # human or org
```

## Optional POWER.md frontmatter

None known beyond the five above. Additional keys are ignored by Kiro but harmless.
