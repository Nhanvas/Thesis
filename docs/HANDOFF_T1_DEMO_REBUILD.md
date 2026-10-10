# HANDOFF_T1_DEMO_REBUILD — thesis project → Project 2 (SzScan), 2026-10-10

**From:** the thesis project (Project 1). **To:** Project 2, which owns `web_demo/` and does the work.
**Carried by:** Boti. **Read with:** `docs/DEMO_REBUILD_BRIEF.md` (2026-10-08, what the pipeline is) and
the new `web_demo/THESIS_CONTEXT_FOR_DEMO.md` (rev 2026-10-10, delivered with this file).

Deadline context: report submission **15/10**; the report needs the demo's results by **13/10** at the
latest. Defense 05–06/11.

Ownership (unchanged, `PROJECT2_SETUP.md` §9.1): Project 2 decides how to build and edits everything in
`web_demo/`, including its own docs. The thesis project edits `src/` and `docs/` only. This file states
what the thesis changed, what the demo must become, how the result is checked, and what the report
needs back. It does not edit any `web_demo/` file.

---

## 1 · What changed on the thesis side

The system the demo re-implements (V1, "rlg": GAE v1 `gae_joint_seed42.pt`, recon + graph-mean latent +
gamma-AEC, equal weights, PELT, fixed operating point) is **retired as the thesis system**. The thesis now
reports the **final system** (git tag `p3-frozen`). Every V1 statement in `web_demo/` docs is stale:
`CLAUDE.md` (model identity, three readouts, source files for parameters, 9.76 s/h),
`THESIS_CONTEXT_FOR_DEMO.md` §2–§6, `SZSCAN_SPEC_v5.md` §1.3, §1.5, §1.6, §1.7, §5.5 (PELT),
§6.3 (robust z-score wording), §6.7 (reconstruction branch, `.pernode.npy` definition), §8 O1/O2/O5,
`DEMO_BUILD_HANDOFF.md` §4, `PROJECT2_SETUP.md` §2 (code list) and §9.2(D) (timing, operating point),
`STEP8_9_PREDEFENSE_CHECKLIST.md` §1 (stage list includes gamma-AEC and PELT).

The earlier application-tier run (V1 app, 16/76 at 52.4 FP/day) and the pre-freeze timings
(9.76 s/h, 10.83 s/h) belong to the earlier system and are **not** reused for the final system.

## 2 · The final system (what the demo must compute)

All code below is in `src/` (read-only for Project 2; import, never copy, never edit).

| stage | definition | defining code |
|---|---|---|
| signal | 18 bipolar channels, 256 Hz; band-pass 0.5–60 Hz + 60 Hz notch on the whole file; 4-s windows; signal-loss window = raw std < 1e-10 V on all 18 channels | `preprocessing.py` constants; same ops as `x1_external.filter_windows` / `file_features` |
| z-score statistics | per subject, per channel mean/std (ddof 1) over **every 10th window of the whole recording** (files in name order, counter over every window), each window filtered with 3-s padding | `x1_external.labelfree_stats` + `window_padded` (label-free rule used for the external validation) |
| graph + node features | CAR → wPLI + AEC (0.5/0.5) → top 20 % edges; band powers (5); 7 added features (log band power ×5, log line length, signed-log kurtosis) | `c1b_build_trainset.graph_and_bp`, `c1b_build_trainset.f7` |
| model | GAE v2 **clean seed 42**, node input 30, GCN 30→64→16, 3,964 params; added features normalised with the training constants in the checkpoint's `.json` (clip ±4 → [0, 1]) | `p2_dump_seeds23.run_model`; checkpoint `data/models_v2/gae_v2_clean_seed42.pt`, sha256 in `docs/PROVENANCE_V2.md` |
| per-channel distance | per channel: LedoitWolf Mahalanobis of the 16-d node latent, fitted on **all non-signal-loss windows of the subject** | as `x1_external.model_outputs` / `p2_test_dump.py` |
| ensemble score | per-channel robust-z (median/MAD) → order statistics 6, 9, 12 of 18 and the channel mean → each minus its centred ±15-min (451-window) running median inside each file → patient percentile → equal mean = ONE score | `e22_test_oneshot.final_scalar` (uses `e17b_latent_family.member`, `p2_scalars.pct`) |
| alarm budget | p_i = clip(q_i, 0.005, 0.02); q_i = share of the patient's 5-window-smoothed mean of the four members' robust-z above k | `p3_levers.member_mean_z`, `q_of`; k, smoothing, floor/cap from `results/p3c_freeze/freeze.json` (point "balanced") |
| detector | per file: centred 5-window mean (signal loss = NaN), threshold = (1 − p_i) quantile of all smoothed values, contiguous runs, merge gaps ≤ 90 s | `p2_scalars.d1_events` |
| onset/offset | per event: ruptures KernelCPD (rbf, min_size 2), 2 change points on the unsmoothed score over the event ± 15 windows; accepted if the inner segment has ≥ 2 windows and a mean above both outer segments, else the detector's boundaries; re-merged | `p3_levers.localize(mode="cpd")` (→ `e18_cpd_localizer.cpd_event`) |
| channel panel | per channel, p95 over the event's windows of \|robust-z\| of the per-channel distance (before the drift correction) | the quantity of `attribution_v8.py` |

The six detector/localizer lines are exactly `e23_test_look7.evaluate` minus its scoring call. Events are
per file (no event crosses a file). Parameters are **read from the files**, never typed.

## 3 · Requirements for the rebuilt demo

1. **Label-free.** The three hard guards and the write guard stay; `test_guards.py` stays green. No
   function that reads labels may be called (the thesis modules contain such functions; import is fine,
   calling is not — a runtime test should prove it).
2. **Only the 8 test subjects**, frozen UI, no evaluation metric and no operating-point parameter in the
   product (the alarm budget p_i is internal).
3. **Panel title text** becomes `Channel-level latent anomaly — Event N`. Neutral XAI wording; no
   localization / SOZ language. Signal-loss windows have no latent → skipped; an event made only of
   signal loss shows "not available".
4. **Timeline row.** The score is now a patient-percentile mean in [0, 1], not a robust z-score. The UI
   label `Seizure Detection Score` stays; SPEC §6.3's wording ("robust z-score, can be negative") must
   change. The zero line falls outside a [0, 1] auto-scale — Project 2 decides (keep no reference line, or
   draw the line at a stated level such as 0.5); never a fake value.
5. **Non-causal by design** (post-hoc review): every per-subject fit needs the whole uploaded recording;
   the flow stays "upload all files → Phase B once per subject → Process".
6. **Interface contract** (§6) if Project 2 writes its own code instead of the reference, so the thesis
   gate and timing scripts run unchanged.

## 4 · Divergence from the thesis system — now ONE item (rewrite SPEC §1.6 and the committee answer)

| item | thesis (CHB-MIT runs) | demo |
|---|---|---|
| per-subject z-score statistics | `data/processed/{subj}_stats.json`: computed **after excluding annotated seizure windows and the 4-h post-seizure buffer** (inherited preprocessing; a label-dependent step the thesis discloses) | every 10th window of the whole recording, label-free (the rule already used for the thesis's external validation) |

The earlier three items are **closed** for the final system:
- per-channel LedoitWolf fits, robust-z, percentiles and q_i are fitted on all windows of the patient,
  label-free, **in the thesis system itself** (author decision 08/10: label-free whole-recording
  per-patient fitting is part of the unsupervised system) → not a divergence;
- no window is dropped and post-ictal segments are scored in the thesis's continuous-timeline protocol
  too (they count as false alarms there) → not a divergence;
- PELT and its background statistics are gone.

Size of the remaining divergence: measured by the identity gate (§5 step 6) on chb03 — thesis statistics
vs label-free statistics, same code. Report as measured; never tune the demo toward the thesis numbers.

## 5 · Work plan (Project 2 → Claude Code; Boti runs the commands)

| step | what | done when |
|---|---|---|
| 0 | Commit the 6 locally modified `web_demo/` docs (they predate this rebuild) so the work starts clean | `git status` clean in `web_demo/` tracked files |
| 1 | Backend on the final system. **Option A (recommended, saves 1–2 days):** review and apply the thesis-written reference implementation `F:/Study/Thesis/Agent/t1_demo/t1_demo_reference.patch` (one commit on top of `f37a7b1`; tested only on synthetic EDFs with a fake GAE — torch is not available in the thesis cloud). **Option B:** write it, keeping §6 | `pytest web_demo/backend/tests` all green on the laptop, including the real-GAE test |
| 2 | UI: panel title; timeline row decision (§3.4); nothing else | screenshots match the locked mockups except the title text |
| 3 | `web_demo/` docs updated by Project 2 (list in §1); `THESIS_CONTEXT_FOR_DEMO.md` replaced by the thesis's rev 2026-10-10; SPEC §1.6 rewritten per §4; BUILD_PROGRESS gets a section for the rebuild | docs no longer describe V1 as current |
| 4 | Real-data smoke: process `chb16` through the real UI (Create New → Process), open Analysis, click an AI event, check panel, export | no error; events, panel and export appear |
| 5 | **Freeze:** commit + tag `szscan-frozen-v3`, push | tag on GitHub |
| 6 | **Identity gate** (thesis script, Boti runs): `python src/t1_demo_gate.py gate --dataset F:/Study/Thesis/Dataset/CHB-MIT` — chb03, seed 42, demo fed the thesis statistics must give the look-#7 counts (detector **7/23**, localized **7/22** tp/fp, read by the script from `results/e23_test_look7/per_subject_seed.csv`); then the label-free run is reported | `results/t1_demo/GATE.md` says PASS. **FAIL ⇒ stop**, send GATE.md to the thesis project; explain by mechanism before any change |
| 7 | **Timing:** `python src/t1_demo_gate.py timing --dataset ...` (chb16, 5 runs, headless = same functions) | `results/t1_demo/TIMING.md` (median s/h + per stage) |
| 8 | **Application tier** (instructions 11.5): old `szscan.db` + `uploads/` moved aside (not deleted); ≥ 75 GB free on F: (estimated 280 h × ~240 MB/h of cache); `batch_ingest.py --all` (or the UI by hand); `export_tier2.py` **before any review**; `python src/t1_app_tier.py --tier2-dir web_demo/report_handback/tier2_v4` | `results/application_eval_v4/SUMMARY.md`; any defect ⇒ the whole 8-subject run is repeated |
| 9 | Checks on the frozen build: network-off run of Create New → Process → Analysis; look at chb06 long files; O4b (where events fall around known seizures, eyes only); screenshots (§7 R4) | notes + PNGs |

Runtimes (estimated, not measured on the laptop): step 6 30–60 min; step 7 30–60 min; step 8 2–4 h
(+ copying); the reference measured ~3.4 s/h Phase A and ~6.6 s/h features on the cloud CPU.

## 6 · Interface contract (needed by `src/t1_demo_gate.py`; the reference implements it)

`web_demo/backend/pipeline_demo.py` must expose:
- `MODEL_TAG`, `WIN_S`;
- `process_subject_headless(edf_paths, cache_dir=None, max_workers=2, stats_override=None, timing=None) -> dict`
  with keys `scores`, `flags`, `dists` ({filename: [n_windows, 18], NaN at signal loss}), `baseline`,
  `stats` ((mean, std) volts), `events` ({filename: [(onset_s, offset_s)]}, localized), `detector`
  (same shape, before the localizer), `budget` (`.top`, `.q`), `n_windows`; `timing` filled with
  `phase_a`, `stats`, `features`, `gae`, `distances_and_score`, `events`, `phase_b`, `stage2`, `total`
  (seconds); Phase A arrays cached as `{stem}.filtered.npy`, `.flag.npy`, `.moments.npy` in `cache_dir`;
- `process_subject_phase_b(filtered, flags, moments, stats_override=None) -> obj` with `.scores`,
  `.dists`, `.stats`;
- `process_subject_events(scores, flags, dists, trace=None) -> (events {filename: [obj .onset_sec,
  .offset_sec]}, budget)`, filling `trace["detector"]`.
`stats_override` exists only for the gate; the application never sets it.
`web_demo/backend/export_tier2.py` must write `files.csv`, `{subject}_events.csv` (columns read by
`src/eval_application_events.py`) and `MANIFEST.txt` with lines `commit <sha>` and
`uncommitted changes in web_demo/backend or src: no|YES`.

## 7 · What the report needs back (send to the thesis project via Boti)

| # | item | form |
|---|---|---|
| R1 | identity gate + label-free effect on chb03 | `results/t1_demo/GATE.md`, `gate.json` (committed) |
| R2 | processing time per hour of EEG on the laptop, median of 5 runs + per stage; plus the real upload-flow time per subject from the application run | `results/t1_demo/TIMING.md`, `results/t1_demo/ingest_timing.csv` |
| R3 | application tier: per subject tp, n_ref, fp, hours; pooled and subject-mean sensitivity, precision, F1, FP/day (scorer counts) | `results/application_eval_v4/SUMMARY.md`, `per_subject.csv`, `pooled.json`, the export + MANIFEST |
| R4 | screenshots for the report figure "Screens of the review application", three panels: (a) recording list with the Create New panel / import; (b) Analysis with the timeline and one AI event selected; (c) channel panel with the review buttons. Real recording with an AI event; no calendar date (only `Recording N, HH:MM:SS`); no internal names on screen | 3 PNG, full resolution |
| R5 | architecture facts for the figure "Architecture of the review application": boxes and arrows as built (browser UI → FastAPI → upload manager → Phase A threads / Phase B + Process worker process → SQLite + per-file cache; thesis modules imported read-only; checkpoint verified by hash; no network) | short list, confirmed against the frozen code |
| R6 | the one-item divergence statement (§4) and the committee answer, rewritten by Project 2 | one paragraph |
| R7 | network-off evidence (what was run, what worked) | two lines |
| R8 | build commit + tag | `szscan-frozen-v3` sha |

Report wording rule (unchanged): no step/phase/prompt/file names (`CC_*`, "fix round", tags) in anything
the committee sees. Numbers only from the committed result files.

## 8 · Project 2 knowledge — add / replace / remove (Boti does this by hand)

**Add** (latest versions are in the repo at `F:\Study\Thesis\Code\`, all pushed):
- `docs\HANDOFF_T1_DEMO_REBUILD.md` (this file) · `docs\DEMO_REBUILD_BRIEF.md` · `docs\PROVENANCE_V2.md`
- `results\p3c_freeze\freeze.json` · `data\models_v2\gae_v2_clean_seed42.json`
- final-system code (read-only): `src\x1_external.py`, `src\c1b_build_trainset.py`, `src\p2_dump_seeds23.py`,
  `src\p2_scalars.py`, `src\e16_recording_baseline.py`, `src\e17b_latent_family.py`, `src\e22_test_oneshot.py`,
  `src\p3_levers.py`, `src\e18_cpd_localizer.py`, `src\e23_test_look7.py`, `src\attribution_v8.py`
- thesis-side scoring (to know the contract, never run inside the demo): `src\t1_demo_gate.py`,
  `src\t1_app_tier.py`, `src\eval_application_events.py`
- `F:\Study\Thesis\Agent\t1_demo\t1_demo_reference.patch` (optional, if Project 2 wants to read the
  reference in chat; Claude Code reads it from disk)

**Replace:** `web_demo\THESIS_CONTEXT_FOR_DEMO.md` (rev 2026-10-10 from the thesis project) · the
`web_demo\backend\*.py` copies with the current files on disk (after step 1, again after step 5) ·
`web_demo\CLAUDE.md`, `SZSCAN_SPEC_v5.md`, `DEMO_BUILD_HANDOFF.md`, `BUILD_PROGRESS.md`,
`PROJECT2_SETUP.md` after Project 2 updates them in step 3.

**Remove** (V1 only, now misleading): `src\ensemble_recipe.py`, `src\cpd_pipeline_v14.py`,
`src\retrain\fp_budget_operating_point.py`, `src\phaseB\latent_anomaly.py`, `src\retrain\retrain_io.py`,
`src\dataprep\compute_gamma_aec.py`. Keep `preprocessing.py`, `graph_construction.py`,
`feature_extraction.py`, `gae_joint.py` (still imported underneath), `szcore_eval.py` (still "know it is
forbidden"), `edf_order.py`.
