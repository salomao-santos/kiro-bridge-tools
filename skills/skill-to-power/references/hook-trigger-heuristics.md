# Hook Trigger Heuristics

Phrase patterns in source SKILL.md → recommended hook `when.type` and filter.

## Phrase → hook type

| Source signal (regex, case-insensitive) | `when.type` | Default filter / pattern | Notes |
|---|---|---|---|
| `auto.?trigger\|whenever\|each time\|at start of conversation\|on every prompt` | `promptSubmit` | none | `then.type: askAgent` with body-derived prompt |
| `on save\|when .+ saved\|after saving\|file save` | `fileSave` | `when.patterns: ["**/*.<ext>"]` (extract `<ext>` from body) | If no ext mentioned, use `["**/*"]` |
| `on create\|when .+ created\|new file` | `fileCreate` | same pattern logic | — |
| `on delete\|when .+ deleted` | `fileDelete` | same pattern logic | — |
| `before .* commit\|pre-commit` | `preToolUse` | `when.toolName: shell`, `when.argMatch: "git commit"` | — |
| `after .* commit\|post-commit` | `postToolUse` | same as above | — |
| `before .* tool\|pre.tool.use` | `preToolUse` | extract tool from body | — |
| `after .* tool\|post.tool.use` | `postToolUse` | extract tool from body | — |
| `after task\|when task .+ completes\|post.task` | `postTaskExecution` | none | — |
| `before task\|pre.task` | `preTaskExecution` | none | — |
| `when agent stops\|on agent stop\|when response complete` | `agentStop` | none | — |
| `on demand\|review my\|manually invoke` | `manual` | none | User triggers explicitly |

## Built-in tool category filters (use in `when.toolName`)

- `read` — all built-in file read tools
- `write` — all built-in file write tools
- `shell` — all built-in shell command tools
- `web` — all built-in web tools
- `spec` — all built-in spec tools
- `*` — all tools (built-in + MCP)

## Prefix filters

- `@mcp` — all MCP tools (regex: `@mcp.*`)
- `@powers` — all Powers tools
- `@builtin` — all built-in tools
- Custom regex: `@mcp.*sql.*` matches any MCP SQL tool

## Direct mapping from builders-style `hooks:` block

Source frontmatter:
```yaml
hooks:
  PreToolUse:
    - matcher: Bash(aws bedrock-agentcore-control create-*)
      command: aws sts get-caller-identity --query Account --output text
      once: true
```

Maps to `hooks/<slug>.kiro.hook`:
```json
{
  "enabled": true,
  "name": "Auto-fetch caller identity",
  "description": "Runs aws sts get-caller-identity before bedrock-agentcore-control create-* calls",
  "version": "1",
  "when": {
    "type": "preToolUse",
    "toolName": "shell",
    "argMatch": "aws bedrock-agentcore-control create-"
  },
  "then": {
    "type": "askAgent",
    "prompt": "Run: aws sts get-caller-identity --query Account --output text. Use the result as context."
  }
}
```

The `once: true` source field has no direct Kiro equivalent — preserve as note in hook `description`.

## Conflict resolution

If multiple phrases match in the source body, prefer the most specific:
1. Explicit `hooks:` frontmatter wins over body phrases.
2. File-pattern hooks (`fileSave/Create/Delete`) win over tool hooks.
3. Tool hooks win over prompt/agent hooks.
4. `manual` is the fallback when intent is unclear.

When no signal matches with confidence, ask the user (per SKILL.md step 4) rather than guessing.
