#!/usr/bin/env python3
"""Entrypoint lomba: salin gambar entri yang sudah jadi ke folder output.

Hanya stdlib, tanpa render ulang, tanpa network. Dijalankan dari folder repo:
    python3 -P -s main.py
Grader menjalankan program di container dengan repo read-only (/bot) dan
folder output writable; folder output dibaca dari env MAKEFUN_OUTPUT_DIR
(default "/output"). Program menulis <out_dir>/entry.png, byte-identik
dengan entry.png di sebelah file ini.
"""

import os
import shutil
import sys


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(base, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    dst = os.path.join(out_dir, "entry.png")
    if not os.path.isfile(src):
        print("entry.png tidak ditemukan di %s" % base, file=sys.stderr)
        return 1
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(src, dst)
    print("wrote %s" % dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
