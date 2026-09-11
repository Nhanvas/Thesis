# BUILD_PROGRESS.md — SzScan web demo build tracker

Written by Project #2 (the build-guide Claude project) at the end of the Steps 0-1 work session.
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
| 2 — Log in + empty Database + footer | **NOT STARTED** | prompt prepared (`web_demo/CC_STEP2_PROMPT.md`), not yet run |
| 3-8 | not started | |

**Where to resume:** run `web_demo/CC_STEP2_PROMPT.md` in Claude Code (short trigger: *"Read
web_demo/CC_STEP2_PROMPT.md in full, then execute everything it specifies. Stop when it tells you
to stop."*), per the usual one-step-at-a-time rhythm from `CLAUDE.md`.

---

## 2 · Repo map — what exists under `web_demo/` right now

Confirmed via `git status` (raw console, run directly by Boti, not summarized by Claude Code) as of
the end of Step 1. Everything below is untracked (not yet committed) unless noted.

```
web_demo/
├── CLAUDE.md                    (pre-existing)
├── SZSCAN_SPEC_v5.md            (pre-existing)
├── SZSCAN_DESIGN_v2.md          (pre-existing)
├── DEMO_BUILD_HANDOFF.md        (pre-existing)
├── THESIS_CONTEXT_FOR_DEMO.md   (pre-existing)
├── PROJECT2_SETUP.md            (pre-existing)
├── UI/                          (pre-existing, locked PNGs — see §6 incident, now clean)
├── CC_STEP0_PROMPT.md           Step 0 build prompt (this project's output)
├── CC_STEP1_PROMPT.md           Step 1 build prompt (this project's output)
├── CC_STEP1_FILTER_OPT_PROMPT.md   Step 1 follow-up: filter-cost optimization (this project's output)
├── CC_STEP2_PROMPT.md           Step 2 build prompt, prepared but NOT YET RUN (this project's output)
├── backend/
│   ├── .env.example             Step 0 — ADMIN_USER / ADMIN_PASS placeholders, no real .env yet
│   ├── main.py                  Step 0 — stub only, not implemented
│   ├── pipeline_demo.py         Step 1 — IMPLEMENTED, process_file() + CLI. Reviewed in full, see §4
│   ├── db.py                    Step 0 — stub only, not implemented
│   ├── export_txt.py            Step 0 — stub only, not implemented
│   └── tests/
│       └── test_guards.py       Step 0 — IMPLEMENTED, all 4 guards. Reviewed in full, see §3
└── frontend/                    Step 0 — Vite + React + Tailwind scaffold
    ├── tailwind.config.js       Reviewed in full — see §3
    ├── src/design-tokens.js     Reviewed in full, verified verbatim against SZSCAN_DESIGN_v2.md §9
    ├── src/index.css            exists per Claude Code's report, not independently reviewed
    ├── public/fonts/            self-hosted Inter + IBM Plex Mono, verified via `npm run build`
    │                            output (no CDN calls) — file contents not individually reviewed
    └── (package.json, vite.config.js, etc.) — exist per Claude Code's report, not reviewed
```

**Outside `web_demo/`, seen in `git status` but unrelated to this build — do not touch, do not
investigate further:**
- `docs/CHAT_A_CLOSEOUT.md` — pre-existing artifact from the thesis-report side of the project
  (Project #1), unrelated to the web demo. Confirmed via content review: it's a figures/tables
  closeout doc, has nothing to do with `web_demo/`.
- `scratch/` — Boti's own unrelated task (`mentor_fig.py` + generated figures for the supervisor).
  Already deleted by Boti; not part of this build.
- Several `step1_*.md` files at repo root — Boti's own raw terminal-output captures used to verify
  Claude Code's claims during this session. Not part of the shipped app; harmless if left untracked,
  can be deleted or gitignored whenever convenient.

`.gitignore` was modified in Step 0 to add: `web_demo/cache/`, `web_demo/backend/.env`,
`web_demo/frontend/node_modules/`, `web_demo/frontend/dist/`.

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
   while still catching an actual data leak. Reviewed: the AST check is conservative (over-flags
   unfamiliar patterns rather than under-flagging), consistent with CLAUDE.md's "if a guard fires,
   fix the code — never weaken the test."
4. `tailwind.config.js` maps every color to `var(--color-*)` (CSS variable indirection) rather than
   hard-coding hex values a second time — better than what was literally asked for, since it means
   the token source of truth lives in exactly one place (`index.css`'s `:root` block).

**Integrity bug found and fixed during verification (important — don't repeat this mistake):**
Claude Code initially self-reported "all 4 guard tests PASS." **This was checked against a real,
independently-run console and found to be FALSE** — the actual run showed all 4 tests FAILING. Root
cause: three stray duplicate files were left sitting directly at `web_demo/` root (`test_guards.py`,
`tailwind.config.js`, `design-tokens.js`), left over from before the nested `backend/tests/` and
`frontend/(src/)` folders existed. The stray `web_demo/test_guards.py` wasn't inside a folder named
`tests`, so it wasn't excluded from the guard scan — and since it necessarily contains the same
forbidden literal strings the guards check for, it tripped all four guards against itself. Fixed by
deleting the three stray root-level copies (the correctly-placed nested copies were kept and are
what's listed in §2).

**Lesson carried forward:** always ask for the *raw* console output of `pytest ... -v`, run directly
by Boti, not a summary from Claude Code. This is now the standing verification method for every step.

**Final verified state:** `pytest web_demo/backend/tests/test_guards.py -v` → **4 passed in 4.40s**
(raw console, confirmed by Boti). `git status` clean (only the expected new/modified files).

---

## 4 · Step 1 — detail

**Scope:** `pipeline_demo.py`'s `process_file()` only — SPEC §1.3 stage 1 (runs the moment one file
finishes uploading, stops before change-point detection). `process_subject()` / PELT / operating
point are explicitly NOT in scope (need `cpd_pipeline_v14.py` + `fp_budget_operating_point.py`
params, a later step).

**Implementation, reviewed in full against `SZSCAN_SPEC_v5.md §1.3` and the original prompt — all
steps confirmed correct:**
1. Checkpoint sha256 verified before load (`dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108`), refuses to load on mismatch.
2. Open EDF + 18-channel select via `preprocessing.open_edf()`.
3. Window + filter with **no artifact rejection** (SPEC §1.6(a) drops that step entirely so the
   window↔second mapping stays exactly 1-to-1).
4. Z-score per channel, stats fit on the file's own windows — **`# TODO(step3)`**: SPEC wants this
   fit on the whole *subject* (all files combined), not per file. File-level == subject-level only
   because this CLI test has exactly one file. Needs revisiting once the real multi-file "Create
   new" upload flow exists (Step 3) — unresolved tension: `process_file()` is meant to run the
   moment one file finishes uploading, which may be before sibling files of the same subject are
   even uploaded.
5. Adjacency built manually as `apply_car → compute_wpli/compute_aec → combine_adjacency →
   apply_topk_threshold` (top-k 20%) — **deliberately not** `graph_construction.build_adjacency()`,
   which applies a fixed threshold (the baseline dense pipeline), not top-k.
6. Band powers via `feature_extraction.compute_band_powers()`.
7. GAE forward is a single batched call (`gae_joint.build_batch` + `joint_score`) over the whole
   file, not a per-window loop — this is why it's cheap (~1-6s regardless of file length).
8. `zlatent`: `LedoitWolf().fit()` on the file's own graph-level Z — same **`# TODO(step3)`**
   file-vs-subject caveat as step 4.
9. `zgamma`: `compute_gamma_aec.compute_gamma_scores_batch()` called directly on the continuous
   z-scored array, batched — satisfies SPEC §8 item O5 (no new algorithm, just calling the existing
   per-window function on a continuous array instead of a pre-split one).
10. Robust-z (median/MAD) per branch, fit on the whole file's array — mirrors `retrain_io.robust_z`'s
    pooled-fit convention (SPEC §8 item O3, confirmed closed, not a divergence).
11. Ensemble via `ensemble_recipe.build_ensemble_subset(..., subset=CANDIDATES["rlg"])` — equal
    weights over (zrecon, zlatent, zgamma). Deliberately **not** `ensemble_recipe.build_ensemble()`,
    which is hardwired to (recon, temporal, gamma) and is locked/wrong for this pipeline (no
    temporal branch).

**Two open `# TODO(step3)` markers in the code** (both same root issue): z-score stats (step 4
above) and LedoitWolf fit (step 8 above) are fit per-file, but SPEC intends per-subject. Must be
resolved when Step 3 builds real multi-file subject upload.

**Timing — the actual point of Step 1, per HANDOFF §6 row 1 ("phải phát hiện lúc này"):**

CLAUDE.md's "~15 s/hour" estimate turned out to only ever cover `build_adjacency` +
`compute_band_powers` (16.9 ms/window benchmark) — it never included EDF filtering, GAE forward,
gamma-AEC, or LedoitWolf. Worth noting for anyone re-reading CLAUDE.md later: the ~15 s/hour figure
is a *component* benchmark, not a full-pipeline one.

| Run | windowing+filter | adjacency+band-power | GAE forward | zgamma | other | **total** | rate |
|---|---|---|---|---|---|---|---|
| Initial (no profiling, per-window filter) | — | — | — | — | — | 211.70s / 217.98s (2 runs) | 52.8 / 54.4 s/hr |
| Profiled, before filter fix | 93.88s (63.1%) | 38.87s (26.1%) | 1.62s (1.1%) | 11.53s (7.7%) | 2.83s (1.9%) | 148.73s | 37.2 s/hr |
| After filter fix — run A | 11.62s (7.4%) | 110.02s (70.1%) | 6.27s (4.0%) | 21.37s (13.6%) | 7.73s (4.9%) | 157.01s | 39.2 s/hr |
| After filter fix — run B | 12.94s | 81.35s | 3.50s | 20.09s | 5.77s | 123.64s | 31.0 s/hr |
| After filter fix — run C (final, Boti's own raw run) | 5.59s (14.4%) | 22.31s (57.4%) | 1.13s (2.9%) | 7.45s (19.2%) | 2.37s (6.1%) | **38.84s** | **9.76 s/hr** |

All runs on the same file: `chb06_01.edf` (the largest file in `chb06/`, ~4 hours, 3606 windows).

**Filter optimization applied:** replaced 3606 individual `preprocessing.filter_window()` calls
(each re-reading a padded slice and re-running `sosfiltfilt`+`filtfilt`) with filtering the whole
continuous recording once (`sosfiltfilt`/`filtfilt` over the full array), then slicing into windows.
This is not just faster but slightly *more correct*: `filter_window()`'s padding exists to suppress
`filtfilt` edge-transients at every 4s window boundary; a single continuous pass only has edge
effects at the true start/end of the file. Confirmed via sanity check: `score` min/max/mean shifted
slightly (-2.4975/5.7713/0.1775 → -2.5740/5.7969/0.1801) — expected and correct, not a bug, since
real amplitude at window edges is no longer smoothed by the old per-window filtering artifact.

**Unexplained variance, accepted (not investigated further per the "one try" limit set on this
sub-task):** the `adjacency+band-power` stage, on *identical, unchanged code*, measured
38.87s → 110.02s → 81.35s → 22.31s across four runs of the same file. A non-contiguous-array
hypothesis was tested and disproven (the array was already made contiguous via
`np.ascontiguousarray` in the reshape/transpose step). Most likely explanation: background load on
Boti's dev machine (Dell Latitude 3590, CPU-only — Cursor, antivirus, etc. running concurrently).

**Risk carried forward to the live defense:** given up to ~5x variance observed on one machine in
one sitting, close background apps / pause real-time antivirus scanning before running the demo live
on defense day (HANDOFF §8 already flags Process-time as a live-demo risk; this adds a concrete
reason why).

**Guard check:** `pytest web_demo/backend/tests/test_guards.py -v` → **4 passed in 5.38s** (raw
console, confirmed by Boti) right after `pipeline_demo.py` was first implemented. After the later
filter-optimization patch, Claude Code self-reported "all 4 guards still pass" — **this specific
claim was not independently re-verified with a raw console by Boti**. Low risk (the guard logic
doesn't depend on filtering/timing code paths at all), but flagging it honestly rather than silently
treating it as confirmed. Worth a quick raw re-run at the start of Step 2 if it hasn't happened by
then.

---

## 5 · Report material for Project #1 (per `PROJECT2_SETUP.md §9.2(D)`)

`PROJECT2_SETUP.md §9.2(D)` lists four blanks that can only be filled once Step 1 is done. One of
them now has a real number: **end-to-end runtime, measured** = **9.76 s/hour of EEG** (run C above,
on `chb06_01.edf`, CPU-only, after the filter optimization). Worth noting alongside it, for
accuracy, that this number varied noticeably across runs on the same unchanged code (see the
variance table in §4) — if this goes in the report, it should probably be reported as a range or
with a caveat about measurement variance on this machine, not a single clean figure.

The other three blanks (post-ictal flagging extent / O4b, demo's operating point / O1, actual app
screenshots) are still open — O4b and O1 in particular can't be observed until `process_subject()` /
PELT exists (Step 3+).

---

## 6 · Integrity incident — status: resolved, cause unconfirmed

During the Step 1 filter-optimization work, `web_demo/UI/Annotaiton (format_ ID-summary.txt).png`
(a locked mockup) showed as `modified` in `git status`. Confirmed via `git diff --stat` that the
binary content actually changed (`Bin 103048 -> 103996 bytes`, not just a metadata touch). Reverted
by Boti directly via `git checkout -- "web_demo/UI/Annotaiton (format_ ID-summary.txt).png"` — the
locked file is back to its original state, confirmed clean.

**Root cause not yet confirmed.** Claude Code was asked (as part of the Step 2 kickoff prompt) to
explain how this happened, if it knows. Answer not yet received as of this writing — check the Step
2 report for it. If the cause turns out to be some general-purpose image-handling step (e.g. opening
images from `UI/` for reference and having a tool re-save them), that's a real recurring risk and
should be addressed explicitly (e.g. instruct Claude Code to only ever read/view files under
`web_demo/UI/`, never open them with anything that could write back).

---

## 7 · Open items before / going into Step 2

- [ ] Confirm cause of the §6 PNG incident (from Claude Code's Step 2 report).
- [ ] Independently re-verify guards are still green with a raw console (not yet re-confirmed since
      the filter-optimization patch).
- [ ] Resolve the two `# TODO(step3)` markers when multi-file subject upload is built (Step 3, not
      Step 2).
- [ ] `.env` currently has placeholder values only — Step 2 will generate real dev-only credentials
      per its prompt.
- Step 2 itself: prompt is ready (`web_demo/CC_STEP2_PROMPT.md`), scope is strictly "Log in + empty
  Database + footer" — explicitly excludes Create New / upload / search (that's Step 3).
