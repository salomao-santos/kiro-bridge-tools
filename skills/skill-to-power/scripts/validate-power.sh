#!/usr/bin/env bash
# validate-power.sh <path-to-power-dir>
# Validates a generated Kiro Power directory.
# Exits 0 on pass, non-zero with <file>:<line>: <error> lines on failure.

set -uo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <path-to-power-dir>" >&2
  exit 2
fi

POWER_DIR="$1"

if [ ! -d "$POWER_DIR" ]; then
  echo "error: $POWER_DIR is not a directory" >&2
  exit 1
fi

python3 - "$POWER_DIR" <<'PYEOF'
import json
import os
import re
import sys

power_dir = sys.argv[1]
errors = []

ALLOWED_WHEN_TYPES = {
    "promptSubmit", "agentStop", "preToolUse", "postToolUse",
    "fileCreate", "fileSave", "fileDelete",
    "preTaskExecution", "postTaskExecution", "manual",
}
REQUIRED_POWER_KEYS = {"name", "displayName", "description", "keywords", "author"}
REQUIRED_HOOK_KEYS = {"enabled", "name", "when", "then"}


def err(file, line, msg):
    errors.append(f"{file}:{line}: {msg}")


# (a) POWER.md exists + frontmatter parses
power_md = os.path.join(power_dir, "POWER.md")
if not os.path.isfile(power_md):
    err(power_md, 0, "POWER.md missing")
else:
    with open(power_md, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        err(power_md, 1, "frontmatter delimiters --- not found at top")
    else:
        fm_text = m.group(1)
        try:
            import yaml
            fm = yaml.safe_load(fm_text) or {}
        except ImportError:
            fm = {}
            for line in fm_text.splitlines():
                kv = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
                if kv:
                    fm[kv.group(1)] = kv.group(2).strip()
        except Exception as e:
            err(power_md, 1, f"frontmatter YAML parse error: {e}")
            fm = {}

        # (a) required keys
        missing = REQUIRED_POWER_KEYS - set(fm.keys())
        for k in missing:
            err(power_md, 1, f"missing required key: {k}")

        # (b) keywords is list with >=1 item
        kws = fm.get("keywords")
        if kws is not None:
            if not isinstance(kws, list):
                err(power_md, 1, "keywords must be a YAML list")
            elif len(kws) < 1:
                err(power_md, 1, "keywords list is empty")

# (c, d) hook files
hooks_dir = os.path.join(power_dir, "hooks")
if os.path.isdir(hooks_dir):
    for fname in sorted(os.listdir(hooks_dir)):
        if not fname.endswith(".kiro.hook"):
            continue
        fpath = os.path.join(hooks_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            err(fpath, e.lineno, f"invalid JSON: {e.msg}")
            continue
        missing = REQUIRED_HOOK_KEYS - set(data.keys())
        for k in missing:
            err(fpath, 1, f"missing required hook key: {k}")
        when = data.get("when", {})
        wtype = when.get("type") if isinstance(when, dict) else None
        if wtype is None:
            err(fpath, 1, "when.type missing")
        elif wtype not in ALLOWED_WHEN_TYPES:
            err(fpath, 1, f"when.type '{wtype}' not in allowed enum")

# (e) scripts executable
scripts_dir = os.path.join(power_dir, "scripts")
if os.path.isdir(scripts_dir):
    for fname in sorted(os.listdir(scripts_dir)):
        fpath = os.path.join(scripts_dir, fname)
        if os.path.isfile(fpath) and not os.access(fpath, os.X_OK):
            err(fpath, 0, "script is not executable (chmod +x)")

# (f) mcp.json (if present) parses + has mcpServers
mcp_json = os.path.join(power_dir, "mcp.json")
if os.path.isfile(mcp_json):
    try:
        with open(mcp_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "mcpServers" not in data:
            err(mcp_json, 1, "missing root key: mcpServers")
    except json.JSONDecodeError as e:
        err(mcp_json, e.lineno, f"invalid JSON: {e.msg}")

if errors:
    for e in errors:
        print(e)
    sys.exit(1)

print("OK: Power directory is valid.")
PYEOF
