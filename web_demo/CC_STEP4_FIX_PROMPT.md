# CC_STEP4_FIX_PROMPT.md — Step 4 fix round 1

Boti compared the running app against `UI/B1a`/`B1b`/`B1d` live. Read your own `web_demo/CC_STEP4_REPORT.md`
first, then `web_demo/SZSCAN_DESIGN_v2.md §3` (EEG waveform tokens) and `§9` (CSS variables), then copy
`UI/B1a*.png`, `UI/B1b*.png`, `UI/B1d*.png` to scratch and pixel-compare directly — don't eyeball.

Work through the items below **in order**. Do not skip to item 1 before item 0 is resolved.

## 0. Integrity check — do this first, before touching any code

A screenshot of your own Step 4 completion message shows a source-control diff panel reporting
**"84 files changed +288 -43"**, including entries like `results/attribution_v5/labels/chb03_sz0_review.png`.
Your Step 4 report claims "git status is clean outside the intended files." These two things are in
tension and must be resolved before anything else.

Run `git status` and `git diff --stat` yourself, in a real terminal, right now, and paste the RAW output.
Determine and state explicitly:
- Did **this session** touch anything under `results/`, `data/models_retrain/`, `data/processed/`, or
  `docs/`? If yes — **stop**, that is a guard violation per `CLAUDE.md`'s write guard. Do not proceed to
  the rest of this prompt until this is resolved and explained.
- If the `results/attribution_v5/labels/*` changes are pre-existing / unrelated Project #1 work that was
  already sitting uncommitted in the shared repo before this session started (both projects share one
  repo per `DEMO_BUILD_HANDOFF.md §2`), prove it — e.g. `git log -1 --format=%cI -- <one of those files>`
  showing a commit/mtime that predates this session, or `git diff --stat -- web_demo` scoped down to show
  only the files this step actually touched.

## 1. EEG canvas background renders black/dark instead of cream

A real subject (`chb15_01_short`) renders the Panel EEG canvas with a dark navy/black background across
all 18 channels. Per `SZSCAN_DESIGN_v2.md §3`/`§9`, `--color-eeg-canvas` must be `#FEFBEF` — this is a
fixed, non-negotiable token.

Find where the canvas background is actually painted. A `<canvas>` element does **not** inherit CSS
variables into `ctx.fillStyle` automatically — if the code assumed it would, or hardcoded a dark
fallback, that's the bug. Fix so the canvas reads the real `--color-eeg-canvas` value (e.g. via
`getComputedStyle`) and fills with it before any waveform is drawn.

## 2. Waveform reads as dense vertical noise, not a legible trace

Same screenshot: every channel row looks like uniform vertical static rather than a distinguishable EEG
shape. Before changing rendering code, determine which of these is true — test both, don't guess:

- **(a) Real bug** — the decimation window is computed wrong, so each pixel column pulls from a far
  larger sample range than it should, collapsing the min/max envelope into full-height streaks
  everywhere.
- **(b) Correct rendering of a genuinely dense signal at that specific zoom/scale** — the screenshot was
  at a 2-hour window and 7 µV amplitude, a very sensitive scale. At that combination ordinary EEG
  amplitude will clip against the row height almost everywhere, which can legitimately look like solid
  streaks. Test directly: open the same file at a **shorter window (e.g. 10–30 min) and a coarser
  amplitude (e.g. 20–30 µV)** and screenshot the result. If it now shows a recognizable wavy trace, (a)
  is ruled out — say so plainly, and separately consider (as a UX default choice, not a spec violation
  either way — SPEC does not mandate a specific initial `[X] hr` / `[X] uV`) whether the app should open
  a file at a less extreme default than 2 hr / 7 µV. State what default you chose, if you change it, and
  why.

If it's (a), fix the decimation/min-max logic and re-verify with a screenshot.

## 3. Filter toggle buttons (`lff`, `hff`, `60`) render as large solid violet pills

Pixel-compare against `UI/B1a`/`B1b`/`B1d` directly: the mockups show each filter control as ordinary
body text with a **small colored dot** to its left marking on/off state — not a large solid
violet-filled pill wrapping the whole label. Fix the styling to match. `UI/` wins on anything visible.

## 4. General sizing — measure, don't eyeball

Boti reports the overall Analysis screen (channel row height, spacing, controls) looks oversized next to
the mockup. Copy `UI/B1a.png` to scratch, screenshot your running app at the same resolution, and take
actual pixel measurements (channel-row height, canvas width, toolbar button height) rather than a visual
guess — this is exactly the mistake that cost 3 rounds in Step 2 (`BUILD_PROGRESS.md §5.2` #2/#3, the
header-sizing saga). Report the measured numbers on both sides and the CSS change made to close the gap.

## 5. Re-confirm scope — no code change needed here

Boti also noted the Panel Event list and Channel Attribution panel (right side of the mockups) are
missing. **This is correct and intentional** — `CC_STEP4_PROMPT.md`'s scope boundary explicitly excludes
mini-timeline, Panel Event, and Channel Attribution from Step 4 (Steps 5–7). Do not add them now. Just
confirm in your report that this is understood as by-design, so a future review doesn't mistake it for a
regression.

## Verification before writing your report

- Raw `git status` / `git diff --stat` output from item 0.
- Screenshot of the fixed canvas (cream background) with a legible waveform, at a window/amplitude
  combination where the trace actually reads as EEG.
- Screenshot of the corrected filter-toggle styling.
- The item-4 measurement numbers, before and after.
- `pytest web_demo/backend/tests/test_guards.py -v` — raw output.

Write your report to `web_demo/CC_STEP4_FIX_REPORT.md`. Give Boti exact restart commands if anything
needs restarting.
