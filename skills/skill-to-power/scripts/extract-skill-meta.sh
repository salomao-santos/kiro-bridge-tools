#!/usr/bin/env bash
# extract-skill-meta.sh <path-to-skill-dir>
# Reads SKILL.md, parses frontmatter + body, emits JSON to stdout.
# Exits non-zero on missing file or parse error.

set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <path-to-skill-dir>" >&2
  exit 2
fi

SKILL_DIR="$1"
SKILL_MD="$SKILL_DIR/SKILL.md"

if [ ! -f "$SKILL_MD" ]; then
  echo "error: $SKILL_MD not found" >&2
  exit 1
fi

python3 - "$SKILL_DIR" "$SKILL_MD" <<'PYEOF'
import json
import os
import re
import sys

skill_dir = sys.argv[1]
skill_md = sys.argv[2]

with open(skill_md, "r", encoding="utf-8") as f:
    text = f.read()

# Split frontmatter and body
fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
if not fm_match:
    print(json.dumps({"error": "no frontmatter found"}), file=sys.stderr)
    sys.exit(1)

fm_text = fm_match.group(1)
body_md = fm_match.group(2)

# Parse YAML frontmatter
try:
    import yaml
    fm = yaml.safe_load(fm_text) or {}
except ImportError:
    # Crude fallback: key: value pairs only (no nesting). Good enough for variant 1/2/3.
    fm = {}
    for line in fm_text.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
            fm[key] = val

name = fm.get("name", "")
description = fm.get("description", "")
if isinstance(description, str):
    description = description.strip()

# Extract H2 sections
h2_sections = []
current = None
for line in body_md.splitlines():
    m = re.match(r"^##\s+(.+?)\s*$", line)
    if m:
        if current:
            h2_sections.append(current)
        title = m.group(1)
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        current = {"title": title, "slug": slug, "body": ""}
    elif current is not None:
        current["body"] += line + "\n"
if current:
    h2_sections.append(current)

# Subdir detection
def has(sub):
    return os.path.isdir(os.path.join(skill_dir, sub))

# Standard keys consumed into top-level fields
consumed = {"name", "description"}
extra = {k: v for k, v in fm.items() if k not in consumed}

out = {
    "name": name,
    "description": description,
    "body_md": body_md,
    "h2_sections": h2_sections,
    "has_scripts": has("scripts"),
    "has_agents": has("agents"),
    "has_examples": has("examples"),
    "has_references": has("references"),
    "has_steering": has("steering"),
    "has_assets": has("assets"),
    "has_tools": has("tools"),
    "has_mcp_json": os.path.isfile(os.path.join(skill_dir, ".mcp.json")) or os.path.isfile(os.path.join(skill_dir, "mcp.json")),
    "has_claude_commands": os.path.isdir(os.path.join(skill_dir, ".claude", "commands")),
    "extra_frontmatter": extra,
}

print(json.dumps(out, ensure_ascii=False, indent=2))
PYEOF
