---
name: skill-to-power
description: Convert a Claude Code Skill directory into an equivalent Kiro Power directory. Use when user says "convert skill to power", "migrate skill to kiro", "skill to power", or provides a SKILL.md path and asks for Power output.
---

# skill-to-power

Meta-skill that ingests a Claude Code Skill directory and emits a Kiro Power directory with valid `POWER.md`, split `steering/`, optional `hooks/`, optional `mcp.json`, and verbatim `scripts/`. Runs a validator at the end.

## Inputs

- `SOURCE_PATH` — absolute path to a Skill directory (the dir containing `SKILL.md`), or to a parent dir that contains multiple skills (one `SKILL.md` per subdirectory).
- `OUTPUT_PATH` *(optional)* — absolute path for the generated Power. Default: `<parent-of-SOURCE>/<skill-name>-power/`.

## Outputs

A Kiro Power directory:
```
<name>-power/
├── POWER.md                # required
├── steering/               # one or more workflow .md files
├── hooks/                  # optional, *.kiro.hook JSON files
├── mcp.json                # optional, MCP server config
├── scripts/                # optional, copied verbatim
└── examples/               # optional, copied verbatim
```

## Procedure

### 1. Locate source
- Verify `SOURCE_PATH/SKILL.md` exists. If `SOURCE_PATH` is a parent dir, list each child containing a `SKILL.md` and process each in a loop. Skip `.zip`-only inputs and tell the user to unzip first.
- Run `scripts/extract-skill-meta.sh "$SOURCE_PATH"` and capture the JSON output. Fields:
  ```json
  {
    "name": "...",
    "description": "...",
    "body_md": "...",
    "h2_sections": [{"title": "...", "slug": "...", "body": "..."}],
    "has_scripts": true,
    "has_agents": false,
    "has_examples": false,
    "has_references": false,
    "has_steering": false,
    "has_mcp_json": false,
    "has_claude_commands": false,
    "extra_frontmatter": {"triggers": "...", "aliases": [...], "hooks": {...}, "metadata": {...}, "license": "..."}
  }
  ```

### 2. Decide output path
Default `<parent>/<name>-power/`. If it exists, append `-2`, `-3`, etc. Confirm with user on collision.

### 3. Detect ambiguity signals
Scan source `description` + body for:
- Trigger phrases: `auto-trigger | whenever | each time | after every | on save | at start of conversation`
- MCP hints: `MCP | @mcp | mcpServers | server URLs`
- `>2` H2 sections → multi-file steering split
- `hooks:` block in source frontmatter → direct, no question
- `.mcp.json` in source → direct copy

### 4. Ask up to 3 yes/no clarifications — only if signals fire
Skip entirely when no signals. Otherwise ask:
- Hook signal: `"Source mentions <phrase>. Generate a Kiro hook (type: <inferred>)?"`
- MCP signal: `"Source mentions MCP. Generate mcp.json scaffold?"`
- Many H2 sections: `"Split body into N steering files (one per H2)?"`

### 5. Build POWER.md
Render `templates/POWER.md.template` with:
- `{{NAME}}` ← source `name` (kebab-case, lowercase)
- `{{DISPLAY_NAME}}` ← Title Case of name. If `aliases[0]` present, use it instead.
- `{{DESCRIPTION}}` ← source `description` with routing phrases stripped (`use when...`, `trigger:`, `whenever...`)
- `{{KEYWORDS_JSON_ARRAY}}` ← JSON array of 5–8 strings: top nouns/verbs from description + name tokens + `triggers` field split on commas. Preserve CJK characters.
- `{{AUTHOR}}` ← `extra_frontmatter.metadata.author` → else `git config user.name` → else `"Community"`
- `{{OVERVIEW}}` ← first paragraph of source body
- `{{STEERING_INDEX}}` ← bulleted list of generated steering files with one-line descriptions. **If no steering dir is created, omit the `## Steering Files` heading entirely.**
- `{{SCRIPTS_TABLE}}` ← markdown table of files in `scripts/` (script | platform | description). **If no scripts dir, omit the `## Scripts` heading entirely.**

> **Optional-dir rule:** `steering/`, `hooks/`, `scripts/`, `examples/`, and `mcp.json` are ALL OPTIONAL in a Kiro Power. The minimum valid Power is a single `POWER.md` file. Do not create empty dirs. Do not emit headings for absent sections.

### 6. Split body into steering/ (conditional)
**Skip this step entirely when:**
- Body has 0–2 H2 sections AND source has no `agents/`, `references/`, or pre-existing `steering/`. In that case keep the whole body inside `POWER.md` after the frontmatter.

**Otherwise:**
- Each H2 in source body → `steering/<slugified-h2-title>.md`. Body of that file = the H2 content (heading stripped).
- Source already has `steering/`? Copy those files first, then append H2 splits without overwriting.
- Preserve CJK and other UTF-8 verbatim.
- When steering is created, replace body H2 content in POWER.md with the `## Steering Files` index pointing at the new files.

### 7. Convert agents/ (if present, optional)
Each `agents/*.md` → `steering/agent-<name>.md` (creates `steering/` if not already). If a persona body contains "use proactively", "after every X", or similar, also queue a hook in step 8.

### 8. Generate hooks/
Only when step 3 fired, source frontmatter has `hooks:`, or user opted in. Mapping (see `references/hook-trigger-heuristics.md` for full table):

| Source signal | `when.type` | Notes |
|---|---|---|
| builders-style `hooks.PreToolUse[*].matcher` | `preToolUse` | Map `matcher` → tool filter |
| "before/after every commit" | `preToolUse` / `postToolUse` | Filter `shell`, match `git commit` |
| "on save" / "when file saved" | `fileSave` | Extract file patterns from body |
| "each prompt" / "auto-context" / "at start of conversation" | `promptSubmit` | Default `then.type: askAgent` |
| "after task" | `postTaskExecution` | — |
| "on demand" / "review my X" | `manual` | — |

Render `templates/hook.kiro.hook.template` per hook. Filename: `hooks/<slug>.kiro.hook`.

### 9. Copy scripts/ verbatim (optional)
Only if source has `scripts/`. `cp -R <source>/scripts/* <output>/scripts/`. Preserve executable bits. No transformation. If absent, do not create empty `scripts/` dir.

### 10. Copy references/ → steering/ (optional)
Only if source has `references/`. Kiro has no `references/`; merge into `steering/` with original filenames (creates `steering/` if needed). Do not overwrite existing steering files (prefix with `ref-` on collision).

### 11. mcp.json
- Source has `.mcp.json` → copy to `<output>/mcp.json` (drop leading dot)
- Else user confirmed in step 4 → render `templates/mcp.json.template`
- Else skip — do not create empty file

### 12. Handle .claude/commands/ (if present)
Each command file → `steering/command-<name>.md` with header note: `> Originally a Claude Code slash command. In Kiro, invoked via description routing rather than slash syntax.`

### 13. Validate
Run `scripts/validate-power.sh "$OUTPUT_PATH"`. Report pass/fail to user with any error lines verbatim.

### 14. Multi-skill repos
If `SOURCE_PATH` contained multiple SKILL.md files, output goes to `<parent>-powers/<name>-power/` per skill. Validate each.

## Edge cases

- **No scripts:** skip `scripts/` dir entirely.
- **No auto-trigger language:** skip `hooks/` dir entirely.
- **Rich frontmatter (builders pattern):** preserve `aliases` as POWER.md HTML comment block at end of body; convert `hooks:` to real `.kiro.hook` files; map `allowed-tools` glob patterns to `when` tool filters; lift `metadata.author` → `author`.
- **`triggers:` field (devops-agent pattern):** split on commas, dedupe, append to `keywords[]`.
- **Bilingual CJK descriptions:** UTF-8 pass-through, no transliteration.
- **Source already has `steering/`:** merge; do not overwrite.
- **`.zip` distribution:** refuse, ask user to unzip.
- **Name collision in output:** append numeric suffix, do not overwrite.

## Files in this skill

- `SKILL.md` — this file
- `templates/POWER.md.template` — POWER.md skeleton
- `templates/steering.md.template` — steering doc skeleton
- `templates/hook.kiro.hook.template` — hook JSON skeleton
- `templates/mcp.json.template` — MCP scaffold
- `references/mapping-rules.md` — full source-field → target-field map
- `references/hook-trigger-heuristics.md` — phrase → hook type table
- `references/frontmatter-variants.md` — known skill frontmatter shapes
- `scripts/extract-skill-meta.sh` — parse SKILL.md → JSON
- `scripts/validate-power.sh` — validate generated Power dir
- `examples/input-skill/python-skill/` — sample source skill (simple, with hook trigger)
- `examples/output-kiro-power/python-power/` — expected output (POWER + steering + hooks + scripts)
- `examples/input-skill/pptx-skill/` — sample source skill (rich body, sibling .md files, no auto-trigger)
- `examples/output-kiro-power/pptx-power/` — expected output (POWER + steering + scripts, NO hooks)

## Verification

Run on each bundled sample:
- `scripts/extract-skill-meta.sh examples/input-skill/python-skill` → valid JSON. Manual conversion should reproduce `examples/output-kiro-power/python-power/`. `scripts/validate-power.sh examples/output-kiro-power/python-power/` must exit 0.
- `scripts/extract-skill-meta.sh examples/input-skill/pptx-skill` → valid JSON. Manual conversion should reproduce `examples/output-kiro-power/pptx-power/`. `scripts/validate-power.sh examples/output-kiro-power/pptx-power/` must exit 0.
