# CC_STEP4_PROMPT.md — Step 4: Analysis screen — Panel EEG + toolbar + scrub (no events yet)

**Prerequisite:** Step 3 is fully closed (6 fix rounds, see `web_demo/BUILD_PROGRESS.md §6` — read it,
especially the "Six fix rounds" table and the pattern that every real bug this build has hit so far was
found by live browser interaction, never by curl or automated checks alone). Confirm
`pytest web_demo/backend/tests/test_guards.py -v` is green before doing anything else.

Five real subjects already exist in the DB from Step 3 testing — **reuse them, don't re-upload**:
`chb06` (1 file), `chb13` (2 files), `chb15` (2 files), `chb14` (6 files), `chb16` (12 files). The last
three are short-duration EDFs built from real `chb15` headers/data (a handful of minutes each) — good
for fast iteration; use `chb06` or `chb13` for anything where a more realistic single-hour-scale
recording matters.

Read in this order before writing any code:
1. `web_demo/SZSCAN_SPEC_v5.md` §6.1 (header), §6.2 (time format rule), §6.4 (Panel EEG + toolbar) —
   in full. §6.3 (mini-timeline) and §6.5 (Panel Event) are **out of scope this step** — read them only
   enough to know what NOT to build yet, don't implement them.
2. `web_demo/DEMO_BUILD_HANDOFF.md §5` — the waveform-serving performance constraints. This is the part
   of the step most likely to go wrong if skimmed: 18 channels × 256 Hz × 1 hour ≈ 16.6 million points
   per file. That must never be sent to the browser undecimated.
3. `web_demo/SZSCAN_DESIGN_v2.md §3` (EEG waveform colors/opacity) and `§9`'s existing CSS tokens.
4. View the actual mockups (copy to scratch first, never open `web_demo/UI/` directly): `UI/B1a*.png`
   (Panel EEG + toolbar, full layout), `UI/B1b*.png` (the `⊲▷ [X] hr` window-length popover),
   `UI/B1d*.png` (whichever state that filename covers — check both variants if there's more than one).

## Scope boundary

**In scope:**
- Wiring the Database screen's "Open" button to actually navigate to a new Analysis screen for the
  selected subject/file (currently a stub per Step 3's documented decision).
- The Analysis screen's header (SPEC §6.1): `<ID> (<N> alerts to check)` using the file's existing
  `Alert` count already computed and stored from Step 3 — this is just reading existing data, not new
  logic. Previous/Next (switches **file**, not event, within the same subject). A "Viewed" button that
  sets the current file's status per SPEC §5.2 (this doesn't depend on events existing). Export button
  rendered but disabled (SPEC's own condition — "only enable once every file is Viewed" — already holds
  vacuously true or false depending on state, no new logic needed to make this correct). A dropdown to
  pick which file to view, listing every file with its alert count in parentheses. Progress `x/N`.
- Panel EEG itself: the waveform canvas, fixed to the 18 standard channels (reuse
  `preprocessing.py`'s channel-picking/dedup logic — don't reinvent it), rendering the currently-uploaded
  file's real EEG data for whatever time window is in view.
- The toolbar (SPEC §6.4): `⊲▷ [X] hr` window-length control with its popover, `⇕ [X] uV` amplitude
  dropdown (5/7/10/15/20/30 µV, pure frontend, no backend call), the three filter toggles
  (`lff 0.5 Hz` / `hff 60 Hz` / `60`), and the bottom scrub bar with play speed `1x/2x/4x/8x` (default
  1x). The `⏮⏭ Select Range` button can render in its correct toolbar position but does not need to be
  functional yet (Step 6 scope) — say plainly in your report whether you left it inert or omitted it,
  don't guess silently.
- Playhead: clickable only on Panel EEG (no mini-timeline exists yet to sync with — that's fine, it's
  Step 5's job to add that sync).
- The empty "Event Time" row at the bottom of Panel EEG can render as an empty strip (no blocks yet,
  since no events UI exists this step) — don't build event-block rendering logic yet, just leave the
  space so Step 5/6 has somewhere to add it without a layout change.

**Out of scope, still:** mini-timeline (top panel with the Seizure Detection Score line + Detections
row), Panel Event (the review list on the right), Channel Attribution panel, Select Range's actual
event-creation behavior, Export's actual file generation. All later steps.

## The core technical problem — waveform serving

**Do not send raw or lightly-sampled EEG arrays to the browser.** Per HANDOFF §5:
- The backend must serve waveform data **for the currently-viewed time window only**, decimated to
  roughly 2–4 points per pixel of canvas width, using a **min/max envelope** per decimated bucket (for
  each pixel-column's underlying sample range, keep both the min and the max value) — not naive
  subsampling, which would flatten out real spikes that clinicians specifically need to see.
- Changing the toolbar's window-length control (`⊲▷ [X] hr`) must trigger a new backend call at a
  different decimation level appropriate to the new window size and pixel width.
- Changing the amplitude control (`⇕ [X] uV`) is **pure frontend rescaling** — no backend call.
- Toggling a filter must have the backend return **both** the raw and filtered series together in one
  call (not two round-trips) — the frontend overlays them per SPEC §6.4's "when filter is on, the
  filtered wave is prominent, raw recedes as a faint background — raw is never fully hidden."

**Before writing new filtering code, check what Phase A already produced.** Step 3's build already
bandpass+notch-filters the entire continuous recording once per file (this is exactly the same
filtering the pipeline needs, and it's supposed to be identical to what a clinician sees — SPEC §6.4:
"3 filter khớp đúng bước preprocessing thật"). Check whether Phase A's existing cache
(`.filtered.npy` or similar — check `pipeline_demo.py`/`upload_manager.py` for what's actually
persisted per file) already contains this continuous filtered array, and whether the **raw, unfiltered**
continuous array is also cached anywhere. Reuse whichever of these already exist rather than
re-deriving them; if the raw (unfiltered) continuous array isn't currently persisted anywhere and you
need it for the raw/filtered dual-view, extend the existing Phase A cache to also store it — don't
build a second, parallel filtering pipeline that could drift from the pipeline's real filter
parameters. Filter coefficients themselves must come from `preprocessing.py`'s actual constants
(`_BP_SOS`, `_NOTCH_B`/`_NOTCH_A`) or equivalent — never hand-typed magic numbers, per `CLAUDE.md`'s
standing rule.

Design the actual endpoint shape (one endpoint vs several, exact JSON layout) yourself — the
requirements above are non-negotiable, the wire format is your call. State your design and why in the
report.

## General standing rules (apply as always)

- No fake data, no algorithm not present in the real pipeline (SPEC §0).
- Never hardcode a filter/threshold value from memory — read from the source file.
- If something in this prompt conflicts with a mockup or the SPEC once you're actually looking at the
  code, stop and say so rather than silently picking an interpretation.
- Use `claude-in-chrome` from the start of this step, not reactively after a bug is found — every one of
  Step 3's 6 rounds was found by live interaction, not curl.

## Verification required before writing your report

1. Open a real subject (e.g. `chb13`, 2 files) from the Database via "Open" — confirm it navigates to a
   real Analysis screen (not the old stub message) with the correct subject/file loaded.
2. Confirm the waveform actually renders — real EEG shape, not a flat line or placeholder — and pans
   correctly if you scrub/seek within the file.
3. Change the window-length control and confirm the view actually re-renders at a sensible new zoom
   level (not just a UI popover that doesn't do anything).
4. Change the amplitude control and confirm the waveform rescales instantly with **no** network request
   fired (check this directly, don't assume).
5. Toggle a filter and confirm the visual difference (filtered prominent, raw faint background, per
   SPEC §6.4) — and confirm this cost the backend one combined call, not two.
6. Switch between Previous/Next files within the subject and confirm the header/dropdown/waveform all
   update to the newly-selected file correctly.
7. Click "Viewed" and confirm the file's status actually updates (check the Database screen afterward
   too, since Step 3 already wired Status display there).
8. Pixel-compare the built screen against `UI/B1a`/`B1b`/`B1d` directly.
9. `pytest web_demo/backend/tests/test_guards.py -v` and `git status` — paste raw output. This step
   touches real EDF file reads for the first time outside the Step 1/3 pipeline path, so actually think
   about whether anything here risks the guards rather than assuming it's a trivial pass.

**Write your report to `web_demo/CC_STEP4_REPORT.md`.** Cover: the waveform-serving endpoint design and
why, what you found already cached from Phase A vs what you added, the `⏮⏭ Select Range` inert-vs-omitted
call, and all nine verification results above. Give Boti the exact start commands for backend + frontend.

## Stop condition

Do not start Step 5 (mini-timeline + Panel Event + 3-panel sync). Stop once Panel EEG renders real,
correctly-decimated waveform data for a real uploaded subject, the toolbar controls all function as
specified, file navigation and Viewed-marking work, and the report file above is written.
