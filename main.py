#!/usr/bin/env python3
"""Duskline News — front page for 26 November 2026.

The front page ships in this repository as a finished image,
``entry.png``. This program only carries that file over to
``$MAKEFUN_OUTPUT_DIR/entry.png`` — it draws nothing itself.

It uses nothing but the Python standard library, touches no network,
reads no clock and rolls no dice. The repository directory is only
ever read from, never written to — the single file it writes is the
copy in the output directory — so the program runs cleanly even when
the repository is mounted read-only. Running it twice produces the
same bytes both times.
"""

import hashlib
import os
import shutil
import sys

IMAGE = "entry.png"
EXPECTED_SHA256 = "14a04936b1f1b89cfc75d286a573403b06914a125de580509c7dd7541889c159"


def _fail(message):
    print("error: " + message, file=sys.stderr)
    return 1


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run():
    here = os.path.dirname(os.path.abspath(__file__))
    shipped = os.path.join(here, IMAGE)
    if not os.path.isfile(shipped):
        return _fail(IMAGE + " is missing from the repository")
    if os.path.getsize(shipped) == 0:
        return _fail(IMAGE + " is empty")

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        return _fail("cannot create output directory %r: %s" % (out_dir, exc))

    target = os.path.join(out_dir, IMAGE)
    try:
        shutil.copyfile(shipped, target)
    except OSError as exc:
        return _fail("cannot write %r: %s" % (target, exc))

    try:
        if os.path.getsize(target) != os.path.getsize(shipped):
            return _fail("copied image is incomplete: %r" % target)
        digest = _sha256(target)
    except OSError as exc:
        return _fail("cannot verify %r: %s" % (target, exc))
    if digest != EXPECTED_SHA256:
        return _fail("copied image hash mismatch: %r" % target)

    print(
        "wrote %s (%d bytes, sha256 %s)"
        % (target, os.path.getsize(target), digest)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
