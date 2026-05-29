"""Shared utilities for power-creator scripts."""
from __future__ import annotations

from pathlib import Path


def parse_power_md(power_path: Path) -> tuple[str, str, str]:
    """Parse a POWER.md file, returning (name, description, full_content).

    Also accepts SKILL.md as a fallback so this works on legacy skill dirs
    being converted to Powers.
    """
    if isinstance(power_path, str):
        power_path = Path(power_path)

    candidates = [power_path / "POWER.md", power_path / "SKILL.md"]
    md_file = next((p for p in candidates if p.exists()), None)
    if md_file is None:
        raise FileNotFoundError(f"No POWER.md or SKILL.md in {power_path}")

    content = md_file.read_text()
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError(f"{md_file.name} missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError(f"{md_file.name} missing frontmatter (no closing ---)")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (
                    frontmatter_lines[i].startswith("  ") or frontmatter_lines[i].startswith("\t")
                ):
                    continuation_lines.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            else:
                description = value.strip('"').strip("'")
        i += 1

    return name, description, content


# Back-compat alias for code paths that still expect parse_skill_md.
parse_skill_md = parse_power_md
