---
name: agent-creator
description: Create Kiro agent JSON files from scratch or from a description. Use when user says "create a kiro agent", "new kiro agent", "generate agent json", "kiro agent for X", "build agent", "write agent config", or wants to configure tools, resources, mcpServers, hooks, toolsSettings, allowedTools, toolAliases, or welcomeMessage for a Kiro agent. Auto-triggers on phrases like "create agent", "write agent json", "agent creator", "build kiro agent", "new .kiro/agents file", "kiro agent creator", "generate kiro agent".
metadata:
  source: kiro-bridge-tools/skills/agent-creator
---

# Agent Creator

Skill for creating valid Kiro agent JSON files (`.kiro/agents/<name>.json`).
Covers all configurable fields: tools, allowedTools, toolsSettings, resources, mcpServers, hooks, toolAliases, welcomeMessage, and model.

## Output

A single file: `.kiro/agents/<name>.json` in the user's project.

```
<project-root>/
└── .kiro/
    └── agents/
        └── <name>.json
```

## Procedure

### 1. Gather intent

Ask (or infer from context):
- What is the agent's specialty/domain?
- What tasks will it perform?
- What tools does it need? (file system, shell, AWS, Docker, databases, etc.)
- Does it need MCP servers?
- Does it need to run commands on startup (hooks)?
- Which tools require user confirmation vs. auto-allow?

Skip questions already answered by the user's request.

### 2. Draft name and description

- `name`: kebab-case, lowercase, ≤64 chars. Matches the filename without `.json`.
- `description`: one sentence, imperative voice. What the agent does + its domain.
- `prompt`: system-level instruction. Include: role, behavior constraints, key responsibilities, any safety rules (e.g., "always verify before executing").

### 3. Select tools

Choose from available Kiro tools:

| Tool | Purpose |
|------|---------|
| `fs_read` / `read` | Read files |
| `fs_write` / `write` | Write/create files |
| `execute_bash` / `shell` | Run shell commands |
| `grep` | Search file contents |
| `glob` | Match file patterns |
| `use_aws` / `aws` | AWS SDK calls |
| `@<server>` | All tools from an MCP server |
| `@<server>/<tool>` | Specific MCP tool |

For MCP servers: list them in `mcpServers` and reference as `@<server-name>` in `tools`.

### 4. Configure allowedTools

`allowedTools` = subset of `tools` that auto-execute without user confirmation.

Rules of thumb:
- Read-only tools → safe to auto-allow (`fs_read`, `grep`, `glob`, read-only MCP tools)
- Write/destructive tools → require confirmation (exclude from `allowedTools`)
- For AWS: set `"autoAllowReadonly": true` in `toolsSettings.use_aws` instead of listing each read-only API

### 5. Configure toolsSettings

Per-tool constraints. Common patterns:

```json
"toolsSettings": {
  "use_aws": { "autoAllowReadonly": true },
  "execute_bash": { "autoAllowReadonly": true },
  "write": { "allowedPaths": ["src/**", "*.yaml"] },
  "shell": { "allowedCommands": ["npm test", "git diff", "docker-compose ps"] }
}
```

### 6. Add resources

Files/URIs always injected into context when the agent runs.

| Pattern | Example |
|---------|---------|
| Local file | `"file://README.md"` |
| Glob | `"file://docs/**/*.md"` |
| Skill | `"skill://.kiro/skills/**/SKILL.md"` |
| Remote URL | `"https://docs.example.com/api"` |

Keep list focused: only files the agent needs for every interaction.

### 7. Configure mcpServers (optional)

Two server types:

**stdio (command-based):**
```json
"mcpServers": {
  "my-server": {
    "command": "my-mcp-server",
    "args": ["--flag", "value"],
    "env": { "SECRET": "$ENV_VAR" },
    "timeout": 30000
  }
}
```

**HTTP:**
```json
"mcpServers": {
  "my-server": {
    "url": "https://api.example.com/mcp",
    "type": "http"
  }
}
```

### 8. Configure hooks (optional)

Commands run automatically. Two hook points:

| Hook | When it runs |
|------|-------------|
| `agentSpawn` | Once when agent loads |
| `userPromptSubmit` | Before each user message is processed |

Use `agentSpawn` for: AWS identity check, docker status, git state.
Use `userPromptSubmit` for: fast-changing state (file counts, running containers).

Hook fields:
- `command` (required): shell command
- `timeout_ms`: max wait in ms
- `cache_ttl_seconds`: reuse previous output for N seconds
- `max_output_size`: truncate output at N bytes

### 9. Set toolAliases (optional)

Friendly names for long MCP tool paths:

```json
"toolAliases": {
  "@docker/docker_ps": "containers",
  "@database/query_read_only": "query"
}
```

### 10. Set model (optional)

Default: inherits from Kiro workspace setting.
Override: `"model": "claude-sonnet-4"` or `"claude-opus-4"`.

### 11. Set welcomeMessage (optional)

Short greeting shown when user switches to this agent. One sentence: what it does and what to say first.

### 12. Write the file

Write to `.kiro/agents/<name>.json`. Use `templates/agent.json.template` as base.
Confirm path with user if `.kiro/agents/` doesn't exist yet.
Omit any optional fields not needed — do not write empty arrays or objects.

## Field reference

```
name              string   required  kebab-case agent identifier
description       string   required  one-line summary
prompt            string   required  system instructions
model             string   optional  model override
tools             array    optional  all available tools (including MCPs)
allowedTools      array    optional  auto-executed subset of tools
toolsSettings     object   optional  per-tool constraints
toolAliases       object   optional  shorthand names for MCP tool paths
resources         array    optional  files/URIs always in context
mcpServers        object   optional  MCP server definitions
hooks             object   optional  { agentSpawn: [...], userPromptSubmit: [...] }
welcomeMessage    string   optional  greeting shown on agent load
```

## Files in this skill

- `SKILL.md` — this file
- `templates/agent.json.template` — full-featured template with all fields
- `references/schema.md` — complete field schema with types and constraints
- `examples/aws-specialist-agent.json` — AWS infra agent
- `examples/code-review-agent.json` — code review agent
- `examples/mobile-app-agent.json` — backend agent with Docker + database MCPs
