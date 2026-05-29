#!/usr/bin/env python3
"""unpack.py <pptx-file> <out-dir> — extract .pptx archive to directory."""
import sys
import zipfile
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print("usage: unpack.py <pptx-file> <out-dir>", file=sys.stderr)
        sys.exit(2)
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        sys.exit(1)
    dst.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(src, "r") as z:
        z.extractall(dst)
    print(f"unpacked {src} → {dst}/")


if __name__ == "__main__":
    main()
