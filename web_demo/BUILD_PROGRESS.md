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
| 7 — Channel Attribution Panel | **DONE** | initial build + **2** fix rounds; round 2 changed the attribution *definition* itself, decided by Project #1 (thesis authority) — see §10 below, **read it before starting Step 8**. Committed: `cf5ee88` |
| 8 — Export `.txt` | **DONE** | initial build + **2** fix rounds (round 2: Export-button styling + a score-format false alarm traced to a stale server) — see §11 below |
| 9 — cache 8 subjects + pick live-upload subject | **IN PROGRESS** — phase 1 & 1b done; phase 2 (`chb03`/`chb06`/`chb14`/`chb15`/`chb17`/`chb18` still need a real upload+process) not started | see §15 below |

**Where to resume:** Step 9 phase 2 — upload + process the 6 remaining real subjects
(`chb03`/`chb06`/`chb14`/`chb15`/`chb17`/`chb18`) through the real Create-New→Process flow. Before
drafting that prompt: `chb16`'s upload session is sitting `done: true`, unacknowledged — someone
needs to open the app and click through the "Processing complete" panel first (one-subject-in-flight
rule), and §14 below has two open decisions (file-count-per-subject scope; the `DELETE` endpoint's
on-disk cleanup) that are Boti's call, not something to assume an answer to. Also still read §10.4
below (one open item from Step 7 not yet resolved) and `STEP8_9_PREDEFENSE_CHECKLIST.md` (uploaded
alongside this file — report needs + the fixed Tier 2 rules for Step 9, agreed with Project #1
2026-09-25). Don't assume anything on that checklist is already done just because it's listed there.

**One open item carried out of Step 7, not yet resolved:** an unexplained Human event (id 86,
`chb13_03.edf`) appeared in the DB between fix round 1 and fix round 2; neither round created it,
and Boti isn't fully certain whether he drew it himself live-testing. Verify before treating `chb13`
as a clean subject for anything Tier-2-related (§14).

---

## 2 · Repo map — what exists under `web_demo/` right now

```
web_demo/
├── CLAUDE.md                    (pre-existing, English; Step 7 round 2: "~15 s/hour" component
│                                  estimate replaced with the true end-to-end 9.76 s/hour figure,
│                                  ~5× run-to-run variance caveat kept — see §10.2)
├── SZSCAN_SPEC_v5.md            (translated to English in Step 5 — see §8.6; includes C18. Step 6
│                                  added C19. Step 7 added C20 (attribution definition) and C21
│                                  (round-2 closure note); §1.6 restructured from two lettered groups
│                                  into 3 numbered divergences — see §10.2. Step 8 fix round 1 added
│                                  C22 (§7.2's `N`-counting interpretation, locked) — see §11.2)
├── SZSCAN_DESIGN_v2.md          (translated to English in Step 5 — see §8.6)
├── DEMO_BUILD_HANDOFF.md        (translated to English in Step 5 — see §8.6)
├── THESIS_CONTEXT_FOR_DEMO.md   (pre-existing, English; Step 7 round 2: §5 "PROVISIONAL" wording
│                                  replaced — attribution evaluation is now closed, see §10.2)
├── PROJECT2_SETUP.md            (pre-existing, shared with Project #1, still Vietnamese — out of
│                                  scope for the Step 5 translation pass; §9.2(B) updated in Step 7
│                                  round 2, same PROVISIONAL correction as THESIS_CONTEXT_FOR_DEMO.md)
├── STEP8_9_PREDEFENSE_CHECKLIST.md   **new, Step 7 round 2** — report needs for Step 8/9 + the fixed
│                                  Tier 2 rules, agreed with Project #1 2026-09-25. Reference only,
│                                  not a build prompt. Read before drafting any Step 8/9 prompt
├── UI/                          (pre-existing, locked PNGs + Logo.png — still clean, never modified)
├── BUILD_PROGRESS.md            this file
├── spec_docs_diff.md            `git diff` output from the Step 5 English-translation replacement
│                                  (informational, can be deleted once reviewed)
├── CC_STEP0_PROMPT.md … CC_STEP3_FIX6_PROMPT.md/_REPORT.md   (Steps 0–3, see §3–§6)
├── CC_STEP4_PROMPT.md, CC_STEP4_REPORT.md, CC_STEP4_FIX_PROMPT.md, CC_STEP4_FIX_REPORT.md
│                                  Step 4 — see §7 (not retroactively expanded in this file)
├── CC_STEP5_PROMPT.md … CC_STEP5_FIX7_PROMPT.md/_REPORT.md (+ _SCREENSHOTS/ per round)   Step 5, §8
├── CC_STEP6_PROMPT.md / _REPORT.md                    Step 6 initial build (+ CC_STEP6_SCREENSHOTS/)
├── CC_STEP6_FIX_PROMPT.md / _FIX_REPORT.md            Step 6 fix round 1 (+ _SCREENSHOTS/)
├── CC_STEP6_FIX2_PROMPT.md / _FIX2_REPORT.md          Step 6 fix round 2 (+ _SCREENSHOTS/)
├── CC_STEP7_PROMPT.md / _REPORT.md                    **new** Step 7 initial build
│                                  (+ CC_STEP7_SCREENSHOTS/: panel_ai_event_full.jpg,
│                                  prestepB_accept_eventtime_strip.jpg, prestepB_accept_expanded_row.jpg,
│                                  sha256_before/after/final.txt)
├── CC_STEP7_FIX_PROMPT.md / _FIX_REPORT.md            **new** Step 7 fix round 1 — scrub bar +
│                                  panel layout (+ CC_STEP7_FIX_SCREENSHOTS/: live_stateA/B/C_*.jpg,
│                                  live_1440wide_event3.jpg, mockup_B2a_reference.png)
├── CC_STEP7_FIX2_PROMPT.md / _FIX2_REPORT.md          **new** Step 7 fix round 2 — attribution
│                                  formula change (+ CC_STEP7_FIX2_SCREENSHOTS/:
│                                  event46_table_2decimal.png, sha256_before/after_part1_2/final.txt)
├── CC_STEP8_PROMPT.md / _REPORT.md                    **new** Step 8 initial build — Export `.txt`
├── CC_STEP8_FIX_PROMPT.md / _FIX_REPORT.md            **new** Step 8 fix round 1 — score format,
│                                  file order, guard comment, C22
├── CC_STEP8_FIX2_PROMPT.md / _FIX2_REPORT.md          **new** Step 8 fix round 2 — Export button
│                                  styling, score-format false alarm (stale server), this file
├── backend/
│   ├── .env                     real dev credentials, gitignored (see §5.1)
│   ├── .env.example
│   ├── main.py                  FastAPI app — auth + /api/subjects + upload/process + waveform
│   │                             endpoints. `get_waveform(file_id, start_sec, end_sec, width_px,
│   │                             request)` has no filter-state parameter by design (Step 5 fix
│   │                             round 5/6 — see §8.2). Step 6: `POST /api/files/{id}/events`
│   │                             (create Human event); `PATCH /api/events/{id}` now also takes
│   │                             `onset_sec`/`offset_sec` (Human events only). Step 7: attribution
│   │                             endpoint(s) added — routes to `attribution.py`
│   ├── attribution.py           **new, Step 7.** `get_event_attribution` — loads a subject's
│   │                             persisted `pernode_baseline.npy`, computes
│   │                             `score = percentile(|robust-z|, 95, axis=0)` per channel for an
│   │                             event's windows, returns rank + score. Never recomputes the
│   │                             baseline on read. Returns `{"available": false, ...}` if the
│   │                             baseline file is missing for that subject. Formula finalized in
│   │                             fix round 2 (§10.2) — round-1 version used a PROVISIONAL mean-of-raw
│   │                             definition, now replaced
│   ├── backfill_pernode.py      **new, Step 7.** `main()` — per-node score backfill for files
│   │                             already in the DB before Step 7. Step 7 round 2 added a separate
│   │                             `backfill_baselines()` (`--baseline` flag) — computes and persists
│   │                             `pernode_baseline.npy` per subject from already-cached
│   │                             `.pernode.npy` files only; no model call, no EDF read, no CPD, no
│   │                             `events` table write
│   ├── pipeline_demo.py         process_file() (Step 1) + Phase A/B split (Step 3) + per-window
│   │                             per-channel reconstruction scoring, `.pernode.npy` (Step 7). Round 2:
│   │                             `process_subject_phase_b` also computes `pernode_baseline_out`
│   │                             (med/MAD over every window of every file of the subject, the same
│   │                             `filenames_sorted` set the existing z-score/LedoitWolf/robust-z fits
│   │                             already use) right after the per-file loop that builds `pernode_out`
│   ├── upload_manager.py        UploadSession, session_id-keyed draft storage, ready_to_process
│   │                             gating, start_process() w/ allowlist validation. Untouched by Step 7
│   │                             — the existing `_finalize_draft_dir` directory-rename mechanism
│   │                             already carries `pernode_baseline.npy` along automatically, same as
│   │                             `.pernode.npy`
│   ├── pipeline_worker.py       Phase B / Process run as a genuine subprocess. Step 7: `_run_phase_b`
│   │                             also writes `pernode_baseline.npy` in the same call that writes each
│   │                             file's `.pernode.npy`
│   ├── waveform_serving.py      decimated-window serving for Panel EEG (raw+filtered, per
│   │                             `DEMO_BUILD_HANDOFF.md §5`); `usable_duration_seconds()` —
│   │                             floors to whole 4 s windows, drops any trailing partial window
│   ├── db.py                    SQLite schema; `_recording_label()` for "Recording N" (C17). Step 6:
│   │                             `create_event()`, `update_event_times()`; `Event N` names are
│   │                             derived at read time from onset order, never stored (§9.2). Step 7:
│   │                             `attribution_status` table (per-channel Accept/Reject, keyed by
│   │                             event id + channel name), Save/Clear all queries
│   ├── export_txt.py            **Step 8.** `build_subject_export` — per-subject `.txt` report,
│                                  reuses `attribution.get_event_attribution` + `db._subject_status`
│                                  verbatim (see §11)
│   └── tests/
│       └── test_guards.py       all 4 guards, reconfirmed PASS (4/4) after every round through
│                                  Step 8 fix round 2 (last raw-console check: this round's own run)
└── frontend/                    Vite + React + Tailwind
    ├── src/screens/LoginScreen.jsx      Step 2
    ├── src/screens/DatabaseScreen.jsx   Step 2 + Step 3
    ├── src/screens/CreateNewPanel.jsx   Step 3
    ├── src/screens/AnalysisScreen.jsx   Step 4 (EEG Panel/toolbar/scrub) + Step 5 (heaviest-edited
    │                                     file that step — playback window-advance, amplitude
    │                                     options, filter defaults, scrub-bar file-wide sync,
    │                                     mini-timeline/Event-Panel/EEG-Panel row-grouping layout —
    │                                     see §8.2–§8.5); Step 6 added the Select Range state
    │                                     machine (`selectRangeActive`/`markingOnsetSec`/
    │                                     `editingEventId`) and moved the header title next to Previous;
    │                                     Step 7 fix round 1 rebuilt the right column into a stacked
    │                                     Event Panel + Attribution Panel confined to the EEG card's
    │                                     height, each scrolling internally (§10.2) — this superseded
    │                                     Step 7's own initial second-row layout, which is not to be
    │                                     repeated for any future panel; Step 8 wired the Export
    │                                     button's `onClick` to a real download and (fix round 2) made
    │                                     its enabled-state className conditional so it renders
    │                                     identically to `Previous`/`Next`/`Viewed` (§11.3)
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
    ├── src/components/AttributionPanel.jsx   **new, Step 7.** Head diagram (18 bipolar connecting
    │                                     lines, teal scale) + `Rank/Channel/Score/Status` table +
    │                                     Save/Clear all, per `UI/B2a`. Step 7 fix round 1: repositioned
    │                                     into the stacked right column, title moved between head
    │                                     diagram and table. Fix round 2: the one permitted frontend
    │                                     touch — score display `.toFixed(5)` → `.toFixed(2)` (the
    │                                     API already returns a rounded internal value; this was purely
    │                                     a display-formatting call, nothing else in the file changed)
    ├── src/attributionStyle.js          **new, Step 7.** Teal colour-scale helpers for the head
    │                                     diagram + table, mirroring `eventStyle.js`'s pattern
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
         `--color-uncertain: #FFE262` and `--color-uncertain-text: #D97706`; Step 7 added the teal
         attribution tokens already present in `SZSCAN_DESIGN_v2.md §4`/§9; otherwise unchanged
         since Step 0)
```

Outside `web_demo/`, untouched by any of this: `tables/tables_ch2.md`, `docs/VERIFIED_CORRECTIONS.md`,
`docs/EXHIBIT_SET_FINAL.md`, `docs/PROJECT_STATUS.md`, `docs/RUBRIC_TRACKING.md`,
`docs/VERIFIED_NUMBERS.md`, `src/figures/*.py`, `figures/*.png`, `rank_readout.py`,
`results/attribution_v7/*` — all confirmed by Boti directly as his own Project #1 / report-writing
work in a separate, concurrent session, unrelated to the demo build. `bme11/` (repo root) is also
Boti's own, unrelated, untouched by any web_demo work; correctly left unstaged in the Step 7 commit
(`cf5ee88`). `check_t8p8.py` also untouched. **`src/*.py`** (the single-source thesis files —
`cpd_pipeline_v14.py`, `ensemble_recipe.py`, `gae_joint.py`, `retrain_io.py`, `edf_order.py`, and the
rest of the read-only list in `CLAUDE.md`) have never been touched by any web_demo step, through
Step 7, and never should be — that's a hard rule, not a fact about what's happened so far. If a future
step ever seems to need a change in there, that's a stop-and-report-to-Project-#1 situation, not a
silent edit.

**Git hygiene reminder (from Step 2, still holds):** commit `web_demo/` changes and `docs/`/`src/figures/`/
`figures/`/`rank_readout.py`/`results/` changes separately, never in the same `git add .`. Step 7's own
commit (`cf5ee88`) followed this correctly — `git add web_demo/` only, `bme11/` left unstaged, verified
via `git status` before committing.

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
paid off repeatedly in Step 3, Step 5, and Step 7 (see §6, §8, §10).

**Final verified state:** `pytest web_demo/backend/tests/test_guards.py -v` → 4 passed (raw
console, confirmed by Boti). `git status` clean.

---

## 4 · Step 1 — detail

*(unchanged — see the prior version of this file for the full account: `process_file()` only,
9.76 s/hour final measured timing on `chb06_01.edf`, guard check 4/4 passed. This is the figure
Step 7 round 2 restored to `CLAUDE.md` in place of a stale component-level estimate — see §10.2.)*

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

*(Step 7 fix round 1 later found this exact same class of `max`-vs-reachable-range bug again, on the
same scrub bar, this time from a Step 5-round-7-introduced regression — see §10.2. The two are
related but distinct: round 7 here fixed `max` pointing at the wrong *thing entirely* (`maxStart`
instead of `usable_duration_seconds`); Step 7's bug was the same input using the *right* thing
(`usable_duration_seconds`) as `max` while its `value` could never reach it. Worth knowing both
exist if this control ever misbehaves again.)*

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
  meaningful is an open product decision for Boti, raised in rounds 4/5, not acted on. **Still open
  as of Step 7 — see §14.**
- `chb06` has a real, correct `.npy` cache on disk from ad hoc measurement scripts but has never
  been uploaded through the actual Create-New flow — it has no DB rows and does not appear in the
  app. If a real ~4-hour file is wanted for testing the window-length control's larger options or
  the mini-timeline's untested pan/zoom case, `chb06` would need a real upload, not just its
  existing cache. **Still open as of Step 7 — see §14.**
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
  Reject/Uncertain (code-level confirmation only). *(Later verified live in Step 7 Pre-step B — see
  §10.1.)*

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

> **Superseded (2026-09-25):** Step 7's Pre-step A deleted all Human events on `chb13_02.edf`/
> `chb13_03.edf` (the 5 rows above). By fix round 2 of Step 7, `chb13_03.edf` had gained one new,
> unexplained Human event (id 86) not created by any documented session — see §10.4. This
> supersedes the state above; don't rely on it for `chb13`'s current event list.

---

## 10 · Step 7 — detail

**Scope:** Channel Attribution Panel — per-window, per-channel reconstruction scores; the attribution
definition itself; endpoints; persisted per-channel Accept/Reject; the panel UI (`UI/B2a`); SPEC note
C20. Per `DEMO_BUILD_HANDOFF.md §6` row 7. Initial build + **2 fix rounds** — round 2 changed the
attribution *definition*, not just its implementation, following a methodological decision from
Project #1 (thesis authority), confirmed by Project #2. Reports: `CC_STEP7_REPORT.md`,
`CC_STEP7_FIX_REPORT.md`, `CC_STEP7_FIX2_REPORT.md`. Committed: `cf5ee88`.

### 10.1 Initial build

- **Pre-step A:** deleted the 5 Human test events left on `chb13_02.edf`/`chb13_03.edf` from Step 6
  (the provenance dump confirming which were AI/CPD vs. Human/hand-drawn ran first).
- **Pre-step B:** one authorized, irreversible Accept on an Unseen AI event of a *synthetic* test file
  — the first live confirmation of the Accept fill (`#16A34A`), an item Step 6 fix round 1 had left
  unverified (§9.3).
- **Part 1 (new backend):** per-window, per-channel reconstruction scores (`{stem}.pernode.npy`), plus
  a backfill for files already in the DB before this step.
- **Part 2:** the attribution definition — **first pass, PROVISIONAL**: arithmetic mean aggregation
  across an event's windows, the raw unscaled per-node reconstruction score shown as "Score" — plus the
  attribution endpoint and persisted per-channel Accept/Reject (`attribution_status` table,
  Save/Clear all).
- **Part 3:** the panel itself, per `UI/B2a` — head diagram with 18 bipolar connecting lines (not
  dots, since CHB-MIT is bipolar data), teal colour scale, `Rank/Channel/Score/Status` table.
- **Part 4:** live verification via `claude-in-chrome`.
- **Part 5:** SPEC note C20 recorded, items 2 (aggregation) and 3 (score shown) explicitly marked
  PROVISIONAL DEFAULTS pending Boti's confirmation.
- Guards 4/4 green.

### 10.2 Two fix rounds

**Round 1 (`CC_STEP7_FIX_PROMPT.md`/`_REPORT.md`)** — two defects Boti found testing the running app
live, plus one read-only measurement:

- **Scrub bar couldn't reach 100 %.** Root cause: since Step 5 fix round 7, the `<input>`'s `max` was
  `usable_duration_seconds` (the whole file) while its `value` (`windowStartSec`) tops out at
  `duration − windowLength` — the handle could never physically reach the track's end. Fixed to
  `max = maxStart = duration − windowLength`, input disabled when the window is ≥ the file. Verified at
  4 window lengths; handle reaches exactly 100 % at file end. *(A related-but-distinct scrub-bar bug
  was already fixed once before, in Step 5 fix round 7 — see the note at the end of §8.2. That fix
  pointed `max` at the wrong quantity entirely; this one had the right quantity but the wrong
  reachability math.)*
- **Event Panel + Attribution Panel mispositioned.** Traced to **Project #2's own Step 7 prompt**
  (Part 3), which wrongly told Claude Code to place these two panels in a second row below the EEG
  card at natural height, citing the "Analysis screen may scroll" rule — that rule is about the page,
  not these two panels, and the result contradicted `UI/B2a`. **That instruction was withdrawn.**
  Rebuilt as a stacked right column (`relative` + `absolute inset-0 flex flex-col`, each panel
  `flex-1 min-h-0 overflow-y-auto`) whose total height equals the EEG card's — matching `UI/B2a`'s
  measured ~49 %/49 % split with a small gap; each panel scrolls internally; the Attribution Panel's
  `Save | Clear all` footer is pinned outside its scroll region; the panel title was moved to sit
  between the head diagram and the table, per the mockup. Verified live at 1366×768 (the real defense
  machine) and a forced 1440-wide layout, in 3 states (no event / expanded event / another event);
  right-column bottom = EEG-card bottom within 1 px in every case.
- **Status-default check:** confirmed `attribution_status` genuinely defaults to unset — event 46's
  18 saved rows were Boti's own earlier manual test, not a bug.
- **Part C (read-only measurement, no code change):** on `chb13_03.edf`'s 4 real AI events, compared
  the current raw-score ranking against a per-file robust-z ranking. 3 of 4 events showed high rank
  correlation (Spearman ρ 0.91–0.96) between raw and per-file-z; event 46 showed the raw ranking mostly
  tracking each channel's static baseline noise level (ρ=0.76 to the channel's own baseline, ρ=0.10 to
  z) rather than event-specific anomaly. This became the evidence base Project #1 used to decide
  round 2.

**Round 2 (`CC_STEP7_FIX2_PROMPT.md`/`_REPORT.md`)** — closed both PROVISIONAL defaults, per a
methodological decision made by Project #1 (the thesis project) and confirmed by Project #2,
2026-09-25:

- **New formula:** `score = percentile(|robust-z|, 95, axis=0)` per channel across an event's windows,
  where `z = |(x − med) / mad|`, `mad` with **no** 1.4826 factor — copied exactly from
  `src/attribution_pipeline.py` lines ~514–520 (including the `np.abs()` at line 519 that the original
  Step 7 report had dropped from its own citation).
- **Baseline scope:** every window of every file belonging to the **same subject** as the event's file
  (not per-file) — the 2026-09-12 scope decision already on record. Computed once in Phase B, persisted
  as `pernode_baseline.npy` (stacked `[2, 18]` float32: row 0 = median, row 1 = MAD), namespaced by the
  subject's upload directory the same way `.pernode.npy` already is — no subject-name prefix inside the
  filename itself, since the subject id isn't known yet at the point in the pipeline where the file is
  first written. **Never recomputed on read.**
- Backfilled for all 4 subjects then in the DB (`chb13`, `chb14`, `chb15`, `chb16`) from already-cached
  `.pernode.npy` files only — no CPD, no `events` table write.
- **Display:** `|z|` (already non-negative — no sign-formatting problem), 2 decimal places. The one
  permitted frontend touch this round: a single `.toFixed(5)` → `.toFixed(2)` in
  `AttributionPanel.jsx` — the API itself already returned a rounded internal value; nothing else in
  that file changed.
- **Classification:** the SAME divergence already in `SZSCAN_SPEC_v5.md` §1.6 — **not a new one**. Only
  the baseline scope differs from the thesis formula (whole-subject recording vs. interictal-only), and
  that's exactly what the existing divergence already covers for `zrecon`/`zlatent`/`zgamma`.
- **Gate results, all passed:** independent recompute matched the live API to **6 decimals** on all 4
  events (`chb13_03.edf` ids 46–49) — not merely within the ≤0.005 display tolerance the gate required;
  sha256 of every `.filtered`/`.raw`/`.score` cache unchanged across 3 checkpoints; guards 4/4; the
  ranking **genuinely changed** from the old raw-score order (event 46: 2 of the old top-3 channels
  dropped out entirely); the 2-decimal display collisions found (2 pairs, event 46) were confirmed
  genuinely close internally, not a rounding artifact of the kind that undermined an earlier
  4-decimal choice.
- **Doc corrections bundled into the same round:** `CLAUDE.md`'s stale "~15 s/hour" component-level
  estimate replaced with the true end-to-end measured **9.76 s/hour** (`chb06_01.edf`, Step 1),
  ~5× run-to-run variance caveat kept, not dropped; `THESIS_CONTEXT_FOR_DEMO.md` §5 and
  `PROJECT2_SETUP.md` §9.2(B) changed from "PROVISIONAL" to "closed — blind human-reader labels,
  approved, result negative" (no UI wording change, still no metric on screen); `SZSCAN_SPEC_v5.md`
  §1.6 restructured from two lettered groups, (a)/(b), into **exactly three numbered divergences**,
  matching the thesis report's own enumeration — (1) normalization/covariance/robust-z fit on the
  whole recording, no artifact rejection, attribution's baseline included here; (2) no post-ictal
  buffer; (3) PELT penalty/threshold background stats estimated on the whole recording. All existing
  evidence (the chb06/chb13 AUROC/Spearman table, the post-ictal justification, the prepared committee
  answer) kept verbatim — a re-grouping, not a rewrite.

### 10.3 Decisions recorded outside `SZSCAN_SPEC_v5.md` this step

- The attribution scoring formula (p95 of `|robust-z|`, whole-subject baseline) is a **methodological**
  decision, made by Project #1, not a demo-side product choice — recorded here and in C20/C21, not
  something Project #2 originated.
- The round-1 layout defect's root cause (Project #2's own prompt wording) is recorded plainly so it
  isn't repeated: the "Analysis screen may scroll" rule from the design doc applies to the page, never
  to a panel that a locked mockup positions and sizes explicitly.

### 10.4 Open item — not yet resolved

An unexplained Human event (id 86, `chb13_03.edf`, onset≈1077.0 s / offset≈2247.3 s, non-integer
seconds — consistent with a live Select Range drag rather than a fixture) appeared in the DB
sometime between the round 1 and round 2 reports. Neither fix round created, edited, or deleted any
`chb13` event (both rounds' reports confirm this explicitly). Boti believes he likely drew it
himself while live-testing the app after round 1, but isn't fully certain. **Verify the exact DB row
(and, if the schema has one, any timestamp) before treating `chb13` as a clean subject for anything
Tier-2-related** — see `STEP8_9_PREDEFENSE_CHECKLIST.md §2` item 2 ("no test events left in the DB").

### 10.5 Committed

`git commit cf5ee88`, 2026-09-25 — *"Step 7: channel attribution panel (p95 |robust-z|, per-subject
baseline) — 2 fix rounds closed"*, 37 files changed, +2832/−54. `git add web_demo/` only; `bme11/`
correctly left unstaged; `git status` checked clean before committing, per the Git hygiene rule in §2.

---

## 11 · Step 8 — detail

**Scope:** Export `.txt` — implement `export_txt.py` (was a stub), wire `GET
/api/subjects/{id}/export`, and connect the Analysis screen's already-existing Export button to a
real browser download. Per `DEMO_BUILD_HANDOFF.md §6` row 8 / `SZSCAN_SPEC_v5.md §7`. Initial build
+ **2 fix rounds**. Reports: `CC_STEP8_REPORT.md`, `CC_STEP8_FIX_REPORT.md`,
`CC_STEP8_FIX2_REPORT.md`.

### 11.1 Initial build

- **Backend:** `export_txt.py`'s `build_subject_export` reuses Step 7's `attribution.
  get_event_attribution` verbatim and `db._subject_status`/`db.get_subject(...)["status"]` for the
  server-side enablement gate — no second implementation of either. New `GET /api/subjects/{id}/
  export` endpoint in `main.py`, 403s if the subject isn't fully `Viewed`.
- **Frontend:** only the Export button's `onClick` was rewired (from a
  `showBanner("...not implemented yet")` placeholder to a real `exportSubjectTxt(subjectId)` call in
  `AnalysisScreen.jsx`); the pre-existing `exportEnabled` boolean and the button's CSS classes were
  left untouched at this point, per the initial prompt's scope.
- **Judgment call (not spec text):** `Number of Seizures in File: N` = the count of every `Event`
  block listed below that file, AI (incl. Rejected) + Human combined — both derived from the same
  `db.list_events(file_id)` call so they can't drift apart. Flagged for confirmation; **locked as
  C22 in fix round 1** (§11.2).
- **Comment/blank-status/missing-baseline handling:** `Comment:` line omitted when empty (never
  printed blank); an unreviewed channel prints the literal `Unreviewed` label, never a blank field;
  an event with no baseline/`.pernode.npy` cache omits its whole `Channel Attribution` block
  (**never hit** in testing — all 4 subjects in the DB at the time had both cache files for every
  file); `Review Status:` printed only for `Source: AI` events, per §6.5.
- **Guard workaround (no guard code changed):** guard 2 flags any appearance of the phrase "Number
  of Seizures" as a string constant; `export_txt.py` builds that one required export label from two
  concatenated literal halves so the guard never sees the whole phrase, since a genuine write of a
  self-computed count is required by spec but indistinguishable, to the guard, from the runtime read
  of ground-truth data it exists to catch.
- **Verified live** (`claude-in-chrome`) on the real subject `chb13` (both files already `Viewed`) —
  full header/event/attribution content correctness, the `N`-vs-actual-Event-count check, the
  date-leak grep (clean), 6-decimal attribution scores not re-rounded to the UI's 2-decimal display
  value — plus, disclosed, a temporary use of the synthetic test subject `chb15` to exercise the
  disabled→enabled transition live and cover the `Unseen` AI-review-status branch (no real subject's
  data has one); `chb15` was reverted to its pre-test file statuses afterward. Guards 4/4 green.

### 11.2 Fix round 1 (`CC_STEP8_FIX_PROMPT.md`/`_FIX_REPORT.md`)

Four items, all done:

1. **Score formatting.** `_attribution_rows` now prints each channel score as a fixed
   `f"{row['score']:.6f}"` string instead of a bare rounded float, so trailing zeros are never
   dropped by Python's default float-to-str conversion (e.g. `1.27291` next to `0.050504` — an
   inconsistent digit count, not a precision difference). Print-format only; the underlying 6-decimal
   internal precision was already correct since Step 7 fix round 2.
2. **File order** — verified, not fixed: `db.list_files_by_filename`'s `ORDER BY filename` was
   already a genuine SQL sort on the file-name string, not `meas_date`/insertion order. Checked
   directly against every subject then in the DB; none currently has a file-name-vs-Recording-N
   ordering difference, so the `ORDER BY` clause itself was the only available evidence — sufficient
   on its own.
3. **Guard-2 workaround documented** with a 3-line comment above `_SEIZURE_COUNT_LABEL`, without
   spelling out the guarded phrase itself. Guards re-run afterward: still 4/4.
4. **`N`-interpretation locked in the spec** as a dated `C22` parenthetical on `SZSCAN_SPEC_v5.md
   §7.2`'s existing "In the export file:" bullet — the author-confirmed reading (AI incl. Rejected +
   Human, combined), closing the judgment call from §11.1.

Guards 4/4 green throughout.

### 11.3 Fix round 2 (`CC_STEP8_FIX2_PROMPT.md`/`_FIX2_REPORT.md`)

Two live-testing findings from Boti plus a documentation update:

1. **Export button didn't visually read as "enabled."** A real, code-level difference, not a JPEG
   artifact: the button's base classes (`bg-white/70 text-text-muted`) were identical whether enabled
   or disabled — only `disabled:opacity-50` (which only applies while the HTML `disabled` attribute
   is set) distinguished the two states, so the *enabled* button still rendered at full opacity with
   the same muted 70%-white background and grey (`#64748B`) text as its disabled state, instead of
   the solid white (`#FFFFFF`) background / near-black (`#0F172A`) text every sibling button
   (`Previous`/`Next`/`Viewed`) uses. Fixed in `AnalysisScreen.jsx`: the Export button's className is
   now conditional on `exportEnabled` — `bg-white text-text` (matching its siblings exactly) when
   enabled, the original `bg-white/70 text-text-muted opacity-50` look kept unchanged when disabled.
   Verified live via computed style (`getComputedStyle`, not eyeballing) on 2 subjects at full
   progress: `chb13_03.edf` (2/2, real data, already `Viewed`) and `chb15` (marked `Viewed`/`Viewed`
   live through 2 real Viewed-button clicks, then reverted to its prior `Viewing`/`Viewing` state
   afterward, same disclosed-synthetic-subject pattern as §11.1) — both now compute
   `background-color: rgb(255, 255, 255)`, `color: rgb(15, 23, 42)`, `opacity: 1`, identical to the
   `Viewed` button. The prompt's own example (`chb06_06.edf`, 18/18) could not be reproduced exactly:
   `chb06` is not currently uploaded into the demo DB (only `chb13`/`chb14`/`chb15`/`chb16` are) and
   processing a fresh ~4-hour, 18-file subject was out of scope for a styling fix — `chb15` was used
   as the second live subject instead, disclosed here rather than silently substituted.
2. **`.6f` score-format regression — false alarm, confirmed, no code change.** `export_txt.py`'s
   `_attribution_rows` still had the `.6f` formatting on disk exactly as fix round 1 left it. Root
   cause: the running backend (`uvicorn main:app`, no `--reload` flag) had been started *before* fix
   round 1's edit was saved that same session (process start ≈13:19, file saved ≈14:21, same day) —
   a stale, never-reloaded process serving pre-fix bytecode, fully explaining Boti's un-fixed
   `chb13-summary.txt` download without any code being wrong. Backend restarted; a fresh export
   (triggered through the live app, `GET /api/subjects/chb13/export` → `200`) confirmed all 90 score
   lines across `chb13`'s 5 events now have exactly 6 digits after the decimal point, including the
   exact previously-flagged line (`8  FZ-CZ  1.272910  Unreviewed`).
3. **This section.**

Guards 4/4 green throughout. No `git add`/`commit`/`push` run in either fix round.

---

## 12 · Integrity incident (from Step 1) — status: resolved, cause still unconfirmed

*(unchanged — see the prior version of this file: `UI/Annotaiton (format_ ID-summary.txt).png` was
modified during Step 1 filter-optimization work, reverted via `git checkout`, root cause never
confirmed, zero recurrence since across Steps 2, 3, 5, 6 and 7 — the only file-hygiene slips since
have been visual/scratch, never a data-integrity repeat: a scratch PNG left in `UI/` at Step 6 §9.4,
and Step 7's own prompt-wording defect (§10.2), which was a layout bug, not a data-integrity one.)*

---

## 13 · Report material for Project #1 (per `PROJECT2_SETUP.md §9.2(D)`)

End-to-end runtime measured = **9.76 s/hour of EEG** (Step 1, not re-measured since; restored to
`CLAUDE.md` in Step 7 round 2 in place of a stale ~15 s/hour component-level estimate that had crept
back into that file — see §10.2). Note for the report's own timing discussion: this is still a
**single point figure with ~5× run-to-run variance** (per-stage timing, needed for the report, is
still open — `STEP8_9_PREDEFENSE_CHECKLIST.md §1`).

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

**New from Step 7, worth noting for the report's methodology discussion:**
- The attribution formula's own closure (round 2) is the clearest instance yet of the build-measure-
  correct loop the report already documents for Steps 5/6: a read-only measurement (Part C, round 1)
  produced the evidence, and a **methodological** authority (Project #1) made the actual call — not
  Project #2 guessing, and not an implementation detail decided in isolation from the thesis's own
  scoring definition.
- The p95-|robust-z| definition is, by construction, the exact formula in
  `src/attribution_pipeline.py` — worth citing directly if the report discusses why the demo's
  attribution panel is defensible as "the same measurement, shown live," not a separate invented
  metric.
- The round-1 layout defect (§10.2) is a useful cautionary instance for the report's own account of
  the *process*, not just the *product*: a wrong instruction from the guide project itself produced a
  wrong build, caught only by Boti's own live use against the locked mockup — an argument for why the
  mockup-wins-on-anything-visible authority rule (`SZSCAN_SPEC_v5.md`'s own authority order) matters
  in practice, not just on paper.

Still open: **O4b** (post-ictal flagging extent — still needs Analysis-screen-level visual review
against known seizure timing, unchanged since Step 3/4) and the **cataloged screenshot set** for
report use (Step 5's `CC_STEP5_FIX*_SCREENSHOTS/` folders, plus Step 7's three rounds of
screenshots, now hold a substantial number of real, captioned screenshots — worth reviewing for
reuse before generating new ones for the report, per `STEP8_9_PREDEFENSE_CHECKLIST.md §1`'s
Figure 3.6 requirement).

---

## 14 · Open items going into Step 9

**Carried over from Step 7, not yet resolved:**

- [ ] **Event id 86 on `chb13_03.edf`** (§10.4) — confirm whether Boti created it live-testing or
      whether it needs investigating further. Resolve before treating `chb13` as a clean subject for
      anything Tier-2-related.

**Handled in the Step 7 chats (nothing left to do by hand):**

- [x] Delete the Human test events in `chb13_02`/`chb13_03` — Pre-step A.
- [x] Verify the Accept fill `#16A34A` live once, on a synthetic file — Pre-step B.
- [x] Record the attribution definition actually implemented in the spec (C20, then closed in C21).
- [x] Restructure `SZSCAN_SPEC_v5.md §1.6` into exactly 3 numbered divergences, matching the report.
- [x] Correct `CLAUDE.md`'s stale timing figure and the "PROVISIONAL" wording in
      `THESIS_CONTEXT_FOR_DEMO.md`/`PROJECT2_SETUP.md`.

**Handled in the Step 8 chats (nothing left to do by hand):**

- [x] `.6f` score-format regression Boti flagged from his `chb13-summary.txt` export — confirmed a
      false alarm (stale, un-reloaded backend process), not a code defect; no fix needed. §11.3 item 2.
- [x] Export button's enabled state didn't visually match its sibling buttons — real computed-style
      bug, fixed and verified live on 2 subjects. §11.3 item 1.

**Deferred on purpose (decide at Step 9 / pre-defense, not before Step 9):**

- [ ] **Filter stages.** The three toolbar buttons (`lff` / `hff` / `60`) are clickable but all gate the same
      single cached bandpass+notch series (§8.5), which sits badly with the anti-staging principle
      (`SZSCAN_SPEC_v5.md §0`: a button that reflects nothing real). The real pipeline has two operations
      (one 0.5–60 Hz bandpass, one 60 Hz notch), so "separable" `lff`/`hff` would mean applying
      high-pass / low-pass filters that are *not* in the pipeline. Options for Boti: (a) keep as is,
      (b) collapse to the two real stages, (c) separate stages with new filters. Needs a decision, not
      code, until then.
- [ ] Synthetic test subjects under `chb14`/`chb15`/`chb16` were built from `chb15` clips — they are not real
      subject data and must be removed before any demo run so no subject row shows synthetic data under a
      real subject's name. **Also now a hard requirement of Tier 2** (`STEP8_9_PREDEFENSE_CHECKLIST.md §2`
      item 2: only real EDF uploads of the 8 TEST subjects, no synthetic files).
- [ ] A real ~4 h file (`chb06`) through the real Create-New flow, if the window-length control's larger
      options and the mini-timeline's pan/zoom (`DOMAIN_SEC` hardcoded to 3600) are to be tested. Its
      cache exists but was never attached to a real subject/file record.

**New from Step 7, deferred to Step 8/9 by design (see `STEP8_9_PREDEFENSE_CHECKLIST.md` for the full
list, not repeated here in full):**

- [ ] Report screenshots: (a) import/process a recording, (b) Figure 3.6 (timeline + attribution of
      the *same* recording, captured post-round-2, no `meas_date` calendar dates visible).
- [ ] Per-stage timing (ingest/filter, adjacency+band-power, GAE scoring incl. per-node, CPD, total),
      median + range, on a frozen build.
- [ ] No-network-egress evidence.
- [ ] `SZSCAN_SPEC_v5.md` O1 recorded with the exact operating-point parameters the demo uses.
- [ ] Tier 2's 6 fixed rules (freeze+tag, clean 8-subject DB, per-subject export of unreviewed AI
      events only, demo never scores itself, rerun-all-on-error, no UI metric).

**Low priority / known:**

- [ ] **Keep the Claude project's uploaded copies in sync with the repo.** Re-upload the repo versions
      of `SZSCAN_SPEC_v5.md`, `SZSCAN_DESIGN_v2.md`, `CLAUDE.md`, `THESIS_CONTEXT_FOR_DEMO.md`,
      `PROJECT2_SETUP.md`, and this file after every step; the repo is the source of truth. (Note from
      Step 6: the project's copies were found stale at that point — same risk applies now that Step 7
      touched four of these five files.)
- [ ] Commit hygiene: keep splitting `web_demo/` commits from `docs/`/`tables/`/`src/figures/`/
      `figures/`/`rank_readout.py`/`results/` commits. Step 7's commit (`cf5ee88`) followed this
      correctly.
- [ ] `--color-uncertain-bg` (`#FFFBEB`) is visually indistinguishable from white (§9.3); the pale row
      highlight of an expanded Uncertain event barely shows. Left as-is.
- [ ] `UI/B1a`/`B2a` show no avatar while the shared `Header.jsx` renders one on Analysis (§9.3) — a
      flagged extrapolation Boti accepted.
- [ ] Step 8 (Export) will read rank/channel/score/status of each event's attribution from what Step 7
      persists (`attribution_status` table + the attribution endpoint) — now using the **closed**
      p95-|robust-z| definition, not the round-1 PROVISIONAL one.

**New from Step 9 phase 1/1b, decisions needed before phase 2 (both Boti's call, see §15):**

- [ ] **File-count-per-subject scope** for the 6 remaining subjects (`chb03`/`chb06`/`chb14`/`chb15`/
      `chb17`/`chb18`) — full real file set (246.39 h combined) vs. a representative subset, per the
      `chb13` precedent (2 of its 33 real files were used, not the full subject).
- [ ] `DELETE /api/subjects/{id}` doesn't clean up `uploads/{subject_id}/` on disk (only the DB rows) —
      confirmed by reading `main.py` directly. Deliberately deferred to a final cleanup pass before the
      demo is considered complete, per Boti's own decision — **not** an active bug needing a fix now.

---

## 15 · Step 9 — detail (phase 1 + phase 1b; phase 2 not started)

**Scope so far:** Step 9 is **cache 8 subjects + pick live-upload subject** per
`DEMO_BUILD_HANDOFF.md §6` row 9. Only the first two of its three planned phases have run. **Reports:**
`CC_STEP9_PROMPT.md`/`CC_STEP9_PHASE1_REPORT.md` (phase 1), `CC_STEP9_PHASE1B_PROMPT.md`/
`CC_STEP9_PHASE1B_REPORT.md` (phase 1b), `CC_STEP9_CHECKPOINT_PROMPT.md` (this section's own source).
Guards 4/4 green throughout both phases. No `git add`/`commit`/`push` run in either.

### 15.1 Phase 1 — 8-subject inventory + synthetic-data cleanup

Every real-vs-synthetic call was made by **SHA-256 comparison against the actual dataset file on
disk**, not filename inference or the DB's own stored duration:

- **`chb14`, `chb15`, `chb16`** (all three) held synthetic data — truncated, re-encoded
  `chb15_NN_short.edf` clips filed under 3 different subject ids, byte-different from every real EDF.
  Deleted via the app's real Delete flow (DB rows) plus manual cache-directory cleanup — the
  `DELETE /api/subjects/{id}` endpoint itself never touches `uploads/{subject_id}/` on disk (read
  directly in `main.py`; now tracked as an open item in §14, deliberately deferred, not a bug to fix
  now).
- **`chb06`** has **no subject row at all** in the DB — the "18-file, full Progress" state Boti's own
  screenshots showed is not the DB's current state. It does have an orphaned, never-finalized partial
  upload on disk: 1 real, byte-identical `chb06_01.edf` (Phase A + raw cache, no score/PELT, no DB
  row). Left in place, not deleted, for phase 2 to possibly reuse.
- **`chb03`** similarly has an orphaned partial upload (2 real, byte-identical files, Phase A cache
  only), zero DB row. Also left in place.
- **`chb17`/`chb18`** have no data anywhere — never touched by any upload.
- **`chb13`** is the only subject with genuinely real, fully-processed, cached data (2 of its 33 real
  files, matching the precedent noted in §14).
- Real file count / total duration on disk, read from each EDF's own header (not the DB, not
  estimated): `chb03` 38 files/38.00 h, `chb06` 18/66.74 h, `chb13` 33/33.00 h (2 already uploaded),
  `chb14` 26/26.00 h, `chb15` 40/40.01 h, `chb16` 19/19.00 h, `chb17` 21/21.01 h, `chb18` 36/35.64 h —
  **246.39 h total across the 7 subjects still needing a real upload+process at the time** (before
  phase 1b processed `chb16`).
- A time-estimate gap was flagged, not glossed over: the existing `9.76 s/hour` figure (`CLAUDE.md`)
  measures only Phase A+B (`pipeline_demo.process_file`) — it never calls
  `cpd_pipeline_v14.detect_events` (PELT), which the real app's Create-New flow runs as a **separate**
  stage, 6 times per subject (once per `pen_mult` in `DEFAULT_PENS`). No isolated PELT timing existed
  anywhere in the repo at the start of phase 1 — resolved in phase 1b (§15.2).

### 15.2 Phase 1b — real PELT / Phase A+B timing, measured on `chb16`

Driven by literally replaying `web_demo/frontend/src/api.js`'s own upload sequence against the running,
unmodified server (real cookie-session login, real `POST /api/uploads/current` →
19× `POST /api/uploads/current/files` sequential → `POST /api/uploads/current/process`) — not a CLI
shortcut, because `claude-in-chrome`'s `file_upload` tool caps combined attachments at 10 MB, far
below `chb16`'s ~915 MB of real EDFs. A parallel poller logged every state transition's wall-clock
timestamp from `GET /api/uploads/current`; no source file in `web_demo/` was modified to take the
measurement.

- **Phase A+B real wall-clock:** 271.56 s for 19.00 h → **14.29 s/hour** — **1.46×** the existing
  `9.76 s/hour` figure. Two real causes, not a bug: genuine upload-transfer overhead (~58.4 s total),
  and unbounded per-file Phase A thread concurrency (`upload_manager.py` spawns one background thread
  per file the instant its bytes land, not waiting for the previous file — up to 19 concurrent threads
  observed on this dev machine's 4-physical/8-logical-core CPU). The concurrency finding is an **open
  item, not fixed** (§14) — deliberately deferred, since the measured total time above is already
  comfortable without a fix; revisit (cap concurrent Phase A threads) before the defense if timing
  margin ever becomes a real concern.
- **Process/PELT alone:** 68.03 s for 19.00 h → **3.58 s/hour** — only **~25%** of Phase A+B's own
  wall-clock for the same subject. Recorded in `SZSCAN_SPEC_v5.md §1.7` as **C23** (this checkpoint):
  PELT is **not** the dominant cost, contradicting §1.7's own prior text.
- **Revised total-time estimate for the 6 subjects still needing upload** (`chb03`/`chb06`/`chb14`/
  `chb15`/`chb17`/`chb18`, 227.3 h combined): **~50.5 min** using phase 1's `9.76 s/h` lower bound +
  real PELT, or **~67.7 min** using this run's own real `14.29 s/h` rate + real PELT — either way,
  comfortably inside one working session, not the "long unattended run" phase 1 flagged as a risk.
- No crash, no retry, no error at this scale; `chb16`'s operating point converged normally
  (`pen_mult = 1.0`).
- **`chb16` kept in the DB deliberately** (memo `"CC_STEP9_PHASE1B timing run"`), fully and genuinely
  processed through the real flow — all 19 real files SHA-256-confirmed, 41 events recorded. This is
  `chb16` done for phase 2 already, not throwaway work. One loose end, left deliberately: the in-memory
  upload session is still `done: true`, **unacknowledged** — the exact state a real user leaves it in
  before clicking through the "Processing complete" panel. This blocks starting a **new** Create-New
  session system-wide (one-subject-in-flight rule) until someone opens the app and dismisses it; it is
  a manual UI action for Boti, not something for a future prompt to script around, and does not affect
  `chb16`'s own already-committed DB row.

### 15.3 Not yet done — phase 2

Uploading and processing the other 6 real subjects (`chb03`, `chb06`, `chb14`, `chb15`, `chb17`,
`chb18`) has **not started**. Blocked on: (a) `chb16`'s unacknowledged upload session being dismissed
in the app first, (b) Boti's decision on file-count-per-subject scope (§14). No pipeline, upload, or
DB state was touched writing this section — documentation only.
