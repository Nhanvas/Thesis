# CC_STEP1_PROMPT.md — Step 1: pipeline_demo.py (process_file) + CLI, real timing

**Prerequisite: Step 0 must already be green** (`pytest web_demo/backend/tests/test_guards.py -v` all
passing) before starting this. If it isn't, stop and say so instead of proceeding.

Read before doing anything else, in this order:
1. `web_demo/CLAUDE.md`
2. `web_demo/SZSCAN_SPEC_v5.md` §1 in FULL (§1.1–§1.7) — this is the measured justification for the
   pipeline below. Do not reason about the architecture from memory or from a summary; read it.
3. `web_demo/DEMO_BUILD_HANDOFF.md` §4 and §6 (row 1)
4. `web_demo/THESIS_CONTEXT_FOR_DEMO.md` §2, §3

Read-only source you will import from (never edit, never copy into `web_demo/`):
- `src/dataprep/preprocessing.py` — `open_edf()`, `filter_window()`, `WIN_SAMPLES`, `FS`, `COMMON_CHANNELS`
- `src/dataprep/graph_construction.py` — `apply_car()`, `compute_wpli()`, `compute_aec()`,
  `combine_adjacency()`, `apply_topk_threshold()`, `DEFAULT_ALPHA`, `DEFAULT_KEEP_RATIO`
- `src/dataprep/feature_extraction.py` — `compute_band_powers()`
- `src/dataprep/compute_gamma_aec.py` — `compute_gamma_scores_batch()`, `make_gamma_filter()`, `BATCH_SIZE`
- `src/retrain/gae_joint.py` — `GAEModel`, `load_checkpoint()`, `build_batch()`, `joint_score()`,
  `N_CH`, `LATENT_DIM`, `BIAS_FP_CANONICAL`
- `src/ensemble_recipe.py` — `build_ensemble_subset()`, `CANDIDATES["rlg"]`

## Goal (Step 1 of 9 — DEMO_BUILD_HANDOFF.md §6)

"`pipeline_demo.py` + CLI chạy 1 file → in ra độ dài score. Đo thời gian thật" — done when the measured
wall-clock rate is close to the ~15 s/hour estimate in `CLAUDE.md` ("Measured cost: ~16.9 ms per 4 s
window ⇒ ~15 s per hour of EEG").

**Scope: only `process_file()`** (HANDOFF §4 stage 1 — runs the moment one file finishes uploading, stops
BEFORE change-point detection). Do **not** implement `process_subject()` / PELT / operating point in this
step — those need parameters read live from `cpd_pipeline_v14.py` and `fp_budget_operating_point.py`
(SPEC §8, items O1/O2), which belong to a later step.

## Checkpoint identity

Load `data/models_retrain/gae_joint_seed42.pt` and verify its sha256 equals
`dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108` before using it. Abort with a clear
error if it doesn't match — never trust the filename alone.

## `process_file(edf_path: str, device: str = "cpu") -> np.ndarray`

Implement in `web_demo/backend/pipeline_demo.py`, in this order:

1. **Open + channel select.** `preprocessing.open_edf(edf_path)`. If it returns `None` (a common channel
   is missing), raise a clear error — don't silently drop the file.
2. **Window + filter, NO artifact rejection.** For every non-overlapping 4 s window (1024 samples @
   256 Hz) in the file — skip none — call `preprocessing.filter_window(raw, start, end)` (bandpass
   0.5–60 Hz + notch 60 Hz, zero-phase). **Do not apply the ±5 SD artifact-rejection step** from
   `preprocessing.py` Step 4 — SPEC §1.6(a) drops it entirely so the window↔second mapping stays exactly
   1-to-1 (`t_seconds = window_index * 4`).
3. **Z-score per channel.** Compute mean/std per channel from this file's filtered windows and apply to
   all of them.
   ⚠️ SPEC says these stats should be fit on "toàn bộ window của SUBJECT" (all files of the subject
   combined), not per file — but this CLI test only has one file, so file-level == subject-level here.
   Add a `# TODO(step3): revisit once multi-file subject upload exists — z-scoring a file the moment it
   finishes uploading is in tension with fitting stats across the whole subject if sibling files are
   still uploading` comment at this point in the code. Do not try to solve that tension now.
4. **Adjacency — top-k 20%, not the default fixed-threshold pipeline.** For each window:
   `apply_car()` → `compute_wpli()` + `compute_aec()` → `combine_adjacency(alpha=DEFAULT_ALPHA)` →
   `apply_topk_threshold(keep_ratio=DEFAULT_KEEP_RATIO)`.
   **Do NOT call `graph_construction.build_adjacency()`** — it applies `apply_fixed_threshold` (the
   baseline dense pipeline), not top-k; using it silently produces near-fully-connected graphs, which is
   the wrong topology for this model.
5. **Band powers.** `feature_extraction.compute_band_powers(window)` → `[18, 5]` per window.
6. **GAE forward → zrecon + graph-level Z.** Batch the per-window adjacency `[B,18,18]` and band-power
   `[B,18,5]` tensors. Call `gae_joint.build_batch(A, Xt, device)`, then `gae_joint.joint_score(model,
   pg, A, Xn, B, per_node=False)` for the raw reconstruction MSE (pre-robust-z `zrecon`). Separately keep
   the graph-level latent `z.mean(dim=1)` per window (mirrors `latent_anomaly.latent_pool`) for the next
   step.
7. **zlatent.** Fit `sklearn.covariance.LedoitWolf()` on the graph-level `Z` of this file's windows (same
   file-vs-subject caveat as step 3 — reuse the same TODO, don't duplicate the explanation). Then
   `cov.mahalanobis(Z)` → raw latent distance per window.
8. **zgamma — continuous, satisfies SPEC §8 item O5.** `compute_gamma_aec.compute_gamma_scores_batch()`
   already operates per-window and needs no interictal/ictal split. Call it directly, batched (e.g.
   `compute_gamma_aec.BATCH_SIZE` windows at a time), on this file's **z-scored** windows (same input
   convention as `compute_gamma_aec.process_subject()` — it reads from the z-scored preprocessed arrays,
   not raw EEG). This is O5's whole requirement: no new algorithm, just calling the existing per-window
   function on a continuous array instead of a pre-split one.
9. **Robust-z each branch.** Median/MAD, fit on the whole file's array for that branch — mirrors
   `retrain_io.robust_z`'s pooled-fit convention exactly (SPEC §8 item O3 is closed: confirmed not a
   divergence). Do not import `retrain_io.robust_z` itself (it takes two pre-split arrays and
   concatenates them); write a short single-array version locally in `pipeline_demo.py`:
   `med = np.median(x); mad = np.median(np.abs(x-med)) + 1e-9; z = (x-med)/mad`.
10. **Ensemble — reuse the single source, do not hand-roll weights.** Call
    `ensemble_recipe.build_ensemble_subset({"zrecon": zr, "zlatent": zl, "zgamma": zg},
    subset=ensemble_recipe.CANDIDATES["rlg"])` — default weights are equal, reproducing the locked
    zrecon+zlatent+zgamma 1/3-each recipe (CLAUDE.md: "three readouts... equal 1/3 weights... no LSTM /
    temporal branch").
    **Do NOT use `ensemble_recipe.build_ensemble()`** — that one is hardwired to (recon, temporal,
    gamma) and is LOCKED; this demo has no temporal branch.
11. **Return** `score: np.ndarray`, length must equal the number of windows in the file.

## CLI

Add a `if __name__ == "__main__":` block to `pipeline_demo.py`:
```
python web_demo/backend/pipeline_demo.py --edf_path <path to one .edf> [--device cpu]
```
On run, print: file name, number of windows, `score.shape`, min/max/mean of `score` (sanity check only —
**do not present raw score values as a clinical readout**, this is a dev CLI), the **real wall-clock time
elapsed**, and the derived seconds-per-hour-of-EEG rate for comparison against the ~15 s/hour estimate.

## Test data

Use files from the eight allowed test subjects only —
`chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18` — under
`F:/Study/Thesis/Dataset/CHB-MIT/<subj>/`. Run the shortest file you can find first (fast smoke test),
then time one full ~1-hour file for the real §6 comparison.

## Guard check before you stop

Run `pytest web_demo/backend/tests/test_guards.py -v` again — `pipeline_demo.py` is new code and must
still pass all four guards (no `build_timeline_masked`, no seizure-field reads, no `_interictal.npy` /
`_ictal.npy` loads, no writes outside `web_demo/`).

## Stop condition — report, then stop

- wall-clock time for the ~1 hour file, and the computed s/hour rate vs. the ~15 s/hour estimate
- score array length vs. expected window count for that file
- guard test output (all four still green)
- the two `# TODO(step3)` locations left in the code
- anything about the pipeline that looked numerically off (e.g. a branch dominating the ensemble, NaNs,
  a flat score) — SPEC §8 item O4b (post-ictal flagging) is explicitly something to *observe* here, not
  fix

Do not start Step 2.
