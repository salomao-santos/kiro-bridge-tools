---
name: "auto-formatter"
displayName: "Auto Formatter"
description: "Format Python files. Runs black and isort, then reports diffs."
keywords: ["python", "format", "black", "isort", "lint", "style", "autoformat"]
author: "Salomão Santos"
---

# Auto Formatter

## Overview

Lightweight power that auto-formats Python source files on save.

## Steering Files

- [workflow.md](steering/workflow.md) — formatter workflow steps
- [style.md](steering/style.md) — style rules + project conventions

## Scripts

| Script | Platform | Description |
|---|---|---|
| `check.sh` | macOS / Linux | Verifies a file passes black + isort without changes |

## Hooks

- `hooks/auto-format.kiro.hook` — fires on save of `**/*.py`, runs the formatter workflow
