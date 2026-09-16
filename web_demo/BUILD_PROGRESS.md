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
| 3 — Create new → upload → Process → subject appears in table | **DONE** | took **4** fix rounds past the initial build, all found via live browser testing, none caught by automated/curl checks — see §6 below, read it before starting Step 4 |
| 4-9 | not started | |

**Where to resume:** start Step 4 per `DEMO_BUILD_HANDOFF.md §6` row 4 — Analysis screen: Panel EEG +
toolbar + scrub, no events yet, compare against `UI/B1a`, `B1b`, `B1d`. No open blockers carried over
from Step 3 beyond the two low-priority items in §6.4 (never manually verified, not blocking).

---

## 2 · Repo map — what exists under `web_demo/` right now

```
web_demo/
├── CLAUDE.md                    (pre-existing)
├── SZSCAN_SPEC_v5.md            (pre-existing)
├── SZSCAN_DESIGN_v2.md          (pre-existing)
├── DEMO_BUILD_HANDOFF.md        (pre-existing)
├── THESIS_CONTEXT_FOR_DEMO.md   (pre-existing)
├── PROJECT2_SETUP.md            (pre-existing, shared with Project #1)
├── UI/                          (pre-existing, locked PNGs + Logo.png — still clean, never modified)
├── BUILD_PROGRESS.md            this file
├── CC_STEP0_PROMPT.md           Step 0 build prompt
├── CC_STEP1_PROMPT.md           Step 1 build prompt
├── CC_STEP1_FILTER_OPT_PROMPT.md   Step 1 follow-up: filter-cost optimization
├── CC_STEP2_PROMPT.md           Step 2 initial build prompt
├── CC_STEP2_FIX_PROMPT.md       Step 2 fix round 1 (logo + header, first attempt)
├── CC_STEP2_FIX2_PROMPT.md      Step 2 fix round 2 (numeric header target + logo re-check)
├── CC_STEP2_FIX3_PROMPT.md      Step 2 fix round 3 (LoginScreen logo source + favicon) — closed it out
├── CC_STEP2_FIX3_REPORT.md      Claude Code's written report for round 3
├── CC_STEP3_PROMPT.md           Step 3 initial build prompt
├── CC_STEP3_REPORT.md           Step 3 initial build report
├── CC_STEP3_FIX_PROMPT.md       Step 3 fix round 1 (panel auto-close + overlay layout)
├── CC_STEP3_FIX_REPORT.md       report for round 1
├── CC_STEP3_FIX2_PROMPT.md      Step 3 fix round 2 (PROCESS never enables)
├── CC_STEP3_FIX2_REPORT.md      report for round 2
├── CC_STEP3_FIX3_PROMPT.md      Step 3 fix round 3 (unlock Project ID/Memo until PROCESS)
├── CC_STEP3_FIX3_REPORT.md      report for round 3
├── CC_STEP3_FIX4_PROMPT.md      Step 3 fix round 4 (minimize/restore bug + 2 author decisions + font check)
├── CC_STEP3_FIX4_REPORT.md      report for round 4 — most recent Step 3 state
├── backend/
│   ├── .env                     real dev credentials, gitignored (see §5.1)
│   ├── .env.example
│   ├── main.py                  FastAPI app — auth + /api/subjects + upload/process endpoints
│   ├── pipeline_demo.py         process_file() (Step 1) + Phase A/B split (Step 3)
│   ├── upload_manager.py        NEW in Step 3 — UploadSession, session_id-keyed draft storage,
│   │                             ready_to_process gating, start_process() w/ allowlist validation
│   │                             at click-time, _wait_phase_b_then_process, _finalize_draft_dir
│   ├── pipeline_worker.py       NEW in Step 3 — Phase B / Process run as a genuine subprocess
│   │                             (works around a hang when run from a thread/ProcessPoolExecutor
│   │                             inside the uvicorn process on this machine — see CC_STEP3_REPORT.md)
│   ├── db.py                    SQLite schema for subjects/files/events
│   ├── export_txt.py            still a stub (Step 8 scope)
│   └── tests/
│       └── test_guards.py       all 4 guards, reconfirmed PASS after every Step 3 round
└── frontend/                    Vite + React + Tailwind
    ├── src/screens/LoginScreen.jsx      Step 2
    ├── src/screens/DatabaseScreen.jsx   Step 2 (empty state) + Step 3 (real rows, search,
    │                                     delete, overlay-panel host, keeps CreateNewPanel
    │                                     mounted across minimize per round 4)
    ├── src/screens/CreateNewPanel.jsx   NEW in Step 3 — upload UI, 4 fix rounds, see §6.2
    ├── src/components/Header.jsx        Step 2
    ├── src/components/icons.jsx         Step 3 — upload/status icons
    ├── src/components/ConfirmDialog.jsx NEW in Step 3 — reused for both subject-delete and
    │                                     draft-discard confirmations
    ├── src/api.js                       Step 3 — upload/process/search/delete endpoints
    ├── src/assets/logo.png              Step 2
    ├── public/favicon.png                Step 2
    └── (design-tokens.js, tailwind.config.js, etc. — unchanged since Step 0)
```

Outside `web_demo/`, untouched by any of this: `tables/tables_ch2.md` and `docs/VERIFIED_CORRECTIONS.md`
(Project #1 artifacts), `check_t8p8.py` (unrelated pre-existing MNE debugging script at repo root).

**Git hygiene reminder (from Step 2, still holds):** commit `web_demo/` changes and `docs/`/report
changes separately, never in the same `git add .`.

---

## 3 · Step 0 — detail

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
paid off again in Step 3 (see §6).

**Final verified state:** `pytest web_demo/backend/tests/test_guards.py -v` → 4 passed (raw
console, confirmed by Boti). `git status` clean.

---

## 4 · Step 1 — detail

**Scope:** `pipeline_demo.py`'s `process_file()` only — SPEC §1.3 stage 1. `process_subject()` /
PELT / operating point explicitly NOT in scope (later step).

**Implementation reviewed in full against `SZSCAN_SPEC_v5.md §1.3`** — checkpoint sha256 verified
before load, 18-channel select, window+filter with no artifact rejection (per §1.6a), z-score
per-channel (file-level at the time — later resolved in Step 3, see §6.1), adjacency via
manual `apply_car → wpli/aec → combine → topk` (not `build_adjacency()`, which is fixed-threshold),
band powers, GAE forward batched, `zlatent` via `LedoitWolf` (same file-vs-subject caveat, also
resolved in Step 3), `zgamma` via continuous call to `compute_gamma_scores_batch`, robust-z per
branch, ensemble via `build_ensemble_subset(..., subset=CANDIDATES["rlg"])`.

**Timing — final measured:** **9.76 s/hour of EEG** on `chb06_01.edf` (CPU-only), after fixing
`filter_window()` to filter the whole continuous recording once instead of per-window. Noted
variance across runs (22-110s on the adjacency+band-power stage on identical code, same file) —
attributed to background load on the dev machine, not a code bug. Not re-investigated further.

**Guard check:** 4 passed (raw console) right after implementation.

---

## 5 · Step 2 — detail

**Scope:** Log in + empty Database + footer, per `DEMO_BUILD_HANDOFF.md §6` row 2 and
`SZSCAN_SPEC_v5.md §4`/`§5.1`. Explicitly out of scope: Create New panel, upload, Process, search
filtering, Delete/Open row actions — all Step 3.

**Initial build (`CC_STEP2_PROMPT.md`):** backend session auth (`.env`-sourced credentials, session
cookie, login/logout endpoints), `db.py` schema (no seed data), frontend Login + Database screens.
Dev credentials generated: `ADMIN_USER=AdminSzScan` / `ADMIN_PASS=tvEb7KbacjHD` (still current,
Boti has not rotated them — fine for a local dev-only demo, SPEC §4 confirms this isn't a real
security mechanism).

**Backend verified correct throughout, no issues at any point:** curl-based auth flow checked in the
initial report, later reconfirmed via actual browser use — real backend log shows
`POST /api/login → 200`, `GET /api/subjects → 200`, `POST /api/logout → 200`, subsequent
`POST /api/login → 200` again. One transient `Request failed (502)` during the fix rounds, caused
by the backend terminal having been closed/killed while the frontend dev server was being
restarted — not a code bug, resolved by restarting `uvicorn`.

### 5.1 What matched the mockup on the first try

Header gradient colors, footer bar (exact copy, exact background), page background, brand violet
button, Database empty-state wording (`No data`), 7-column table structure, avatar dropdown with
`Log out` (`UI/A0b`) — all correct from the initial build, no rework needed.

### 5.2 What didn't match, and took 4 rounds to close out

| # | Issue | Root cause | Fixed in |
|---|---|---|---|
| 1 | Column headers missing literal `\|` before "No. files"/"Status" | The mockup renders `\| No. files` / `\| Status` as actual pixel/text content — invisible in the SPEC's prose table, only visible by reading the PNG directly | round 1 |
| 2 | Header undersized (measured 10.8% of viewport height vs mockup's 12.9%) | Guessed from visual inspection alone, no way to self-verify | round 1 (undershot) |
| 3 | Header oversized (15.7%) after round 1's fix | Same cause — blind guessing, overcorrected | round 2, fixed with a **precise numeric target** (measured 12.9% target, computed exact Tailwind class change: `py-6→py-5`, `h-20→h-16`, 128px→104px) instead of another visual guess — converged correctly |
| 4 | Header/Login logo showing a generic placeholder icon, not the real logo | See §5.3 — this was the expensive one | rounds 1-3 |
| 5 | Favicon invisible on light browser tabs | `Logo.png` is solid white with transparent background — fine on the purple header, illegible as a tab icon | round 3 (added a colored `favicon.png`, not spec-required, quick polish) |

### 5.3 The logo saga — read this before trusting any future "file exists" check

This took 3 fix rounds and is the clearest lesson from Step 2, worth internalizing for every future
step:

1. **Round 1** (`CC_STEP2_FIX_PROMPT.md`) asked Claude Code to copy `UI/Logo.png` into the frontend
   and wire it in. It silently didn't happen — `git diff` showed zero changes to any logo-related
   file. Root cause, found later: `web_demo/frontend/src/assets/logo.png` **already existed** —
   Claude Code's very first Step 2 build had generated its own placeholder icon at exactly that
   filename before `Logo.png` was ever provided. Every later "does the logo file exist" check came
   back "yes" — because a file existed, just the *wrong one*. **A file-existence check is not a
   content-correctness check.** (This exact lesson resurfaced in Step 3 — see §6's "trust but
   verify" pattern throughout.)
2. **Round 2** (Cursor Agent, free tier) was tried specifically because it has a built-in browser +
   screenshot tool (`browser_take_screenshot`) that Claude Code's CLI session lacked at the time — a
   legitimate capability-based tool choice, not habit. It hit its free usage limit mid-task and made
   **zero** file changes. Lesson: Cursor's free tier is not reliable for a multi-step agentic task.
   (Superseded in Step 3 by Claude Code's own `claude-in-chrome` skill, connected to Boti's real
   browser — no usage-limit issue, and this is what actually caught 3 of Step 3's 4 bugs.)
3. Manually diagnosed with `cp` + `cmp` (byte-level file comparison) instead of trusting further
   AI self-reports — confirmed the asset file itself was now correct, but the **Log in screen**
   still rendered the old icon.
4. **Round 3** (`CC_STEP2_FIX3_PROMPT.md`) investigated properly (`grep` first, report findings
   before editing) and found `LoginScreen.jsx` had *already* been fixed to use the correct asset —
   but that fix had been swept into an unrelated Project #1 commit and was never visually
   re-verified after. Final pixel-crop comparison against the actual `Logo.png` file confirmed both
   the Database header and Log in screen now render the correct mark.

**Process lesson also adopted from this saga:** starting with round 3, prompts ask Claude Code to
write its final report to a `.md` file instead of printing to the terminal. **Used for every Step 3
round without exception, and should continue for every future step.**

### 5.4 Screenshot-comparison methodology note

Comparing "header as % of screenshot height" across rounds produced one confusing measurement
that turned out to be an artifact of one screenshot including the full browser chrome
(tabs/address bar/bookmarks) while earlier ones didn't. **When pixel-comparing future screenshots
against mockups, always first identify and exclude browser chrome, or use a chrome-independent
ratio (e.g. header height ÷ avatar diameter) instead of raw % of image height.**

### 5.5 Final verified state

- `pytest web_demo/backend/tests/test_guards.py -v` → 4 passed (raw console, confirmed by Boti).
- Logo on both Database header and Log in screen pixel-confirmed identical to `web_demo/UI/Logo.png`.
- Favicon confirmed visible/legible in the browser tab.
- Nothing under `web_demo/UI/` ever showed as modified — held up across every round since.

---

## 6 · Step 3 — detail

**Scope:** Create New panel, file upload with validation, two-stage pipeline execution
(Phase A/B on upload, Process → PELT), minimize-to-toast, single-subject concurrency lock, Delete
(subject-level only), Search, Database table showing real rows. Per `DEMO_BUILD_HANDOFF.md §6` row 3
and `SZSCAN_SPEC_v5.md §1.5, §1.6, §2, §5.1, §5.4-5.7, §8`. Out of scope, still: Analysis screen
(Open is a deliberate stub — see §6.3), Panel Event, mini-timeline, attribution, Select Range, Export.

**Took 4 fix rounds past the initial build — all 4 rounds' bugs were found by live browser testing,
none were caught by Claude Code's own automated/curl checks.** This is the single biggest lesson
from Step 3: curl proves an endpoint responds correctly; it cannot catch a panel that closes itself
on scroll, a layout that visually pushes instead of overlays, a button wired to the wrong state, or
an edit that silently reverts on remount. Round 1 onward used `claude-in-chrome` (Claude Code's
browser-control skill, connected to Boti's real Chrome) for verification — this materially improved
report quality (round 2 and 4's reports show direct state proof, e.g. a backend JSON snapshot
captured mid-test showing `phase_b_done: false, ready_to_process: true`, not just narrated claims).

### 6.1 Initial build — architectural decisions made

- **Phase A / Phase B split**, resolving the tension between SPEC §5.5 ("stage 1 starts per file on
  upload, before siblings may exist") and §1.6a ("z-score/LedoitWolf fit on the whole subject").
  Phase A (per file, on upload completion): 18-channel read, filter, window — flips the file's icon
  to ✕. Phase B (once, when every file is uploaded): concatenate raw windows subject-wide, fit
  z-score mean/std + `LedoitWolf`, then run CAR→adjacency→band-powers→GAE→zrecon/zlatent/zgamma→
  robust-z→ensemble **per file** using those subject-wide stats. Resolves both `# TODO(step3)`
  markers carried over from Step 1.
- **Operating point (O1):** `BUDGETS["balanced"]=40.0` read from `fp_budget_operating_point.py` at
  runtime, never hardcoded. Demo-time calibration: grid-search `pen_mult` per subject on the
  concatenated global score timeline, pick whichever value's resulting event-rate (events/24h) is
  closest to 40/day. Confirmed non-degenerate (no subject produced 0 events). Example from round 2
  fix testing: `chb06`, 3 files, `pen_mult=2.0` → 28.76 events/day. Full original grid + single-file
  calibration numbers are in `CC_STEP3_REPORT.md`.
- **Project ID = subject ID directly**, validated against the 8-subject allowlist. Initially bound
  at session creation; **revised in round 3** (see §6.2) to be re-validated and bound only at the
  moment PROCESS is clicked, so the field could stay editable throughout.
- **Event → file assignment** via cumulative offset per SPEC §1.5 — no `edf_index` module invented.
- **File ordering / "Start date" column** uses `raw.info['meas_date']` (the real EDF header
  datetime) directly, **not** `edf_order.py`'s summary-text heuristic. Confirmed present and valid
  for all 8 allowlisted subjects (spot-checked one file per subject, 2026-09-13 — all returned real
  anonymized-but-valid datetimes, none `None`). `pipeline_demo.py` already raises
  `UnsupportedEdfError` if a file's `meas_date` is missing, so the no-fallback-needed case is a
  deliberate, already-defended choice, not an oversight. **`edf_order.py` stays in the repo
  completely unmodified but is genuinely unused** — confirmed via
  `grep -rn "meas_date" web_demo/backend/*.py`: only referenced in `pipeline_demo.py` (read) and
  `db.py` (schema comment), `edf_order.py` is not in that call path at all. `meas_date` solves the
  chb03_24/25 cross-midnight ordering problem `edf_order.py`'s swap-heuristic was built for, without
  needing the heuristic — decided to leave it as dead code rather than wire it in, since a full
  datetime is strictly more correct than a time-of-day-only heuristic.
- **Infra note:** the GAE/PELT pipeline was found to hang at 0% CPU when run from a thread or a
  `ProcessPoolExecutor` inside the `uvicorn` process on this specific dev machine — reproducible
  only in that hosting context. Worked around by running Phase B and Process as a genuine separate
  `subprocess.Popen` (`web_demo/backend/pipeline_worker.py`). Root cause not fully chased down (an
  intermittent Phase-B-not-triggering symptom was also reported early on, mitigated via a
  poll-triggered safety net — this was superseded by round 2's rework of `ready_to_process`/
  `start_process`, and hasn't recurred as a distinct symptom since).

### 6.2 Four fix rounds

| Round | Bug / decision | Root cause / resolution |
|---|---|---|
| 1 | Panel auto-closed after a few seconds / on scroll | Session-polling `useEffect` misread expected 404s (no backend session yet, before any file added) as "the session disappeared," closing the panel. Fixed: poll gated on `hasSession`, not `panelMode`. |
| 1 | Panel pushed/resized the Database table instead of overlaying it | `main` was a shared-width flex row (table `flex-1` + panel `w-[420px] shrink-0`) — a real layout partner, not an overlay. Fixed: panel changed to `absolute top-0 right-0 bottom-0` anchored to `main`'s right edge (`z-30`); table reverted to plain full-width block flow. Verified via `getBoundingClientRect()`: table width identical whether panel open or closed. |
| 2 | PROCESS button never enabled once every file showed ✕ | `upload_manager.py`'s `ready_to_process` incorrectly required `phase_b_done` — an internal computation-ordering concern (Phase B needs to run before PELT) that SPEC §5.5 never says should gate the *button*. Fixed: gate is upload-completion only (`all files == "uploaded"`); clicking PROCESS itself sets `processing=True` immediately (showing the existing full-panel loading state) and a background wait loop nudges/waits for Phase B before running PELT. Traced and explicitly ruled out as a round-1 regression — the coupling predates round 1 entirely. |
| 3 | *(author decision, not a bug)* Unlock Project ID/Memo for editing at any time, not just pre-upload | Upload storage was keyed by the literal Project ID text (`uploads/{project_id}/`) — a moving target once the field became editable after upload. Fixed: session now keyed by an internal immutable `session_id` (`secrets.token_hex(8)`); files land in `_draft_{session_id}/` during upload/Phase A/B, only relocated to `uploads/{project_id}/` once PROCESS validates the (possibly-just-edited) ID against the allowlist **and** Phase B has fully finished (so the rename can't race an open file handle). Verified with both a rejection (invalid ID at PROCESS-click → toast, nothing bound, files stay listed) and a subsequent successful correction (`chb06` → succeeds, lands under the corrected ID on disk and in the DB). |
| 4 | Minimize → restore silently reverted any Project-ID/Memo edits back to the session's original value | `CreateNewPanel` was fully unmounted on minimize (conditional render on `panelMode === 'open'`), destroying local React state; restoring remounted a fresh instance whose one-shot hydration effect fired again and overwrote the edit. This was flagged as a risk by the build-guide project *before* round 3 shipped, and confirmed exactly as predicted on first live test. Fixed: `CreateNewPanel` now stays mounted for the panel's entire open/minimized lifetime; a `hidden` prop toggles a Tailwind `hidden`/`flex` class instead of unmounting. Verified in both the no-files-yet and files-already-uploaded cases. |
| 4 | *(author decision, reversing an earlier explicit agreement)* Add a confirmation dialog to × | Reused `ConfirmDialog.jsx` unmodified. Wording: *"Discard this draft? Any uploaded files and progress will be lost."* — deliberately distinct from the delete-subject wording since the entity/stakes differ. Shown only when there's real content to lose (non-empty Project ID/Memo, or ≥1 file) — a completely blank panel still closes instantly, no dialog. Verified for both the no-files and with-files cases, plus the blank-panel fast path. |
| 4 | *(author decision)* Remove the progress bar from the Processing / Upload-Complete states | `SZSCAN_DESIGN_v2.md §8`'s existing "no fake %" rule already argued against an animated bar with no real signal behind it; author chose outright removal over building a real (coarse, file-count-based) alternative. **`UI/A2a`/`A2b` mockups do show a bar — this is now a deliberate, recorded departure from the mockup**, not an oversight; flagged explicitly in the round-4 report per the fix prompt's own instruction to note such discrepancies. |
| 4 | Font mismatch flagged by author on the Processing panel | Investigated, not reproduced: `getComputedStyle()` confirmed `Inter, sans-serif` was already correctly applied via inheritance from `body`; no `font-mono` or conflicting inline style anywhere in the component. No code change made. Likely explanation offered (not confirmed): the now-removed progress bar — an element with no analog anywhere else in the app — made the panel *read* as visually inconsistent even though the text itself was rendering correctly. |

### 6.3 Verified by Boti himself, live in a real browser (not just Claude Code's own checks)

- Full create → upload → Process → subject-appears-in-table cycle, multiple times, `chb06`, with
  1 and with 3 files.
- Minimize/restore now preserves in-progress edits, both with and without files already uploaded.
- × discard confirmation — correct wording, appears only when there's real content to lose.
- Progress bar confirmed gone from both the Processing and Upload-Complete states.
- Search — partial match, button-triggered (not per-keystroke), correct `No results for '...'`
  wording on a miss.
- Delete — subject-level confirmation dialog works and actually deletes ("Are you sure you want to
  delete this process?" → Yes → row gone); selecting a **child file row** and clicking Delete
  correctly does nothing, per SPEC §5.6.
- Open — correctly shows "Opening the Analysis screen isn't implemented yet (Step 4)." instead of
  navigating or erroring, per the original build's documented stub.
- Allowlist enforcement re-confirmed authoritative at PROCESS-click time with two different invalid
  IDs across two separate tests (`chb99typo` in round 3, `chb06new` just now) — both correctly
  rejected with the exact toast; both times, correcting the ID and clicking PROCESS again succeeded.
  **This rejection behavior is intentional, not a bug** — `CLAUDE.md`: *"Do not relax this — serving
  a training subject would mean demoing on training data."*

### 6.4 Two scope items never manually verified in a browser — carried forward, low priority

Both were exercised only via Claude Code's own `curl` tests in the original Step 3 build, never
clicked through by a human, and not touched by any of the 4 fix rounds:
- The `File rejected — unsupported format or channel configuration.` toast for a malformed/
  wrong-channel-config upload.
- The single-subject concurrency lock (`UI/A1d`'s "processing another subject, please wait" message
  when "Create new" is clicked while a subject is already mid-pipeline).

**Accepted as lower risk, not blocking Step 3's close**, given four rounds already went into this
step and the report deadline (15 Oct 2026). Revisit opportunistically — e.g. Step 9's cache-building
pass touches all 8 subjects and would likely surface a format-rejection issue if one exists.

### 6.5 Final verified state

- `pytest web_demo/backend/tests/test_guards.py -v` → 4 passed (raw console, confirmed by Boti,
  independently, after **every one** of the 4 fix rounds — most recent as of round 4).
- `git status` clean outside `web_demo/` except `.gitignore`. `tables/tables_ch2.md` and
  `docs/VERIFIED_CORRECTIONS.md` remain pre-existing Project #1 artifacts, untouched across all of
  Step 3. `check_t8p8.py` (repo root, untracked) is an unrelated pre-existing MNE debugging script,
  also untouched.
- Nothing under `web_demo/UI/` ever showed as modified across any round.

---

## 7 · Integrity incident (from Step 1) — status: resolved, cause still unconfirmed

During the Step 1 filter-optimization work, `web_demo/UI/Annotaiton (format_ ID-summary.txt).png`
(a locked mockup) was modified (`git diff --stat` showed `Bin 103048 -> 103996 bytes`). Reverted via
`git checkout`, confirmed clean at the time.

**Root cause never confirmed.** Asked again explicitly in `CC_STEP2_PROMPT.md`'s side-note; Claude
Code's answer: it has no visibility into the prior (Step 1) session's tool calls and can't say what
touched the file. No further leads. **Not re-investigating further** — but the mitigation (explicit
"never write to UI/, copy to scratch first" instruction in every prompt since) has held up cleanly
across Step 2's 4 rounds and Step 3's 4 rounds with zero recurrence, which is the practically
important outcome even without a root cause.

---

## 8 · Report material for Project #1 (per `PROJECT2_SETUP.md §9.2(D)`)

End-to-end runtime measured = **9.76 s/hour of EEG** (Step 1, with the noted run-to-run variance
caveat, not re-measured since).

**Operating point (O1) is now implemented and demonstrated working** (§6.1) — one of the four blanks
flagged after Step 1 is now fillable: a real, label-free, per-subject FP-budget calibration example
exists (`chb06`, `pen_mult=2.0` → 28.76 events/day against the 40/day balanced target; full grid in
`CC_STEP3_REPORT.md`).

Still open: **O4b** (post-ictal flagging extent — needs Analysis-screen-level visual review of events
against known seizure timing, Step 4+) and a **formally cataloged set of app screenshots** for report
use — real screenshots exist informally from Step 2 and Step 3's testing (Login, Database, Create New
panel, Processing/Done states) but haven't been organized/captioned for direct report inclusion yet.

---

## 9 · Open items before / going into Step 4

- [ ] Two Step 3 items never manually verified (§6.4) — optional revisit later, not blocking.
- [ ] Commit hygiene: still no urgent cleanup needed, just keep splitting `web_demo/` commits from
      `docs/`/`tables/` commits going forward.
- [ ] Organize existing screenshots (Login, Database, Create New flow) for report use — no new
      screenshots needed, just cataloging (see §8).
- [ ] Step 4 itself: prompt not yet written. Scope per `DEMO_BUILD_HANDOFF.md §6` row 4 —
      Analysis screen: Panel EEG + toolbar + scrub, **no events yet** (mini-timeline/Panel
      Event/attribution are Step 5+). Compare against `UI/B1a`, `B1b`, `B1d`. Read
      `SZSCAN_SPEC_v5.md §6.1-6.4` in full and `DEMO_BUILD_HANDOFF.md §5`'s waveform-serving notes
      (decimation, min/max envelope, raw+filtered dual-serve) before drafting — this step is
      canvas-rendering-heavy and has real technical subtlety (18.6M points/file, must not ship to
      the browser undecimated). Given Step 3 took 4 rounds specifically because visual/interactive
      bugs don't show up in curl tests, plan to use `claude-in-chrome` from round 1 of Step 4
      onward rather than adding it reactively after a bug is found.
