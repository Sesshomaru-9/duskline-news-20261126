# Duskline News — 26 November 2026

Entry for the make.fun bounty **news-image-20261126**: "Sum up 26 November's
world news in one image" ($100 USDC).

## What it is

`main.py` draws a one-page newspaper front page (1024×1024 PNG) summing up
the world news of Thursday 26 November 2026, using only Pillow and the
Python standard library. No network, no randomness, no clock: two runs
write byte-identical output.

## The seven stories

- **Lead — Gulf:** Houthi missiles hit Saudi Arabia's Ras Tanura oil
  refinery; a drone struck Riyadh's tallest tower for the second time in a
  week, wounding at least 11, as the Iran war widens.
- **Space:** BepiColombo reaches Mercury orbit after an eight-year journey.
- **Egypt:** Fuel tanker crash ignites a fire near Cairo; at least 30 killed.
- **North Korea:** Pyongyang orders Switzerland to close its diplomatic
  office.
- **Bangladesh:** Garment wages raised 36% after worker protests.
- **United States:** Democrats reclaim Congress in the midterm comeback.
- **Climate:** Norway's supreme court voids disputed oil licences in a
  climate ruling.

The wire ticker adds Nvidia's 5% slide, Poundland nearing administration,
the Gukesh–Sindarov chess title match, Sooryavanshi's 204 off 53 balls,
the Mississippi plane crash, the freed Colombian hostages, Sudan drone
strikes and the Gaza strike.

Sources: Reuters, Associated Press, The Hindu, C54 News and the Daily
Debrief briefing of 26 November 2026.

## How to run

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py   # writes /tmp/out/entry.png
```

The program writes exactly one file, `entry.png`, into
`$MAKEFUN_OUTPUT_DIR` (or a fresh temp directory outside this repository
when the variable is unset). It never writes into its own repository.

## License

MIT — see `LICENSE`.
