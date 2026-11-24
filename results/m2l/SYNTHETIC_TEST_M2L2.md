# Synthetic test of the M2L code, delivery M2L2 (chat F2-03, 24/11/2026)

Changes since M2L1 (written after the L2 outputs, before any L3 output; L2's code path unchanged):
- `m2l_core.py`: new `rec_job_multi` / `_one_segment` — L3-short reads each EDF once and processes all its segments of
  every length in one job (one process per segment would have cost about 10 h of process start-up for the 5- and 10-min
  segments alone, computed from about 12,000 segments); each segment is processed exactly as `rec_job` processes a
  recording. `rec_job` (L2, L3-eval) is unchanged.
- `m2l_run.py`: L3-short uses the batched jobs; **PROJ gate added to L3-short and L3-eval** (DESIGN §8 lists PROJ for all
  notebooks; M2L1 had it only in L2): one job measured with one worker, rate × 1.45 (L2's measured build time / its
  projection: 18,154 s / 12,488 s and 16,664 s / 11,434 s), LPT over the files, STOP above 10.5 h.
- `m2l_read.py`: PROJ added to the gates the L3 readings require (A0). The `--l2` reading is unchanged.
- `m2l_make_notebooks.py`: runtimes of the L3 notebooks (computed from L2's measured job times).

Code tested (sha256, first 16 hex): `m2l_core.py` 9690cac7f91f52b2, `m2l_run.py` 4263c38f81c7adb8, `m2l_read.py`
af59fe0fa231afd5. Build container: 2 CPU cores, python 3.13.18, numpy 2.5.3, scikit-learn 1.9.1, torch 2.15.0, mne 1.12.1.

| check | result |
|---|---|
| U1 rules, U2 units | PASS |
| P1 `M2L_L2_REC`, `M2L_L2_ROB` (every gate; 1,080 rows; no .npz / EDF) | PASS (256 s, 258 s) |
| R2 reader `--l2` | PASS |
| P4 `M2L_L3_SHORT_A` / `_B` with PROJ (segments 2, 3 / 4, 5 min) and reader `--l3short` | PASS (276 s, 272 s; M2L1: 735 s, 537 s) |
| P4 `M2L_L3_EVAL` with PROJ and reader `--l3` | PASS (161 s) |
| P2 PN01 per-recording statistics = x1_external label-free statistics | PASS (mean 5.6e-18 of SD, SD 0) |
| P3 PN01 per-recording rows = the V5 chain on the x1_external .npz at the same k | PASS |
| NEG1 G-c · NEG2 G-feat1 · NEG3 G-chain · NEG4 G-struct[dev] · NEG5 G-sel · NEG6 edited module | PASS |

Full run (positives and negatives, fresh world) 1,854 s. Not covered: real amplitudes, runtime and memory on Kaggle
(PROJ measures one real job and stops above 10.5 h).
