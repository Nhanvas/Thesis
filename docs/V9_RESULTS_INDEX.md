# V9 results index

One row per V9 task. Full detail is in each report (`F:/Study/Thesis/Defense/v9_reports/`, moved
there from `Agent/inbox/` by V9-CLEANUP); this is a pointer table, not a summary of findings.

| Task | Question | Script | Results dir | Commit | Report |
|---|---|---|---|---|---|
| T1 | SzScan login failure + cold-start reliability -- diagnose and fix | `web_demo/` (no new `src/v9_*.py`; diagnosis-then-fix) | n/a (fix only) | `7c10842` (fixes + chb24 allowlist), `a05eff1` (start/stop launchers) | `V9_T1_REPORT.md` |
| T2 | Hospital EEG files (clin01, clin02): can the final system run on them; is there anything usable for the committee? | none (header/signal inspection only) | `F:/Study/Thesis/Defense/clinical/` (outside repo, never committed -- privacy rule) | n/a | `V9_T2_REPORT.md` |
| T3 | Failure anatomy of the final frozen system (seed 42, balanced point) -- Part A | `src/v9_anatomy.py` | `results/v9_anatomy/` | `0df7dc1` | `V9_T3_REPORT.md` |
| T4 | Siena verification on all 14 patients (T3 only had 3) | `src/v9_anatomy.py --siena-full`, `src/v9_eeg_samples.py --siena-full` | `results/v9_anatomy/siena14/` | `c5d5942` | `V9_T4_REPORT.md` |
| C1 | Run the final system on clin01/clin02 (qualitative, privacy-safe, no seizure annotation) | `src/v9_clinical_run.py` | `F:/Study/Thesis/Defense/clinical/run/` (outside repo, never committed except the script) | `5dfa6ad` | `V9_C1_REPORT.md` |
| E1 | Does the graph autoencoder help? Non-graph baselines (Mahalanobis/IsolationForest/kNN) on the identical pipeline | `src/v9_e1_baselines.py` | `results/v9_e1/` | `cc0e2ce` | `V9_E1_REPORT.md` |
| E1b | Give the winning arms (B4, F) their own fair operating point, then evaluate once | `src/v9_e1b_calibrate.py` | `results/v9_e1b/` | `0a1eb4b` | `V9_E1B_REPORT.md` |
| E2 | Paired comparison + competing-anomaly (artifact) veto -- what are the false alarms | `src/v9_e2_veto.py` | `results/v9_e2/` | `de9134f` | `V9_E2_REPORT.md` |
| E3 | Short-seizure branch (multi-scale score) for the <=20s miss | `src/v9_e3_short.py` | `results/v9_e3/` | `9bb5b85` | `V9_E3_REPORT.md` |
| E4 | kNN baseline (B4) on every CHB-MIT case -- which patients are actually hard | `src/v9_e4_knn24.py` | `results/v9_e4/` | `66a9bcb` | `V9_E4_REPORT.md` |
| V1 | Real-EEG evidence for every claim the committee questioned (hard patients, Siena vs CHB-MIT, web-demo events, false-alarm types, model comparison, attribution concordance) | `src/v9_eeg_evidence.py` | `results/v9_v1/` | `7f171a0` (first attempt crashed the laptop; resumed and fixed in the same commit) | `V9_V1_REPORT.md` |

Tag `v9-results` marks the state after all of the above (plus the V9-CLEANUP commits) landed.

## Notes
- T2 and C1 touch real clinical EDFs (clin01, clin02); per `web_demo/CLAUDE.md`-style privacy rules
  repeated in their own prompts, nothing from those two tasks enters this repo except C1's wrapper
  script -- their outputs live only under `F:/Study/Thesis/Defense/clinical/`.
- V9-V1's first attempt (`docs/prompts/V9_V1_EEG_EVIDENCE.md`) froze the laptop; the fix (a windowed
  Siena reader, verified against the frozen pipeline) and the full resumed run are both in `7f171a0`
  -- see `docs/prompts/V9_V1_RESUME.md` and `V9_V1_REPORT.md` for what happened and why.
- `results/v9_anatomy/xcache/` and each experiment's `_parts/`/`_m/` subfolders are gitignored,
  regenerable caches (rerun the experiment's own script); not part of any commit above.

## Added 31/10 (V9 part 2)

| Task | Question | Script | Results dir | Commit | Report |
|---|---|---|---|---|---|
| V1-FIX | Fix figure defects; channel-count slide figure; chb06 background check | `src/v9_eeg_evidence.py` | `results/v9_v1/fix/` | `7dd9869` | `V9_V1_FIX_REPORT.md` |
| X1 | Are focal seizures missed because of the order-statistic members? 3rd-largest member | `src/v9_x1_focal.py` | `results/v9_x1/` | `cc5e73c` | `V9_X1_REPORT.md` |
| X3 | 4-fold patient-wise cross-validation of the GAE over all CHB-MIT cases (Kaggle), kNN and GAE + kNN on identical inputs, matched-FP and paired F1/precision | `src/v9_x3_*.py` | `results/v9_x3/` | `039bd16`, `1a6c904`, `d131bb4`, `f3ff19a` | `V9_X3_PREP_REPORT.md`, `V9_X3_REPORT.md` |
| X6 | Does ASR (artifact removal) delete seizure activity? power and contrast | `src/v9_x6_asr.py` | `results/v9_x6/` | `5c3d1ef` | `V9_X6_REPORT.md`, `V9_FINAL_REPORT.md` |
| FINAL | Hard patients on three detectors; Siena gap decomposition; slide figure pack; number check | `src/v9_final_*.py` | `results/v9_final/` | `a1c28ab`, `4bcfb60` | `V9_FINAL_REPORT.md` |

Tag `v9-final` marks the state after all of the above.
