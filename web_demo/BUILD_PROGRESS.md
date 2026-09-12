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
| 2 — Log in + empty Database + footer | **DONE** | took 4 fix rounds past the initial build — see §5 below, read it before starting Step 3 |
| 3-8 | not started | |

**Where to resume:** start Step 3 per `DEMO_BUILD_HANDOFF.md §6` row 3 — Create new → upload →
Process → subject appears in the table. No open blockers carried over from Step 2 (see §8).

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
├── UI/                          (pre-existing, locked PNGs + Logo.png — see §6, still clean)
├── CC_STEP0_PROMPT.md           Step 0 build prompt
├── CC_STEP1_PROMPT.md           Step 1 build prompt
├── CC_STEP1_FILTER_OPT_PROMPT.md   Step 1 follow-up: filter-cost optimization
├── CC_STEP2_PROMPT.md           Step 2 initial build prompt
├── CC_STEP2_FIX_PROMPT.md       Step 2 fix round 1 (logo + header, first attempt)
├── CC_STEP2_FIX2_PROMPT.md      Step 2 fix round 2 (numeric header target + logo re-check)
├── CC_STEP2_FIX3_PROMPT.md      Step 2 fix round 3 (LoginScreen logo source + favicon) — closed it out
├── CC_STEP2_FIX3_REPORT.md      Claude Code's written report for round 3 (first time using a
│                                 file instead of terminal output — worked well, adopt going forward)
├── backend/
│   ├── .env                     real dev credentials, gitignored (see §5.1)
│   ├── .env.example
│   ├── main.py                  FastAPI app — auth endpoints + /api/subjects, implemented Step 2
│   ├── pipeline_demo.py         Step 1 — process_file() + CLI, unchanged since Step 1
│   ├── db.py                    SQLite schema for subjects/files, implemented Step 2 (schema only)
│   ├── export_txt.py            still a stub (Step 8 scope)
│   └── tests/
│       └── test_guards.py       all 4 guards, reconfirmed PASS at the end of Step 2 (see §5.5)
└── frontend/                    Vite + React + Tailwind
    ├── src/screens/LoginScreen.jsx      implemented Step 2
    ├── src/screens/DatabaseScreen.jsx   implemented Step 2 (empty state only, per scope)
    ├── src/components/Header.jsx        implemented Step 2, went through 3 fix rounds — see §5.2-5.4
    ├── src/assets/logo.png              real logo asset (copied from UI/Logo.png, byte-verified)
    ├── public/favicon.png               added in Step 2 round 3, not spec-required, quick polish
    └── (design-tokens.js, tailwind.config.js, etc. — unchanged since Step 0)
```

**Git hygiene note (new, from Step 2):** a `LoginScreen.jsx` fix got swept into an unrelated
Project #1 commit (`cad708e`, "caption sheet revision 2 and the final exhibit list") at some point
— harmless content-wise (confirmed correct), but it blurs the `web_demo/` vs `docs/` ownership
line from `PROJECT2_SETUP.md §9.1`. **Going forward: commit `web_demo/` changes and `docs/`/report
changes separately, never in the same `git add .`.**

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
by Boti, not a summary from Claude Code. Standing verification method for every step since.

**Final verified state:** `pytest web_demo/backend/tests/test_guards.py -v` → 4 passed (raw
console, confirmed by Boti). `git status` clean.

---

## 4 · Step 1 — detail

**Scope:** `pipeline_demo.py`'s `process_file()` only — SPEC §1.3 stage 1. `process_subject()` /
PELT / operating point explicitly NOT in scope (later step).

**Implementation reviewed in full against `SZSCAN_SPEC_v5.md §1.3`** — checkpoint sha256 verified
before load, 18-channel select, window+filter with no artifact rejection (per §1.6a), z-score
per-channel (file-level for now — **`# TODO(step3)`**, SPEC wants subject-level), adjacency via
manual `apply_car → wpli/aec → combine → topk` (not `build_adjacency()`, which is fixed-threshold),
band powers, GAE forward batched, `zlatent` via `LedoitWolf` (same **`# TODO(step3)`** file-vs-subject
caveat), `zgamma` via continuous call to `compute_gamma_scores_batch`, robust-z per branch, ensemble
via `build_ensemble_subset(..., subset=CANDIDATES["rlg"])`.

**Two open `# TODO(step3)` markers** — z-score stats and LedoitWolf fit are per-file, SPEC intends
per-subject. **Still unresolved, carry into Step 3** (see §8).

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
   content-correctness check.** Any future prompt asking an agent to "add file X" should also ask
   it to check whether a file already sits at that exact path and, if so, diff/compare content
   before assuming its own edit is needed.
2. **Round 2** (Cursor Agent, free tier) was tried specifically because it has a built-in browser +
   screenshot tool (`browser_take_screenshot`) that Claude Code's CLI session lacked — a legitimate
   capability-based tool choice, not habit. It hit its free usage limit mid-task and made **zero**
   file changes (confirmed via `git diff --stat` showing only unrelated Project #1 report-figure
   renames). Lesson: Cursor's free tier is not reliable for a multi-step agentic task; if reusing it
   later, budget for hitting the limit, or use it only for short, single-shot requests.
3. Manually diagnosed with `cp` + `cmp` (byte-level file comparison) instead of trusting further
   AI self-reports — confirmed the asset file itself was now correct, but the **Log in screen**
   still rendered the old icon.
4. **Round 3** (`CC_STEP2_FIX3_PROMPT.md`) investigated properly (`grep` first, report findings
   before editing) and found `LoginScreen.jsx` had *already* been fixed to use the correct asset —
   but that fix had been swept into an unrelated Project #1 commit (see the git hygiene note in
   §2) and was never visually re-verified after. Final pixel-crop comparison against the actual
   `Logo.png` file confirmed both the Database header and Log in screen now render the correct
   mark.

**Process lesson also adopted from this saga:** starting with round 3, prompts ask Claude Code to
write its final report to a `.md` file (`CC_STEP2_FIX3_REPORT.md`) instead of printing to the
terminal — an earlier round's report got cut off mid-way in the terminal's scrollback and lost the
first two sections. **Use this for every future step's fix/report prompts.**

### 5.4 Screenshot-comparison methodology note

Comparing "header as % of screenshot height" across rounds produced one confusing measurement
(30.7%) that turned out to be an artifact of one screenshot including the full browser chrome
(tabs/address bar/bookmarks) while earlier ones didn't. **When pixel-comparing future screenshots
against mockups, always first identify and exclude browser chrome, or use a chrome-independent
ratio (e.g. header height ÷ avatar diameter) instead of raw % of image height.**

### 5.5 Final verified state

- `pytest web_demo/backend/tests/test_guards.py -v` → **4 passed** (raw console, confirmed by Boti,
  after all Step 2 rounds — this is the most recent guard confirmation as of this writing).
- Logo on both Database header and Log in screen pixel-confirmed identical to `web_demo/UI/Logo.png`
  (crop-compared directly, not eyeballed).
- Favicon confirmed visible/legible in the browser tab.
- Nothing under `web_demo/UI/` ever showed as modified across any of the 4 rounds — the "never
  write to UI/, copy to scratch to view" instruction held up in practice throughout, even though
  the original Step 1 PNG-modification incident's root cause (see §6) is still unknown.

---

## 6 · Integrity incident (from Step 1) — status: resolved, cause still unconfirmed

During the Step 1 filter-optimization work, `web_demo/UI/Annotaiton (format_ ID-summary.txt).png`
(a locked mockup) was modified (`git diff --stat` showed `Bin 103048 -> 103996 bytes`). Reverted via
`git checkout`, confirmed clean at the time.

**Root cause never confirmed.** Asked again explicitly in `CC_STEP2_PROMPT.md`'s side-note; Claude
Code's answer: it has no visibility into the prior (Step 1) session's tool calls and can't say what
touched the file. No further leads. **Not re-investigating further** — but the mitigation (explicit
"never write to UI/, copy to scratch first" instruction in every prompt since) has held up cleanly
across all of Step 2's 4 rounds with zero recurrence, which is the practically important outcome
even without a root cause.

---

## 7 · Report material for Project #1 (per `PROJECT2_SETUP.md §9.2(D)`)

Unchanged from Step 1: end-to-end runtime measured = **9.76 s/hour of EEG** (with the noted
run-to-run variance caveat). The other three blanks (post-ictal flagging extent / O4b, demo's
operating point / O1, actual app screenshots) are still open — O4b and O1 need `process_subject()` /
PELT (Step 3+). **Real app screenshots are now available** (Step 2's Log in and Database screens) —
worth flagging to Project #1 as usable report material if screenshots of a working screen are
wanted before the full app is done.

---

## 8 · Open items before / going into Step 3

- [ ] Resolve the two `# TODO(step3)` markers in `pipeline_demo.py` (z-score stats and LedoitWolf
      fit currently per-file, SPEC wants per-subject) — this is explicitly Step 3 scope now that
      real multi-file subject upload is being built.
- [ ] Commit hygiene: separate `web_demo/` commits from `docs/`/report commits going forward (see
      §2) — no urgent cleanup needed, just don't repeat the mix-up.
- [ ] If a visual-heavy sub-task comes up in Step 3+ (unlikely — Step 3 is mostly upload/state
      logic, not layout-heavy) and Cursor's browser-verification tool seems worth it again, check
      Cursor's usage-limit reset or Pro status first — don't assume free-tier quota is available.
- [ ] Step 3 itself: prompt not yet written. Scope per `DEMO_BUILD_HANDOFF.md §6` row 3 + SPEC §5.5:
      Create new panel, file upload with per-file status icons, two-stage processing
      (`process_file` on upload, `process_subject`/PELT on "Process" click — **PELT/operating point
      not built yet, this is where O1/O2 from SPEC §8 first become unavoidable**), single-subject
      concurrency lock, minimize-to-toast behavior. This is a substantially bigger step than Step 2
      — plan for it to need its own careful read of SPEC §5.5 in full before drafting the prompt.
