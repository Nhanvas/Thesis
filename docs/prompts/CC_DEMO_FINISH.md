# CC_DEMO_FINISH — finish SzScan on the final system and run it on the 8 test patients (2026-10-12)

**For:** Claude Code on the author's laptop, started in `F:/Study/Thesis/Code`.
**Estimated runtime (not measured): 5–9 h in total**, most of it Stage 5 (the application run over
~280 h of EEG). It is meant to run overnight. Stop rules are strict: when one fires, stop, write the
handback file (Stage 8) with what happened, and do nothing else.

## Read first (in this order)

1. `web_demo/CLAUDE.md` (rev 2026-10-10): guards, model identity, parameter rules. **Binding.**
2. `docs/HANDOFF_T1_DEMO_REBUILD.md` §2–§7: the final system, the work plan, the interface contract,
   what the report needs back (R1–R8).
3. `web_demo/CC_T1_RUN_REPORT.md`: what was already done (backend rebuilt and committed as `936b8e0`,
   tags `szscan-frozen-v3`, `demo-final-v1`; 11/11 tests green). Then `results/t1_demo/GATE.md`
   (identity gate PASS on chb03) and `results/t1_demo/TIMING.md` (median 21.68 s per hour of EEG).

Do not re-do what those files show as done.

## Ground rules

- Never read seizure annotations from application code; never weaken `test_guards.py`; never hardcode a
  parameter (read `results/p3c_freeze/freeze.json` and the checkpoint `.json`).
- Never edit `src/`, `docs/`, `data/` or any committed result. Thesis-side scripts in `src/` are **run**,
  not edited. You write inside `web_demo/`, `results/application_eval_v4/` (only through
  `src/t1_app_tier.py`) and `F:/Study/Thesis/Reports/v8/figures/app_screens/`.
- Archive, never delete. Stage explicit paths; never `git add` a whole directory that can hold unrelated
  work (`bme11/` is unrelated and must not be touched).
- Memory: the laptop has 16 GB. Before Stage 5, check free memory; if Chrome, Edge or Cursor are running,
  **stop and ask the author to close them** (chb06 needs up to ~10 GB during its per-patient fit). Run
  nothing else heavy at the same time.
- No calendar dates on screen or in exports (anonymised `meas_date`).

## Stage 0 — Preconditions (5 min)

```
cd /f/Study/Thesis/Code
git status -s            # no modified TRACKED file under web_demo/ or src/ (untracked is fine)
git log --oneline -5     # 51608f5 / 936b8e0 present
git tag | grep -E "szscan-frozen-v3|demo-final-v1"
sha256sum data/models_v2/gae_v2_clean_seed42.pt data/models_v2/gae_v2_clean_seed42.json   # = CLAUDE.md
df -h /f                 # need >= 100 GB free
python -m pytest web_demo/backend/tests -q   # 11 passed
```
STOP if any check fails.

## Stage 1 — Tidy `web_demo/` (15–30 min)

The folder holds ~150 step prompts/reports and screenshot folders from earlier build rounds.
1. Create `web_demo/archive/cc_history/`. Move every `web_demo/CC_*.md` and every `web_demo/CC_*_SCREENSHOTS/`
   there (`git mv` for tracked files, `mv` + explicit `git add` for untracked ones). Also move there:
   `PROJECT2_INSTRUCTIONS.md`, `PROJECT_STATUS.md`, `REPORT_HANDBACK.md`, `REPORT_REPLY_TO_PROJECT2_2.md`,
   `REPORT_REPLY_TO_PROJECT2_3.md`, `REPORT_REQUEST_TO_PROJECT2.md`, `spec_docs_diff.md`,
   `backend/uvicorn.log`. Keep at top level: `CLAUDE.md`, `SZSCAN_SPEC_v5.md`, `SZSCAN_DESIGN_v2.md`,
   `DEMO_BUILD_HANDOFF.md`, `BUILD_PROGRESS.md`, `THESIS_CONTEXT_FOR_DEMO.md`, `SPEC_C29_AMENDMENT.md`,
   `STEP8_9_PREDEFENSE_CHECKLIST.md`, `PROJECT2_SETUP.md`, `UI/`, `backend/`, `frontend/`, `report_handback/`, `archive/`.
2. Grep the kept docs for paths into the moved files and fix those references.
3. Update the stale docs listed in `docs/HANDOFF_T1_DEMO_REBUILD.md` §1 so they no longer describe the
   earlier system as current (a short "superseded by the final system, see CLAUDE.md" note plus the
   corrected facts is enough; SPEC §1.6 becomes the one-item divergence of HANDOFF_T1 §4).
   `BUILD_PROGRESS.md` gets a section "Rebuild on the final system (2026-10-10 → 10-13)".
4. Commit: `web_demo: archive build-round prompts and screenshots; docs describe the final system`.

## Stage 2 — Timeline row (HANDOFF_T1 §3.4) (15–30 min)

The score is now a patient-percentile mean in [0, 1]. **Decision (thesis project): fixed y-range [0, 1],
no reference line, no threshold line** (the threshold is an internal operating-point parameter and must
not appear in the product). Label `Seizure Detection Score` unchanged. Update SPEC §6.3 wording
(the score is a percentile mean in [0, 1], not a robust z-score). Nothing else in the UI changes.
Run the tests; commit `web_demo: timeline row for the [0, 1] ensemble score`.

## Stage 3 — Real-UI smoke test (20–40 min)

Start backend and frontend as in `DEMO_BUILD_HANDOFF.md`. Use a **temporary** database: move the
current `web_demo/backend/szscan.db` and `web_demo/backend/uploads/` to
`web_demo/_old_data_2026-10-12/` first (rename, not delete; it is the earlier application's data).
Through the real UI: Log in → Create New (chb17, the smallest test subject) → Process → open Analysis →
click an AI event → check the channel panel title `Channel-level latent anomaly — Event N` → Accept one
event → Export `.txt`. Record what you did and any error. Then stop the servers, delete only this
temporary chb17 subject **through the application's own Delete** (so the database is clean for Stage 5),
and confirm `db.list_subjects()` is empty.
STOP on any error that is not cosmetic; describe it by mechanism.

## Stage 4 — Freeze (5 min)

`git diff 936b8e0 -- web_demo/backend src` must show no change to backend logic (docs, tests unchanged or
only added). If backend logic changed: run the identity gate again
(`python src/t1_demo_gate.py gate --dataset F:/Study/Thesis/Dataset/CHB-MIT`, 30–60 min, must PASS).
Then `git tag szscan-frozen-v4`. Do not push yet.

## Stage 5 — Application run on the 8 test patients (estimated 3–6 h)

Rules (project instructions 11.5): frozen build, clean database, 8 test subjects, export **before any
review**, one run, any defect ⇒ repeat the whole run.
```
cd /f/Study/Thesis/Code/web_demo/backend
export HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 NO_PROXY=""   # network-off evidence
python batch_ingest.py --dataset F:/Study/Thesis/Dataset/CHB-MIT --all          # writes uploads/_ingest_timing.csv
python export_tier2.py --out ../report_handback/tier2_v4
cd /f/Study/Thesis/Code
python src/t1_app_tier.py --tier2-dir web_demo/report_handback/tier2_v4         # writes results/application_eval_v4/
```
Check `MANIFEST.txt` says `uncommitted changes in web_demo/backend or src: no` and names the
`szscan-frozen-v4` commit. Copy `web_demo/backend/uploads/_ingest_timing.csv` to
`results/application_eval_v4/ingest_timing.csv`.
STOP on any defect (crash, a subject with missing files, coverage issue): write it down, do not tune,
do not re-run partially.

## Stage 6 — Screenshots for the report (20–40 min)

Same method as the earlier build rounds (see `web_demo/archive/cc_history/CC_STEP7_REPORT.md`). Browser
window 1600 × 1000, full-resolution PNG, saved to `F:/Study/Thesis/Reports/v8/figures/app_screens/`:
- `a_import.png` — recording list with the Create New panel open (import view);
- `b_analysis.png` — Analysis of a chb03 file with one AI event selected, timeline row and EEG visible;
- `c_panel_review.png` — the channel panel (`Channel-level latent anomaly — Event N`) with the
  Accept / Reject / Uncertain buttons.
For (b) and (c) choose an exported chb03 event that overlaps an annotated seizure, checked outside the
application (export CSV against the CHB-MIT summary file, by you, never by application code). Reviews made for the screenshots happen **after** the export.
No calendar date on screen; no internal names.

## Stage 7 — Push (2 min)

Only if every stage passed: commit the application results and handback with explicit paths
(`results/application_eval_v4/*`, `web_demo/report_handback/tier2_v4/*`,
`web_demo/report_handback/DEMO_FINAL_HANDBACK.md`), then `git push origin main --tags`.

## Stage 8 — Handback (always, also after a STOP)

Write `web_demo/report_handback/DEMO_FINAL_HANDBACK.md`, short, with:
- R1 gate: link to `results/t1_demo/GATE.md` (and the re-run if Stage 4 needed it);
- R2 timing: `results/t1_demo/TIMING.md` + per-subject wall-clock from `ingest_timing.csv`;
- R3 application run: the per-subject table and the pooled + subject-mean lines from
  `results/application_eval_v4/SUMMARY.md`, copied, not retyped;
- R4 screenshot paths; R5 architecture boxes as built (from `CC_T1_RUN_REPORT.md` Stage 1.7, re-checked
  against the frozen code); R6 the one-item divergence paragraph; R7 network-off evidence (the proxy
  setting of Stage 5, grep for network libraries, whether the frontend loads anything from the internet,
  e.g. web fonts); R8 build commit and tag;
- every stop, deviation and runtime (measured).
