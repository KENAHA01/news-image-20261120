"""Entrypoint for news-image-20261120 (Python 3.13, standard library only).

Copies the front-page image drawn by make_image.py on the builder
machine to the grader's output directory. No network, no Pillow here:
the sandbox only needs this file and entry.png.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(os.path.join(HERE, "entry.png"),
                    os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
