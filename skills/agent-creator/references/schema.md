# Kiro Agent JSON Schema

Reference for all fields in `.kiro/agents/<name>.json`.

## Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Agent identifier. kebab-case, lowercase, ≤64 chars. Must match filename without `.json`. |
| `description` | string | yes | One-line summary shown in agent picker. Imperative voice. |
| `prompt` | string | yes | System-level instructions. Defines role, behavior, and constraints. |
| `model` | string | no | Model override. E.g. `"claude-sonnet-4"`, `"claude-opus-4"`. Inherits workspace default if omitted. |
| `tools` | string[] | no | All tools available to the agent. Includes MCP references (`@server`, `@server/tool`). |
| `allowedTools` | string[] | no | Subset of `tools` that execute without user confirmation. |
| `toolsSettings` | object | no | Per-tool constraints (see below). |
| `toolAliases` | object | no | Friendly name → full MCP tool path. |
| `resources` | string[] | no | Files/URIs always injected into context. |
| `mcpServers` | object | no | MCP server definitions (see below). |
| `hooks` | object | no | Lifecycle commands (see below). |
| `welcomeMessage` | string | no | Greeting shown when user switches to this agent. |

---

## tools

List of tool identifiers the agent can invoke.

```json
"tools": [
  "fs_read",
  "fs_write",
  "execute_bash",
  "grep",
  "glob",
  "use_aws",
  "@my-server",
  "@my-server/specific_tool"
]
```

**Built-in tool IDs:**

| ID | Alias | Purpose |
|----|-------|---------|
| `fs_read` | `read` | Read file contents |
| `fs_write` | `write` | Write/create files |
| `execute_bash` | `shell` | Run shell commands |
| `grep` | — | Search inside files |
| `glob` | — | Match file paths by pattern |
| `use_aws` | `aws` | AWS SDK API calls |

**MCP references:**
- `@<server-name>` — all tools from that MCP server
- `@<server-name>/<tool-name>` — one specific tool

---

## allowedTools

Subset of `tools` that auto-execute without a confirmation prompt.

```json
"allowedTools": [
  "fs_read",
  "grep",
  "glob",
  "@server/read_only_tool"
]
```

Omit write/destructive tools here; they'll ask for confirmation.

---

## toolsSettings

Per-tool constraint objects. Keys must match tool IDs in `tools`.

### use_aws

```json
"use_aws": {
  "autoAllowReadonly": true,
  "allowedServices": ["s3", "lambda", "cloudformation", "ec2", "iam", "logs"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `autoAllowReadonly` | boolean | Skip confirmation for read-only AWS API calls |
| `allowedServices` | string[] | Restrict to specific AWS service namespaces |

### execute_bash / shell

```json
"execute_bash": {
  "autoAllowReadonly": true,
  "allowedCommands": ["git diff", "git log", "npm test", "docker-compose ps"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `autoAllowReadonly` | boolean | Skip confirmation for non-mutating commands |
| `allowedCommands` | string[] | Whitelist of exact command strings allowed |

### fs_write / write

```json
"fs_write": {
  "allowedPaths": ["src/**", "tests/**", "*.yaml", "*.json"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `allowedPaths` | string[] | Glob patterns for writable paths |

---

## toolAliases

Map verbose MCP tool paths to short names used in conversations.

```json
"toolAliases": {
  "@docker/docker_ps": "containers",
  "@docker/docker_logs": "logs",
  "@database/query_read_only": "query"
}
```

---

## resources

Context injected into the agent at every turn.

```json
"resources": [
  "file://README.md",
  "file://docs/**/*.md",
  "file://infrastructure/**/*.yaml",
  "skill://.kiro/skills/**/SKILL.md",
  "https://docs.example.com/api"
]
```

| Scheme | Example | Notes |
|--------|---------|-------|
| `file://` | `file://README.md` | Relative to project root. Supports globs. |
| `skill://` | `skill://.kiro/skills/**/SKILL.md` | Kiro skill content |
| `https://` | `https://docs.example.com` | Remote URL fetched at agent load |

---

## mcpServers

### stdio server

```json
"mcpServers": {
  "my-server": {
    "command": "my-mcp-binary",
    "args": ["--flag", "value"],
    "env": {
      "API_KEY": "$MY_ENV_VAR"
    },
    "timeout": 30000
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `command` | string | Binary/script to launch the MCP server |
| `args` | string[] | CLI arguments |
| `env` | object | Env vars. Use `$VAR` to reference process env. |
| `timeout` | number | Max startup time in ms |

### HTTP server

```json
"mcpServers": {
  "remote-server": {
    "url": "https://mcp.example.com/endpoint",
    "type": "http"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | HTTP endpoint |
| `type` | string | Must be `"http"` |

---

## hooks

### agentSpawn

Runs once when the agent loads. Output injected into context.

```json
"hooks": {
  "agentSpawn": [
    {
      "command": "aws sts get-caller-identity",
      "timeout_ms": 10000,
      "cache_ttl_seconds": 300
    }
  ]
}
```

### userPromptSubmit

Runs before each user message is processed.

```json
"hooks": {
  "userPromptSubmit": [
    {
      "command": "git diff --name-only HEAD~1",
      "timeout_ms": 3000,
      "max_output_size": 2048
    }
  ]
}
```

### Hook fields

| Field | Type | Description |
|-------|------|-------------|
| `command` | string | Shell command to run |
| `timeout_ms` | number | Max wait in milliseconds |
| `cache_ttl_seconds` | number | Reuse previous output for N seconds (agentSpawn only) |
| `max_output_size` | number | Truncate stdout at N bytes |

Multiple hooks allowed per lifecycle event — they run in array order.
