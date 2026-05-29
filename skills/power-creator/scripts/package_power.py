#!/usr/bin/env python3
from __future__ import annotations
"""Package a Power folder into a distributable .power zip file.

Usage:
    python -m scripts.package_power <path/to/power-folder> [output-directory]
"""

import fnmatch
import sys
import zipfile
from pathlib import Path

from scripts.quick_validate import validate_power


EXCLUDE_DIRS = {"__pycache__", "node_modules"}
EXCLUDE_GLOBS = {"*.pyc"}
EXCLUDE_FILES = {".DS_Store"}
ROOT_EXCLUDE_DIRS = {"evals"}


def should_exclude(rel_path: Path) -> bool:
    parts = rel_path.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    if len(parts) > 1 and parts[1] in ROOT_EXCLUDE_DIRS:
        return True
    name = rel_path.name
    if name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in EXCLUDE_GLOBS)


def package_power(power_path, output_dir=None):
    power_path = Path(power_path).resolve()
    if not power_path.exists():
        print(f"Error: Power folder not found: {power_path}")
        return None
    if not power_path.is_dir():
        print(f"Error: Path is not a directory: {power_path}")
        return None

    power_md = power_path / "POWER.md"
    if not power_md.exists():
        if (power_path / "SKILL.md").exists():
            print("Warning: only SKILL.md present, no POWER.md. Run skill-to-power first.")
        print(f"Error: POWER.md not found in {power_path}")
        return None

    print("Validating Power...")
    valid, message = validate_power(power_path)
    if not valid:
        print(f"Validation failed: {message}")
        return None
    print(f"OK: {message}\n")

    power_name = power_path.name
    if output_dir:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path.cwd()

    power_filename = output_path / f"{power_name}.power"
    try:
        with zipfile.ZipFile(power_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in power_path.rglob("*"):
                if not file_path.is_file():
                    continue
                arcname = file_path.relative_to(power_path.parent)
                if should_exclude(arcname):
                    print(f"  Skipped: {arcname}")
                    continue
                zipf.write(file_path, arcname)
                print(f"  Added: {arcname}")
        print(f"\nPackaged: {power_filename}")
        return power_filename
    except Exception as e:
        print(f"Error creating .power file: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.package_power <path/to/power-folder> [output-directory]")
        sys.exit(1)
    power_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    print(f"Packaging Power: {power_path}")
    if output_dir:
        print(f"   Output directory: {output_dir}")
    print()
    result = package_power(power_path, output_dir)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
