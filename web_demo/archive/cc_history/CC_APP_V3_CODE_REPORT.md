# CC_APP_V3_CODE_REPORT.md — App v3 code: signal-loss rule, merge constant, headless entry

Executed per `web_demo/CC_PROMPT_APP_V3_CODE.md` + inline clarifications (a)-(e). Code and
tests only — no recording was uploaded, processed or scored, and the backend was never
started. All edits are inside `web_demo/`.

**Commit:** `3336bd7fe063fe86cc8878de4d4ec44fd50bb883`
**Scope W reference (src/continuous_eval.py) pinned to:** git blob hash
`888d9cd94f33ad03dc9eca3e607d0e00c2fb6af9` (see "Pinning the Scope W reference" below)

---

## 1. Why a blob hash, not a commit hash (clarification e)

`src/continuous_eval.py` is **untracked** — `git log --oneline -- src/continuous_eval.py`
returns nothing, and `git status` shows it as `?? src/continuous_eval.py`. Checking the
commits that correspond to its own Amendments (A2-A6) confirms this is deliberate: every one
of those commits (`5685bee`, `e229b9d`, `571a940`, `77c1911`, `f88dca6`) touches only
`docs/CC_PROMPT_CONTINUOUS_EVAL.md` — the eval is pre-registered in that doc before the code
that implements it is written or run, and the code itself is never committed. So there is no
commit hash to pin.

Instead I pinned the exact snapshot read for this task with `git hash-object
src/continuous_eval.py`, which prints a content-addressed SHA-1 **without writing anything**
(no `-w`, nothing added to the object database, no file touched, nothing outside `web_demo/`
affected):

```
888d9cd94f33ad03dc9eca3e607d0e00c2fb6af9
```

Re-running the same command after finishing all edits reproduced the identical hash, confirming
the file was not modified in between (I never edited it — read-only for this whole task).

---

## 2. Side-by-side: Scope W vs application

| # | Scope W (`src/continuous_eval.py` @ blob `888d9cd9`) | Application (`web_demo/backend/pipeline_demo.py` @ commit `3336bd7`) |
|---|---|---|
| Threshold constant | `SIGNAL_LOSS_STD_V = 1e-10` — L276, comment quotes the chb17b_69 root cause | `SIGNAL_LOSS_STD_V = 1e-10` — L127, comment quotes **Amendment A2 verbatim**: *"a window is flagged as signal loss when the standard deviation of the raw (unfiltered) signal is below 1e-10 V on every one of the 18 channels; the threshold is fixed, not tuned (real EEG ~1e-5 V, flat ~1e-22 V)."* Defined once; every exclusion below reads this constant. |
| Flag computation | `compute_signal_loss_flags(raw, n_windows)` — L279-289: per-window streaming loop, `raw.get_data(start=i*WIN_SAMPLES, stop=...)`, `flags[i] = np.all(seg.std(axis=1) < SIGNAL_LOSS_STD_V)` | `compute_signal_loss_flags(raw_windows)` — L130-139: vectorized, `np.all(raw_windows.std(axis=2) < SIGNAL_LOSS_STD_V, axis=1)`. Same quantity (raw/unfiltered per-channel std per window); not streamed because Phase A already holds the whole file's raw windows in RAM at once (no bounded-memory need the thesis-side streaming loop has). |
| Where it's computed from | `raw_for_artifact = P.open_edf(...)`, flags read directly off the raw EDF (L422-424) | `process_file_phase_a`: computed from `raw_windows` (the RAW, unfiltered, pre-float32-downcast windows, still float64) immediately after they're built and before the float32 cast (L293-300 in the diff) |
| Persistence | `np.savez(mpath, ..., is_signal_loss=is_signal_loss, ...)` into the per-subject mask cache (L470-472) | `np.save(flag_path, flag)` → `{cache_dir}/{stem}.flag.npy`, alongside `.filtered.npy`/`.raw.npy`/`.bandpass.npy` (L323 area); also returned on `PhaseAResult.flag` |
| z-score mean/std fit | **Not excluded.** `sum_parts`/`sumsq_parts` (L441-448, `ch_mean_W`/`ch_std_W` at L508-513) accumulate over **every** window unconditionally — no mask applied before or during this pass | **Not excluded** either — `ch_mean`/`ch_std` computed over all windows, unchanged by this task. Confirmed intentional: mirrors Scope W exactly by NOT masking here. |
| LedoitWolf (zlatent) | `fit_mask_W = ~is_signal_loss` (L479); `cov = LedoitWolf().fit(all_graph_z[fit_mask_W])` (L530) | `fit_mask = ~is_signal_loss` (`pipeline_demo.py` L522-524); `cov = LedoitWolf().fit(_masked(all_graph_z, fit_mask))` (L544) |
| Robust-z median/MAD (all 3 branches) | `median_mad(all_zrecon[fit_mask_W])`, `all_zlatent[fit_mask_W]`, `all_zgamma[fit_mask_W]` (L532-534) | `_median_mad(_masked(all_zrecon, fit_mask))`, `all_zlatent`, `all_zgamma` (L556-558) |
| Fused score at flagged windows | `ens_W[is_signal_loss] = 0.0` (L540) | `score[flag_by_filename[f]] = 0.0` (L575) |
| CPD penalty variance / magnitude background | `inter_mask = ~is_signal_loss` (L1066, `load_subject_data`, scope `W`), passed into `cpd_pipeline_v14.detect_changepoints` → `_robust_variance(smoothed, inter_mask)` + magnitude-percentile background | `inter_mask = ~is_signal_loss` (`pipeline_demo.py` L703-705), passed to `cpd_pipeline_v14.detect_events(..., inter_mask=inter_mask, merge_s=FIXED_MERGE_S)`. **`cpd_pipeline_v14.py` itself was never edited** — `inter_mask` is its own pre-existing parameter. |
| Per-channel attribution baseline | *(no equivalent — Scope W never computes per-node attribution at all)* | `compute_pernode_baseline([_masked(pernode_out[f], ~flag_by_filename[f]) for f in filenames_sorted])` (L526-534 area) — the application's own extension of the same rule to its own feature, per instruction (a) ("...and the per-channel attribution baseline"), since it is architecturally the same median/MAD-over-the-whole-subject-set fit as robust-z, just scoped to channel-wise reconstruction error for the UI's Channel Attribution Panel. |

### Which Scope W fits exclude flagged windows for the z-score stats — directly answered

**None.** Scope W's subject-wide channel z-score mean/std (`ch_mean_W`, `ch_std_W`) are
accumulated from `sum_parts`/`sumsq_parts` unconditionally over every window during Pass 1
(`src/continuous_eval.py` L441-448, finalized L508-513) — `is_signal_loss` is not consulted
anywhere in that accumulation. Flagged windows only start being excluded **downstream** of
z-scoring: at the LedoitWolf fit, the three robust-z median/MAD fits, the fused-score
zero-forcing, and the CPD `inter_mask`. The application mirrors this precisely — Phase B's
`ch_mean`/`ch_std` computation (`pipeline_demo.py`'s two `per_file_axis2_sum`/
`per_file_sqdev_axis2_sum` loops) was **not touched** by this change, confirmed by the
bit-identical test passing with the frozen code (whose z-score stats code is textually
identical).

---

## 3. How the flag reaches each subprocess (clarification a)

Phase B and the stage-2 "Process" subprocess (`pipeline_worker.py`, launched via
`subprocess.Popen` from `upload_manager.py` — see that module's own comment on why a plain
OS subprocess is required on this Windows dev machine) never receive the raw EEG signal or
anything derived from it directly; they only ever get file paths or small arrays, same as the
existing `filtered_paths` convention:

1. **Phase A** (`process_file_phase_a`, runs on a background thread) computes `flag` from
   `raw_windows` and, when `cache_dir` is given, persists it to `{cache_dir}/{stem}.flag.npy`
   — exactly parallel to `.filtered.npy`/`.raw.npy`/`.bandpass.npy`. `PhaseAResult.flag_path`
   records the path; `PhaseAResult.flag` carries the array in-process for same-process callers.

2. **Phase B subprocess** (`pipeline_worker.py::_run_phase_b`): `upload_manager.py`'s
   `_maybe_run_phase_b` builds a `flag_paths = {fn: str(f.phase_a.flag_path) ...}` dict
   alongside the existing `filtered_paths` dict (same loop, same filter), and passes both into
   the worker's JSON payload (`{"filtered_paths": ..., "flag_paths": ...}`). The worker reads
   `payload.get("flag_paths")` and forwards it to
   `pipeline_demo.process_subject_phase_b_from_paths(filtered_paths, flag_paths=flag_paths, ...)`,
   which does `{fn: np.load(p) for fn, p in flag_paths.items()}` — a path in, a tiny bool
   array out, same pattern as `filtered_paths` → `filtered_by_filename`.

3. **Stage-2 subprocess** (`pipeline_worker.py::_run_process_events`): stage 2 only ever
   received one path (`score_npz_path`) pointing at an `.npz` of per-file score arrays —
   there was no second path slot to add without changing that calling convention. Since flag
   arrays are a few bytes per window (one bool per 4 s), I embedded them **inside the same
   `.npz`** under a prefixed key: `upload_manager.py::_run_process` now also writes
   `savez_payload[f"flag__{fn}"] = phase_a.flag` for every file before calling
   `np.savez(score_npz_name, **savez_payload)`. The worker's `_run_process_events` splits the
   loaded keys back into `scores` (no prefix) and `flags` (prefix `flag__`, stripped) and calls
   `pd.process_subject_events(scores, flag_by_filename=flags or None)`. This still satisfies
   "only get file paths/score arrays" — the flags are score-array-shaped data traveling through
   the exact same single-path npz hand-off, never the raw signal.

4. **`process_subject_headless`** (new, no DB/HTTP/subprocess at all — runs Phase A and Phase B
   directly in one Python process via `ThreadPoolExecutor(max_workers=2)`): flags never cross a
   process boundary here, they're just `PhaseAResult.flag` passed straight into
   `process_subject_phase_b(..., flag_by_filename=flag_by_filename)` in-memory, and separately
   persisted to `{cache_dir}/{stem}.flag.npy` by `process_file_phase_a` as a side effect (so the
   thesis side can also read them straight off disk if it wants to, without re-deriving them).

Every one of these paths defaults its new parameter (`flag_by_filename` / `flag_paths`) to
`None`, which is byte-identical to the pre-change code (`_masked(arr, None) is arr`,
unmodified object handed to `LedoitWolf.fit`/`_median_mad`; `inter_mask=None` matches
`detect_events`'s own default) — existing callers that don't know about flags yet
(`backfill_pernode.py`, `backfill_scores.py`, `measure_stage_timing.py`,
`report_handback/scripts/measure_timing_chb06_01.py`) are untouched and still compile and run
exactly as before.

---

## 4. Constants (clarification: item 2)

```python
FIXED_MAG_PCT  = 50     # unchanged
FIXED_PEN_MULT = 2.0    # unchanged
FIXED_MERGE_S  = 90     # new — same value as cpd_pipeline_v14.detect_events's own default
```

All three are now passed explicitly to the single `detect_events` call in
`process_subject_events`:

```python
events_global = cpd_pipeline_v14.detect_events(
    global_score, FIXED_PEN_MULT, min_mag_pct=FIXED_MAG_PCT,
    inter_mask=inter_mask, merge_s=FIXED_MERGE_S,
)
```

`FIXED_MERGE_S=90` equals `detect_events`'s own hardcoded default, so making it explicit
changes no behavior now — the validation-selected value comes in a later instruction, per the
prompt's own "Leave the current values... the new values come in a later instruction."
`MIN_MAG_PCT` (the separate, unrelated PELT-default constant used only by the retired
`calibrate_operating_point`) was left untouched.

---

## 5. Test output (full, `web_demo/backend/tests/`, all tests including `test_guards.py`)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Dell Latitude 3590\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: F:\Study\Thesis\Code\web_demo\backend
plugins: anyio-4.15.1
collecting ... collected 9 items

tests/test_guards.py::test_guard_no_build_timeline_masked PASSED         [ 11%]
tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED     [ 22%]
tests/test_guards.py::test_guard_no_labeled_npy PASSED                   [ 33%]
tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED       [ 44%]
tests/test_signal_loss_v3.py::test_flagged_windows_zero_and_excluded_from_every_fit PASSED [ 55%]
tests/test_signal_loss_v3.py::test_bit_identical_when_no_flagged_window PASSED [ 66%]
tests/test_signal_loss_v3.py::test_detect_events_receives_the_three_constants PASSED [ 77%]
tests/test_signal_loss_v3.py::test_process_subject_headless_matches_live_phase_a_plus_b PASSED [ 88%]
tests/test_signal_loss_v3.py::test_guards_module_still_importable PASSED [100%]

============================== warnings summary ===============================
C:\Users\Dell Latitude 3590\AppData\Local\Programs\Python\Python311\Lib\site-packages\torch_geometric\llm\utils\backend_utils.py:26
  C:\Users\Dell Latitude 3590\AppData\Local\Programs\Python\Python311\Lib\site-packages\torch_geometric\llm\utils\backend_utils.py:26: DeprecationWarning: `torch_geometric.distributed` has been deprecated since 2.7.0 and will no longer be maintained. For distributed training, refer to our tutorials on distributed training at https://pytorch-geometric.readthedocs.io/en/latest/tutorial/distributed.html or cuGraph examples at https://github.com/rapidsai/cugraph-gnn/tree/main/python/cugraph-pyg/cugraph_pyg/examples
    from torch_geometric.distributed import (

C:\Users\Dell Latitude 3590\AppData\Local\Programs\Python\Python311\Lib\site-packages\torch\jit\_script.py:1488
C:\Users\Dell Latitude 3590\AppData\Local\Programs\Python\Python311\Lib\site-packages\torch\jit\_script.py:1488: DeprecationWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 9 passed, 3 warnings in 39.13s ========================
```

All five required cases are covered by `test_signal_loss_v3.py` (synthetic EDFs built with
`pyedflib` directly — `mne`'s EDF writer needs the `edfio` package, not installed in this
environment, so no new dependency was pulled in just for the test):

- **Flat segment → score 0 and excluded from every fit**
  (`test_flagged_windows_zero_and_excluded_from_every_fit`): a 24-window synthetic recording
  with windows 10-12 forced flat. Verified directly (not inferred from numerics) by
  monkeypatching `pipeline_demo._median_mad` and `pipeline_demo.LedoitWolf.fit` to record the
  length of every array they're called with — both see exactly `24 - 3 = 21` rows, proving the
  3 flagged windows never reach any fit. Also asserts the flagged indices' scores are exactly
  `0.0` and every non-flagged score is finite (guards against the flagged windows' raw
  GAE/connectivity output — potentially numerically undefined, per Amendment A2's own root
  cause — leaking into a shared fit).

- **No flat window → bit-identical** (`test_bit_identical_when_no_flagged_window`): loads
  `git show szscan-frozen-v2:web_demo/backend/pipeline_demo.py` into a throwaway module via
  `exec`, runs its `process_file_phase_a`+`process_subject_phase_b` on an 8-window synthetic
  EDF with no flat segment, and compares against the current code's output (flags computed but
  all `False`). `max(abs(new - old)) == 0.0` exactly.

- **`detect_events` receives the three constants**
  (`test_detect_events_receives_the_three_constants`): monkeypatches
  `cpd_pipeline_v14.detect_events` to record its kwargs, calls `process_subject_events`, asserts
  `pen_mult == FIXED_PEN_MULT`, `min_mag_pct == FIXED_MAG_PCT`, `merge_s == FIXED_MERGE_S`.

- **`process_subject_headless` matches the live path**
  (`test_process_subject_headless_matches_live_phase_a_plus_b`): a synthetic two-file subject
  (10 and 14 windows, with flat windows in each file) run through `process_subject_headless`
  and, separately, through `process_file_phase_a` + `process_subject_phase_b` directly — scores
  match exactly for both files. Also checks the returned `flag_by_filename` matches the known
  flat-window indices and that `{stem}.flag.npy` was persisted for both files.

- **Existing label guards still pass unchanged**: `test_guards.py`'s four guard tests ran
  unmodified in the same session and all passed (`test_guards_module_still_importable` is just
  a collection-sanity check that the new test file doesn't break the guard module's own
  importability).

---

## 6. `git status -s` before and after

**Before** (start of this task — matches the harness-provided `gitStatus` snapshot, verified
with my own `git status -s` run before any edit):

```
 M .gitignore
?? bme11/
?? results/continuous_eval/
?? src/continuous_eval.py
?? src/continuous_eval_step0.py
?? web_demo/CC_OVERNIGHT_RUN_PROMPT.md
?? web_demo/CC_PART2_PART4_PROMPT.md
?? web_demo/CC_PART3_RERUN_V2_PROMPT.md
?? web_demo/CC_PROMPT_APP_V3_CODE.md
?? web_demo/CC_PROMPT_APP_WINDOW_DIAG.md
?? web_demo/CC_PROMPT_SCORER_AND_LABELS_FIX.md
?? web_demo/CC_PROMPT_SCORER_BOUNDARY.md
?? web_demo/CC_REPORT_HANDBACK_PART3_PROMPT.md
?? web_demo/CC_VERIFY_AND_RUN_PART3_PROMPT.md
?? web_demo/REPORT_HANDBACK.md
?? web_demo/REPORT_REPLY_TO_PROJECT2_3.md
?? web_demo/REPORT_REQUEST_TO_PROJECT2.md
?? web_demo/backend/uvicorn.log
?? web_demo/report_handback/
```

**After** (post-commit `3336bd7`):

```
 M .gitignore
?? bme11/
?? results/continuous_eval/
?? src/continuous_eval.py
?? src/continuous_eval_step0.py
?? web_demo/CC_OVERNIGHT_RUN_PROMPT.md
?? web_demo/CC_PART2_PART4_PROMPT.md
?? web_demo/CC_PART3_RERUN_V2_PROMPT.md
?? web_demo/CC_PROMPT_APP_V3_CODE.md
?? web_demo/CC_PROMPT_APP_WINDOW_DIAG.md
?? web_demo/CC_PROMPT_SCORER_AND_LABELS_FIX.md
?? web_demo/CC_PROMPT_SCORER_BOUNDARY.md
?? web_demo/CC_REPORT_HANDBACK_PART3_PROMPT.md
?? web_demo/CC_VERIFY_AND_RUN_PART3_PROMPT.md
?? web_demo/REPORT_HANDBACK.md
?? web_demo/REPORT_REPLY_TO_PROJECT2_3.md
?? web_demo/REPORT_REQUEST_TO_PROJECT2.md
?? web_demo/backend/uvicorn.log
?? web_demo/report_handback/
```

Identical: the four files this task changed
(`web_demo/backend/pipeline_demo.py`, `web_demo/backend/pipeline_worker.py`,
`web_demo/backend/upload_manager.py`, `web_demo/backend/tests/test_signal_loss_v3.py`) are now
committed in `3336bd7` and so no longer appear as working-tree changes; every other line is
pre-existing, unrelated state untouched by this task. Nothing outside `web_demo/` was modified;
`.gitignore`'s modification predates this task and was not touched. This report
(`web_demo/CC_APP_V3_CODE_REPORT.md`) is written but intentionally **not committed**, per
instruction.

---

## 7. Scope judgment call (unchanged from the earlier summary, repeated for the written record)

The prompt's explicit "Changes" list named only `pipeline_demo.py` plus tests. I additionally
wired the live subprocess plumbing (`pipeline_worker.py`, `upload_manager.py`) so the
signal-loss rule takes effect on the real upload → Phase B → Process flow, not only on
`process_subject_headless`. Clarification (a)'s phrase "the Phase B and stage-2 subprocesses
only get file paths/score arrays" only makes sense as a real constraint on those two files
(that is literally `pipeline_worker.py`'s own docstring: *"Talks to the parent over two small
JSON files... plus paths to the .npy/.npz arrays already sitting on disk — never large arrays
over stdio/pipes"*), so I read it as in-scope. No backend was started, no file outside
`web_demo/` was touched, and every new parameter defaults to `None` / byte-identical behavior
for any caller that doesn't pass it.
