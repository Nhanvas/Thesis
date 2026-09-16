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
| 3 — Create new → upload → Process → subject appears in table | **DONE** | took **6** fix rounds past the initial build — see §6 below, read it before starting Step 4 |
| 4-9 | not started | |

**Where to resume:** start Step 4 per `DEMO_BUILD_HANDOFF.md §6` row 4 — Analysis screen: Panel EEG +
toolbar + scrub, no events yet, compare against `UI/B1a`, `B1b`, `B1d`. No open blockers carried over
from Step 3. Five real subjects already exist in the DB from Step 3 testing and are kept
deliberately for Step 4 to use without re-uploading: `chb06` (1 file), `chb13` (2 files), `chb15`
(2 files), `chb14` (6 files), `chb16` (12 files) — the last three are short-duration EDFs built from
real `chb15` headers/data (see §6.2 round 5), not full-length recordings.

---

## 2 · Repo map — what exists under `web_demo/` right now

```
web_demo/
├── CLAUDE.md                    (pre-existing)
├── SZSCAN_SPEC_v5.md            (pre-existing, amended 2026-09 — C17, see §6.2 round 5)
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
├── CC_STEP3_FIX4_REPORT.md      report for round 4
├── CC_STEP3_FIX5_PROMPT.md      Step 3 fix round 5 (A1/A2 leftover verification + C17 implementation)
├── CC_STEP3_FIX5_REPORT.md      report for round 5
├── CC_STEP3_FIX6_PROMPT.md      Step 3 fix round 6 (logout dropdown z-index bug) — closed Step 3 out
├── CC_STEP3_FIX6_REPORT.md      report for round 6 — most recent Step 3 state
├── backend/
│   ├── .env                     real dev credentials, gitignored (see §5.1)
│   ├── .env.example
│   ├── main.py                  FastAPI app — auth + /api/subjects + upload/process endpoints
│   ├── pipeline_demo.py         process_file() (Step 1) + Phase A/B split (Step 3)
│   ├── upload_manager.py        UploadSession, session_id-keyed draft storage, ready_to_process
│   │                             gating (upload-completion only, round 2), start_process() w/
│   │                             allowlist validation at click-time (round 3), _finalize_draft_dir
│   ├── pipeline_worker.py       Phase B / Process run as a genuine subprocess (works around a
│   │                             uvicorn-hosting-context hang — see CC_STEP3_REPORT.md)
│   ├── db.py                    SQLite schema for subjects/files/events; `_recording_label()`
│   │                             renders "Start date" as `Recording N, HH:MM:SS` (C17, round 5) —
│   │                             N from `meas_date`-ascending order, separate from and non-
│   │                             disruptive to filename-based event-offset assignment (SPEC §1.5)
│   ├── export_txt.py            still a stub (Step 8 scope)
│   └── tests/
│       └── test_guards.py       all 4 guards, reconfirmed PASS after every Step 3 round (6/6)
└── frontend/                    Vite + React + Tailwind
    ├── src/screens/LoginScreen.jsx      Step 2
    ├── src/screens/DatabaseScreen.jsx   Step 2 (empty state) + Step 3 (real rows, search,
    │                                     delete, overlay-panel host, keeps CreateNewPanel
    │                                     mounted across minimize per round 4)
    ├── src/screens/CreateNewPanel.jsx   Step 3 — upload UI, 6 fix rounds, see §6.2
    ├── src/components/Header.jsx        Step 2, fixed in Step 3 round 6 (avatar dropdown z-index —
    │                                     pre-existing bug, only became visible after round 1's
    │                                     layout change; see §6.2)
    ├── src/components/icons.jsx         Step 3 — upload/status icons
    ├── src/components/ConfirmDialog.jsx Step 3 — reused for both subject-delete and
    │                                     draft-discard confirmations
    ├── src/api.js                       Step 3 — upload/process/search/delete endpoints
    ├── src/assets/logo.png              Step 2
    ├── public/favicon.png                Step 2
    └── (design-tokens.js, tailwind.config.js, etc. — unchanged since Step 0)
```

Outside `web_demo/`, untouched by any of this: `tables/tables_ch2.md`, `docs/VERIFIED_CORRECTIONS.md`,
`docs/EXHIBIT_SET_FINAL.md`, `docs/PROJECT_STATUS.md`, `docs/RUBRIC_TRACKING.md`,
`docs/VERIFIED_NUMBERS.md`, `src/figures/*.py` — all confirmed Project #1 / report-writing artifacts
edited by the author directly, unrelated to the demo build. `check_t8p8.py` (unrelated pre-existing
MNE debugging script at repo root) also untouched.

**Git hygiene reminder (from Step 2, still holds):** commit `web_demo/` changes and `docs/`/`src/figures/`
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
paid off repeatedly in Step 3 (see §6).

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
`Log out` (`UI/A0b`) — all correct from the initial build visually, no rework needed at the time.
**Caveat added in Step 3 round 6:** "visually correct" here meant pixel-matched against the mockup,
not functionally click-tested — the dropdown's `Log out` button turned out to be unclickable
(z-index bug) the whole time, only discovered and fixed in Step 3. See §6.2 round 6.

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
   content-correctness check.**
2. **Round 2** (Cursor Agent, free tier) was tried specifically because it has a built-in browser +
   screenshot tool (`browser_take_screenshot`) that Claude Code's CLI session lacked at the time — a
   legitimate capability-based tool choice, not habit. It hit its free usage limit mid-task and made
   **zero** file changes. Lesson: Cursor's free tier is not reliable for a multi-step agentic task.
   (Superseded in Step 3 by Claude Code's own `claude-in-chrome` skill, connected to Boti's real
   browser — no usage-limit issue, and this is what actually caught 5 of Step 3's 6 bugs.)
3. Manually diagnosed with `cp` + `cmp` (byte-level file comparison) instead of trusting further
   AI self-reports — confirmed the asset file itself was now correct, but the **Log in screen**
   still rendered the old icon.
4. **Round 3** (`CC_STEP2_FIX3_PROMPT.md`) investigated properly (`grep` first, report findings
   before editing) and found `LoginScreen.jsx` had *already* been fixed to use the correct asset —
   but that fix had been swept into an unrelated Project #1 commit and was never visually
   re-verified after. Final pixel-crop comparison against the actual `Logo.png` file confirmed both
   the Database header and Log in screen now render the correct mark.

**Process lesson also adopted from this saga:** starting with round 3, prompts ask Claude Code to
write its final report to a `.md` file instead of printing to the terminal. **Used without exception
ever since.**

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
(Open is a deliberate stub, resolved in Step 4 — see §6.3), Panel Event, mini-timeline, attribution,
Select Range, Export.

**Took 6 fix rounds past the initial build — every bug found was found by live browser testing,
none were caught by Claude Code's own automated/curl checks.** This is the single biggest lesson
from Step 3: curl proves an endpoint responds correctly; it cannot catch a panel that closes itself
on scroll, a layout that visually pushes instead of overlays, a button wired to the wrong state, an
edit that silently reverts on remount, or a dropdown painted invisibly behind another element.
Round 1 onward used `claude-in-chrome` (Claude Code's browser-control skill, connected to Boti's real
Chrome) for verification — this materially improved report quality (several rounds' reports show
direct state proof, e.g. a backend JSON snapshot captured mid-test showing
`phase_b_done: false, ready_to_process: true`, or `document.elementFromPoint()` proving which DOM
element actually painted on top — not just narrated claims).

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
  at session creation; **revised in round 3** to be re-validated and bound only at the moment
  PROCESS is clicked, so the field could stay editable throughout (see round 3 below).
- **Event → file assignment** via cumulative offset per SPEC §1.5 — no `edf_index` module invented.
- **File ordering / "Start date" column** uses `raw.info['meas_date']` (the real EDF header
  datetime) directly, **not** `edf_order.py`'s summary-text heuristic — confirmed present and valid
  for all 8 allowlisted subjects (spot-checked one file per subject, 2026-09-13, none `None`).
  `edf_order.py` stays in the repo completely unmodified but is genuinely unused (confirmed via
  `grep -rn "meas_date" web_demo/backend/*.py`) — `meas_date` solves the chb03_24/25 cross-midnight
  ordering problem without the heuristic. **Round 5 later reused this exact `meas_date` ordering for
  C17's display — see below.**
- **Infra note:** the GAE/PELT pipeline was found to hang at 0% CPU when run from a thread or a
  `ProcessPoolExecutor` inside the `uvicorn` process on this specific dev machine — reproducible
  only in that hosting context. Worked around by running Phase B and Process as a genuine separate
  `subprocess.Popen` (`web_demo/backend/pipeline_worker.py`).

### 6.2 Six fix rounds

| Round | Bug / decision | Root cause / resolution |
|---|---|---|
| 1 | Panel auto-closed after a few seconds / on scroll | Session-polling `useEffect` misread expected 404s (no backend session yet) as "the session disappeared," closing the panel. Fixed: poll gated on `hasSession`, not `panelMode`. |
| 1 | Panel pushed/resized the Database table instead of overlaying it | `main` was a shared-width flex row (table `flex-1` + panel `w-[420px] shrink-0`) — a real layout partner, not an overlay. Fixed: panel changed to `absolute top-0 right-0 bottom-0` anchored to `main`'s right edge (`z-30`); table reverted to plain full-width block flow. **This layout change is what indirectly exposed round 6's pre-existing Header bug** — see below. |
| 2 | PROCESS button never enabled once every file showed ✕ | `upload_manager.py`'s `ready_to_process` incorrectly required `phase_b_done` — an internal computation-ordering concern that SPEC §5.5 never says should gate the *button*. Fixed: gate is upload-completion only; clicking PROCESS itself waits for Phase B behind the existing full-panel loading state before running PELT. Traced and explicitly ruled out as a round-1 regression. |
| 3 | *(author decision, not a bug)* Unlock Project ID/Memo for editing at any time, not just pre-upload | Upload storage was keyed by the literal Project ID text — a moving target once editable. Fixed: session keyed by an internal immutable `session_id`; files land in `_draft_{session_id}/`, only relocated to `uploads/{project_id}/` once PROCESS validates the (possibly-edited) ID against the allowlist **and** Phase B has fully finished. Verified with both a rejection and a subsequent successful correction. |
| 4 | Minimize → restore silently reverted any Project-ID/Memo edits back to the session's original value | `CreateNewPanel` was fully unmounted on minimize, destroying local React state; restoring remounted a fresh instance whose one-shot hydration effect fired again and overwrote the edit. Fixed: `CreateNewPanel` now stays mounted for the panel's entire open/minimized lifetime; a `hidden` prop toggles visibility instead of unmounting. |
| 4 | *(author decision, reversing an earlier explicit agreement)* Add a confirmation dialog to × | Reused `ConfirmDialog.jsx`. Wording: *"Discard this draft? Any uploaded files and progress will be lost."* Shown only when there's real content to lose (non-empty Project ID/Memo, or ≥1 file) — a completely blank panel still closes instantly. |
| 4 | *(author decision)* Remove the progress bar from the Processing / Upload-Complete states | `SZSCAN_DESIGN_v2.md §8`'s "no fake %" rule already argued against an animated bar with no real signal behind it; author chose outright removal over a real (coarse, file-count-based) alternative. **`UI/A2a`/`A2b` mockups do show a bar — this is a deliberate, recorded departure from the mockup.** |
| 4 | Font mismatch flagged by author on the Processing panel | Investigated, not reproduced: `getComputedStyle()` confirmed `Inter, sans-serif` was already correctly applied via inheritance. No code change made. |
| 5 | *(verification, no bug found)* Malformed/wrong-channel upload rejection (A1) | Confirmed already correct — `pipeline_demo.py` raises `UnsupportedEdfError`, caught and surfaced verbatim as `File rejected — unsupported format or channel configuration.`. Proved live with a genuinely corrupted EDF (truncated real header), not just a renamed text file. |
| 5 | *(verification, no bug found)* Single-subject concurrency lock (A2) | Confirmed already correct — `upload_manager.py`'s single module-level `_current` slot blocks a second `start_session` with the exact `UI/A1d` message. Proved live with a real DOM click timed via JS against a confirmed `processing: true` backend state, since the short test recordings process too fast for screenshot-paced clicking to reliably land in the window. |
| 5 | *(author decision, C17)* "Start date" column changed from absolute date to `Recording N, HH:MM:SS` | CHB-MIT/PhysioNet applies a fixed per-patient date shift for de-identification — ordering, time-of-day, and spacing between recordings stay meaningful within one subject, but the absolute year (e.g. 2075) has no meaning and is a real risk of an awkward defense-day question. Fixed in `db.py` only: N computed by sorting each subject's files on `meas_date` ascending (display-only ordering) — confirmed **separate from and non-disruptive to** the filename-based event-offset assignment (SPEC §1.5). Proved against a genuine ordering mismatch: `chb03_24.edf`/`chb03_25.edf`, where filename order and `meas_date` order disagree — `chb03_24` correctly showed **Recording 2** despite its lower filename number. `SZSCAN_SPEC_v5.md §5.1` amended accordingly by the author, with a footnote explaining the PhysioNet date-shift reasoning. |
| 6 | Avatar dropdown's "Log out" button rendered hidden/unclickable | Pre-existing `Header.jsx` bug (present since Step 2, never actually click-tested before — only visually mockup-compared), only became *visible* after round 1's layout change gave `main` a `position: relative` stacking context. With both the dropdown and `main`'s subtree at `z-index: auto`, CSS paints by DOM order — `main` comes after `<Header>` in the JSX tree, so it painted on top wherever the two overlapped on screen. Confirmed identical failure on a completely fresh page load (Create New never opened), ruling out `CreateNewPanel` as the cause. Fixed with one line: explicit `z-50` on the dropdown. |

### 6.3 Verified by Boti himself, live in a real browser (not just Claude Code's own checks)

- Full create → upload → Process → subject-appears-in-table cycle, multiple times, multiple real
  allowlisted subjects, with 1 file and with multiple files.
- Minimize/restore preserves in-progress edits, both with and without files already uploaded.
- × discard confirmation — correct wording, only appears when there's real content to lose.
- Progress bar gone from both Processing and Upload-Complete states.
- Search (partial match, button-triggered, not per-keystroke) — filters correctly, `No results
  for '...'` on miss.
- Delete — subject-level confirmation dialog works and actually deletes; selecting a **child file
  row** and clicking Delete correctly does nothing (per SPEC §5.6).
- Open — correctly shows the "isn't implemented yet (Step 4)" stub (now to be replaced by a real
  Analysis screen in Step 4).
- Allowlist enforcement at PROCESS-click time — confirmed with multiple different invalid IDs
  rejected with the exact toast, and correction-then-retry succeeding each time. **This rejection
  behavior is intentional, not a bug.**
- `Recording N, HH:MM:SS` (C17) renders correctly across multiple real subjects, no absolute year
  anywhere.
- Avatar → Log out → back to Login screen — works end-to-end.

### 6.4 Final verified state

- `pytest web_demo/backend/tests/test_guards.py -v` → 4 passed (raw console, confirmed by Boti,
  independently, after **every one** of the 6 fix rounds).
- `git status` clean outside `web_demo/` except pre-existing, confirmed-unrelated Project #1 /
  report-writing edits (`docs/*.md`, `src/figures/*.py`, `tables/tables_ch2.md`) — all explicitly
  confirmed by the author as his own work in a different project, not touched by any Step 3 round.
- Nothing under `web_demo/UI/` ever showed as modified across any round.
- Five real subjects deliberately left in the DB for Step 4 to reuse without re-uploading: `chb06`,
  `chb13`, `chb15`, `chb14`, `chb16` (see §1's "where to resume" note).

---

## 7 · Integrity incident (from Step 1) — status: resolved, cause still unconfirmed

During the Step 1 filter-optimization work, `web_demo/UI/Annotaiton (format_ ID-summary.txt).png`
(a locked mockup) was modified (`git diff --stat` showed `Bin 103048 -> 103996 bytes`). Reverted via
`git checkout`, confirmed clean at the time.

**Root cause never confirmed.** No further leads. **Not re-investigating further** — but the
mitigation (explicit "never write to UI/, copy to scratch first" instruction in every prompt since)
has held up cleanly across Step 2's 4 rounds and Step 3's 6 rounds with zero recurrence, which is the
practically important outcome even without a root cause.

---

## 8 · Report material for Project #1 (per `PROJECT2_SETUP.md §9.2(D)`)

End-to-end runtime measured = **9.76 s/hour of EEG** (Step 1, with the noted run-to-run variance
caveat, not re-measured since).

**Operating point (O1) is now implemented and demonstrated working** — a real, label-free,
per-subject FP-budget calibration example exists (`chb06`, `pen_mult=2.0` → 28.76 events/day against
the 40/day balanced target; full grid in `CC_STEP3_REPORT.md`).

Still open: **O4b** (post-ictal flagging extent — needs Analysis-screen-level visual review of events
against known seizure timing, Step 4+) and a **formally cataloged set of app screenshots** for report
use — real screenshots exist informally from Steps 2–3's testing but haven't been organized/captioned
for direct report inclusion yet.

Note: C17 (the `Recording N` display decision, §6.2 round 5) is a pure demo-UX/display decision — it
does not touch the model, pipeline, or any scientific result, so it does **not** need to be routed to
the advisor per `PROJECT2_SETUP.md §9.2(C)` (that channel is for divergences from the thesis
*method*, which this isn't).

---

## 9 · Open items before / going into Step 4

- [ ] Commit hygiene: keep splitting `web_demo/` commits from `docs/`/`tables/`/`src/figures/`
      commits going forward.
- [ ] Organize existing screenshots (Login, Database, Create New flow) for report use — no new
      screenshots needed, just cataloging (see §8).
- [ ] Step 4 itself: prompt being drafted next. Scope per `DEMO_BUILD_HANDOFF.md §6` row 4 —
      Analysis screen: Panel EEG + toolbar + scrub, **no events yet** (mini-timeline/Panel
      Event/attribution are Step 5+). Compare against `UI/B1a`, `B1b`, `B1d`. This step is
      canvas-rendering-heavy with real technical subtlety (18.6M points/file, must not ship to the
      browser undecimated — see `DEMO_BUILD_HANDOFF.md §5`). Given Step 3 took 6 rounds specifically
      because visual/interactive bugs don't show up in curl tests, use `claude-in-chrome` from round
      1 of Step 4 onward.
