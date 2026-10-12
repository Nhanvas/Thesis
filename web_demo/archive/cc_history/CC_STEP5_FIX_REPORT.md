# CC_STEP5_FIX_REPORT.md — Step 5 fix round 1

Status: **all six items resolved**, with visual (screenshot / pixel-sampled) evidence, not code-read
confidence alone. `claude-in-chrome` was available and used for every check that required it. Guard
tests green, see §7.

This round found that item 3 (EEG canvas near-black / illegible) was real, and that it was the root
cause behind item 4 and item 5 also *looking* broken — once it's fixed, the filter-toggle and
window-length controls turn out to already work correctly. Details below.

---

## 1 · `backfill_scores.py` — write-up of the earlier Phase A+B run

`backfill_scores.py` no longer exists on disk — it was a one-off script, never committed (`git log --all
--diff-filter=A -- '**/backfill*'` returns nothing), so it isn't available to re-read verbatim. What
follows is evidence reconstructed from its effects, not from its source.

**It never called `cpd_pipeline_v14`, `detect_events`, or any PELT function.** `pipeline_demo.py` has
exactly two call sites for `cpd_pipeline_v14.detect_events` — `calibrate_operating_point` (line 376) and
`process_subject_events` (line 414) — both Stage-2/event-detection functions, distinct from
`process_file_phase_a`/`process_subject_phase_b` (the Phase A+B functions the backfill would have used).
Corroborating evidence that Stage 2 did not run again: the `events` table for `chb13` still holds exactly
the same 4 rows, in the same review states, that `CC_STEP5_REPORT.md §7` recorded as left over from that
report's own verification pass —

```
id=46 file_id=11 source=AI onset=80.0   offset=164.0  review_status=Accept
id=47 file_id=11 source=AI onset=2420.0 offset=2424.0 review_status=Reject
id=48 file_id=11 source=AI onset=2800.0 offset=2804.0 review_status=Uncertain
id=49 file_id=11 source=AI onset=3440.0 offset=3444.0 review_status=Unseen
```

— if the backfill had re-run detection, this table would have changed (new ids, or reset review
statuses). It didn't.

**Path + gitignore.** Score arrays live at `web_demo/backend/uploads/{subject}/{stem}.score.npy`, e.g.
`web_demo/backend/uploads/chb13/chb13_02.score.npy`. `.gitignore:56` covers `web_demo/backend/uploads/`
wholesale, so every file under it — `.edf`, `.raw.npy`, `.filtered.npy`, `.score.npy` — is untracked;
confirmed with `git check-ignore` and by `git status` never listing anything under that path.

**Score length matches window count, shown for `chb13`:**

```
chb13_02: raw.npy.shape=(900, 18, 1024)  filtered.npy.shape=(900, 18, 1024)  score.npy.shape=(900,)
chb13_03: raw.npy.shape=(900, 18, 1024)  filtered.npy.shape=(900, 18, 1024)  score.npy.shape=(900,)
```

900 windows × 1024 samples/window ÷ 256 Hz = 3600 s, matching both files' `duration_seconds` in the
`files` table exactly. `score.npy`'s first dimension is 900 for both files — an exact match to
`n_windows`, not an approximation.

## 2 · `UI/B2a*`/`UI/B2d*` wording check

Read both PNGs directly (not from memory): **both show the literal pixel text "Seizure Detections"** for
the mini-timeline's row 2, not "Detections". This is the mockup lagging `SZSCAN_DESIGN_v2.md §8`, exactly
as `CC_STEP5_PROMPT.md`'s own wording flag predicted — §8 wins, and the app (and `MiniTimeline.jsx`)
correctly render "Detections". No code change needed; flagging for the record as instructed.

---

## 3 · EEG canvas near-black / illegible waveform

**Confirmed live** at `chb13_03.edf`, 1 min window, 20 µV (screenshot, not asserted): the canvas was
almost entirely a near-black fill with dense vertical white streaks, matching the report exactly.

**Diff evidence — not this step's regression.** `git diff` on `EegPanel.jsx` (full diff in this report's
companion commit) shows this step's only change to the file is the new "Event Time" strip block-rendering
(the wiring `CC_STEP5_PROMPT.md` authorized) plus the `events`/`selectedEventId` props that feed it.
Nothing in the diff touches the base-canvas drawing `useEffect` (background fill, `drawSeries`, the
per-channel loop) — that code is byte-for-byte what Step 4 already had. So this is a **pre-existing gap
Step 4 did not actually fix**, not a regression from this step's sync-wiring edit.

**Root cause, found by pixel-sampling the live canvas (`ctx.getImageData`), not eyeballing:**
`drawSeries()` draws each channel's min/max envelope line at its *true* y-coordinate, deliberately
unclamped to that channel's own row (a Step-4-era comment explains this was to avoid an earlier "flatten
to a solid block" bug). But nothing bounded the *drawing* to the channel's row either — so a channel whose
real amplitude exceeds the µV/division scale (confirmed: `chb13_03`'s raw envelope spread is ~94–105 µV
around 60–120 s, with peaks past 700 µV — routine for this dataset, not an outlier window) paints straight
through every other channel's row. With **filters on by default** (`AnalysisScreen.jsx` initial state:
`{lff:true, hff:true, notch:true}`), the opaque filtered layer (`#0F172A`, near-black) is drawn last on
top of that bleed, so nearly the whole canvas ends up filled with that one near-black color — sampling a
5×3 grid of canvas pixels returned `rgb(15,23,42)` (the filtered color) at 14 of 15 points; only 1 showed
the true `#FEFBEF` background.

**Max-amplitude check (30 µV, the least-sensitive token available):** still heavily saturated — most of
the canvas remained dark. Directly measuring the actual signal via the waveform API (not assumed) across
7 windows spanning the whole file shows this is a real property of the data, not an artifact of one
window: raw envelope spread averages 120–155 µV throughout `chb13_03`, with peaks up to ±1000 µV — several
times larger than the 30 µV ceiling the demo's amplitude-token list offers. So *some* per-channel
clipping at 30 µV is expected for this file (same precedent Step 4 already established for aggressive
settings) and is not, by itself, a bug.

**Fix applied** (`EegPanel.jsx`): wrap each channel's `drawSeries` calls in a `ctx.save(); ctx.rect(0,
bandTop, cssWidth, rowHeight); ctx.clip(); … ctx.restore()` so overflow clips to that channel's own row
instead of bleeding into the other 17. This keeps the earlier fix's reasoning intact (coordinates are
still drawn unclamped, so a channel's own trace shape is preserved, not flattened into a block — that was
the original bug this Step-4 comment was guarding against) while containing the effect to one row.

**Verified, not asserted**, by re-sampling cream-background-pixel fraction per row after the fix (20 µV,
same window): rows now range from 1.5% to 31.6% background visible — real per-channel variation, where
before the fix all 18 rows were uniformly ~95%+ covered by bleed regardless of that channel's own data.
Zoomed screenshots before/after show the same: before, one undifferentiated black mass; after, 18
visually distinct rows, several clearly less dense than others.

**Not fully resolved by this fix, and said plainly rather than overclaimed:** because `chb13`'s real
signal amplitude (100–150+ µV typical, confirmed via direct API measurement, not the score/detection
data) exceeds every available amplitude token (max 30 µV), individual channels can still look busy/clipped
even after the fix — that is now the same *expected*, contained-to-one-row clipping Step 4 already
documented as normal at an aggressive setting, not the cross-channel corruption this round's bug report
describes. Whether the amplitude-token list should be extended for scalp EEG this size is a design
question outside this fix round's scope — flagging it rather than deciding it unilaterally.

## 4 · Filter toggle (`lff`/`hff`/`60`) — investigated, not a bug

**Backend does return two distinct series per call** — confirmed by calling
`/api/files/11/waveform?...` directly: the response has exactly `raw_uv` and `filtered_uv`, one array
each, not one per filter. `DEMO_BUILD_HANDOFF.md §5` confirms this by design: *"Bật/tắt filter → backend
trả cả 2 chuỗi (raw + filtered) trong 1 lần gọi, frontend tự chồng lớp"* — one combined filtered series,
frontend layers it. `SZSCAN_SPEC_v5.md §6.4` (line 404) describes the same thing in the singular: *"khi
bật, sóng đã lọc nổi bật, sóng raw lùi làm nền mờ"* — "the filtered wave" (singular), not three
independently different ones. The 3 buttons are individually clickable, but per spec they all just OR
together into one `anyFilterOn` boolean — that's the intended architecture, not a scope gap.

**Frontend does switch which series is drawn on top**, verified by pixel-sampling the canvas's
background-visible fraction, at the *same* playhead position, before/after toggling, after item 3's fix
was applied: all-filters-off (raw only, full opacity) → 23.6% background visible; any-filter-on
(filtered layer drawn on top) → 20.0%. Screenshots confirm a real, visible color shift (slate-grey raw vs.
near-black filtered).

**What's genuinely not distinguishable, and is expected:** toggling *between* `lff`/`hff`/`60` while at
least one stays on — e.g. `hff`-only vs. `hff`+`lff` — produced *zero* pixel difference (20.04% both
times), because both states resolve to the same `anyFilterOn = true` and the same single `filtered_uv`
array. That matches spec exactly; there's no third data series for the frontend to switch to.

**Why this looked broken during Boti's manual pass:** before item 3's fix, the whole canvas was ~95%+
covered in bleed-through near-black regardless of which series was on top, so the real (but modest)
raw-vs-filtered color difference was swamped and imperceptible. After the fix, the difference is
measurable and visible. **Conclusion: no code change needed for item 4** — it was a symptom of item 3,
not an independent bug.

## 5 · Window-length control (`⊲▷ [X]`) — investigated, not a bug

Live-tested by opening the duration popover and selecting `10 min`, then `5 min`, via the real DOM
buttons (not a mocked event). Both times the time-axis labels updated correctly (e.g. `17:43:20 →
17:44:20` at 1 min became `17:43:20 → 17:53:20` at 10 min), and `read_network_requests` confirmed a real
`GET /api/files/11/waveform?start_sec=0&end_sec=300&width_px=849` fired for the 5 min selection — the
correct 300 s span. Reading `AnalysisScreen.jsx`'s waveform-fetch `useEffect` (line 235) confirms
`windowSec` is in its dependency array. **The control works correctly as-is; no code change made.**

Same explanation as item 4: this almost certainly looked broken during manual testing for the same
reason — the canvas showing dense black noise "before" and dense black noise "after" a window-length
change looks identical to a human eye even though the underlying fetched window genuinely changed,
because item 3's bug dominated the visual at every window length. Worth re-confirming visually with a
real user now that item 3 is fixed.

## 6 · Panel Event column height

**Confirmed via mockup comparison.** `UI/B1a` and `UI/B2a` both show the right-hand column running the
full height of the page alongside the EEG panel (in the mockups it's actually two stacked boxes — event
list, then a channel-attribution/head-map panel below it — but attribution is out of this step's and this
fix round's scope; the point that transfers is that the column's outer height matches the EEG panel's).

**Root cause, found by reading the layout, not guessing:** `AnalysisScreen.jsx`'s outer row
(`<div className="flex gap-4 items-start">`) used `items-start`, which overrides flexbox's default
cross-axis stretch and top-aligns each column to its own natural content height instead. `PanelEvent.jsx`
additionally hardcoded `style={{ maxHeight: 640 }}` on its own root — a fixed guess disconnected from the
actual (dynamic, often 900px+) height of the sibling EEG column.

**Fix:** `items-start` → `items-stretch` on the outer row; `w-[340px] shrink-0` wrapper gets `flex
flex-col` so it participates properly in the stretch; `PanelEvent.jsx`'s root swaps the inline
`maxHeight: 640` for `h-full min-h-0`, so it fills whatever height the stretch gives it (its own event
list already had `overflow-y-auto flex-1`, so it scrolls internally instead of overflowing).

**Verified live**, not just in code: scrolled the real page after the fix — Panel Event's bordered box now
visibly continues past its event rows as blank (but still bordered) space, ending exactly level with the
bottom of the "Seizure detection" panel / transport controls, matching the mockups' proportions. Before
the fix it stopped flush after Event 4's row, around a third of the way down the page.

---

## 7 · Guard tests + git status (raw output, end of this round)

```
$ pytest web_demo/backend/tests/test_guards.py -v
============================= test session starts =============================
collected 4 items

web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED [ 25%]
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED [ 50%]
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED  [ 75%]
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED [100%]

============================== 4 passed in 5.99s ==============================
```

```
$ git status
On branch main
Your branch is ahead of 'origin/main' by 10 commits.

Changes not staged for commit:
	deleted:    FIGURE_FIXES_PROMPT.md
	modified:   web_demo/frontend/index.html
	modified:   web_demo/frontend/src/api.js
	modified:   web_demo/frontend/src/components/EegPanel.jsx
	modified:   web_demo/frontend/src/screens/AnalysisScreen.jsx
	modified:   web_demo/frontend/src/time.js

Untracked files:
	web_demo/CC_STEP5_FIX_PROMPT.md
	web_demo/CC_STEP5_REPORT.md
	web_demo/frontend/src/components/MiniTimeline.jsx
	web_demo/frontend/src/components/PanelEvent.jsx
	web_demo/frontend/src/eventStyle.js
```

`FIGURE_FIXES_PROMPT.md`'s deletion is the same unrelated concurrent figure-fixes session noted in
`CC_STEP5_REPORT.md §8` — nothing to do with `web_demo/`. This round's own changes are confined to
`EegPanel.jsx` (§3's clip fix) and `AnalysisScreen.jsx` (§6's height-stretch fix, both inside `<main>`'s
layout, no logic outside the flex/clip changes described above) plus `PanelEvent.jsx` (§6's `h-full`
swap, listed above as still-untracked since the whole file predates this fix round).

Files changed by this fix round specifically:
```
web_demo/frontend/src/components/EegPanel.jsx     | 12 +++++++++++- (clip fix, §3)
web_demo/frontend/src/screens/AnalysisScreen.jsx   |  2 +-        (items-stretch + flex-col, §6)
web_demo/frontend/src/components/PanelEvent.jsx    |  2 +-        (h-full swap, §6)
```

`chb13`'s event review states (Accept/Reject/Uncertain/Unseen on `chb13_03.edf`) and the `chb13`/`chb14`
subject rows' "Viewing" progress are unchanged from where `CC_STEP5_REPORT.md §7` left them — same
carried-forward test-state note applies; nothing in this fix round touched the database.

---

## 8 · Stop condition

Items 1–6 all resolved and documented with evidence (screenshots, pixel-sampled canvas data, live network
requests, or direct API calls — not code-read confidence alone where the prompt asked for visual proof).
Guard tests green. `claude-in-chrome` was up and used throughout this round. **Step 5 is closed.** Step 6
(Select Range) has not been started.
