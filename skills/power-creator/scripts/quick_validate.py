#!/usr/bin/env python3
from __future__ import annotations
"""Quick validation for a Kiro Power directory.

Checks: POWER.md present, valid YAML frontmatter, required keys (name,
description), kebab-case name, description length and forbidden chars.

Falls back to SKILL.md when a legacy skill directory is passed, so this
doubles as a pre-conversion check.
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


ALLOWED_PROPERTIES = {
    "name", "description", "license", "allowed-tools",
    "metadata", "compatibility", "keywords", "author",
    "aliases", "triggers", "hooks",
}


def _parse_frontmatter(content: str) -> tuple[bool, str, dict]:
    if not content.startswith("---"):
        return False, "No YAML frontmatter found", {}
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format", {}
    fm_text = match.group(1)
    if yaml is None:
        # Lightweight fallback: extract name + description only
        fm = {}
        for line in fm_text.splitlines():
            if line.startswith("name:"):
                fm["name"] = line.split(":", 1)[1].strip().strip('"\'')
            elif line.startswith("description:"):
                fm["description"] = line.split(":", 1)[1].strip().strip('"\'')
        return True, "ok", fm
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}", {}
    if not isinstance(fm, dict):
        return False, "Frontmatter must be a YAML dictionary", {}
    return True, "ok", fm


def validate_power(power_path) -> tuple[bool, str]:
    power_path = Path(power_path)

    candidate_files = [power_path / "POWER.md", power_path / "SKILL.md"]
    md = next((p for p in candidate_files if p.exists()), None)
    if md is None:
        return False, "POWER.md not found (also accepts legacy SKILL.md)"

    content = md.read_text()
    ok, msg, fm = _parse_frontmatter(content)
    if not ok:
        return False, msg

    unexpected = set(fm.keys()) - ALLOWED_PROPERTIES
    if unexpected:
        return False, (
            f"Unexpected key(s) in {md.name} frontmatter: {', '.join(sorted(unexpected))}. "
            f"Allowed: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    if "name" not in fm:
        return False, f"Missing 'name' in {md.name} frontmatter"
    if "description" not in fm:
        return False, f"Missing 'description' in {md.name} frontmatter"

    name = fm.get("name", "")
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        if not re.match(r"^[a-z0-9-]+$", name):
            return False, f"Name '{name}' should be kebab-case (lowercase letters, digits, hyphens only)"
        if name.startswith("-") or name.endswith("-") or "--" in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        if len(name) > 64:
            return False, f"Name is too long ({len(name)} chars). Max is 64."

    description = fm.get("description", "")
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if description:
        if "<" in description or ">" in description:
            return False, "Description cannot contain angle brackets (< or >)"
        if len(description) > 1024:
            return False, f"Description is too long ({len(description)} chars). Max is 1024."

    compatibility = fm.get("compatibility", "")
    if compatibility:
        if not isinstance(compatibility, str):
            return False, f"Compatibility must be a string, got {type(compatibility).__name__}"
        if len(compatibility) > 500:
            return False, f"Compatibility is too long ({len(compatibility)} chars). Max is 500."

    return True, f"Power is valid! ({md.name})"


# Back-compat alias
validate_skill = validate_power


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.quick_validate <power_directory>")
        sys.exit(1)
    valid, message = validate_power(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)
