# CC_STEP6_FIX_REPORT.md — Step 6, fix round 1

**Scope confirmed:** visual adjustments only. Select Range behaviour, event create/edit/delete logic,
and the event-numbering scheme from `CC_STEP6_REPORT.md` were not touched — verified by regression
test in §6 item 10, and by leaving every review state / test event already stored for `chb13_03.edf`
(and `chb13_02.edf`) exactly as found.

## 0 · Pre-flight

`pytest web_demo/backend/tests/test_guards.py -v` was green before starting (see §7 for the raw output
run again at the end). `claude-in-chrome` was connected on the first `tabs_context_mcp` call — no
reconnect needed. No `git add`/`commit`/`push` was run at any point (confirmed below in §7).

Read first, in full, before writing any code: `UI/B1a`, `UI/B2a`, `UI/A0c`, `UI/A0a` (copied to scratch
and viewed), `SZSCAN_DESIGN_v2.md` §1/§2/§9/§10, `Header.jsx`, `eventStyle.js`, `MiniTimeline.jsx`, the
Event Time strip inside `EegPanel.jsx`, `index.css` `:root`, `tailwind.config.js`, `design-tokens.js`.

All mockup measurements below are pixel-measured from the locked PNGs (1440px wide) with a small
Python/PIL script, not eyeballed — see the exact scan ranges in the commands run during this session.
Per the resolution warning, every comparison is a **fraction of header height**, never a raw pixel
match between mockup and live app (the two are rendered at different pixel densities).

## 1 · Analysis header: button group moved next to the file dropdown

**Before:** `Previous / Next | Viewed / Export` sat immediately after the title, with `ml-auto` only on
the file-dropdown wrapper — leaving a large gap between the button group and the dropdown.

**Change (`AnalysisScreen.jsx`, `headerCenter`):** wrapped `Previous / Next | Viewed / Export` in a new
`<div className="flex items-center gap-3 ml-auto shrink-0">`, moved `ml-auto` there, and removed it from
the file-dropdown wrapper. Title stays first (left), untouched. No button behaviour, enabled/disabled
logic, or the Progress bar was touched.

**Verified live:** `exportBtn.getBoundingClientRect().right` = 1116.6, `fileDropdown...left` = 1128.6 —
a 12px gap, exactly the `gap-3` spacing used everywhere else in this row, confirming the group now sits
immediately left of the dropdown rather than floating after the title. Matches `UI/B1a`/`B2a`'s layout
(title left, then the whole cluster — Previous/Next, divider, Viewed/Export, file dropdown — packed
together on the right). Screenshot: `after_analysis_header_minitimeline.jpg`.

## 2 · Header sizing: logo + wordmark + avatar

### Measurements (fraction of header height)

| Element | Mockup (measured, px / 132px header) | Live BEFORE (px / 104px header) | Live AFTER (px / 104px header) |
|---|---|---|---|
| Header height | 132px (reference) | 104px | 104px — **unchanged**, see note below |
| Logo mark | 83px → **0.629** | 62px → 0.596 | 62px → 0.596 (**not changed** — already close) |
| Wordmark (ink height) | 35px → **0.265** | 36px → 0.346 | 27px → 0.260 |
| Avatar diameter | 67px → **0.508** (only `UI/A0a`/`A0c` show one) | 66.5px → 0.639 | 56px → 0.538 |

Mockup pixel source: `UI/A0a.png`/`A0c.png`/`B1a.png`/`B2a.png` are all 1440px wide; the header/body
color-boundary sits at y=132 in all four (measured independently, identical). Logo-icon and wordmark
ink bounding boxes are pixel-identical across all four mockups too (83px / 35px). Live values are
`getBoundingClientRect()` reads plus a pixel-scan of a saved screenshot for the wordmark's actual ink
height (a DOM rect gives the line-box, not the glyph height, so it isn't the same measurement as the
mockup's pixel-scanned ink height — the screenshot scan keeps the comparison apples-to-apples).

**Why header height didn't change:** `Header.jsx` sizes the header via `py-5` padding around whichever
child is tallest. The logo mark (`h-16` = 64px, untouched) was already the tallest child before this
fix and still is after shrinking the avatar and wordmark — so the header's own height (104px) is
unaffected. Only the avatar and wordmark actually needed to shrink; the logo mark's own proportion
(0.596 live vs. 0.629 mockup) was already close enough that changing it would have meant *growing* the
header to keep it the tallest element, which nothing in the prompt asked for.

**Changes (`Header.jsx`):**
- Wordmark: `text-5xl` → `text-4xl` (48px → 36px font-size). Ink height 36px → 27px (0.346 → 0.260 of
  header height, target 0.265).
- Avatar: `w-16 h-16` → `w-14 h-14` (64px → 56px), person icon `w-10 h-10` → `w-9 h-9` (40px → 36px, kept
  proportional to the button). Diameter 66.5px → 56px (0.639 → 0.538 of header height, target 0.508).
- Logo mark: **not changed** (already close to target, see above).

### Per-screen check

- **Database** (`UI/A0a`/`A0c`): the only mockups that show an avatar at all, so both the wordmark and
  avatar targets above come from here. Before/after: `before_database_header.jpg`,
  `after_database_header.jpg`. Confirmed proportions moved from 0.346/0.639 to 0.260/0.538, both now
  much closer to 0.265/0.508.
- **Analysis** (`UI/B1a`/`B2a`): shares the exact same `Header.jsx` component and thus the exact same
  logo/wordmark sizes as Database (`getBoundingClientRect()` confirmed identical: 64px logo, 56px
  avatar, 104px header, on both screens). The logo+wordmark portion of `UI/B1a`/`B2a` is pixel-identical
  to `UI/A0a`/`A0c` (measured above), so the same fix is correct here too. **The avatar is the one
  thing I could not directly verify against Analysis's own mockup**: `UI/B1a` and `B2a` don't render an
  avatar at all in the top-right — that space is filled edge-to-edge by the file-dropdown pill instead
  (confirmed by pixel-diffing the top-right corner of `B1a` against its own local background: the only
  non-background blob found there is the white dropdown pill, x=1220-1400, not a purple circle). Since
  `Header.jsx` is one shared component with fixed Tailwind classes, there is no way to size the avatar
  differently per screen without adding screen-conditional props — not something the prompt asked for,
  and Boti's own complaint ("the avatar... looks oversized") was stated generally, not scoped to one
  screen. I sized it from the one mockup that shows it (Database) and applied the same shared fix to
  Analysis; flagging this as the one extrapolation in this section rather than a directly-verified match.
- **Log in** (`UI/A0c`'s login state — same PNG as the Database "not logged in" state per the prompt's
  own file list): confirmed by reading `LoginScreen.jsx` that it does **not** import or render
  `Header.jsx` at all — the login page is its own full-bleed gradient background with a centered card,
  a separate component. Nothing to check or fix here; noted per the prompt's own instruction to check
  only if it shares the component.

## 3 · Event blocks: solid colour, no hatch

**Change (`eventStyle.js`, `blockStyle()`):** Accept/Reject/Uncertain all changed from their old
opacities (0.75 / 0.55 / 0.75) to **1** (full opacity); Reject's `hatch: true` changed to `hatch: false`.
Human (already 1/no-hatch) and unreviewed AI (already 1/no-hatch) unchanged. This is the one shared
function behind both the mini-timeline's Detections row and `EegPanel.jsx`'s Event Time strip, so both
picked up the change automatically — no separate edit needed in either component. Checked `UI/B2a` and
the `UI/B3a-c` mockups from Step 6: both the mini-timeline and the Event Time strip show plain solid
blocks in every mockup that has one, no hatching anywhere — so the shared change is the correct
interpretation for both surfaces, not just one.

**Interpretation of "full màu":** full-opacity token colour, i.e. `opacity: 1` in the object `blockStyle`
returns (this is what actually reaches the `style.color`/`opacity` CSS on both the mini-timeline block
and the Event Time strip block) — not a change to the hex values themselves (those are unchanged except
for Uncertain, see §4).

**Kept unchanged, verified live:** dimming to opacity 0.4 while another event is selected (computed
style confirmed: dimmed blocks show `opacity: "0.4"`, their `backgroundColor` unchanged); the selected
block's own violet outline (`outline: "rgb(124, 58, 237) solid 2px"`, i.e. `--color-interaction`) and
full opacity; Human's solid `#2563EB`; block geometry/position (no changes to `left`/`width` math in
either component).

**Live pixel/computed-style sample** (`chb13_03.edf`, no event selected — see §6 item 5 for the full
readout): Reject `rgb(220, 38, 38)` = `#DC2626`, opacity 1, `backgroundImage: "none"` (confirms no
hatch); Human `rgb(37, 99, 235)` = `#2563EB`, opacity 1; Uncertain `rgb(255, 226, 98)` = `#FFE262`,
opacity 1. **No Accept-status event exists anywhere in the current database** (checked directly:
`SELECT review_status, COUNT(*) FROM events WHERE source='AI' GROUP BY review_status` returns only
Reject/Uncertain/Unseen) — so Accept's fill could not be pixel-sampled live this round. I deliberately
did not create one to check: the only way to get an Accept-status event is to Accept a real, currently
Unseen AI event on some file, and there is no "un-accept" control in the app (§6.5's expand panel has no
"undo review" button) — doing that would permanently and irreversibly change real stored review data on
a file outside (or inside) the explicitly protected `chb13_03.edf`, for a purely cosmetic check, without
Boti's authorization. Accept's code path is identical to Reject/Uncertain's (same `switch` in the same
function, same rendering call site), so this is a structural/code-level confirmation rather than a
fresh screenshot — flagging the gap rather than silently treating it as verified.

## 4 · Uncertain colour → `#FFE262`

**Single source of truth changed** (`index.css` `:root`): `--color-uncertain: #FFE262` (was `#D97706`);
added `--color-uncertain-text: #D97706` for text/thin-stroke use. `design-tokens.js` and
`tailwind.config.js` updated to match (`colorUncertainText` / `uncertain-text` added) — confirmed by
grep afterward that `D97706`/`FFE262` only appear in these two token files (plus comments); no second
hard-coded hex anywhere else. `--color-uncertain-bg` (`#FFFBEB`) left alone, per the prompt.

**Applied everywhere the old fill was used** (`eventStyle.js`, `PanelEvent.jsx`):
- Mini-timeline block / Event Time strip block (`blockStyle`'s Uncertain case) — now full-opacity
  `#FFE262`, verified live (§3).
- Event Panel row left bar (`listBarColor`'s Uncertain case) — automatically picks up the new value;
  verified live, screenshot `item8_uncertain_row_bar_zoom.png`.
- The Uncertain option in the expanded AI event (`PanelEvent.jsx`'s `AiExpand`, the selected-state
  button fill) — now `bg-uncertain`.

**A bug I found and fixed that wasn't explicitly named in the prompt's location list:** the Event Time
strip prints the event's own name (`Event N`) inside its block, and that label was hardcoded
`text-white` for every status. White-on-`#FFE262` is essentially invisible — confirmed live
(`item9_uncertain_eventtime_label_BROKEN_before_labelfix.png` shows only a faint outline where "Event 5"
should read). The prompt's location list does include "Event Time strip block", so this is squarely in
scope even though the exact sub-element (the name label) wasn't spelled out. Fix: added
`blockLabelColor(event)` to `eventStyle.js` (white normally, `colorUncertainText` for an Uncertain AI
event) and used it in `EegPanel.jsx`'s label `<span>` via an inline `style` instead of the `text-white`
class. Verified fixed: `item9_uncertain_eventtime_label_fixed.png` shows "Event 5" clearly readable in
dark amber.

**A judgment call the prompt didn't explicitly cover, flagged for Boti:** the Uncertain button inside
the expanded AI event (`PanelEvent.jsx`) also had `text-white` on its selected fill — same illegibility
problem, same fix logic (switched to `text-uncertain-text`). This one *is* covered by the prompt's own
"the Uncertain option in the expanded event" location, but the specific mechanism (swapping the text
color rather than the fill) was my own call, not spelled out. Verified live and legible:
`item8_uncertain_expanded_readable.jpg` (the "Uncertain" button reads clearly in dark amber-brown on the
pale yellow fill).

**Visibility check (measured + screenshot, per the prompt's explicit request — no extra styling added,
reporting the numbers and letting Boti decide):**

| Comparison | WCAG contrast ratio | Note |
|---|---|---|
| `#FFE262` fill vs. `#D97706` text (Uncertain button / Event Time label) | **2.47** | Below WCAG AA's 4.5:1 (normal text) and 3:1 (large text) thresholds by the numbers, but the screenshots (`item8_uncertain_expanded_readable.jpg`, `item9_uncertain_eventtime_label_fixed.png`) show it reading clearly at the sizes actually used (short, bold-ish labels) — better than white text's 1.29 by a wide margin either way. |
| `#FFE262` vs. white surface / EEG canvas (`#FEFBEF`) | **1.24** | Low by the numbers — a solid-colour block next to a near-white background — but the mini-timeline screenshot (`item9_uncertain_minitimeline_visibility.png`) shows the yellow block as a visually distinct sliver against the cream canvas; hue difference reads even where luminance contrast is low. Not touching this — no border/shadow added — per the instruction. |
| `--color-uncertain-bg` (`#FFFBEB`, **unchanged this round**) vs. white surface / EEG canvas | **1.037 / 1.0** | Essentially identical — this token was already this close to invisible before this fix round (I didn't touch its value), but the prompt asked me to check and report it regardless of when it happened, so: yes, it is visually indistinguishable from both the white panel background and the EEG canvas. Visible in `item8_uncertain_expanded_readable.jpg`'s pale-yellow "highlighted" row — you can tell it's tinted only because the row above/below it isn't, not because the tint itself reads as a distinct color. |

## 5 · `SZSCAN_DESIGN_v2.md` updates

Minimal, targeted edits only — no reformatting, no rewritten sections, no line-ending changes (git's
own CRLF-on-checkout warning appears for every already-tracked file in this repo on this Windows
checkout, unrelated to my edits — see §7).

- §2 Axis 2 table: Uncertain row now reads `#FFE262` (fill) / `#D97706` for text-or-thin-stroke use, with
  a parenthetical note attributing the decision to `CC_STEP6_FIX_PROMPT.md` and explaining why.
- §2 mini-timeline/Event Time rule sentence: rewritten to describe solid fills for all four states (was:
  ~75%/~55%-plus-hatch), with a new parenthetical noting this relaxes principle 3 ("never convey meaning
  through color alone") for these blocks specifically, and that status text still appears on the Event
  Panel row and its badges.
- §9 token block: `--color-uncertain` value updated, `--color-uncertain-text` row added.
- §10 change table: three new rows (Uncertain status color, Reject block hatch removal, Accept/Uncertain
  block opacity), each with a reason and a pointer back to `CC_STEP6_FIX_PROMPT.md`.

## 6 · Live verification (claude-in-chrome, real UI, real backend)

1. **Before** — `before_database_header.jpg` (Database header, oversized logo/wordmark/avatar).
   Analysis "before" is the Step 6 round's own screenshots (`CC_STEP6_SCREENSHOTS/item9_*.jpg`,
   `item10_*.jpg`) — genuinely pre-this-round evidence, since I measured and edited in the same pass
   this time and didn't want to touch already-stored fixture events just to reproduce a "before" shot.
2. **After, Analysis header** — `after_analysis_header_minitimeline.jpg`: button group now sits
   immediately left of the file dropdown, title on the left. ✅
3. **Measured values** — table in §2. ✅
4. **Database (and Log in) header** — `before_database_header.jpg` / `after_database_header.jpg`;
   Log in doesn't share the component (§2). ✅
5. **Mini-timeline pixel/computed-style sample, no event selected** — Reject `#DC2626` solid (no hatch,
   `backgroundImage: none`), Human `#2563EB`, Uncertain `#FFE262` — all confirmed via computed style
   read directly off the live DOM (§3). Accept not sampled — no Accept-status event exists in the
   current database (§3). ✅ (partial — see note)
6. **Selection dimming/outline** — selected Event 5 (Uncertain): `opacity: "1"`,
   `outline: "rgb(124, 58, 237) solid 2px"`; the other six events: `opacity: "0.4"`, fill colour
   unchanged. Screenshots `item6_selected_dimming.jpg`, `item6_selected_outline_zoom.png`. ✅
7. **Event Time strip** — same solid/no-hatch/full-opacity treatment confirmed via the same computed-
   style query (the strip's blocks and the mini-timeline's blocks share `blockStyle()`, and both
   appeared in the same query result with a matching `title`). ✅
8. **Event Panel Uncertain row** — left bar in `#FFE262` (`item8_uncertain_row_bar_zoom.png`); its own
   text ("Event 5", "Uncertain" button) reads in dark amber, confirmed legible
   (`item8_uncertain_expanded_readable.jpg`). ✅
9. **Visibility screenshots** — table + screenshots in §4. ✅
10. **Select Range regression** — created a disposable Human event on `chb13_03.edf` (onset 18:30:07,
    offset 18:30:21): appeared as Event 6, Human blue block on the mini-timeline, Alert
    `04`→`05` (`item10_regression_create.jpg`, `item10_regression_expanded_human.jpg`). Deleted it:
    Alert back to `04`, block gone, event count back to 7 (`item10_regression_delete_alert_reverted.jpg`).
    Confirmed directly against the database afterward — no residue from this test. ✅
11. **Guard tests + git status/diff --stat** — raw output below.

```
$ pytest web_demo/backend/tests/test_guards.py -v
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 4 items

web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED [ 25%]
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED [ 50%]
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED  [ 75%]
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED [100%]

============================== 4 passed in 5.80s ==============================

$ git status
On branch main
Your branch is ahead of 'origin/main' by 13 commits.
Changes not staged for commit:
	modified:   web_demo/BUILD_PROGRESS.md          [pre-existing, before this round]
	modified:   web_demo/DEMO_BUILD_HANDOFF.md       [pre-existing, before this round]
	modified:   web_demo/SZSCAN_DESIGN_v2.md         [this round's §5 edits, on top of pre-existing]
	modified:   web_demo/SZSCAN_SPEC_v5.md           [pre-existing, before this round]
	modified:   web_demo/backend/db.py               [Step 6, unchanged this round]
	modified:   web_demo/backend/main.py             [Step 6, unchanged this round]
	modified:   web_demo/frontend/index.html         [pre-existing, before this round]
	modified:   web_demo/frontend/src/api.js         [Step 6, unchanged this round]
	modified:   web_demo/frontend/src/components/EegPanel.jsx   [this round: item 4's label fix]
	modified:   web_demo/frontend/src/components/Header.jsx     [this round: item 2]
	modified:   web_demo/frontend/src/design-tokens.js          [this round: item 4]
	modified:   web_demo/frontend/src/index.css                 [this round: item 4]
	modified:   web_demo/frontend/src/screens/AnalysisScreen.jsx [this round: item 1; Step 6 otherwise]
	modified:   web_demo/frontend/src/time.js         [pre-existing, before this round]
	modified:   web_demo/frontend/tailwind.config.js  [this round: item 4]
Untracked files:
	bme11/, rank_readout.py, results/attribution_v7/... [pre-existing, unrelated to web_demo]
	web_demo/CC_STEP5_FIX*.{md,/} , CC_STEP5_REPORT.md   [pre-existing Step 5 artifacts]
	web_demo/CC_STEP6_FIX_PROMPT.md, CC_STEP6_FIX_SCREENSHOTS/   [this round]
	web_demo/CC_STEP6_PROMPT.md, CC_STEP6_REPORT.md              [prior Step 6 round]
	web_demo/UI/uncertain_pill_zoom.png                          [scratch artifact from this round's mockup check]
	web_demo/frontend/src/components/MiniTimeline.jsx  [Step 5, untracked since; unchanged this round]
	web_demo/frontend/src/components/PanelEvent.jsx    [this round: item 4's text-color fix]
	web_demo/frontend/src/eventStyle.js                [this round: items 3 & 4]
	web_demo/spec_docs_diff.md                          [pre-existing]

$ git diff --stat
 web_demo/BUILD_PROGRESS.md                       | 548 +++++++--------
 web_demo/DEMO_BUILD_HANDOFF.md                   | 215 +++---
 web_demo/SZSCAN_DESIGN_v2.md                     | 286 ++++----
 web_demo/SZSCAN_SPEC_v5.md                       | 836 ++++++++++++-----------
 web_demo/backend/db.py                           |  31 +
 web_demo/backend/main.py                         |  42 +-
 web_demo/frontend/index.html                     |   1 +
 web_demo/frontend/src/api.js                     |  19 +
 web_demo/frontend/src/components/EegPanel.jsx    | 177 ++++-
 web_demo/frontend/src/components/Header.jsx      |  13 +-
 web_demo/frontend/src/design-tokens.js           |   4 +-
 web_demo/frontend/src/index.css                  |   7 +-
 web_demo/frontend/src/screens/AnalysisScreen.jsx | 388 +++++++++--
 web_demo/frontend/src/time.js                    |   7 +
 web_demo/frontend/tailwind.config.js             |   1 +
 15 files changed, 1561 insertions(+), 1014 deletions(-)
```

The large line counts on `BUILD_PROGRESS.md`/`DEMO_BUILD_HANDOFF.md`/`SZSCAN_SPEC_v5.md`/
`SZSCAN_DESIGN_v2.md` are **not** from this fix round — `git status` already showed these four files
modified before this session started (a prior, uncommitted pass that appears to have translated large
portions from Vietnamese to English). I checked `git diff -- web_demo/SZSCAN_DESIGN_v2.md` specifically
for the hunks touching my own edits (grepped for the `CC_STEP6_FIX_PROMPT.md` marker I added) and
confirmed my additions are exactly the small, targeted insertions described in §5 — nothing of mine
reformatted or rewrote the file. No `git add`/`commit`/`push` was run. Confirmed nothing outside
`web_demo/` was touched (the untracked `bme11/`, `rank_readout.py`, `results/...` entries all predate
this session).

## 7 · Test-state note

`chb13_03.edf` (file id 11) now holds, in onset order: AI Reject (80s), **Human 1153.4–2323.7s** (Boti's
own test event, left untouched), AI Reject (2420s), **Human 2561.2–2620.9s** (this project's own Step 6
fixture, left in place per `CC_STEP6_REPORT.md`), AI Uncertain (2800s), AI Reject (3440s), **Human
3473.9–3571.4s** (Boti's own test event, left untouched) — 7 events total, Alert `4`. `chb13_02.edf`
(file id 10) holds 2 Human events (19.4–41.8s, 1372.3–1416.8s), also Boti's own, also left untouched —
Alert `2`. Subject `chb13`'s total Alert is `6`, matching what was on screen before I made any change.

The one event I created this round (disposable, onset 18:30:07/offset 18:30:21 on `chb13_03.edf`, used
for the Select Range regression test in §6 item 10) was deleted before finishing — confirmed directly
against the database afterward that only the 7 events listed above remain, with no extra row.

Dev servers (backend `:8000`, frontend `:5173`) were left running for Boti to review live.

## 8 · Stop condition

Stopping here per the prompt. Step 7 (Channel Attribution) not started.
