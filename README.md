# Duskline News — 26 November 2026

One newspaper front page that sums up the world news of Thursday
26 November 2026: a Gulf lead story, six further stories in a
two-column grid, and a wire ticker along the bottom.

The page ships finished in this repository as `entry.png`
(1024×1024). `main.py` does not draw anything: it is standard
library only and just copies that image to
`$MAKEFUN_OUTPUT_DIR/entry.png`, checking its size and sha256
on the way. No network, no clock, no randomness; the repository
itself is never written to.

```sh
MAKEFUN_OUTPUT_DIR=/path/to/out python3 main.py
```
