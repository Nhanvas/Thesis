# CC_STEP5_FIX6_PROMPT.md — Step 5 fix round 6

Three items. One is a decided change to implement (no more back-and-forth needed), one needs
independent verification, one is a repeated layout bug that earlier rounds only partially addressed —
fix the actual structure this time, not another surface patch.

## 1 · Implement the final amplitude-token list — decided, just do it

Boti has decided: floor at **75 µV**. Update `AnalysisScreen.jsx`'s `AMPLITUDE_OPTIONS` from
`[500, 250, 150, 100, 75, 50, 30, 20, 15, 10, 7, 5]` to **`[500, 250, 150, 100, 75]`** — drop
`50/30/20/15/10/7/5` entirely. Update `SZSCAN_SPEC_v5.md §6.4`'s C18 note to match (the dropdown list
and the accompanying explanation of which levels exist and why) — keep the note's existing measurement
data, just correct the final list and the reasoning for where the floor landed. This is the only item
in this round that's simply "do it," not "investigate."

## 2 · Is the ~1-hour file length genuine, or was it truncated somewhere in the pipeline?

Every file currently in the DB shows a duration of exactly ≤ 1 hour, and round 5 attributed this to
`waveform_serving.usable_duration_seconds()`'s own cached window count. That only proves the *cache*
is ≤ 1 hour — it does not prove the *original* `.edf` file is genuinely that short. Verify
independently: for `chb13_02.edf`, `chb13_03.edf`, and `chb06_01.edf`, read the **raw file's own
header** directly (e.g. `mne.io.read_raw_edf(path, preload=False).n_times` / sampling rate, or
equivalent), completely bypassing `pipeline_demo.py`'s cache and `usable_duration_seconds()`. Report
the true raw duration for each file next to the cached duration currently shown in the UI. If they
match, state plainly that these are genuinely ~1-hour recordings (a known, common convention for
individual CHB-MIT files) and not a truncation. If the raw file is actually longer than what's cached,
that's a real bug in Phase A/B's caching — find where the truncation happens and report it (don't fix
without confirming with Boti first, since this could be a deliberate, undocumented scope decision from
an earlier step rather than a bug).

## 3 · Fix the actual layout grouping — mini-timeline full-width, Event Panel paired with EEG Panel

This has been raised multiple times and is still wrong. The mini-timeline (Seizure Detection Score +
Detections rows) and the Event Panel are currently grouped as a side-by-side pair in one row, which
steals horizontal width from the mini-timeline. That pairing is wrong. The correct structure, per
`UI/B2a*.png` and `UI/B1a*.png`:

- **Row 1, full page width:** the mini-timeline alone (Seizure Detection Score + Detections), spanning
  edge to edge — not sharing its row with the Event Panel.
- **Row 2, two columns, starting below the mini-timeline:** left column (wider) = the EEG Panel
  (toolbar + canvas + scrub bar), right column (narrower) = the Event Panel, matching the EEG Panel
  column's full height.

Before touching any code, look directly at `UI/B2a*.png` and describe in your report what grid/flex
structure it implies (which elements share a row, which don't). Then inspect the current DOM/CSS in
`AnalysisScreen.jsx` (or wherever the page layout is composed) and identify the actual wrapping element
that groups mini-timeline with Event Panel instead of grouping EEG Panel with Event Panel. Fix the
grouping itself — this is a structural change (which elements are siblings in which container), not a
height/width tweak on the existing structure, since previous rounds' height-only fixes are exactly what
left this still broken.

**Verification this time must be a literal side-by-side comparison**, not a description: take a
screenshot of the full Analysis screen and place it directly next to the relevant `UI/B2a` (or closest
matching) mockup crop in the report, so the row-grouping can be checked by eye against the source of
truth, not inferred from prose.

## Report

Write to `web_demo/CC_STEP5_FIX6_REPORT.md`, with the mockup-vs-live screenshot comparison for item 3.
Run `pytest web_demo/backend/tests/test_guards.py -v` and `git status` again at the end, raw output
included.

## Stop condition

Stop once all three items are done/verified with evidence and the report is written. Do not start
Step 6 (the SPEC's Select Range step — confusingly numbered the same as this build phase; it means the
next item in `DEMO_BUILD_HANDOFF.md §6`'s table, not this fix round).