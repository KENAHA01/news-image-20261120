#!/usr/bin/env python3
"""news-image-20261120 v21 entrypoint (stdlib only).
Copies the prebuilt entry.png to MAKEFUN_OUTPUT_DIR/entry.png
(default /output). No network, no rendering at run time."""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    src = os.path.join(HERE, "entry.png")
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
