#!/usr/bin/env python3
"""pack.py <src-dir> <pptx-file> — repack directory into .pptx archive."""
import sys
import zipfile
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print("usage: pack.py <src-dir> <pptx-file>", file=sys.stderr)
        sys.exit(2)
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    if not src.is_dir():
        print(f"error: {src} not a directory", file=sys.stderr)
        sys.exit(1)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for path in src.rglob("*"):
            if path.is_file():
                z.write(path, path.relative_to(src))
    print(f"packed {src}/ → {dst}")


if __name__ == "__main__":
    main()
