---
name: auto-formatter
description: Format Python files. Use whenever a .py file is saved in the workspace. Runs black and isort, then reports diffs.
---

# auto-formatter

Lightweight skill that auto-formats Python source files on save.

## Workflow

1. Detect saved file extension. Skip if not `.py`.
2. Run `black <file>` then `isort <file>`.
3. Diff before/after; report changed line ranges to user.
4. If formatter exits non-zero, surface error and abort.

## Style Rules

- Line length: 100
- Quote style: double
- Trailing comma: required on multi-line collections
- Import groups: stdlib, third-party, local — separated by blank lines
