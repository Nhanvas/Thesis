# CC_STEP4_REPORT.md — Step 4: Analysis screen — Panel EEG + toolbar + scrub

Status: **done**, per the stop condition in `CC_STEP4_PROMPT.md`. Step 5 (mini-timeline + Panel
Event + 3-panel sync) not started.

---

## 0 · Prerequisite check

`pytest web_demo/backend/tests/test_guards.py -v` was green before any code was touched, and
green again after every change in this step (raw output in §8). `claude-in-chrome` was used from
the first browser interaction, not after a bug appeared — every visual bug in §7 below was in fact
found this way, not by curl.

---

## 1 · Waveform-serving endpoint design

**One endpoint:** `GET /api/files/{file_id}/waveform?start_sec&end_sec&width_px`
(`web_demo/backend/waveform_serving.py` + the route in `main.py`).

Response shape:
```json
{
  "channels": ["FP1-F7", ...18],
  "start_sec": 0.0, "end_sec": 300.0,
  "usable_duration_seconds": 3600.0,
  "n_buckets": 1205,
  "raw_uv":      [[ [min,max], ... n_buckets ], ... 18 channels],
  "filtered_uv": [[ [min,max], ... n_buckets ], ... 18 channels]
}
```

Why this shape:
- **One bucket per pixel column of canvas width** (`width_px`, measured client-side via
  `ResizeObserver` — see `EegPanel.jsx`), each holding `[min, max]` for that column's underlying
  samples. This *is* the "2-4 points/pixel min/max envelope" HANDOFF §5 asks for: min+max is 2
  points per series, and both raw+filtered together is 4. Decimation happens against the on-disk
  `.npy` cache via `np.memmap` — only the requested `[start_sec, end_sec)` slice is ever pulled off
  disk into RAM (`waveform_serving._load_window`), so a multi-hour file's full array is never
  materialized for one window request.
- **Raw and filtered always returned together, every call.** This is what makes a filter-toggle
  click free: the frontend already has both series for the current window the moment it's fetched,
  so toggling `lff`/`hff`/`60` is a pure re-render (`EegPanel`'s canvas effect), confirmed by network
  log to fire zero requests (§4).
- **Amplitude is never a query param.** The `⇕ [X] uV` control only rescales the same fetched data
  client-side — also confirmed firing zero requests.
- Values are in **µV** (`x 1e6` from the cache's native Volts) so they line up directly with the
  toolbar's amplitude unit.

**Endpoint count:** one, not several — a second endpoint for "just raw" or "just filtered" would
only ever be used together in practice (per HANDOFF §5's own requirement), so splitting them would
just double round trips for no benefit.

---

## 2 · Phase A cache — what already existed vs what I added

Already cached per file since Step 3 (`pipeline_demo.process_file_phase_a`, `{stem}.filtered.npy`):
the whole recording, bandpass(0.5-60Hz)+notch(60Hz) filtered once, reshaped into
`[n_windows, 18, WIN_SAMPLES]` float32, in Volts. **No raw (unfiltered) continuous array was
persisted anywhere** — Phase A only ever kept the filtered version.

Added this step: `process_file_phase_a` now also reshapes and caches the **unfiltered** `data`
array it already reads (before filtering) into `{stem}.raw.npy`, same layout. This reuses data
already in memory during Phase A — no second EDF read, no second pass. `PhaseAResult` gained a
`raw_path` field alongside the existing `filtered_path`.

**Backfill:** the 5 subjects already in the DB from Step 3 (`chb06`, `chb13`, `chb14`, `chb15`,
`chb16`) only had `.filtered.npy` cached. I ran `pipeline_demo.process_file_phase_a(edf_path,
cache_dir=...)` once per existing `.edf` file already sitting in `uploads/{subject}/` to backfill
`.raw.npy` for all 24 files (this also re-wrote `.filtered.npy`, byte-for-byte deterministic
recompute — not a data change). This is a one-off migration, not new demo logic; it wrote only
inside `web_demo/backend/uploads/` (gitignored, confirmed via `git check-ignore`).

No new parallel filtering pipeline was built — the raw/filtered dual-view uses exactly the two
arrays above, both produced by the one real `preprocessing._BP_SOS` / `_NOTCH_B`/`_NOTCH_A`
filter path.

---

## 3 · `⏮⏭ Select Range` — inert, not omitted

Rendered in its correct toolbar position (between the amplitude control and the filter toggles,
matching `UI/B1a`), but with `disabled` set and no click handler — visually greyed out
(`opacity-40 cursor-not-allowed`), with a `title` tooltip saying it's Step 6 scope. I chose inert-
and-visible over omitting it so the toolbar's spacing/layout doesn't shift again when Step 6 wires
it up.

---

## 4 · Verification results (all 9, per the prompt's checklist)

1. **Open a real subject via "Open" → real Analysis screen.** Done for `chb13` (both files) and
   `chb16` (2 of 12 files spot-checked). Header, dropdown, and waveform all loaded for the correct
   subject/file — no stub message.
2. **Waveform renders real EEG shape, pans on scrub.** Confirmed two ways: (a) a zero-alert file
   (`chb13_02`, `chb15_02_short`) visibly renders a calmer/sparser trace than an alert-bearing file
   (`chb13_03`) at the same amplitude scale — real signal, not placeholder noise; (b) clicking the
   scrub bar's `›` (page-forward) on a 1-hour file with a 5-min window fired
   `GET .../waveform?start_sec=300&end_sec=600...` and the canvas + time axis (`17:43:20-17:48:20`
   → `17:48:20-17:53:20`) both updated correctly.
3. **Window-length change re-renders at a new zoom.** Tested `2 hr → 1 min → 5 min` on `chb13_03`;
   each selection fired a new `waveform` request at the corrected `end_sec` and the canvas density
   changed accordingly (network log captured in-session).
4. **Amplitude change rescales instantly, zero network request.** Cleared the network log
   immediately before selecting `30 uV` from the dropdown; `read_network_requests` afterward
   returned zero `/api/` calls. Canvas rescaled instantly.
5. **Filter toggle — visual difference, one combined call.** Toggling all three (`lff`/`hff`/`60`)
   off switched the canvas from the dark, 100%-opacity "filtered" trace (`#0F172A`) to the lighter,
   100%-opacity "raw" trace (`#64748B`) — confirmed by reading the actual canvas pixel color via
   `getImageData`, not just eyeballing. Zero network requests fired for the toggle (cleared+checked
   the log the same way as #4) — both series were already in the one waveform response.
6. **Previous/Next switches file correctly.** `chb13_03 → chb13_02` (Previous) and
   `chb15_01_short → chb15_02_short` within `chb16` (Next): header title, alert count, file
   dropdown selection, and waveform data all updated to the new file each time.
7. **Viewed button updates status, Database screen reflects it.** Clicked Viewed on both
   `chb13_02` and `chb13_03`; Database screen afterward showed `chb13_02.edf` → Viewed,
   `chb13_03.edf` → Viewed, subject row → `Viewed` (green check), Progress `02/2`. Also confirmed
   the **View → Viewing** auto-transition (see §6) by opening `chb16`'s first two files and seeing
   `chb16` go from `View` to `Viewing (0/12)` on the Database screen without clicking Viewed.
8. **Pixel-compare against `UI/B1a`/`B1b`/`B1d`.** See §5 below for the itemized comparison —
   close match on everything in scope; the two deliberate structural differences (no mini-timeline,
   no right-column Panel Event/Attribution) are Step 5+ scope per the prompt, not oversights.
9. **`pytest .../test_guards.py -v` and `git status`.** See §8 — 4 passed, and `git status` shows
   only the files this step actually touched.

---

## 5 · Pixel-compare notes vs `UI/B1a` / `B1b` / `B1d`

Matches: header layout (title+alerts, Previous/Next, divider, Viewed, Export, file dropdown, all
in the same navy bar), Progress bar row directly below the header, "Seizure detection" section
title, toolbar control order (`⊲▷ hr` → `⇕ uV` → `Select Range` → filters right-aligned), 18
channel labels down the left, cream (`#FEFBEF`) canvas background, bottom scrub bar with
`«‹ [slider] ›» ▷ [speed]`, empty "Event Time" strip at the bottom of the panel.

Deliberate differences:
- **No mini-timeline, no right-column Panel Event/Channel Attribution.** Both are explicitly
  Step 5+ scope. Rather than reserve blank space for them, Panel EEG takes the full content width
  this step — reserving the layout felt more likely to be mistaken for "built but broken" than
  simply not being there yet.
- **Duration popover is a plain scrollable list**, not the mockup's vertical slider-with-eye-icon
  widget. Same value set, same current-selection highlighting, functionally identical; the slider
  chrome itself wasn't worth building for Step 4's scope. Flagging in case Boti wants the literal
  widget later.
- **A "back to Database" click on the logo** was added — nothing in `UI/` or the SPEC shows how to
  leave the Analysis screen (no back button in any B1 mockup). This is a pragmatic addition, not a
  spec'd control; happy to replace it with something else if there's an intended affordance I
  missed.

---

## 6 · A behavior I inferred, not just implemented literally: View → Viewing

SPEC §5.2 defines three file statuses (`View`/`Viewing`/`Viewed`) but nothing before Step 4 could
ever produce `Viewing` — `Open` was a stub. Since Step 4 is the first place a file is actually
*opened*, I added: opening a file's Analysis screen calls `POST /api/files/{id}/viewing`, which
flips `View → Viewing` (never touches an already-`Viewed` file). This isn't explicitly asked for in
the prompt's in-scope list, but without it `Viewing` would stay permanently unreachable, which
seemed like a bigger gap than adding the one obvious trigger for it. Flagging this inference
explicitly rather than silently assuming it's what was wanted.

---

## 7 · Bugs found by live browser testing (not curl) and fixed

1. **Waveform rendered as a solid black block, not a readable trace.** Root cause: I was clamping
   each channel's min/max line strictly inside its own 38px row. Real scalp EEG amplitude (~80-300
   µV, confirmed even on a zero-alert file — see `waveform_serving` sample values in-session) vastly
   exceeds the SPEC's own default `7 uV` scale, so at that sensitivity nearly every column's line
   spanned the full row and clamping turned that into a solid fill. Fixed by removing the per-band
   clamp entirely — lines now overflow into neighboring channel rows exactly like real clinical EEG
   viewers do at high sensitivity (a known, accepted look, not a bug to hide). **Flagging for
   Boti:** the SPEC's own prescribed default (`7 uV`) makes the demo look genuinely busy/dense at
   this row height on real signal — worth a look before the defense; I did not unilaterally change
   the default since it's explicitly spec'd.
2. **`markFileViewed`/`markFileViewing` responses crashed `EegPanel`** (`Cannot read properties of
   undefined (reading 'map')`) — those two endpoints returned `db.get_file()`'s bare dict, which
   lacks the `channels`/`usable_duration_seconds` fields that only the plain `GET /api/files/{id}`
   handler was adding on top. Fixed by factoring a shared `_file_detail()` helper in `main.py` used
   by all three endpoints, so every file-returning response has the same shape.
3. **Status badge showed "Viewing Viewing"** for a file-level `Viewing` status. Pre-existing bug in
   `DatabaseScreen.jsx`'s `StatusBadge` from Step 3 (`status.replace('Viewing ', '')` is a no-op
   when there's no trailing `(x/N)` fraction, so it echoed the whole string back into itself) —
   never visible before because no file had ever reached `Viewing` status until this step's Open
   flow existed. Fixed by only rendering the fraction span when one is actually present.

---

## 7b · Lint (non-blocking)

`npm run lint` (oxlint) reports 5 warnings in `AnalysisScreen.jsx`, zero errors: two
`set-state-in-effect` (the file-change reset effect and the window-clamp-then-refetch effect — both
intentional, not accidental cascades) and three `ref-in-cleanup` on `playRef` (a plain
`{raf, lastTs}` data container we own, not a DOM node ref — the rule's usual concern doesn't apply
here). Left as-is; all covered behavior was verified working live in the browser regardless.

---

## 8 · Guard test + git status (raw output)

```
$ pytest web_demo/backend/tests/test_guards.py -v
============================= test session starts =============================
collected 4 items

web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED [ 25%]
web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED [ 50%]
web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED  [ 75%]
web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED [100%]

============================== 4 passed in 2.03s ==============================
```

```
$ git status
On branch main
Your branch is ahead of 'origin/main' by 12 commits.

Changes not staged for commit:
	modified:   web_demo/backend/db.py
	modified:   web_demo/backend/main.py
	modified:   web_demo/backend/pipeline_demo.py
	modified:   web_demo/frontend/src/App.jsx
	modified:   web_demo/frontend/src/api.js
	modified:   web_demo/frontend/src/components/Header.jsx
	modified:   web_demo/frontend/src/components/icons.jsx
	modified:   web_demo/frontend/src/screens/DatabaseScreen.jsx

Untracked files:
	web_demo/backend/waveform_serving.py
	web_demo/frontend/src/components/EegPanel.jsx
	web_demo/frontend/src/screens/AnalysisScreen.jsx
	web_demo/frontend/src/time.js
```

Nothing under `UI/`, `docs/`, `data/models_retrain/`, `data/processed/`, or `results/` touched.
`web_demo/backend/szscan.db` and `web_demo/backend/uploads/` (where the `.raw.npy` backfill landed)
are both gitignored, confirmed via `git check-ignore`.

Note: this step left real test state behind on purpose (same precedent as Step 3's `chb13` "A2
concurrency test" memo) — `chb13` is now fully `Viewed`, `chb16`'s first two files are `Viewing`.
Reset them yourself if you'd rather start Step 5 from a clean slate.

---

## 9 · How to run it

Backend (from `web_demo/backend/`):
```
python -m uvicorn main:app --port 8000 --reload
```
Frontend (from `web_demo/frontend/`):
```
npm run dev
```
Then open `http://localhost:5173/`, log in with the admin credentials in `web_demo/backend/.env`,
and click a subject's row (or a specific file row) → **Open**.

---

## 10 · Stop condition

Per `CC_STEP4_PROMPT.md`: Panel EEG renders real, correctly-decimated waveform data; the toolbar
controls (window length, amplitude, filters, Select Range placeholder) all function as specified;
file navigation and Viewed-marking work; this report is written. **Step 5 has not been started.**
