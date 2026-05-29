# Packaging a Power

`scripts/package_power.py` produces a `.power` zip the user can install in Kiro.

```bash
python -m scripts.package_power <path/to/power-folder> [output-dir]
```

## What it does

1. Validates the Power via `scripts/quick_validate.py` (POWER.md frontmatter checks).
2. Walks the Power directory.
3. Zips everything into `<power-name>.power`.
4. Excludes: `__pycache__`, `*.pyc`, `.DS_Store`, `node_modules`, and the root-level `evals/` directory.

## What the `.power` zip contains

Only `POWER.md` is required. Everything else is optional — package whatever's actually present:

```
my-power.power
├── POWER.md               (required)
├── steering/              (if present)
├── hooks/                 (if present)
├── scripts/               (if present)
├── eval-viewer/           (if present)
├── assets/                (if present)
├── examples/              (if present)
├── references/            (if present)
└── mcp.json               (if present)
```

## Update vs. create

When the user asks to **update** an existing installed Power:

- **Preserve the name.** Read the existing `POWER.md` frontmatter `name` field — reuse it. Don't append `-v2`.
- **Copy to a writable location first.** The installed path may be read-only. Copy to `/tmp/<name>/`, edit, package from there.
- **Stage in `/tmp/`** if direct writes to the output dir fail due to permissions.

## Validation gate

`package_power.py` refuses to package if `quick_validate.py` fails. Fix the validation errors first. Common failures:

| Error | Fix |
|---|---|
| `Missing 'name'` | add `name:` to frontmatter |
| `Missing 'description'` | add `description:` to frontmatter |
| `Description cannot contain angle brackets` | strip `<` and `>` |
| `Description is too long (>1024 chars)` | shorten, or run `scripts/run_loop.py` to auto-shrink |
| `Name should be kebab-case` | lowercase letters, digits, hyphens only |

## Installing the `.power`

The user runs Kiro's install command on the `.power` file. Exact UX depends on Kiro version — see Kiro docs.
