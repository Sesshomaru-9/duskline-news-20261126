#!/usr/bin/env python3
"""Duskline News — front page for Thursday 26 November 2026.

Builds a single 1024x1024 newspaper front page (PNG) that sums up the
world news of the day: a Gulf lead story, six further stories in a
two-column grid, and a wire ticker along the bottom.

Everything is drawn procedurally with Pillow — no network, no external
files, no clock, no randomness — so running the program twice produces
a byte-identical PNG. The only file it writes is
``$MAKEFUN_OUTPUT_DIR/entry.png``.

Usage:
    MAKEFUN_OUTPUT_DIR=/path/to/out python3 main.py
"""

import hashlib
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- page setup

PAGE_W = 1024
PAGE_H = 1024
MARGIN = 36
CONTENT_W = PAGE_W - 2 * MARGIN

PAPER = (246, 239, 221)      # warm newsprint
INK = (18, 18, 18)           # near-black body text
SOFT_INK = (74, 74, 74)      # grey secondary text
ACCENT = (163, 18, 18)       # red kickers and dateline
RULE = (18, 18, 18)          # hairline rules
BAND = (14, 14, 14)          # black wire band
BAND_TEXT = (245, 245, 245)
AMBER = (232, 160, 32)

EDITION_LINE = "THURSDAY, 26 NOVEMBER 2026"
EDITION_NOTE = "THE WORLD IN ONE PAGE  •  No. 330"
FOOTER_LINE = (
    "Sources: Reuters  •  Associated Press  •  The Hindu  •  C54 News  •  "
    "Daily Debrief briefing of 26 November 2026."
)

# ------------------------------------------------------------------- stories

LEAD = {
    "tag": "GULF  •  LEAD STORY",
    "head": "Houthi missile hits Ras Tanura refinery; Riyadh tower struck again",
    "body": (
        "Houthi missiles struck Saudi Arabia's Ras Tanura oil refinery, "
        "while a drone hit Riyadh's tallest tower for the second time in a "
        "week, wounding 11 people. The strikes mark a sharp escalation in "
        "the Gulf, threatening the region's oil lifeline and rattling "
        "markets."
    ),
    "caption": "RAS TANURA REFINERY AT DUSK",
}

STORIES = [
    {
        "tag": "SPACE",
        "head": "BepiColombo slips into orbit around Mercury after eight-year voyage",
        "body": (
            "The European-Japanese BepiColombo probe slipped into orbit "
            "around Mercury after an eight-year journey, and will soon "
            "send back close-up images of the cratered planet."
        ),
    },
    {
        "tag": "EGYPT",
        "head": "Fuel tanker crash ignites fire near Cairo, at least 30 killed",
        "body": (
            "A fuel tanker crashed and burst into flames on a highway near "
            "Cairo, killing at least 30 people in a huge blaze that closed "
            "the road for hours."
        ),
    },
    {
        "tag": "NORTH KOREA",
        "head": "Pyongyang orders Switzerland to close its diplomatic office",
        "body": (
            "North Korea has ordered Switzerland to close its diplomatic "
            "office in Pyongyang, in a further chill between the two "
            "countries."
        ),
    },
    {
        "tag": "BANGLADESH",
        "head": "Bangladesh raises garment wages 36% after worker protests",
        "body": (
            "Dhaka announced a 36% rise in the minimum monthly wage for "
            "garment workers after worker protests, a lift for millions in "
            "the world's second-biggest clothing exporter."
        ),
    },
    {
        "tag": "UNITED STATES",
        "head": "Democrats reclaim Congress in midterm comeback",
        "body": (
            "Democrats retook Congress in November's midterm elections, a "
            "result that reshapes the final two years of the presidency."
        ),
    },
    {
        "tag": "CLIMATE",
        "head": "Norway court voids disputed oil licences in climate ruling",
        "body": (
            "Norway's supreme court ruled climate-disputed oil licences "
            "invalid, a landmark decision for oil drilling and the energy "
            "transition."
        ),
    },
]

WIRE_ITEMS = [
    "NVIDIA DOWN 5% AS AI STOCKS SLIDE",
    "POUNDLAND NEARS ADMINISTRATION, 12,000 JOBS AT RISK",
    "GUKESH HOLDS SINDAROV",
    "SOORYAVANSHI 204 OFF 53 BALLS",
    "PLANE CRASH OFF MISSISSIPPI COAST",
    "COLOMBIAN POLICE FREE 20 HOSTAGES",
    "SUDAN DRONE STRIKES",
    "GAZA STRIKE",
]

# --------------------------------------------------------------------- fonts

_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
_SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _typeface(path, size):
    """Load one TrueType face, falling back to Pillow's built-in font."""
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        return ImageFont.load_default()


def load_faces():
    """Return the named set of faces used across the page."""
    return {
        "masthead": _typeface(_SERIF_BOLD, 76),
        "dateline": _typeface(_SANS_BOLD, 15),
        "dateline_note": _typeface(_SANS, 13),
        "kicker": _typeface(_SANS_BOLD, 14),
        "lead_head": _typeface(_SERIF_BOLD, 38),
        "lead_body": _typeface(_SERIF, 16),
        "cell_head": _typeface(_SERIF_BOLD, 20),
        "cell_body": _typeface(_SERIF, 14),
        "caption": _typeface(_SANS_BOLD, 11),
        "wire_label": _typeface(_SANS_BOLD, 15),
        "wire_text": _typeface(_SANS_BOLD, 13),
        "footer": _typeface(_SANS, 11),
    }


# -------------------------------------------------------------- text helpers

def split_lines(draw, text, face, width):
    """Greedy word wrap: split *text* into lines fitting *width* pixels."""
    lines = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if draw.textlength(trial, font=face) <= width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def paint_wrapped(draw, x, y, text, face, fill, width, leading, max_lines=None):
    """Paint wrapped text starting at (x, y); return the bottom y."""
    lines = split_lines(draw, text, face, width)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=face, fill=fill)
        y += leading
    return y


def paint_rule(draw, y, weight=1):
    """Paint a full-width horizontal rule at height *y*."""
    draw.rectangle([MARGIN, y, PAGE_W - MARGIN, y + weight - 1], fill=RULE)


# --------------------------------------------------------- lead illustration

def _blend(first, second, t):
    """Linear blend of two RGB colours at fraction *t* (0..1)."""
    return tuple(round(a + (b - a) * t) for a, b in zip(first, second))


def paint_refinery(draw, box):
    """Procedural dusk scene: gradient sky, sun, refinery silhouettes.

    *box* is (left, top, right, bottom). A caption bar is painted at the
    bottom of the box.
    """
    left, top, right, bottom = box
    width = right - left
    height = bottom - top
    caption_h = 28
    sky_bottom = bottom - caption_h

    # Dusk gradient: deep indigo at the top, burning orange at the horizon.
    stops = [(24, 24, 68), (96, 44, 96), (196, 82, 44), (232, 128, 48)]
    span = sky_bottom - top
    for row in range(span):
        frac = row / max(span - 1, 1)
        seg = min(int(frac * (len(stops) - 1)), len(stops) - 2)
        local = frac * (len(stops) - 1) - seg
        colour = _blend(stops[seg], stops[seg + 1], local)
        draw.line([(left, top + row), (right, top + row)], fill=colour)

    # Low sun, half-sunk behind the tanks, clear of the tower row.
    sun_cx = left + int(width * 0.89)
    sun_cy = sky_bottom - 58
    sun_r = 34
    draw.ellipse(
        [sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r],
        fill=(244, 214, 130),
    )

    # Drifting smoke puffs.
    smoke = (150, 148, 148)
    for cx, cy, rx, ry in [
        (0.22, 0.30, 34, 13),
        (0.30, 0.22, 26, 10),
        (0.38, 0.32, 22, 9),
    ]:
        px = left + int(width * cx)
        py = top + int(height * cy)
        draw.ellipse([px - rx, py - ry, px + rx, py + ry], fill=smoke)

    # Storage tanks along the base.
    tank_y = sky_bottom - 46
    for cx, w, h in [(0.10, 74, 46), (0.24, 74, 46), (0.52, 60, 40)]:
        tx = left + int(width * cx)
        draw.rounded_rectangle(
            [tx, tank_y, tx + w, sky_bottom], radius=8, fill=(168, 160, 148)
        )
        draw.ellipse([tx, tank_y - 10, tx + w, tank_y + 10], fill=(188, 180, 168))

    # Refinery towers, tallest at the right with a flare flame.
    silhouettes = [
        (0.36, 150, 30),
        (0.47, 118, 26),
        (0.60, 168, 34),
        (0.72, 132, 26),
    ]
    for cx, tall, wide in silhouettes:
        tx = left + int(width * cx)
        draw.rectangle([tx, sky_bottom - tall, tx + wide, sky_bottom], fill=(26, 22, 30))
        draw.rectangle(
            [tx - 3, sky_bottom - tall - 6, tx + wide + 3, sky_bottom - tall],
            fill=(26, 22, 30),
        )

    # Flare flame above the tallest stack.
    flame_x = left + int(width * 0.60) + 17
    flame_top = sky_bottom - 168 - 52
    draw.polygon(
        [
            (flame_x, flame_top),
            (flame_x - 13, sky_bottom - 168),
            (flame_x + 13, sky_bottom - 168),
        ],
        fill=(250, 176, 48),
    )
    draw.polygon(
        [
            (flame_x, flame_top + 16),
            (flame_x - 7, sky_bottom - 168),
            (flame_x + 7, sky_bottom - 168),
        ],
        fill=(250, 232, 160),
    )

    # Ground line and caption bar.
    draw.rectangle([left, sky_bottom - 2, right, sky_bottom], fill=(16, 14, 20))
    draw.rectangle([left, sky_bottom, right, bottom], fill=BAND)
    return sky_bottom


# -------------------------------------------------------------- page sections

def paint_masthead(draw, faces):
    """Nameplate, double rule, and the dateline row. Returns next y."""
    title = "DUSKLINE NEWS"
    tw = draw.textlength(title, font=faces["masthead"])
    draw.text(((PAGE_W - tw) / 2, 24), title, font=faces["masthead"], fill=INK)
    paint_rule(draw, 112, 3)
    paint_rule(draw, 118, 1)
    draw.text((MARGIN, 128), EDITION_LINE, font=faces["dateline"], fill=ACCENT)
    note_w = draw.textlength(EDITION_NOTE, font=faces["dateline_note"])
    draw.text(
        (PAGE_W - MARGIN - note_w, 129),
        EDITION_NOTE,
        font=faces["dateline_note"],
        fill=SOFT_INK,
    )
    return 156


def paint_lead(draw, faces):
    """Lead story text on the left, refinery art on the right."""
    text_w = 560
    art_left = MARGIN + text_w + 32
    art_right = PAGE_W - MARGIN

    draw.text((MARGIN, 156), LEAD["tag"], font=faces["kicker"], fill=ACCENT)
    y = paint_wrapped(
        draw, MARGIN, 180, LEAD["head"], faces["lead_head"], INK, text_w, 46
    )
    paint_wrapped(
        draw, MARGIN, y + 10, LEAD["body"], faces["lead_body"], INK, text_w, 22
    )

    art_bottom = paint_refinery(draw, (art_left, 156, art_right, 424))
    draw.text(
        (art_left + 10, art_bottom + 8),
        LEAD["caption"],
        font=faces["caption"],
        fill=BAND_TEXT,
    )
    return 446


def paint_grid(draw, faces, top):
    """Six stories in two columns and three rows. Returns next y."""
    col_w = (CONTENT_W - 24) // 2
    row_h = 130
    gap = 10
    y = top
    for row in range(3):
        for col in range(2):
            story = STORIES[row * 2 + col]
            x = MARGIN + col * (col_w + 24)
            draw.text((x, y), story["tag"], font=faces["kicker"], fill=ACCENT)
            after_head = paint_wrapped(
                draw, x, y + 22, story["head"], faces["cell_head"],
                INK, col_w, 25, max_lines=2,
            )
            paint_wrapped(
                draw, x, after_head + 6, story["body"], faces["cell_body"],
                INK, col_w, 19, max_lines=3,
            )
            if col == 0:
                draw.line(
                    [(x + col_w + 12, y + 2), (x + col_w + 12, y + row_h - 12)],
                    fill=(170, 160, 140),
                )
        if row < 2:
            paint_rule(draw, y + row_h + 2, 1)
        y += row_h + gap
    return y - gap


def paint_wire(draw, faces, top):
    """Black ticker band with the wire items. Returns next y."""
    band_h = 72
    draw.rectangle(
        [MARGIN, top, PAGE_W - MARGIN, top + band_h], fill=BAND
    )
    label = "WIRE"
    draw.text((MARGIN + 12, top + 12), label, font=faces["wire_label"], fill=AMBER)
    label_w = draw.textlength(label, font=faces["wire_label"])
    ticker = "  •  ".join(WIRE_ITEMS)
    paint_wrapped(
        draw,
        MARGIN + 12 + label_w + 18,
        top + 10,
        ticker,
        faces["wire_text"],
        BAND_TEXT,
        CONTENT_W - label_w - 60,
        19,
    )
    return top + band_h


def paint_footer(draw, faces, top):
    """Sources credit line under the wire band."""
    paint_wrapped(
        draw, MARGIN, top + 10, FOOTER_LINE, faces["footer"],
        SOFT_INK, CONTENT_W, 15,
    )


# ---------------------------------------------------------------------- build

def build_page():
    """Compose the whole front page and return the Pillow image."""
    faces = load_faces()
    page = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
    draw = ImageDraw.Draw(page)

    y = paint_masthead(draw, faces)
    y = paint_lead(draw, faces)
    paint_rule(draw, y, 2)
    grid_bottom = paint_grid(draw, faces, y + 16)
    wire_bottom = paint_wire(draw, faces, grid_bottom + 14)
    paint_footer(draw, faces, wire_bottom)
    return page


def main(argv=None):
    """Write entry.png into $MAKEFUN_OUTPUT_DIR and report its digest."""
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        print("error: MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 2
    target = Path(out_dir) / "entry.png"
    target.parent.mkdir(parents=True, exist_ok=True)

    page = build_page()
    page.save(target, format="PNG")

    raw = target.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    print(f"wrote {target} ({len(raw)} bytes, sha256 {digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
