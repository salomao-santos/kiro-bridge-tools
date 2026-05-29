# Skill ↔ Power — Migration Toolkit

Bidirectional migration between **Claude Code Skills** and **Kiro Powers**, plus a **Power Creator** for authoring Powers from scratch.

## Languages / Idiomas

- 🇧🇷 [Português (BR)](./README-ptbr.md)
- 🇺🇸 [English](./README-en.md)
- 🇪🇸 [Español](./README-es.md)

## Quick Overview

This repo contains three meta-tools:

| Tool | Direction | Purpose |
|------|-----------|---------|
| [`skills/skill-to-power/`](./skills/skill-to-power/) | Skill → Power | Migrate a Claude Code Skill into a Kiro Power |
| [`skills/skill-creator/`](./skills/skill-creator/) | — | Author, evaluate, and optimize Kiro Skills (SKILL.md) |
| [`skills/power-creator/`](./skills/power-creator/) | — | Author, evaluate, and optimize Kiro Powers from scratch |

## Who is this for?

Anyone moving between AI coding tools — **Claude Code, Antigravity, Cursor, Codex, GitHub Copilot** — and **Kiro IDE / Kiro CLI**.

- Coming **from Claude Code into Kiro?** Use `skill-to-power` to convert your Skills, or `power-creator` to author Powers from scratch.
- Staying in Claude Code? Use `skill-creator` to author and improve Kiro-compatible Skills.

## References

- [A Guide for Migrating Claude Code Skills to Kiro Powers — AWS Builder](https://builder.aws.com/content/39DLiJ3W2dTp53IqbWNxsJYgcHB/a-guide-for-migrating-claude-code-skills-to-kiro-powers)
- [Anthropic Skills repository](https://github.com/anthropics/skills)
- [Anthropic `skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
- [Anthropic `internal-comms`](https://github.com/anthropics/skills/tree/main/skills/internal-comms)
- [AWS sample Power with scripts (`aidlc_power`)](https://github.com/aws-samples/sample-power-aidlc-all/tree/main/aidlc_power)
