# Skill Frontmatter Variants

Real-world skill frontmatter shapes observed in the wild. Converter must handle every variant.

## Variant 1: Anthropic minimal (skill-creator, internal-comms, pdf-to-markdown)

```yaml
---
name: skill-name
description: One-paragraph description with "use when..." routing.
license: Complete terms in LICENSE.txt    # optional
---
```

Mapping: trivial. `name` → `name` + Title Case → `displayName`. `description` → split. Author defaults to `"Community"`.

## Variant 2: AWS-ops minimal (env-discovery, health-check, etc.)

```yaml
---
name: env-discovery
description: >
  Use when investigating what AWS services are running, ...
  Uses tag-based Fleet Intelligence: ...
---
```

Mapping: same as Variant 1. Note multi-line `>` folded scalar — preserve newlines.

## Variant 3: DevOps-agent with `triggers` (eks-resilience, aws-wa-review)

```yaml
---
name: eks-resilience-checker-skill-devops
description: Assess Amazon EKS cluster resilience...
triggers: "EKS resilience", "EKS readiness", "Kubernetes resilience check", "韧性评估", "集群评估"
---
```

Mapping: split `triggers` on commas (handle quoted strings), append to `keywords[]`. Preserve CJK.

## Variant 4: EKS-operation-review (Claude Code native)

```yaml
---
name: eks-operation-review
description: >
  Run a structured EKS operational excellence assessment...
  Only activate when the user explicitly requests an EKS operational review...
  Do NOT activate for general Kubernetes questions...
---
```

Companion files:
- `.mcp.json` at skill root → copy to `mcp.json`
- `.claude/commands/eks-operation-review.md` → `steering/command-eks-operation-review.md` with routing note
- `steering/` already present → merge

Mapping: negative-activation language preserved verbatim in `description`.

## Variant 5: Builders rich frontmatter (aws-agentic-ai)

```yaml
---
name: aws-agentic-ai
aliases:
  - bedrock-agentcore
description: "AWS Bedrock AgentCore comprehensive expert..."
context: fork
model: sonnet
skills:
  - aws-mcp-setup
allowed-tools:
  - mcp__aws-mcp__*
  - Bash(aws bedrock-agentcore *)
hooks:
  PreToolUse:
    - matcher: Bash(aws bedrock-agentcore-control create-*)
      command: aws sts get-caller-identity --query Account --output text
      once: true
---
```

Mapping:
- `aliases[0]` → `displayName` (override Title Case of name)
- `aliases[1..]` → POWER.md body HTML comment
- `context: fork` → drop (Skill-only concept)
- `model: sonnet` → drop with note
- `skills: [...]` → POWER.md body `## Dependencies` section
- `allowed-tools` → hook `when.toolName` filters if hook generated; otherwise list in POWER.md body
- `hooks.PreToolUse[*]` → one `hooks/*.kiro.hook` per matcher (see `hook-trigger-heuristics.md`)

Also-present:
```yaml
metadata:
  author: sample-skills-for-builders
  version: "1.0.0"
license: MIT
```

Mapping: `metadata.author` → POWER.md `author`. `metadata.version` → body comment. `license` → body footer.

## Variant 6: Migration state machine (gcp-to-aws)

```yaml
---
name: gcp-to-aws
description: "Migrate workloads from GCP to AWS. Triggers on: ... Runs a 6-phase process: discover, clarify, design, estimate, generate, feedback..."
---
```

Companion files: `references/discover/`, `references/clarify/`, etc. (one dir per phase, ~800 lines each).

Mapping: each phase ref → `steering/phase-<n>-<name>.md`. POWER.md body documents phase order. State machine becomes implicit through steering file ordering.

## Variant 7: aws-migration-toolkit `features/`

```
features/
└── migration-to-aws/
    ├── skills/
    │   └── gcp-to-aws/SKILL.md
    ├── rules/
    ├── .mcp.json
    └── mcp.json
```

Mapping: descend to `skills/gcp-to-aws/` as the actual source. Top-level `mcp.json` copies to power root. `rules/*` → `steering/rule-<name>.md`.

## Required parsing rules

- YAML frontmatter delimited by `---` lines at top of file
- Folded (`>`) and literal (`|`) scalars preserved
- Quoted strings with embedded commas (in `triggers`) parsed as single values
- UTF-8 throughout; no transliteration
- Unknown keys preserved in `extra_frontmatter` JSON blob for the agent to inspect
