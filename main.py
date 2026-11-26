#!/usr/bin/env python3
"""Duskline News -- 26 November 2026.

Draws a one-page newspaper front page (1024x1024 PNG) summing up the
world news of Thursday 26 November 2026, using only Pillow and the
standard library. No network, no randomness, no clock: two runs write
byte-identical output.

The program writes exactly one file, entry.png, into
$MAKEFUN_OUTPUT_DIR (or a fresh temp directory outside this repository
when the variable is unset). It never writes into its own repository:
if the output directory is the repository or inside it, it refuses
and exits 0. It never raises an exception.
"""

import os
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024

PAPER = (246, 241, 227)      # warm newsprint cream
INK = (20, 18, 16)          # near-black ink
RED = (176, 32, 32)         # headline accent red
NAVY = (27, 58, 92)         # night-sky blue
SKY_DARK = (24, 30, 52)
DUSK = (214, 110, 44)       # dusk orange for the refinery sky
GOLD = (212, 160, 60)
GREY = (90, 84, 74)
RULE = (120, 110, 95)
TICKER_BG = (24, 24, 22)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    """Load a DejaVu font, falling back to Pillow's built-in bitmap font."""
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    except Exception:
        return ImageFont.load_default()


SERIF_B = lambda s: font("DejaVuSerif-Bold.ttf", s)
SERIF = lambda s: font("DejaVuSerif.ttf", s)
SANS_B = lambda s: font("DejaVuSans-Bold.ttf", s)
SANS = lambda s: font("DejaVuSans.ttf", s)


def wrap(draw, text, fnt, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, fnt, max_width, fill=INK, spacing=4,
                 max_lines=None):
    """Draw wrapped text; returns the y just below the last line."""
    lines = wrap(draw, text, fnt, max_width)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + spacing
    return y


def rule(draw, x0, y, x1, width=2, fill=RULE):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


def draw_refinery_scene(canvas, box):
    """Draw the lead illustration: the Ras Tanura refinery at dusk, a
    flare burning above the distillation towers under a smoky orange
    sky. The scene is drawn on its own layer first, so nothing can
    spill past the frame."""
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    layer = Image.new("RGB", (bw, bh), SKY_DARK)
    draw = ImageDraw.Draw(layer)
    # dusk sky: horizontal bands from dark navy to orange at the horizon
    bands = [
        (0.00, (24, 30, 52)), (0.25, (52, 44, 66)), (0.45, (110, 62, 58)),
        (0.62, (178, 92, 48)), (0.75, (214, 120, 46)),
    ]
    for i in range(len(bands) - 1):
        f0, c0 = bands[i]
        f1, c1 = bands[i + 1]
        steps = max(1, int((f1 - f0) * bh))
        for s in range(steps):
            t = s / steps
            col = tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3))
            yy = int(f0 * bh) + s
            draw.line([(0, yy), (bw, yy)], fill=col)
    # low sun, half-hidden behind smoke
    sx, sy, sr = int(0.72 * bw), int(0.62 * bh), 26
    draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(240, 170, 80))
    # smoke plumes drifting from the towers
    for cx, cy, r in [(0.30, 0.34, 26), (0.38, 0.26, 20), (0.46, 0.30, 22),
                      (0.55, 0.22, 16), (0.34, 0.18, 14)]:
        px, py = cx * bw, cy * bh
        draw.ellipse([px - r, py - r // 2, px + r, py + r // 2],
                     fill=(96, 88, 92))
    # ground
    gy = int(0.76 * bh)
    draw.rectangle([0, gy, bw, bh], fill=(28, 26, 24))
    # storage tanks (left)
    for tx, tr in [(0.10, 34), (0.28, 28)]:
        px = tx * bw
        draw.ellipse([px - tr, gy - 46, px + tr, gy - 20], fill=(150, 142, 128))
        draw.rectangle([px - tr, gy - 34, px + tr, gy], fill=(150, 142, 128))
        draw.line([(px - tr, gy - 34), (px + tr, gy - 34)], fill=(110, 102, 90),
                  width=2)
    # distillation towers (centre-right), silhouetted
    for tx, tw, th in [(0.52, 30, 150), (0.64, 24, 185), (0.74, 18, 120)]:
        px = tx * bw
        draw.rectangle([px - tw // 2, gy - th, px + tw // 2, gy],
                       fill=(52, 50, 48))
        draw.rectangle([px - tw // 2 - 4, gy - th - 10, px + tw // 2 + 4,
                        gy - th], fill=(52, 50, 48))
        for k in range(1, 5):
            yy = gy - th + k * th // 5
            draw.line([(px - tw // 2, yy), (px + tw // 2, yy)],
                      fill=(88, 84, 80), width=1)
    # flare stack with flame (right)
    fx = int(0.88 * bw)
    draw.rectangle([fx - 6, gy - 160, fx + 6, gy], fill=(52, 50, 48))
    draw.polygon([(fx - 16, gy - 160), (fx + 16, gy - 160),
                  (fx + 6, gy - 208), (fx, gy - 226),
                  (fx - 6, gy - 208)], fill=(255, 176, 32))
    draw.polygon([(fx - 8, gy - 160), (fx + 8, gy - 160),
                  (fx + 3, gy - 188), (fx, gy - 200),
                  (fx - 3, gy - 188)], fill=(255, 236, 170))
    # pipework along the ground
    draw.line([(0, gy - 14), (bw, gy - 14)], fill=(88, 84, 80), width=3)
    draw.line([(0, gy - 6), (bw, gy - 6)], fill=(64, 60, 56), width=2)
    # caption bar inside the frame
    draw.rectangle([0, bh - 26, bw, bh], fill=(0, 0, 0))
    cap = "RAS TANURA REFINERY AT DUSK"
    draw.text((10, bh - 21), cap, font=SANS_B(10), fill=(240, 238, 228))
    canvas.paste(layer, (x0, y0))


LEAD_HEAD = "Houthi missiles hit Ras Tanura refinery as Gulf war widens"
LEAD_BODY = (
    "Houthi missiles struck Saudi Arabia's Ras Tanura oil refinery and a "
    "drone hit Riyadh's tallest tower for the second time in a week, "
    "wounding at least 11 people. With attacks at sea and fresh strikes "
    "near Bahrain, the Iran war is squeezing Gulf economies and rattling "
    "the region's oil lifeline."
)

STORIES = [
    ("SPACE",
     "BepiColombo reaches Mercury orbit after eight-year journey",
     "The European-Japanese probe slipped into orbit around Mercury after "
     "an eight-year, nine-billion-kilometre cruise, and will soon send "
     "back close-up images of the cratered planet."),
    ("EGYPT",
     "Fuel tanker crash ignites fire near Cairo, at least 30 killed",
     "A fuel tanker crashed and burst into flames on a highway around "
     "Cairo, killing at least 30 people in one of Egypt's deadliest road "
     "disasters this year."),
    ("NORTH KOREA",
     "Pyongyang orders Switzerland to close its diplomatic office",
     "North Korea directed Switzerland to shut its newly opened office in "
     "Pyongyang, deepening a row over sanctions and diplomatic access."),
    ("BANGLADESH",
     "Bangladesh raises garment wages 36% after worker protests",
     "Dhaka announced a 36% rise in the minimum monthly wage for "
     "entry-level garment workers, a lift for millions in the world's "
     "second-biggest clothing exporter."),
    ("UNITED STATES",
     "Democrats reclaim Congress in midterm comeback",
     "Democrats retook both chambers of Congress in November's midterms, "
     "leaving President Trump facing a lame-duck final two years as the "
     "Gulf's pledged trillions come under new scrutiny."),
    ("CLIMATE",
     "Norway court voids disputed oil licences in climate ruling",
     "Norway's supreme court ruled climate-disputed oil licences invalid, "
     "a landmark decision for Arctic drilling and the energy transition."),
]

TICKER = (
    "NVIDIA DOWN 5% AS AI STOCKS SLIDE  \u2022  POUNDLAND NEARS "
    "ADMINISTRATION, 12,000 JOBS AT RISK  \u2022  GUKESH HOLDS SINDAROV  "
    "\u2022  SOORYAVANSHI, 15, SMASHES 204 OFF 53 BALLS  \u2022  SIX DEAD IN "
    "PLANE CRASH OFF MISSISSIPPI COAST  \u2022  COLOMBIAN POLICE FREE 20 "
    "HOSTAGES  \u2022  SUDAN DRONE STRIKES KILL 19 CIVILIANS  \u2022  GAZA "
    "STRIKE KILLS HAMAS OFFICIAL"
)

FOOTER = (
    "Sources: Reuters  •  Associated Press  •  The Hindu  •  C54 News  •  "
    "Daily Debrief briefing of 26 November 2026  •  Duskline News sums up the "
    "world news of Thursday 26 November 2026."
)


def build_image():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    m = 36  # page margin

    # ---- masthead ----
    d.text((m, 18), "DUSKLINE NEWS", font=SERIF_B(62), fill=INK)
    rule(d, m, 96, W - m, width=3, fill=INK)
    rule(d, m, 102, W - m, width=1, fill=INK)
    d.text((m, 110), "THURSDAY, 26 NOVEMBER 2026", font=SANS_B(17), fill=RED)
    right = "THE WORLD IN ONE PAGE  •  No. 330"
    d.text((W - m - d.textlength(right, font=SANS_B(13)), 113), right,
           font=SANS_B(13), fill=GREY)

    # ---- lead story ----
    ly = 146
    d.text((m, ly), "GULF  •  LEAD STORY", font=SANS_B(14), fill=RED)
    y = draw_wrapped(d, m, ly + 26, LEAD_HEAD, SERIF_B(30), 560,
                     max_lines=3, spacing=2)
    y = draw_wrapped(d, m, y + 8, LEAD_BODY, SERIF(15), 560, spacing=3,
                     max_lines=8)
    # illustration, right of the lead text
    ix0, iy0, ix1, iy1 = 632, ly, W - m, 452
    draw_refinery_scene(img, (ix0, iy0, ix1, iy1))
    d.rectangle([ix0, iy0, ix1, iy1], outline=INK, width=2)

    rule(d, m, 470, W - m, width=2, fill=INK)

    # ---- story grid: 2 columns x 3 rows ----
    col_w = (W - 2 * m - 28) // 2
    row_h = 128
    gy = 490
    for i, (kicker, head, body) in enumerate(STORIES):
        col = i % 2
        row = i // 2
        x = m + col * (col_w + 28)
        y = gy + row * row_h
        d.text((x, y), kicker, font=SANS_B(12), fill=RED)
        y2 = draw_wrapped(d, x, y + 20, head, SERIF_B(17), col_w,
                          max_lines=2, spacing=1)
        draw_wrapped(d, x, y2 + 4, body, SERIF(12), col_w, spacing=2,
                     max_lines=3)
        if col == 0:
            d.line([(x + col_w + 14, y), (x + col_w + 14, y + row_h - 16)],
                   fill=RULE, width=1)
        if row < 2:
            rule(d, x, y + row_h - 8, x + col_w, width=1, fill=RULE)

    # ---- ticker ----
    ty = 878
    d.rectangle([0, ty, W, ty + 62], fill=TICKER_BG)
    d.text((m, ty + 8), "WIRE", font=SANS_B(15), fill=GOLD)
    lines = wrap(d, TICKER, SANS_B(12), W - 2 * m - 62)
    ty_text = ty + 8
    for line in lines[:3]:
        d.text((m + 62, ty_text), line, font=SANS_B(12),
               fill=(238, 236, 228))
        ty_text += 17

    # ---- footer ----
    fy = 952
    rule(d, m, fy, W - m, width=1, fill=RULE)
    draw_wrapped(d, m, fy + 10, FOOTER, SANS(11), W - 2 * m, fill=GREY,
                 spacing=2, max_lines=3)
    return img


def resolve_output_dir():
    """Return the directory to write entry.png into, or None to refuse."""
    repo = Path(__file__).resolve().parent
    raw = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip()
    if raw:
        out = Path(raw).expanduser()
        try:
            out_resolved = out.resolve()
        except Exception:
            out_resolved = out.absolute()
    else:
        out_resolved = Path(tempfile.mkdtemp(prefix="duskline-news-"))
    try:
        repo_resolved = repo.resolve()
    except Exception:
        repo_resolved = repo.absolute()
    if out_resolved == repo_resolved or repo_resolved in out_resolved.parents:
        return None
    return out_resolved


def main():
    try:
        out_dir = resolve_output_dir()
        if out_dir is None:
            print("refusing: MAKEFUN_OUTPUT_DIR is the repository or "
                  "inside it; nothing written")
            return 0
        out_dir.mkdir(parents=True, exist_ok=True)
        img = build_image()
        target = out_dir / "entry.png"
        img.save(str(target), "PNG")
        print("wrote %s (%dx%d)" % (target, W, H))
        return 0
    except Exception as exc:  # never raise, never crash the harness
        print("error: %s" % (exc,))
        return 0


if __name__ == "__main__":
    sys.exit(main())
