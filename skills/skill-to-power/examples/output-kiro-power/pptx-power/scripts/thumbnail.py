#!/usr/bin/env python3
"""thumbnail.py <pptx-file> — render slide thumbnails as PNG grid."""
import sys
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print("usage: thumbnail.py <pptx-file>", file=sys.stderr)
        sys.exit(2)
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        sys.exit(1)
    out_dir = src.with_suffix("")
    out_dir.mkdir(exist_ok=True)
    subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "png", "--outdir", str(out_dir), str(src)],
        check=True,
    )
    print(f"thumbnails written to {out_dir}/")


if __name__ == "__main__":
    main()
