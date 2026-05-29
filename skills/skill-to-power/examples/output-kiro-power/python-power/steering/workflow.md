# Workflow

1. Detect saved file extension. Skip if not `.py`.
2. Run `black <file>` then `isort <file>`.
3. Diff before/after; report changed line ranges to user.
4. If formatter exits non-zero, surface error and abort.
