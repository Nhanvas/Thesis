# BUILD_PROGRESS.md — SzScan web demo build tracker

Written by Project #2 (the build-guide Claude project) at the end of each step's work session.
**Read this file first when opening a new chat to continue the build** — it replaces having to
re-read the whole prior conversation. Update it at the end of every future step.

Authority: this file is informational only, it does not override anything in
`DEMO_BUILD_HANDOFF.md`, `CLAUDE.md`, `SZSCAN_SPEC_v5.md`, or `SZSCAN_DESIGN_v2.md` — those are
still the real spec. This is just "what happened and what exists," for continuity.

---

## 1 · Status

| Step (HANDOFF §6) | Status | Notes |
|---|---|---|
| 0 — repo scaffold, Tailwind tokens, `test_guards.py` PASS | **DONE** | see §3 below |
| 1 — `pipeline_demo.py` (`process_file`) + CLI, real timing | **DONE** | see §4 below |
| 2 — Log in + empty Database + footer | **DONE** | took 4 fix rounds past the initial build — see §5 below |
| 3 — Create new → upload → Process → subject appears in table | **DONE** | took **6** fix rounds past the initial build — see §6 below |
| 4 — Analysis screen: Panel EEG + toolbar + scrub, no events yet | **DONE** | see §7 below — **this file's own "update every step" convention was skipped for Step 4 at the time**; §7 is a brief retroactive note, not a full account. `CC_STEP4_REPORT.md`/`CC_STEP4_FIX_REPORT.md` in the repo have the real detail if it's ever needed |
| 5 — Mini-timeline + Event Panel + 3-panel sync | **DONE** | took **7** fix rounds past the initial build, the most of any step so far — see §8 below, **read it before starting Step 6** |
| 6 — Select Range: manual event creation | **DONE** | initial build + **2** UI fix rounds (all visual, requested by Boti after live use) — see §9 below |
| 7 — Channel Attribution Panel | **PROMPT READY** | `CC_STEP7_PROMPT.md` drafted at the end of the Step 6 chat — see §1 "Where to resume" |
| 8-9 | not started | |

**Where to resume:** Step 7 (Channel Attribution Panel) — **the prompt is already written:
`web_demo/CC_STEP7_PROMPT.md`.** Boti runs it in Claude Code with the trigger line, then brings
`CC_STEP7_REPORT.md` (+ raw `pytest` / `git status` output) to a NEW chat for review. Nothing needs to be
decided or asked before running it. The prompt bundles, in order:

- **Pre-step A** — provenance dump of the `chb13` events table (which events are CPD/`AI`, which are
  hand-drawn/`Human`), then deletion of the 5 Human test events (Boti's decision, 2026-09-24).
- **Pre-step B** — one authorized, irreversible Accept on an Unseen AI event of a *synthetic* test file, to
  finally see the Accept fill (`#16A34A`) live (§9.3 open item).
- **Step 7 proper** — Part 1 per-window per-channel reconstruction scores (new backend work: the cache
  holds only the ensemble score; new `{stem}.pernode.npy`, backfill for existing files, consistency gate
  before any UI), Part 2 attribution definition + endpoints + persisted per-channel Accept/Reject,
  Part 3 the panel (`UI/B2a`), Part 4 live verification, Part 5 SPEC note C20.

SPEC note **C19** (the three Step 6 gap-fill decisions, §9.2, plus the kept header title) was **recorded in
`SZSCAN_SPEC_v5.md` during the Step 6 chat** (2026-09-24, approved by Boti) and is no longer part of the
prompt.

Two things the prompt deliberately leaves as **PROVISIONAL DEFAULTS for Boti to confirm in the review
chat** (only if `docs/ATTRIBUTION_SPEC.md §9` / thesis code does not define them): aggregation across an
event's windows = per-channel mean; score shown = the aggregated raw per-node reconstruction score.

**Deliberately deferred — not needed for Step 7, do not raise them before it:** the filter-stage decision
(§12), a real ~4 h `chb06` upload, and removing the synthetic test subjects. All three belong to Step 9
(cache build for the 8 subjects) / pre-defense cleanup.

**Test-data state left in the DB (end of Step 6):** `chb13` (2 real files, `chb13_02.edf` /
`chb13_03.edf`, each exactly 1 hour) and short synthetic test files under `chb14`/`chb15`/`chb16` built
from real `chb15` clips in Step 3. `chb13_03.edf` holds 4 real AI events (from the CPD run, ids 46–49,
review states Reject/Reject/Uncertain/Reject) plus 3 manually drawn Human events; `chb13_02.edf` has no AI
events and 2 Human events — full list in §9.5. **Step 7's Pre-step A deletes those 5 Human events**, so
after Step 7 the `chb13` Alert should read 1. **Correction to this file's Step 3 entry (still valid):**
`chb06_01.edf` has a real `.npy` cache (~4 h) but **zero rows** in the `subjects`/`files` tables — it was
never uploaded through the real Create-New flow and does not appear in the running app. **Correction to
§8.6:** the AI events' review states on `chb13_03.edf` were already Reject/Reject/Uncertain/Reject at Step 6
pre-flight, not Accept/Reject/Uncertain/Unseen — see §9.5.

**Trigger line for Claude Code (English):**
`Read web_demo/CC_STEP7_PROMPT.md in full and execute it exactly as written, in the order given. Use
claude-in-chrome for all live verification from the start; if it is not connected, stop and tell me. Do
not run any git add/commit/push. Write the report to web_demo/CC_STEP7_REPORT.md, then stop. Do not
start Step 8.`

---

## 2 · Repo map — what exists under `web_demo/` right now

```
web_demo/
├── CLAUDE.md                    (pre-existing, already English)
├── SZSCAN_SPEC_v5.md            (translated to English in Step 5 — see §8.6; includes C18)
├── SZSCAN_DESIGN_v2.md          (translated to English in Step 5 — see §8.6)
├── DEMO_BUILD_HANDOFF.md        (translated to English in Step 5 — see §8.6)
├── THESIS_CONTEXT_FOR_DEMO.md   (pre-existing, already English, untouched)
├── PROJECT2_SETUP.md            (pre-existing, shared with Project #1, still Vietnamese — out of
│                                  scope for the Step 5 translation pass)
├── UI/                          (pre-existing, locked PNGs + Logo.png — still clean, never modified)
├── BUILD_PROGRESS.md            this file
├── spec_docs_diff.md            `git diff` output from the Step 5 English-translation replacement
│                                  (informational, can be deleted once reviewed)
├── CC_STEP0_PROMPT.md … CC_STEP3_FIX6_PROMPT.md/_REPORT.md   (Steps 0–3, see §3–§6)
├── CC_STEP4_PROMPT.md, CC_STEP4_REPORT.md, CC_STEP4_FIX_PROMPT.md, CC_STEP4_FIX_REPORT.md
│                                  Step 4 — see §7 (not retroactively expanded in this file)
├── CC_STEP5_PROMPT.md           Step 5 initial build prompt
├── CC_STEP5_REPORT.md           Step 5 initial build report (resumed pass, notranslate fix)
├── CC_STEP5_FIX_PROMPT.md / _FIX_REPORT.md            fix round 1
├── CC_STEP5_FIX2_PROMPT.md / _FIX2_REPORT.md          fix round 2
├── CC_STEP5_FIX3_PROMPT.md / _FIX3_REPORT.md          fix round 3 (+ _SCREENSHOTS/)
├── CC_STEP5_FIX4_PROMPT.md / _FIX4_REPORT.md          fix round 4 (+ _SCREENSHOTS/)
├── CC_STEP5_FIX5_PROMPT.md / _FIX5_REPORT.md          fix round 5 (+ _SCREENSHOTS/)
├── CC_STEP5_FIX6_PROMPT.md / _FIX6_REPORT.md          fix round 6 (+ _SCREENSHOTS/)
├── CC_STEP5_FIX7_PROMPT.md / _FIX7_REPORT.md          fix round 7 (+ _SCREENSHOTS/)
├── CC_STEP6_PROMPT.md / _REPORT.md                    Step 6 initial build (+ CC_STEP6_SCREENSHOTS/)
├── CC_STEP6_FIX_PROMPT.md / _FIX_REPORT.md            Step 6 fix round 1 (+ _SCREENSHOTS/)
├── CC_STEP6_FIX2_PROMPT.md / _FIX2_REPORT.md          Step 6 fix round 2 (+ _SCREENSHOTS/)
├── backend/
│   ├── .env                     real dev credentials, gitignored (see §5.1)
│   ├── .env.example
│   ├── main.py                  FastAPI app — auth + /api/subjects + upload/process + waveform
│   │                             endpoints. `get_waveform(file_id, start_sec, end_sec, width_px,
│   │                             request)` has no filter-state parameter by design (Step 5 fix
│   │                             round 5/6 — see §8.2). Step 6: `POST /api/files/{id}/events`
│   │                             (create Human event); `PATCH /api/events/{id}` now also takes
│   │                             `onset_sec`/`offset_sec` (Human events only)
│   ├── pipeline_demo.py         process_file() (Step 1) + Phase A/B split (Step 3). Writes one
│   │                             combined `{stem}.filtered.npy` per file (bandpass+notch applied
│   │                             together at cache time) — no separable filter stages
│   ├── upload_manager.py        UploadSession, session_id-keyed draft storage, ready_to_process
│   │                             gating, start_process() w/ allowlist validation
│   ├── pipeline_worker.py       Phase B / Process run as a genuine subprocess
│   ├── waveform_serving.py      decimated-window serving for Panel EEG (raw+filtered, per
│   │                             `DEMO_BUILD_HANDOFF.md §5`); `usable_duration_seconds()` —
│   │                             floors to whole 4 s windows, drops any trailing partial window
│   ├── db.py                    SQLite schema; `_recording_label()` for "Recording N" (C17). Step 6:
│   │                             `create_event()`, `update_event_times()`; `Event N` names are
│   │                             derived at read time from onset order, never stored (§9.2)
│   ├── export_txt.py            still a stub (Step 8 scope)
│   └── tests/
│       └── test_guards.py       all 4 guards, reconfirmed PASS (4/4) after every Step 5 and Step 6
│                                  round
└── frontend/                    Vite + React + Tailwind
    ├── src/screens/LoginScreen.jsx      Step 2
    ├── src/screens/DatabaseScreen.jsx   Step 2 + Step 3
    ├── src/screens/CreateNewPanel.jsx   Step 3
    ├── src/screens/AnalysisScreen.jsx   Step 4 (EEG Panel/toolbar/scrub) + Step 5 (heaviest-edited
    │                                     file this step — playback window-advance, amplitude
    │                                     options, filter defaults, scrub-bar file-wide sync,
    │                                     mini-timeline/Event-Panel/EEG-Panel row-grouping layout —
    │                                     see §8.2–§8.5); Step 6 added the Select Range state
    │                                     machine (`selectRangeActive`/`markingOnsetSec`/
    │                                     `editingEventId`) and moved the header title next to Previous
    ├── src/components/Header.jsx        Step 2, fixed in Step 3 round 6; Step 6 fix round 1 shrank
    │                                     wordmark (`text-4xl`) and avatar (`w-14 h-14`); shared by
    │                                     Database + Analysis (Login has its own layout)
    ├── src/components/EegPanel.jsx      Step 4; touched in Step 5 for the channel-bleed clip fix
    │                                     and the raw/filtered default-opacity bug (§8.2); Step 6:
    │                                     onset marker, live preview rectangle, block label colour
    ├── src/components/MiniTimeline.jsx  Step 5 — score line + Detections row, view-only, playhead
    │                                     synced one-way from Panel EEG. `DOMAIN_SEC` hardcoded to
    │                                     3600 (known limitation, see §8.7 — no allowlisted file
    │                                     currently exceeds 1h so pan/zoom is untested)
    ├── src/components/PanelEvent.jsx    Step 5 — two-tier filter, AI/Human expand, primary sync
    │                                     source. `HumanExpand` first exercised live in Step 6
    ├── src/eventStyle.js                Step 5 — shared `blockStyle()`/dimOpacity helpers, used by
    │                                     both MiniTimeline and EegPanel's Event Time strip; Step 6
    │                                     fix round 1: solid full-opacity blocks, no hatch,
    │                                     `blockLabelColor()` (§9.3)
    ├── src/components/icons.jsx         Step 3
    ├── src/components/ConfirmDialog.jsx Step 3
    ├── src/api.js                       Step 3 + Step 5 (waveform fetch, never filter-aware — §8.2)
    ├── src/time.js                      Step 5 (time-format helpers)
    ├── src/assets/logo.png              Step 2
    ├── public/favicon.png                Step 2
    └── (design-tokens.js, tailwind.config.js, index.css — Step 6 fix round 1 added
         `--color-uncertain: #FFE262` and `--color-uncertain-text: #D97706`; otherwise unchanged
         since Step 0)
```

Outside `web_demo/`, untouched by any of this: `tables/tables_ch2.md`, `docs/VERIFIED_CORRECTIONS.md`,
`docs/EXHIBIT_SET_FINAL.md`, `docs/PROJECT_STATUS.md`, `docs/RUBRIC_TRACKING.md`,
`docs/VERIFIED_NUMBERS.md`, `src/figures/*.py`, `figures/*.png`, `rank_readout.py`,
`results/attribution_v7/*` — all confirmed by Boti directly as his own Project #1 / report-writing
work in a separate, concurrent session, unrelated to the demo build. `bme11/` (repo root) is also
Boti's own, unrelated, untouched by any web_demo work. `check_t8p8.py` also untouched.

**Git hygiene reminder (from Step 2, still holds):** commit `web_demo/` changes and `docs/`/`src/figures/`/
`figures/`/`rank_readout.py`/`results/` changes separately, never in the same `git add .`.

---

## 3 · Step 0 — detail

*(unchanged from the prior version of this file — see below)*

**Scope:** repo scaffold (`backend/`, `frontend/`, `cache/`), Tailwind tokens from
`SZSCAN_DESIGN_v2.md §9`, `test_guards.py` with the four hard guards.

**Deviations from the brief, and why (all reviewed and accepted):**
1. Tailwind v3, not v4 — v4's default config is CSS-first (`@theme`); the brief asked for tokens
   mapped into `tailwind.config.js`'s `theme.extend`, which is v3's native model.
2. `test_guards.py` excludes any directory literally named `tests` from its own scan (not just its
   own file) — necessary because the guard code has to contain the forbidden literal strings
   (`build_timeline_masked`, `Seizure Start Time`, etc.) to check for them; scanning itself would
   self-flag. Positive-test fixtures live in `pytest`'s `tmp_path`, outside the repo, so this
   exclusion never hides a real violation.
3. Guard #2 ("seizure fields") is asymmetric by design: `Seizure Start Time` / `Seizure End Time`
   are blocked with zero exceptions (no legitimate use case exists). `Number of Seizures` is
   allowed to appear as a regex anchor *only if the captured value is discarded* — checked via AST,
   looking for the captured group bound to `_` rather than a real name. This keeps the pre-existing
   `web_demo/backend/edf_order.py` (which anchors on that text but discards the value) compliant
   while still catching an actual data leak.
4. `tailwind.config.js` maps every color to `var(--color-*)` (CSS variable indirection) rather than
   hard-coding hex values a second time — token source of truth lives in exactly one place
   (`index.css`'s `:root` block).

**Integrity bug found and fixed during verification (important — don't repeat this mistake):**
Claude Code initially self-reported "all 4 guard tests PASS." **This was checked against a real,
independently-run console and found to be FALSE** — the actual run showed all 4 tests FAILING. Root
cause: three stray duplicate files were left sitting directly at `web_demo/` root, left over from
before the nested `backend/tests/` and `frontend/(src/)` folders existed. Fixed by deleting the
three stray root-level copies.

**Lesson carried forward:** always ask for the *raw* console output of `pytest ... -v`, run directly
by Boti, not a summary from Claude Code. Standing verification method for every step since — and it
paid off repeatedly in Step 3 and Step 5 (see §6, §8).

**Final verified state:** `pytest web_demo/backend/tests/test_guards.py -v` → 4 passed (raw
console, confirmed by Boti). `git status` clean.

---

## 4 · Step 1 — detail

*(unchanged — see the prior version of this file for the full account: `process_file()` only,
9.76 s/hour final measured timing on `chb06_01.edf`, guard check 4/4 passed.)*

---

## 5 · Step 2 — detail

*(unchanged — see the prior version of this file: Log in + empty Database + footer, 4 fix rounds,
the logo saga (§5.3, 3 fix rounds — "a file-existence check is not a content-correctness check"),
final verified state confirmed.)*

---

## 6 · Step 3 — detail

*(unchanged — see the prior version of this file: Create New panel, upload, two-stage Phase A/B
pipeline, minimize-to-toast, concurrency lock, Delete, Search — 6 fix rounds, all found by live
`claude-in-chrome` browser testing, none by curl. Operating point O1 demonstrated working:
`chb06`, `pen_mult=2.0` → 28.76 events/day against the 40/day balanced target.)*

---

## 7 · Step 4 — detail (brief — this file's own convention was skipped at the time)

**This section is a retroactive placeholder, not a full account.** Step 4 (Analysis screen: Panel
EEG + toolbar + scrub, no events yet, per `DEMO_BUILD_HANDOFF.md §6` row 4) was completed and
closed before Step 5 began — `CC_STEP5_PROMPT.md`'s own prerequisite line confirms
`CC_STEP4_REPORT.md` + `CC_STEP4_FIX_REPORT.md` existed and were closed, with `chb13`/`chb16` reset
to a clean `View` state at the end of the Step 4 fix round. This file was not updated at that time
to summarize what happened, breaking its own stated convention ("update it at the end of every
future step") — noted here so it isn't repeated.

**What's inferable from Step 5's own reports about what Step 4 built** (not a substitute for
reading `CC_STEP4_REPORT.md`/`CC_STEP4_FIX_REPORT.md` directly if the detail is ever needed):
18-channel canvas rendering, the `lff`/`hff`/`60` filter toggle buttons, the original 6-level
5/7/10/15/20/30 µV amplitude dropdown, the `⊲▷ [X] hr` window-length control, the bottom scrub bar
with playback speed dropdown, and drag-to-seek. Several latent defects in this code were only
caught during Step 5's live testing — a near-black/illegible canvas rendering bug (channel
cross-bleed, fixed in Step 5 fix round 1), a default state that showed already-filtered data
instead of raw (fixed in Step 5 fix round 4), and a hard-stop-at-window-boundary bug in playback
(fixed in Step 5 fix round 3) — suggesting Step 4's own closure may not have exercised every
control as thoroughly as its guard-test-green state implied. Worth keeping in mind for Step 6
onward: a green guard test and a working demo are not the same claim.

---

## 8 · Step 5 — detail

**Scope:** Mini-timeline (score line + Detections row), Event Panel (two-tier filter, AI/Human
expand, Accept/Reject/Uncertain + Save), 3-panel sync (Event Panel as primary control source, per
`SZSCAN_SPEC_v5.md §6.5`), the dimming rule. Per `DEMO_BUILD_HANDOFF.md §6` row 5 and
`SZSCAN_SPEC_v5.md §6.3`/`§6.5`. Out of scope, still: Select Range's actual event-creation behavior
(Step 6), Channel Attribution panel (Step 7), Export (Step 8).

**Took 7 fix rounds past the initial build — the most of any step so far**, and for the first time
a real product decision (the amplitude-token range) got revised mid-step based on build-time
measurement rather than being knowable in advance. `claude-in-chrome` connectivity was unreliable
for much of this step (a stale account-pairing issue after a Claude-account switch, see
`learnings.md`) — Claude Code fell back to Playwright for round 2 and reconnected successfully from
round 3 onward.

### 8.1 Initial build (resumed pass) — one real bug found

Session resumed mid-step after the Chrome extension had to be reinstalled. Found and fixed one bug
not related to the app's own logic: **Chrome's own page-translate feature crashed React** on the
Database screen (`NotFoundError` on `insertBefore`, triggered by `lang="vi"` auto-translate
rewriting live DOM text nodes out from under React's reconciler). Fixed with
`<meta name="google" content="notranslate">`. Verified the 10-item checklist from
`CC_STEP5_PROMPT.md` otherwise passed (mini-timeline rendering against real stored events, per-file
P1–P99 auto-scale, view-only + one-way playhead sync, two-tier filter + `x`/`x/y` count format,
click-to-sync across all 3 panels, Alert-count-updates-on-save, the dimming rule verified via
**computed style**, not eyeballing, wording checks). The backfill script run earlier in the step
(to fill missing per-file score arrays, Phase A+B only) was **not** written up in this pass — had
to be requested separately, see round 1.

### 8.2 Seven fix rounds

| Round | Bug / finding | Root cause / resolution |
|---|---|---|
| 1 | Backfill write-up missing; EEG canvas near-black/illegible | Backfill confirmed: never called `cpd_pipeline_v14`/PELT, wrote `{stem}.score.npy` correctly, lengths verified. Canvas: channel cross-bleed from an unclamped `drawSeries` (an amplitude spike in one channel row bled into neighboring rows); clip fix applied, verified via pixel-sampled before/after (bleed-fraction dropped from ~95%+ uniform to 1.5–31.6% per row, i.e. real per-channel variation restored). Window-length control and filter toggle were **already working** — confirmed via network payloads, just masked visually by the canvas bug. Panel Event's column height fixed to span the full EEG Panel height (`items-start` → `items-stretch`, dropped a hardcoded `maxHeight`). |
| 2 | Scrub bar didn't move Panel EEG when dragged; inline error persisted | Every pixel of a drag fired its own request, stacking against ~0.8–1.3 s/request backend latency — fixed with a 120 ms debounce (verified: 30 requests → 1). Error message left on screen forever after an invalid Save — fixed to clear on status selection/event switch. Gathered amplitude data (not yet acted on): `chb13` median 110.6 µV/peak 1820.8 µV, `chb06` median 105.9 µV/peak 1248.0 µV. Verified Alert-count "02" was arithmetically correct (2/4 events already Rejected), not a bug. Confirmed the Reject-block diagonal hatch is spec-mandated (`SZSCAN_DESIGN_v2.md §2`), not a bug — left untouched. |
| 3 | Playback froze at the window's `end_sec` and never advanced further | Root cause read directly from the existing code (an unconditional `setPlaying(false)` at the boundary). Fixed: when more file remains, shift `windowStartSec` to `end_sec` and let the existing debounced-fetch effect load the next segment; when truly at file end, stop cleanly (verified separately). Verified with 3 timestamped screenshots showing the time-axis genuinely advancing. Implemented the first amplitude-token extension (12 values, 5–500 µV) and confirmed 250 µV produces a legible, connected waveform on the same window round 2 measured — confirming the scale-mismatch diagnosis. |
| 4 | (verification) Do the low µV levels serve a purpose? Is the default view raw or already-filtered? | Even the file's **calmest** segment (found via the model's own ensemble score, not by eye) still measured ~102 µV median spread — no meaningfully calmer regime exists in this file, undercutting the low levels' original justification. **Real bug found:** all three filter toggles defaulted to `true` on page load, so the *filtered* series was drawn prominent from the very first render — confirmed via a live network response (raw ≠ filtered, both genuinely present) and a **pixel-level canvas sample** (`#0F172A` filtered-token color present at load, before any user interaction). Fixed the default to all-`false`; re-verified the base canvas samples raw's `#64748B` token at load. Progressive-filter screenshots showed `(a)` off vs. `(b)/(c)/(d)` on as visibly different, but `(b)/(c)/(d)` appeared identical to a **sparse** (1-in-97-byte) fingerprint — flagged as needing a more rigorous check, not fully trusted yet. |
| 5 | (verification) Re-check the window-length control and the filter-toggle "identical" claim properly | Window-length (`⊲▷ [X] hr`): confirmed **not** a bug — every option ≥ 1 hour collapses correctly to the same `[0, duration]` request because every currently-loaded file is ≤ 1 hour; genuinely different requests confirmed below that boundary (`30 min` ≠ `1 min` ≠ `24 hr`'s full-file clamp). Filter-toggle identity re-checked with a **full-byte** canvas diff (2,322,864/2,322,864 bytes, window pinned fixed, zero `/waveform` requests fired during the sequence) — confirmed `(a)` differs from `(b)/(c)/(d)` by 37.36% of pixels (the real raw→filtered switch), and `(b)`/`(c)`/`(d)` are **exactly** identical, 0 differing bytes — architecturally so, since the backend route (`get_waveform`) has no filter parameter at all and `pipeline_demo.py` caches exactly one combined `{stem}.filtered.npy` per file (bandpass+notch applied together, not separable). |
| 6 | Finalize + implement the amplitude list; is the ≤1h file cap genuine?; fix the mini-timeline/Event-Panel row-grouping layout bug | Amplitude: Boti decided floor = 75 µV → `AMPLITUDE_OPTIONS = [500, 250, 150, 100, 75]`, `SZSCAN_SPEC_v5.md §6.4`/C18 updated to match; `DEFAULT_AMPLITUDE_UV` also moved to 75 (flagged as a judgment call, not explicitly requested). File duration: read the **raw EDF header directly** (bypassing all caches) for `chb13_02/03.edf` (confirmed genuinely, exactly 3600.000 s each) and `chb06_01.edf` (confirmed genuinely ~14427 s / ~4 hours) — corrected round 5's framing from "every file is ≤1h" (true only for the subjects happening to be loaded) to the accurate statement. Layout: read `UI/B2a`/`B1a` first, found the actual bug — `<MiniTimeline>` was nested inside the same flex row as `<PanelEvent>`, narrowing it — moved `<MiniTimeline>` to its own full-width row above the EEG-Panel/Event-Panel pair, verified with a literal mockup-vs-live side-by-side screenshot. |
| 7 | Black vertical bar on `chb15_01_short.edf`; Play failure on the same file; scrub bar not synced to file-wide position | Black bar: read raw `.npy` directly — no NaN/zero-run, smooth (not step-discontinuous) ramps, and the **same kind of large broadband excursion (smaller magnitude) confirmed present in the genuinely real files** (`chb13_02/03.edf`, `chb06_01.edf`) — concluded genuine extreme-amplitude data (likely movement/muscle artifact, common in pediatric scalp EEG), not a bug; nothing changed. Play freeze: every reproduced freeze traced to the **automation tab being backgrounded** (`document.hidden`, zero `requestAnimationFrame` calls) — proved the underlying logic correct via a forced non-throttled scheduler; could not get a clean repro and said so plainly rather than claiming an unverified fix — **Boti's own live re-check afterward confirmed it runs fine**, closing this as environment-specific to the automation session, not a real bug. Scrub sync: real gap — the bottom scrub bar's `<input max>` was clamped to `maxStart` (the window's own reachable range) instead of `usable_duration_seconds` (the whole file), so its handle didn't reflect true file-wide position. Fixed (one line, the `max` attribute only); verified via DOM `value`/`max` at 3 positions — including one reached by clicking an Event Panel row — matching the `window_start/duration` formula exactly, not approximately. |

### 8.3 Also decided this step (not bug fixes)

- **The whole locked spec doc set moved from Vietnamese to English**, for Claude Code to parse more
  reliably (Boti's decision, 2026-09-21). `SZSCAN_SPEC_v5.md`, `SZSCAN_DESIGN_v2.md`, and
  `DEMO_BUILD_HANDOFF.md` were fully translated — content-faithful, no meaning changes.
  `CLAUDE.md`/`THESIS_CONTEXT_FOR_DEMO.md` were already English. `PROJECT2_SETUP.md` stays
  Vietnamese (out of scope). **Any future edit to these three files should be written in English.**
- **C18** (`SZSCAN_SPEC_v5.md §6.4`): the Panel EEG amplitude-token list, revised twice this step —
  first extended (round 3, 5→500 µV, 12 values) once real data showed the original 5–30 µV list was
  far below the signal's real range, then pruned (round 6, down to 5 values: `500/250/150/100/75`)
  once round 4's calm-segment measurement showed the low end never actually served its stated
  purpose. Locked-but-revisable, per the note already written into C18 itself.

### 8.4 Verified by Boti himself, live in a real browser

- Play button working correctly on `chb13_03.edf`, both mid-step and again after round 7's scrub fix.
- Scrub bar, Panel EEG, and mini-timeline confirmed in sync by his own eye after round 7.
- Play on `chb15_01_short.edf` specifically re-tested by him after round 7 and confirmed fine (this
  is what closed round 7's one open item — the freeze only reproduced inside the automation
  session's backgrounded tab, never in his own normal usage).
- The amplitude legibility judgment call itself (150 µV and below "doesn't look like EEG anymore,"
  100 µV "minimum") — his own live viewing, which is what triggered round 6's final token-list
  decision.
- The mini-timeline/Event-Panel/EEG-Panel layout, before and after round 6's fix — confirmed
  "positions are more correct now" (some minor polish still deferred, by his own choice, to a later
  pass once functionality is fully solid — not a Step 5 blocker).

### 8.5 Known limitations / carried forward, not blocking Step 6

- `MiniTimeline.jsx`'s `DOMAIN_SEC` is still hardcoded to 3600 — no currently-loaded file exceeds 1
  hour, so the pan/zoom case for a longer file (e.g. `chb06`, ~4 hours, if it's ever uploaded
  through the real flow) has never been exercised.
- The three filter buttons (`lff`/`hff`/`60`) are independently clickable but **not** independently
  wired to different data — `pipeline_demo.py` only ever caches one combined bandpass+notch series.
  Whether to invest in separately cacheable filter stages so the buttons become individually
  meaningful is an open product decision for Boti, raised in rounds 4/5, not acted on.
- `chb06` has a real, correct `.npy` cache on disk from ad hoc measurement scripts but has never
  been uploaded through the actual Create-New flow — it has no DB rows and does not appear in the
  app. If a real ~4-hour file is wanted for testing the window-length control's larger options or
  the mini-timeline's untested pan/zoom case, `chb06` would need a real upload, not just its
  existing cache.
- `HumanExpand` (the User-added event detail view in Panel Event) is implemented per spec but has
  never been exercised live — no Human event can exist until Step 6 (Select Range) is built.

### 8.6 Test-state note

`chb13_03.edf` was left, across the initial pass, with: Event 1 = Accept, Event 2 = Reject,
Event 3 = Uncertain, Event 4 = Unseen — unchanged through all 7 fix rounds (every round explicitly
confirmed no Save/Accept/Reject/Select Range action was taken during its own live verification).
`chb13`'s subject row currently reads Alert `2` (2 of 4 events Rejected as of round 5's live
testing — up from round 1's `3`). Same precedent as Step 3/4's test-state notes — reset yourself if
you'd rather start Step 6 from a clean slate.

> **Correction (2026-09-24):** Step 6's pre-flight found these four AI events already at
> Reject/Reject/Uncertain/Reject, so the Accept/Reject/Uncertain/Unseen state recorded above was stale
> by the time Step 6 started. See §9.5 for the state at the end of Step 6.

---

## 9 · Step 6 — detail

**Scope:** Select Range — manual event creation on Panel EEG (`SZSCAN_SPEC_v5.md §6.6` plus the
User-added-event bullet of §6.5). Initial build + **2 fix rounds**, all visual adjustments Boti requested
after using the running app; the initial build itself needed no behaviour fixes. Boti tested Select Range
live and confirmed it works and matches the spec (2026-09-24). Guards 4/4 green after every round;
nothing outside `web_demo/` changed. Reports: `CC_STEP6_REPORT.md`, `CC_STEP6_FIX_REPORT.md`,
`CC_STEP6_FIX2_REPORT.md`.

### 9.1 Initial build

- **Backend:** `db.create_event()` (always `source='Human'`, `review_status=NULL` — a Human event has no
  review-status axis at all), `db.update_event_times()`, `POST /api/files/{file_id}/events` (sorts the two
  points, 422 on non-positive duration), `PATCH /api/events/{id}` extended with optional
  `onset_sec`/`offset_sec` (Human events only; 422 on an AI event or on only one of the pair). `DELETE`
  already existed from Step 5.
- **Frontend:** Select Range state machine in `AnalysisScreen.jsx`; `api.js` `createEvent`; onset marker
  (reuses the violet playhead visual) and live preview rectangle (Human blue, 35 %, dashed border) in the
  Event Time row; `PanelEvent.jsx` `HumanExpand` exercised live for the first time.
- **Verified live through `claude-in-chrome`, all 16 items:** marking mode, onset marker, live preview,
  offset lock, onset/offset/duration read back and matching the clicks to sub-second precision,
  chronological insert-in-place (survived a full page reload), person icon and no review controls, blue
  mini-timeline block, Alert +1 in both the Analysis header and the Database, expand fields, Delete
  (Alert −1, block gone), Edit, cancel mid-mark, right-to-left drag, 3-panel sync for a Human event.

### 9.2 Three spec gaps the implementation filled (not written in SPEC v5)

1. **Edit** re-enters the Select Range marking mode scoped to that event: two clicks overwrite its
   onset/offset (same DB id); Delete/Edit are replaced by a hint while the redraw is in progress. This
   mirrors the AI "Reject and redraw" asymmetry of §6.5.
2. **Cancel** = click the `Select Range` toolbar button again while only the onset has been set; no
   partial event is ever written. The button label reads `Click onset…` / `Click offset…` while active.
3. **Numbering:** `Event N` is derived at read time from onset order (`onset_sec ASC, id ASC`) and never
   stored, so inserting a Human event renumbers every later event, consistently in the Event Panel, the
   Event Time row and the mini-timeline. This deliberately does not copy `UI/B3c`, whose sample data is not
   fully chronological (its Event 4 stays last) — read as un-resorted sample data, not a rule. Boti has
   used the running app but has not separately reviewed this reading.

These three (plus the kept header title, §9.4) are decisions, not just implementation detail. They are
recorded in `SZSCAN_SPEC_v5.md` as **C19** (2026-09-24), approved by Boti.

### 9.3 Fix round 1 — Boti's requests after live use

- **Header.** Button group moved next to the file dropdown; wordmark `text-5xl` → `text-4xl`, avatar
  `w-16` → `w-14`; logo mark left alone. Measured as fractions of header height against the 1440 px-wide
  mockups (wordmark 0.346 → 0.260, target 0.265; avatar 0.639 → 0.538, target 0.508). `UI/B1a`/`B2a`
  show **no avatar** (the file dropdown fills that corner); the avatar was sized from `UI/A0a`/`A0c` and
  applied to the shared `Header.jsx`, so Analysis also shows it — a flagged extrapolation that Boti
  accepted. `LoginScreen.jsx` does not use `Header.jsx`.
- **Event blocks.** `blockStyle()` in `eventStyle.js`: Accept/Reject/Uncertain opacity 0.75/0.55/0.75 →
  1, Reject hatch removed. One shared function feeds both the mini-timeline and the Event Time strip; the
  mockups show solid blocks on both. `SZSCAN_DESIGN_v2.md` principle 3 ("never colour alone") is
  explicitly relaxed for these blocks by the author's decision — status text remains on Event Panel rows.
  Dimming (0.4) and the violet selected outline were verified unchanged.
- **Uncertain colour** `#D97706` → `#FFE262` (`--color-uncertain`), with `--color-uncertain-text:
  #D97706` added for text. A real bug surfaced on the way: the white `Event N` label inside the Event
  Time strip block was invisible on yellow; fixed with `blockLabelColor()`. Measured contrast: yellow
  fill vs dark-amber text 2.47, yellow vs the cream canvas 1.24, and `--color-uncertain-bg #FFFBEB` vs
  white ≈ 1.0 (pre-existing, untouched, effectively invisible). Boti judged the new colour clear enough
  live.
- `SZSCAN_DESIGN_v2.md` §2/§9/§10 updated by Claude Code with minimal edits.
- **Not verified live:** the Accept fill colour. No Accept-status event exists in the DB and the app has
  no way back to Unseen, so Claude Code did not create one; Accept goes through the same code path as
  Reject/Uncertain (code-level confirmation only).

### 9.4 Fix round 2

- The header title `<ID> (<N> alerts to check)` moved into the right-hand cluster, directly left of
  `Previous`, matching the mockup. Boti considered removing it as redundant with the file dropdown and
  decided to **keep** it. `N` still tracks the live Alert (a disposable event: +1 on create, back on
  delete).
- Header checked at 1280 px and 1920 px: no overlap, wrap or truncation. **The dev/demo machine's screen
  is 1366×768**, so those widths were simulated by forcing the CSS box width (the header layout does not
  depend on `window.innerWidth`), not by real windows.
- `web_demo/UI/uncertain_pill_zoom.png`, a scratch file Claude Code had created inside the locked `UI/`
  folder in round 1, was moved to `CC_STEP6_FIX_SCREENSHOTS/`. Rule going forward: scratch files never go
  into `UI/`.

### 9.5 Test-state note (end of Step 6)

- `chb13_03.edf` (file id 11), in onset order: AI Reject (80 s) · **Human 1153.4–2323.7 s** (Boti's own) ·
  AI Reject (2420 s) · **Human 2561.2–2620.9 s** (Step 6 fixture, id 76) · AI Uncertain (2800 s) · AI
  Reject (3440 s) · **Human 3473.9–3571.4 s** (Boti's own) — 7 events, Alert 4. The four AI events come
  from the real CPD run; the three Human events were drawn with Select Range.
- `chb13_02.edf` (file id 10): no AI events; 2 Human events (19.4–41.8 s and 1372.3–1416.8 s), Boti's own
  — Alert 2. Subject `chb13` Alert 6.
- No Accept-status event exists anywhere in the DB; Unseen AI events exist on other test files. Every
  disposable event the three rounds created for their own regression tests was deleted.

---

## 10 · Integrity incident (from Step 1) — status: resolved, cause still unconfirmed

*(unchanged — see the prior version of this file: `UI/Annotaiton (format_ ID-summary.txt).png` was
modified during Step 1 filter-optimization work, reverted via `git checkout`, root cause never
confirmed, zero recurrence since across Steps 2, 3, 5 and 6 — the only Step 6 file-hygiene slip was a scratch
PNG left in `UI/`, §9.4.)*

---

## 11 · Report material for Project #1 (per `PROJECT2_SETUP.md §9.2(D)`)

End-to-end runtime measured = **9.76 s/hour of EEG** (Step 1, not re-measured since).

**Operating point (O1)** demonstrated working since Step 3 (`chb06`, `pen_mult=2.0` →
28.76 events/day against the 40/day balanced target).

**New from Step 5, worth noting for the report's design/methodology discussion:**
- The amplitude-token revision (C18) is itself a small case study in build-time measurement
  correcting a pre-registered UI assumption — the original 5–30 µV list was chosen before real data
  existed to check it against, and real per-channel envelope measurements (from `chb13`/`chb06`,
  converging across three independent measurement rounds: subject-level, a busy window, and the
  file's own model-identified calmest window) showed it was off by roughly an order of magnitude.
  Relevant to rubric criterion #4 (*Design considers impacts*) as a concrete example of the
  build-and-measure loop this project has used throughout.
- The raw-vs-filtered default bug (round 4) is a small but real instance of exactly the kind of
  integrity property this project cares about generally: the demo briefly, by default, showed
  processed data while implying it was showing raw data — caught and fixed before it reached any
  real review session.

**New from Step 6, worth noting for the report's design discussion:**
- The Uncertain colour change came from live use, not from the mockups: after the demo Boti saw the
  amber sink into the background and read too close to Reject red, and chose `#FFE262`. Checking it
  live also exposed a second-order defect (white label invisible on yellow) that a colour-token swap
  alone would have shipped — a small example of the build-and-verify loop.
- Dropping the Reject hatch to match the mockups is a recorded trade-off: it relaxes the "never colour
  alone" principle on the timeline blocks, decided by the author, with the text badge kept on the
  Event Panel rows.
- Event numbering is derived from onset order at read time (never stored), which keeps three views
  consistent by construction and lines up with the export's requirement that `Event N` matches the UI.

Still open: **O4b** (post-ictal flagging extent — still needs Analysis-screen-level visual review
against known seizure timing, unchanged since Step 3/4) and the **cataloged screenshot set** for
report use (Step 5's `CC_STEP5_FIX*_SCREENSHOTS/` folders now hold a substantial number of real,
captioned screenshots — worth reviewing for reuse before generating new ones for the report).

---

## 12 · Open items going into Step 7

**Handled inside `CC_STEP7_PROMPT.md` (nothing to do by hand):**

- [x→Step 7] Delete the Human test events in `chb13_02`/`chb13_03` — Pre-step A.
- [x→Step 7] Verify the Accept fill `#16A34A` live once, on a synthetic file — Pre-step B.
- [x→Step 7] Record the attribution definition actually implemented in the spec (C20) — Part 5.

**Done in the Step 6 chat:** SPEC note C19 (Step 6 gap-fill decisions + kept header title).

**Deferred on purpose (decide at Step 9 / pre-defense, not before Step 7):**

- [ ] **Filter stages.** The three toolbar buttons (`lff` / `hff` / `60`) are clickable but all gate the same
      single cached bandpass+notch series (§8.5), which sits badly with the anti-staging principle
      (`SZSCAN_SPEC_v5.md §0`: a button that reflects nothing real). The real pipeline has two operations
      (one 0.5–60 Hz bandpass, one 60 Hz notch), so "separable" `lff`/`hff` would mean applying
      high-pass / low-pass filters that are *not* in the pipeline. Options for Boti: (a) keep as is,
      (b) collapse to the two real stages, (c) separate stages with new filters. Needs a decision, not
      code, until then.
- [ ] Synthetic test subjects under `chb14`/`chb15`/`chb16` were built from `chb15` clips — they are not real
      subject data and must be removed before any demo run so no subject row shows synthetic data under a
      real subject's name.
- [ ] A real ~4 h file (`chb06`) through the real Create-New flow, if the window-length control's larger
      options and the mini-timeline's pan/zoom (`DOMAIN_SEC` hardcoded to 3600) are to be tested. Its
      cache exists but was never attached to a real subject/file record.

**Low priority / known:**

- [ ] **Keep the Claude project's uploaded copies in sync with the repo.** After Step 6 the project's copies
      of `SZSCAN_SPEC_v5.md` (still showed the 12-value amplitude list of C18 round 3), `SZSCAN_DESIGN_v2.md`
      (still showed Uncertain `#D97706`) and `BUILD_PROGRESS.md` were older than the repo's. Re-upload the
      repo versions after every step; the repo is the source of truth.

- [ ] Commit hygiene: keep splitting `web_demo/` commits from `docs/`/`tables/`/`src/figures/`/
      `figures/`/`rank_readout.py`/`results/` commits.
- [ ] `--color-uncertain-bg` (`#FFFBEB`) is visually indistinguishable from white (§9.3); the pale row
      highlight of an expanded Uncertain event barely shows. Left as-is.
- [ ] `UI/B1a`/`B2a` show no avatar while the shared `Header.jsx` renders one on Analysis (§9.3) — a
      flagged extrapolation Boti accepted.
- [ ] Step 8 (Export) will read rank/channel/score/status of each event's attribution from what Step 7
      persists (`attribution_status` table + the attribution endpoint).
