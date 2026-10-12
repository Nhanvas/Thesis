# CC_T1_RUN_ALL_PROMPT.md — everything the report needs, in one unattended run

Supersedes `CC_T1_STEP1_PROMPT.md` (do not run that one). HANDOFF_T1 steps 1 → freeze tag → 6 (gate) → 7 (timing) → 8 (application tier).

**Estimated duration:** several hours in total (estimate, not measured; handoff estimates: gate 30–60 min, timing 30–60 min,
application tier 2–4 h, plus step 1). **The laptop must stay plugged in and awake for the whole run** (disable sleep first).
Nothing else heavy may run at any time (chb06 exhausts memory). Environment for every Python run below:
`TMP`, `TEMP`, `TMPDIR` = `F:/tmp`; pagefile on `F:`.

Read first: `web_demo/CLAUDE.md` (rev 2026-10-10, wins over stale V1 text), `docs/HANDOFF_T1_DEMO_REBUILD.md` §2, §3, §5, §6,
`docs/DEMO_REBUILD_BRIEF.md`, `web_demo/THESIS_CONTEXT_FOR_DEMO.md`.

## Ground rules

- Stages run strictly in order, ONE heavy job at a time. After EACH stage append its section to
  `web_demo/CC_T1_RUN_REPORT.md` (raw command output, not a summary), so a stop leaves a usable report.
- **Any STOP condition below ends the run**: write the report, print the raw evidence, do nothing further. Never "fix and
  continue" past a stop; never re-run a single subject; never tune anything toward thesis numbers.
- Demo code writes only inside `web_demo/`. The thesis scripts in stages 3–5 (`src/t1_demo_gate.py`, `src/t1_app_tier.py`)
  write to `results/` by design; they are run exactly as written, you do not edit them. Never edit `src/`, `docs/`, `UI/`.
- Never `git add .`; commit explicit `web_demo/` paths only. No `git push` (Boti pushes). Never commit `results/`.
- Commit/tag trailers: end commit messages with
  `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_01DApMeNeryLNsMBUAaefvU4`.
- Stated numbers come from files you read. No estimates in the report.

## Stage 1 — backend on the final system (reference patch)

### 1.0 Preconditions (STOP if any fails)
```
cd /f/Study/Thesis/Code
git status -s                                        # no modified tracked files expected
git merge-base --is-ancestor f37a7b1 HEAD && echo base-ok
ls -l /f/Study/Thesis/Agent/t1_demo/t1_demo_reference.patch
sha256sum data/models_v2/gae_v2_clean_seed42.pt data/models_v2/gae_v2_clean_seed42.json   # must equal web_demo/CLAUDE.md
python -c "import torch, torch_geometric; print(torch.__version__)"                         # real-GAE test needs it; missing => STOP
df -h /f
```

### 1.1 Review the patch BEFORE applying (read-only; `git apply --stat`, then read all of it)
Checklist — any FAIL → do not apply, report, STOP:
a. No demo code CALLS a label-reading thesis function (list in `web_demo/CLAUDE.md`). Importing is fine.
b. Both checkpoint sha256 verified before load; `PD.run_model` must resolve to EXACTLY the verified `.pt` (read
   `src/p2_dump_seeds23.py` to confirm the path it loads from `MODEL_TAG`); added-feature constants come from the `.json`.
c. `stats_override` unreachable from `main.py`, `upload_manager.py`, `pipeline_worker.py`, any HTTP path.
d. Every write under `web_demo/`.
e. floor/cap, `smooth`, `k`, `localizer` read from `results/p3c_freeze/freeze.json` at runtime. Open the real file and confirm
   the keys the patch uses exist: `points["balanced"]`, `smooth`, `k`, `localizer`.
f. No budget / k / score parameter / metric returned by any API endpoint or shown in the UI. **Known finding (reviewer, before
   you):** the patch's `UploadSession.snapshot()` returns `"operating_point": {"alarm_budget": ...}` once done. Grep the
   frontend (`grep -rn operating_point web_demo/frontend/src web_demo/backend`). Remove the field from the snapshot (set the
   key to `None` or drop it) and fix any reader; the budget stays internal. Say what you changed.
g. §6 interface contract exists with the stated names and shapes (`MODEL_TAG`, `WIN_S`, `process_subject_headless`,
   `process_subject_phase_b`, `process_subject_events`, `export_tier2.py` MANIFEST lines `commit <sha>` and
   `uncommitted changes in web_demo/backend or src: no|YES`).
h. Signal loss: raw std < 1e-10 V on all 18 channels, excluded from per-subject fits, NaN distance, kept on the timeline.
i. **Signatures:** open the real source and confirm every thesis function the patch calls exists with the arguments used:
   `x1_external.{window_padded, filter_windows, labelfree_stats, file_features, make_ctx, load_18, TAGS}`,
   `c1b_build_trainset.{graph_and_bp, f7}`, `p2_dump_seeds23.run_model`, `p2_scalars.{d1_events, smoothed, pct, score}`,
   `p3_levers.{member_mean_z, q_of, localize}`, `e22_test_oneshot.final_scalar`, `e23_test_look7.evaluate`,
   `preprocessing._NOTCH_B/_NOTCH_A`. Also check that IMPORTING these modules has no import-time effect (reads of labels,
   writes outside `web_demo/`, heavy loads). A mismatch = FAIL.
j. `batch_ingest.py` uses `upload_manager.{start_session, save_upload_to_tmp, add_file, start_process, poll_tick,
   acknowledge_done, UPLOAD_DIR}` and `db.{ALLOWED_SUBJECTS, init_db, list_subjects, list_files_by_filename, list_events}`:
   confirm each exists with that signature.

### 1.2 Apply
`git am --3way <patch>` (the patch is one commit based on `f37a7b1`); on conflict `git am --abort` and STOP. Say what you used.
Do not leave the patch's own commit message as the only record: you will make ONE clean commit in 1.5 (use
`git reset --soft` to the pre-patch HEAD after the tests are green, then commit by explicit paths).

### 1.3 Panel title
`grep -rn "reconstruction anomaly" web_demo/backend web_demo/frontend/src` — the patch already changes the title string in
`AttributionPanel.jsx`; change any remaining occurrence of that title only. Nothing else in the UI changes.

### 1.4 Tests (`pytest web_demo/backend/tests -v`)
- `test_guards.py` 4/4 green, never weakened. If it fires on `web_demo/archive/backend_v1/` files: that is not a reason to edit
  the test; remove those archived V1 scripts from the commit (`git rm`; they stay in history and tag `szscan-frozen-v2`) and
  list them in the report.
- `test_final_system.py` (from the patch): in `test_runtime_label_free`, `monkeypatch.setattr` fails on attribute names that do
  not exist. Keep only names that exist in the real modules; list which you dropped. Do not otherwise soften it.
- Any other pre-existing test tied to V1 (bit-identity vs `szscan-frozen-v2`, `FIXED_*` constants, 3 median/MAD calls, V1 hash)
  is invalid by design: replace it with a final-system equivalent or, if `test_final_system.py` already covers it, move it to
  `web_demo/archive/backend_v1/tests/`. List every test changed and why.
- The real-GAE test must actually RUN (not skip) on this machine. If it skips, STOP.
- All green required before continuing.

### 1.5 Commit and tag
```
git reset --soft <pre-patch HEAD>          # only if you used git am; then:
git add <explicit web_demo/ paths>         # list them
git commit -m "web_demo: backend on the final system (GAE v2 clean seed42, per-channel latent, budget + CPD localizer)"
git tag szscan-frozen-v3
```
Local only. Then `git status -s` must show no modified tracked files under `web_demo/backend` or `src`. Write the Stage 1
section of the report: how applied, checklist a–j PASS/FAIL with file:line evidence, files changed, tests changed, RAW
`pytest -v`, `git status -s`, `git log -1 --stat`, what remains unproven on real data. **STOP if anything is red.**

## Stage 2 — identity gate (thesis script, run as written)
```
python src/t1_demo_gate.py gate --dataset F:/Study/Thesis/Dataset/CHB-MIT
```
Raw output into the report, then `cat results/t1_demo/GATE.md`. **GATE FAIL (or non-zero exit) ⇒ STOP the whole run**:
nothing further runs; the mismatch is for the thesis side to explain. Do not edit anything to make it pass.

## Stage 3 — timing (thesis script, run as written)
```
python src/t1_demo_gate.py timing --dataset F:/Study/Thesis/Dataset/CHB-MIT
```
Nothing else running. Raw output into the report, then `cat results/t1_demo/TIMING.md`. Do not interpret or compare to the
earlier system's figures.

## Stage 4 — application tier (the frozen build, a clean database, the real upload flow)

4.0 Preconditions (STOP if any fails): `df -h /f` shows ≥ 75 GB free; `git rev-parse HEAD` equals the commit of tag
`szscan-frozen-v3`; `git status --untracked-files=no -s -- web_demo/backend src` is empty; no other heavy process running.

4.1 Move the old database and uploads ASIDE (never delete): `ls`/`du` them first, then move `szscan.db` and `uploads/` to
`F:/Study/Thesis/Agent/t1_demo/aside_v2_app/` (same drive, so it is a rename). Confirm the backend directory now holds neither.

4.2 Ingest through the real flow (no browser needed; same `upload_manager` code path as Create New → Process):
```
cd web_demo/backend
python batch_ingest.py --dataset F:/Study/Thesis/Dataset/CHB-MIT --all
```
Raw per-subject lines and the TOTAL line into the report. Any error, rejected file, or STOP line ⇒ STOP: the whole 8-subject
run must be redone later from an empty database (never a single subject). Say so.

4.3 Export BEFORE any review:
```
python export_tier2.py --out ../report_handback/tier2_v4
cat ../report_handback/tier2_v4/MANIFEST.txt
```
MANIFEST must read `uncommitted changes in web_demo/backend or src: no`; otherwise STOP.

4.4 Hand-back copy and scoring (thesis script, run as written):
```
cd /f/Study/Thesis/Code
cp web_demo/backend/uploads/_ingest_timing.csv results/t1_demo/ingest_timing.csv      # R2 hand-back; verify the path first
python src/t1_app_tier.py --tier2-dir web_demo/report_handback/tier2_v4
```
Raw output into the report, then `cat results/application_eval_v4/SUMMARY.md`.

## Final report and STOP

`web_demo/CC_T1_RUN_REPORT.md` holds, per stage: the commands run, RAW output, PASS/STOP status, wall-clock time. Final lines:
`git status -s`, `git log -3 --oneline`, `git rev-parse szscan-frozen-v3`, and the list of files left for Boti
(`results/t1_demo/{GATE.md,gate.json,TIMING.md,timing.csv,ingest_timing.csv}`, `results/application_eval_v4/*`,
`web_demo/report_handback/tier2_v4/*`). Boti commits `results/` and pushes; you do not. Leave the application database
populated (screenshots for the report are taken from it next). Then stop; no UI changes, no doc updates, no further runs.
