# CC_T1_RUN_REPORT.md — run of `CC_T1_RUN_ALL_PROMPT.md` (rev 2)

## Run 1 (stopped) — Sat, Oct 10, 2026 10:45:43 AM

Stage 1.0 failed: `git status -s` showed 2 modified tracked files (`docs/PROJECT_INSTRUCTIONS.md`,
`web_demo/CLAUDE.md`). Per ground rules, run stopped with no further action. Author then committed those
two files; this report is superseded by Run 2 below, which re-executes from Stage 1.0 as instructed.

---

## Run 2 — Sat, Oct 10, 2026 10:51:47 AM

Note on sources: `F:\Study\Thesis\Agent\report_v7\DEMO_FAST_BRIEF.md`, cited in the prompt header as the
primary source of scope, does not exist on disk. Proceeding per the prompt's own statement that it already
resolves any difference between that brief and `docs/HANDOFF_T1_DEMO_REBUILD.md`.

Read-first files confirmed read: `web_demo/CLAUDE.md`, `docs/HANDOFF_T1_DEMO_REBUILD.md` §2/§3/§5/§6,
`docs/DEMO_REBUILD_BRIEF.md`, `web_demo/THESIS_CONTEXT_FOR_DEMO.md`.

### Stage 1.0 — Preconditions

```
$ cd /f/Study/Thesis/Code && git status -s
?? bme11/
?? docs/writing/
?? results/figures_v6/
?? results/x1_external/x1_SUMMARY.md
?? "src/e23_test_look7 (1).py"
?? web_demo/CC_APP_V3_CODE_REPORT.md
?? web_demo/CC_OVERNIGHT_RUN_PROMPT.md
?? web_demo/CC_PART2_PART4_PROMPT.md
?? web_demo/CC_PART3_RERUN_V2_PROMPT.md
?? web_demo/CC_PROMPT_APP_V3_CODE.md
?? web_demo/CC_PROMPT_APP_WINDOW_DIAG.md
?? web_demo/CC_PROMPT_SCORER_AND_LABELS_FIX.md
?? web_demo/CC_PROMPT_SCORER_BOUNDARY.md
?? web_demo/CC_REPORT_HANDBACK_PART3_PROMPT.md
?? web_demo/CC_T1_RUN_ALL_PROMPT.md
?? web_demo/CC_T1_RUN_REPORT.md
?? web_demo/CC_T1_STEP1_PROMPT.md
?? web_demo/CC_VERIFY_AND_RUN_PART3_PROMPT.md
?? web_demo/PROJECT2_INSTRUCTIONS.md
?? web_demo/REPORT_HANDBACK.md
?? web_demo/REPORT_REPLY_TO_PROJECT2_3.md
?? web_demo/REPORT_REQUEST_TO_PROJECT2.md
?? web_demo/SPEC_C29_AMENDMENT.md
?? web_demo/backend/uvicorn.log
?? web_demo/report_handback/
(no modified tracked files — PASS)

$ git merge-base --is-ancestor f37a7b1 HEAD && echo base-ok
base-ok

$ git log -1 --oneline HEAD
905d0b0 figures v6: report figures from committed results

$ ls -l /f/Study/Thesis/Agent/t1_demo/t1_demo_reference.patch
-rw-r--r-- 1 Dell Latitude 3590 197121 115198 Oct 10 09:59 /f/Study/Thesis/Agent/t1_demo/t1_demo_reference.patch

$ sha256sum data/models_v2/gae_v2_clean_seed42.pt data/models_v2/gae_v2_clean_seed42.json
6e310307b046407a18d839273b84c74b2905457ec6ace892b674c6972dac590f *data/models_v2/gae_v2_clean_seed42.pt
d1e2eee9924b9c23aedf1d8da0e2d289e88d2f790ff90c34958aa850870f06c5 *data/models_v2/gae_v2_clean_seed42.json
(both match web_demo/CLAUDE.md's stated hashes — PASS)

$ python -c "import torch, torch_geometric; print(torch.__version__)"
2.12.0+cpu

$ df -h /f
Filesystem      Size  Used Avail Use% Mounted on
F:              466G  178G  289G  39% /f
```

**All Stage 1.0 preconditions PASS.** Proceeding to 1.1 (patch review).

### Stage 1.1 — Patch review (read-only, before applying)

```
$ git apply --stat /f/Study/Thesis/Agent/t1_demo/t1_demo_reference.patch
 web_demo/archive/backend_v1/README.md              |   10
 web_demo/archive/backend_v1/backfill_bandpass.py   |    0
 web_demo/archive/backend_v1/backfill_pernode.py    |    0
 web_demo/archive/backend_v1/backfill_scores.py     |    0
 .../archive/backend_v1/measure_stage_timing.py     |    0
 .../backend_v1/tests/test_signal_loss_v3.py        |    0
 web_demo/backend/attribution.py                    |   60 +
 web_demo/backend/batch_ingest.py                   |   95 ++
 web_demo/backend/export_tier2.py                   |   77 +
 web_demo/backend/pipeline_demo.py                  | 1143 +++++++-------------
 web_demo/backend/pipeline_worker.py                |   57 -
 web_demo/backend/tests/test_final_system.py        |  216 ++++
 web_demo/backend/upload_manager.py                 |   42 -
 .../frontend/src/components/AttributionPanel.jsx   |    4
 14 files changed, 867 insertions(+), 837 deletions(-)
```
All 2070 lines of the patch were read in full. Checklist (file:line against the real `src/` source,
read separately from the patch):

| # | check | result | evidence |
|---|---|---|---|
| a | No demo code calls a label-reading thesis function (list in CLAUDE.md) | **PASS** | `pipeline_demo.py` calls `E22.final_scalar`, `P3L.member_mean_z`/`q_of`/`localize`, `PS.smoothed`/`d1_events`, `C1B.graph_and_bp`/`f7`, `PD.run_model`, `X1.window_padded` — none on the forbidden list (`e22_test_oneshot.test_context`/`.evaluate`, `e23_test_look7.evaluate`, `p2_scalars.subject_context`/`.score`/`.short_refs`/`.caught`, `e18_cpd_localizer.match_errors`, `p3_levers.refs_of`, `x1_external.subject_files`/`.chb_subject`/`.siena_subject`/`.build_subject`, `c1b_build_trainset.build`, `szcore_eval.*`). `process_subject_events` reimplements the non-label-reading prefix of `e23_test_look7.evaluate` inline (six lines, see item g) instead of calling it. `test_final_system.py::test_runtime_label_free` monkeypatches every forbidden entry point to raise and the headless path still runs — PASSED (Stage 1.5). |
| b | Checkpoint sha256 verified before load; `PD.run_model` resolves to the verified `.pt`; added-feature constants from the `.json` | **PASS** | `src/p2_dump_seeds23.py:47` `ck = CKPT / f"gae_v2_{tag}.pt"`, `CKPT = ROOT/"data"/"models_v2"` → with `MODEL_TAG="clean_seed42"` this is byte-identical to `pipeline_demo.py`'s own `CHECKPOINT_PATH`. `run_gae()` calls `verify_checkpoint()` (hashes both `.pt` and `.json` against the two sha256 in CLAUDE.md) immediately before calling `PD.run_model`. `p2_dump_seeds23.py:48-50` reads `add_mean`/`add_std`/`clip` from the checkpoint's own `.json`. |
| c | `stats_override` unreachable from `main.py`, `upload_manager.py`, `pipeline_worker.py`, any HTTP path | **PASS** | Confirmed by source reading: `upload_manager.py`'s `_run_phase_b` builds the worker payload with only `filtered_paths`/`flag_paths`/`moments_paths` (no `stats_override` key); `pipeline_worker.py`'s `_run_phase_b` calls `pd.process_subject_phase_b_from_paths(filtered_paths, payload["flag_paths"], payload["moments_paths"])` with no `stats_override` arg, so it defaults to `None`. Only `src/t1_demo_gate.py` (thesis side, Stage 2) and `web_demo/backend/gate_overlap.py` (new, Stage 1.4, never imported by the app) call it directly. |
| d | Every write under `web_demo/` | **PASS** | New/changed writes: `DEFAULT_HEADLESS_CACHE_DIR = REPO_ROOT/"web_demo"/"backend"/"cache"/"headless"`, `batch_ingest.py`'s `--log` default `uploads/_ingest_timing.csv`, `export_tier2.py`'s `--out`, `gate_overlap.py`'s `--out` default `report_handback/gate_overlap_chb03.csv` — all under `web_demo/`. `data/models_v2/*`, `results/p3c_freeze/freeze.json` are read-only. Note: `src/c1b_build_trainset.py` (imported transitively for `graph_and_bp`/`f7`) does `OUT.mkdir(parents=True, exist_ok=True)` at **import time** against `data/trainset_v2/` — a theoretical import-time effect outside `web_demo/`, but that directory already exists on this machine so it is a no-op (nothing created or modified). Flagging for the record; not treated as a FAIL since no write actually occurs. |
| e | floor/cap, `smooth`, `k`, `localizer` read from `results/p3c_freeze/freeze.json` at runtime | **PASS** | File confirmed to contain exactly the keys used: `k=4.067744298524509`, `smooth=5`, `localizer="cpd"`, `points.balanced=[0.005, 0.02]`. `pipeline_demo.py` reads `FREEZE = json.loads(FREEZE_PATH.read_text())` and indexes `FREEZE["points"]["balanced"]`, `cfg["smooth"]`, `cfg["k"]`, `cfg["localizer"]` — nothing typed in. |
| f | No budget/k/score parameter/metric returned by any API endpoint or shown in the UI | **FIXED** | Confirmed the reviewer's finding: `UploadSession.snapshot()` returned `"operating_point": {"alarm_budget": ...}` once done, and `main.py` returns `session.snapshot()` directly from 5 endpoints (`/api/uploads/current` GET/POST/DELETE, `/api/uploads/current/acknowledge`, `/api/uploads/current/files`) — so the budget was reachable over the API even though no frontend code read it (`grep -rn operating_point web_demo/frontend/src` → 0 hits). **Fix applied:** removed the `"operating_point"` key from `snapshot()` entirely (`web_demo/backend/upload_manager.py`); `session.alarm_budget` itself is still set internally after Process, just never returned. No reader needed fixing (grep confirmed zero frontend/backend consumers of the key). |
| g | §6 interface contract (names/shapes) | **PASS** | `MODEL_TAG="clean_seed42"`, `WIN_S = preprocessing.WIN_S`; `process_subject_headless(edf_paths, cache_dir=None, max_workers=2, stats_override=None, timing=None) -> dict` matches exactly; `process_subject_phase_b(filtered, flags, moments, stats_override=None, timing=None) -> PhaseBResult(.scores, .dists, .baseline, .stats)` matches; `process_subject_events(scores, flags, dists, timing=None, trace=None) -> (events, AlarmBudget(.q, .top))` fills `trace["detector"]` — matches. `export_tier2.py` writes `MANIFEST.txt` lines `commit {sha}` and `uncommitted changes in web_demo/backend or src: {no|YES}` verbatim. The six detector/localizer lines in `process_subject_events` are byte-for-byte the same six lines as `src/e23_test_look7.py:66-74`'s `evaluate()` (verified side by side), minus the scoring call — confirms the brief's claim exactly. |
| h | Signal loss (raw std < 1e-10 V, all 18 ch) excluded from fits, NaN distance, kept on timeline | **PASS** | `SIGNAL_LOSS_STD_V = 1e-10`; `compute_signal_loss_flags`: `np.all(raw_windows.std(axis=2) < SIGNAL_LOSS_STD_V, axis=1)`. `file_features` only builds graph/GAE inputs for `~flag` windows (excluded from the per-subject LedoitWolf fit). `dists[f]` is built as `np.full(..., np.nan)` with only `ok` rows filled — NaN at signal-loss windows. `scores[f] = x[m]` where `x` has one entry per window including flagged ones (via `src/p2_scalars.py:56-63`'s `_full`/`pct`, which fill non-`ok` positions with a flat 0.5 — confirmed by reading those functions directly), so flagged windows keep their place on the timeline with a neutral value, never dropped. |
| i | Signatures of every called thesis function match the real source; importing has no import-time effect | **PASS** (one caveat) | Checked directly against source: `x1_external.window_padded(data, i, notch)`, `.filter_windows(data, notch)`, `.labelfree_stats(files, kind, notch)` (test-only call) — all match. `c1b_build_trainset.graph_and_bp(zw)`→(adj,bp), `.f7(W)` — match. `p2_dump_seeds23.run_model(tag, adj, Xn_all, f7)` — matches. `preprocessing._NOTCH_B/_NOTCH_A` exist (`iirnotch(60.0, Q=30, fs=256)`), `.FS=256`, `.WIN_S=4`, `.WIN_SAMPLES=1024`, `.STATS_SUBSAMPLE=10`, `._BP_SOS` all exist. `e22_test_oneshot.final_scalar(ctx, tag)`, `p3_levers.{member_mean_z(ctx,tag), q_of(sm_m,k), localize(ctx,x,det,thr,mode)}`, `p2_scalars.{smoothed(ctx,sc,smooth), d1_events(ctx,sc,smooth,top)}` all match. Import-time effects: `szcore_eval.py` and `continuous_eval.py` have none (checked module-level code, constants/objects only); `c1b_build_trainset.py` does the benign `data/trainset_v2` mkdir noted under item d. |
| j | `batch_ingest.py`/`export_tier2.py` dependency signatures | **PASS** | `upload_manager.{start_session(project_id,memo), save_upload_to_tmp(data:bytes), add_file(session,filename,tmp_path), start_process(session,project_id,memo), poll_tick(session), acknowledge_done(), UPLOAD_DIR}` and `db.{ALLOWED_SUBJECTS, init_db(), list_subjects(), list_files_by_filename(subject_id), list_events(file_id)}` all exist with the exact signatures used. `UploadSession.snapshot()` already exposes `error`, `files[].status`/`.error`, `ready_to_process`, `done` — everything `batch_ingest.wait()` reads. |

No FAILs. Item f required (and received) the fix the task itself flagged in advance. Item d's note is
informational only (no actual write occurs).

### Stage 1.2 — Apply

```
$ git am --3way /f/Study/Thesis/Agent/t1_demo/t1_demo_reference.patch
Applying: Demo backend on the final thesis system (REFERENCE implementation for Project 2)
```
Applied cleanly, no conflicts, one commit (`d70d7bd`) on top of `905d0b0`.

### Stage 1.3 — Panel title

```
$ grep -rn "reconstruction anomaly" web_demo/backend web_demo/frontend/src
(no matches)
```
The patch's own title change (`AttributionPanel.jsx`: `Channel-level latent anomaly — Event N`) is the
only one; no other occurrence of the old title exists in backend or frontend source.

### Stage 1.4 — Gate-support script

Created `web_demo/backend/gate_overlap.py` (new, not imported by `main.py`/`upload_manager.py`/
`pipeline_worker.py` — confirmed by grep, same status as `stats_override`). Reads
`{stem}.filtered.npy`/`.flag.npy`/`.moments.npy` from the gate script's `--keep-cache` cache dir
(layout confirmed against `src/t1_demo_gate.py`'s own `cmd_gate` read-back code), runs
`process_subject_phase_b` + `process_subject_events` twice on chb03 (thesis statistics from
`data/processed/chb03_stats.json` × 1e-6, then `stats_override=None`), compares localized events
per file by any-overlap-in-seconds, and writes the per-event table to
`web_demo/report_handback/gate_overlap_chb03.csv`. Reads no annotation, calls no label-reading
function. Not yet run (needs the Stage 2 gate cache, which does not exist until Stage 2 runs).

### Stage 1.5 — Tests

```
$ python -m pytest web_demo/backend/tests -v
collected 11 items
test_final_system.py::test_phase_a_and_labelfree_stats_equal_x1 PASSED
test_final_system.py::test_features_equal_x1 PASSED
test_final_system.py::test_events_equal_frozen_e23_evaluate PASSED
test_final_system.py::test_runtime_label_free PASSED
test_final_system.py::test_channel_panel_is_attribution_v8_quantity PASSED
test_final_system.py::test_checkpoint_identity_matches_provenance PASSED
test_final_system.py::test_real_gae_runs_when_torch_is_installed PASSED
test_guards.py::test_guard_no_build_timeline_masked PASSED
test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED
test_guards.py::test_guard_no_labeled_npy PASSED
test_guards.py::test_guard_no_writes_outside_web_demo PASSED
================= 11 passed, 3 warnings in 136.50s (0:02:16) ==================
```
`test_guards.py` 4/4 green, not weakened. It did **not** fire on the archived
`web_demo/archive/backend_v1/*.py` files (test_guards.py excludes any path containing a `tests` dir,
and the non-test archived files contain no guarded string) — so the "git rm archived V1 scripts"
contingency in the prompt did not apply; nothing was removed. `test_final_system.py` ran unmodified
(every `monkeypatch.setattr` name it uses already exists in the real modules — nothing dropped). The
real-GAE test (`test_real_gae_runs_when_torch_is_installed`) actually ran, did not skip. All green.

### Stage 1.6 — Commit and tags

```
$ git reset --soft 905d0b0
$ git add web_demo/archive/backend_v1/README.md web_demo/archive/backend_v1/backfill_bandpass.py \
  web_demo/archive/backend_v1/backfill_pernode.py web_demo/archive/backend_v1/backfill_scores.py \
  web_demo/archive/backend_v1/measure_stage_timing.py web_demo/archive/backend_v1/tests/test_signal_loss_v3.py \
  web_demo/backend/attribution.py web_demo/backend/batch_ingest.py web_demo/backend/export_tier2.py \
  web_demo/backend/gate_overlap.py web_demo/backend/pipeline_demo.py web_demo/backend/pipeline_worker.py \
  web_demo/backend/tests/test_final_system.py web_demo/backend/upload_manager.py \
  web_demo/frontend/src/components/AttributionPanel.jsx
$ git commit -m "web_demo: backend on the final system (GAE v2 clean seed42, per-channel latent, budget + CPD localizer)" ...
[main 936b8e0] web_demo: backend on the final system (GAE v2 clean seed42, per-channel latent, budget + CPD localizer)
 15 files changed, 976 insertions(+), 839 deletions(-)
$ git tag szscan-frozen-v3
$ git tag demo-final-v1
$ git status -s
?? bme11/
?? docs/writing/
?? results/figures_v6/
?? results/x1_external/x1_SUMMARY.md
?? "src/e23_test_look7 (1).py"
?? web_demo/CC_*.md (pre-existing, unrelated untracked docs)
?? web_demo/backend/uvicorn.log
?? web_demo/report_handback/
(no modified tracked files under web_demo/backend or src — confirmed)
```
Local only, no push. `git log -1 --stat` shown above (15 files changed). What remains unproven on real
data: everything — this commit has only been exercised by the synthetic-EDF test suite; Stage 2
(identity gate on chb03, real data) is the first real-recording run.

### Stage 1.7 — Architecture facts (Figure 10), from the committed code

| row | boxes / arrows | file:line evidence |
|---|---|---|
| browser row | React frontend (not re-read here; unchanged by this patch) talks to the backend only via `/api/*` | `web_demo/frontend/src/components/AttributionPanel.jsx` (only UI file this patch touches) |
| server row | FastAPI app, single process, CORS-enabled; `startup` hook calls `db.init_db()` | `web_demo/backend/main.py:42` `app = FastAPI(...)`, `:47` `CORSMiddleware`, `:55-57` `@app.on_event("startup") def _startup(): db.init_db()`; 20+ routes under `/api/...` (`main.py:79-457`) all funnel through `upload_manager`/`db` |
| upload manager → Phase A threads / Phase B+Process worker process | Phase A runs in a `ThreadPoolExecutor` inside the server process; Phase B and Stage 2 run in a genuinely separate OS process via `subprocess.Popen`-equivalent (`subprocess.run`) of `pipeline_worker.py`, because a thread or `ProcessPoolExecutor` worker hangs when the GAE pipeline is invoked from inside the uvicorn host process | `web_demo/backend/upload_manager.py:45-46` `_phase_a_executor = ThreadPoolExecutor(max_workers=_PHASE_A_MAX_CONCURRENCY, ...)`, `:189` `_phase_a_executor.submit(_run_phase_a, ...)`, `:297-317` `_run_worker()`'s `subprocess.run([sys.executable, str(_WORKER_SCRIPT), mode, in_name, out_name], ...)`; `web_demo/backend/pipeline_worker.py:1-16` docstring states the hang reproduction and the subprocess rationale explicitly |
| scoring row | thesis modules imported read-only (never edited/copied); checkpoint verified by sha256 **before** `torch.load` | `web_demo/backend/pipeline_demo.py:66-72` `import preprocessing / x1_external as X1 / c1b_build_trainset as C1B / p2_dump_seeds23 as PD / p2_scalars as PS / e22_test_oneshot as E22 / p3_levers as P3L` (all from `src/`, `REPO_ROOT = Path(__file__).resolve().parents[2]` at `:60`); `:120-121` `def verify_checkpoint(): for path, want in ((CHECKPOINT_PATH, CHECKPOINT_SHA256), (CHECKPOINT_META_PATH, CHECKPOINT_META_SHA256)): ...`; `:278` `verify_checkpoint()` called inside `run_gae()` immediately before `PD.run_model(...)` (which itself calls `torch.load`) |
| storage row | SQLite database + per-file `.npy` cache under `uploads/{subject}/` | `web_demo/backend/db.py:14` `DB_PATH = Path(__file__).resolve().parent / "szscan.db"`, `:63-65` `sqlite3.connect(DB_PATH)`; per-file cache paths from `process_file_phase_a`'s `{stem}.filtered/.raw/.bandpass/.flag/.moments.npy` and Phase B's `{stem}.pernode.npy` / `pernode_baseline.npy` (`pipeline_demo.py`, `pipeline_worker.py:33-40`) |
| never read at runtime | no import of `requests`/`httpx`/`urllib` anywhere in `web_demo/backend` (confirmed by grep — zero hits); annotations, summary seizure fields, `{subj}_ictal.npy`/`_interictal.npy` never read — enforced by `test_guards.py`'s 4 source-scan guards, all green (Stage 1.5) | grep of `web_demo/backend/*.py` for network-library imports → 0 hits; `web_demo/backend/tests/test_guards.py` (Stage 1.5 output above) |

Per the prompt, this goes in the final return block's `FIG10 boxes:` line too.

## Stage 2 — Identity gate on chb03 (attempted, killed — not a GATE result)

Started ~11:10:41. Command:
```
$ cd /f/Study/Thesis/Code
$ export TMP=F:/tmp TEMP=F:/tmp TMPDIR=F:/tmp
$ python src/t1_demo_gate.py gate --dataset F:/Study/Thesis/Dataset/CHB-MIT --keep-cache
```
Raw output captured before the kill:
```
gate: demo pipeline with the thesis statistics ...
```
The run's own background-task supervisor killed the process: **"stopped because the system is
running low on memory."** This is not a GATE FAIL (no scientific mismatch was ever computed — the
run never got far enough to write `results/t1_demo/GATE.md`, which does not exist) and not a
precondition failure caught by Stage 1.0 (nothing else heavy was started by this run itself). It is
the resource risk the brief explicitly warns about (`web_demo/CLAUDE.md` "Environment": *"never run
another heavy job while the demo processes real data"*; the prompt's own time-box note: *"Nothing
else heavy may run (chb06-class memory use)"*).

Evidence:
```
$ powershell -Command "Get-CimInstance Win32_OperatingSystem | Select TotalVisibleMemorySize,FreePhysicalMemory"
TotalVisibleMemorySize FreePhysicalMemory
---------------------- ------------------
              16669212            5106088
(total ~15.9 GB, free ~4.9 GB at the moment checked, after the kill had already freed the run's own memory)

$ powershell -Command "Get-Process | Sort WS -Descending | Select -First 15 Name,Id,WS_MB"
Memory Compression   923.5 MB
EPSecurityService    839.1 MB   (antivirus)
chrome (8 processes) ~741+638+587+478+421+381+352+372 MB  (~4.0 GB total)
claude (this CLI)    382.1 MB
Cursor (2 processes) ~361+303 MB (~0.66 GB)
msedge                187 MB
dwm                   246 MB
```
Partial state left on disk (not deleted -- `ls`/`du` only, per the ground rules):
```
$ du -sh F:/Study/Thesis/Agent/t1_demo/cache/gate
7.1G    F:/Study/Thesis/Agent/t1_demo/cache/gate
```
Phase A completed for all 38 chb03 files (`chb03_01..38.{filtered,raw,bandpass,flag,moments}.npy`
all present) before the kill -- the process died later, inside or after Phase B (per-subject
GAE/LedoitWolf fit on chb03's full window set), before `results/t1_demo/GATE.md` could be written.
`results/t1_demo/` exists but is empty (no `GATE.md`, no `gate.json`).

**Determination: STOP.** This machine has only ~16 GB RAM and roughly 6 GB of it is already held by
Chrome (~4 GB across 8 processes), Cursor and antivirus -- before this run's own per-subject fit
(chb06-class, per CLAUDE.md, peaked at 10.2 GB in the earlier build) needs room. Closing those
applications is the author's call, not something to do unilaterally mid-run. Stages 2-4 did not
produce a result; nothing past Stage 1 is proven. The partial 7.1 GB cache under
`F:/Study/Thesis/Agent/t1_demo/cache/gate` was left in place (a retry overwrites it page by page
regardless, since `process_file_phase_a` always recomputes rather than skipping existing cache
files) in case the author wants to inspect it first.

