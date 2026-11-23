# Synthetic test of the M2L code (chat F2-03, delivery M2L1, 23/11/2026)

`src/m2l_synthetic_test.py`, build container (2 CPU cores; python 3.13.18, numpy 2.5.3, scipy 1.18.1, scikit-learn 1.9.1,
pandas 3.0.5, mne 1.12.1, torch 2.15.0, torch_geometric 2.7.0, ruptures 1.1.10, timescoring 0.0.7). Synthetic EDF only.

Code tested (sha256, first 16 hex): `m2l_core.py` a8265503bcc35256, `m2l_run.py` 822f60120f5fa50e, `m2l_read.py`
2e7a63ac0b6a515f, `m2l_make_notebooks.py` 3a94dbf8ce070f21; record modules as asserted in the notebooks.

| check | result |
|---|---|
| U1 selection rule and minimum-length rule on hand-made tables (none → P0; candidate; sensitivity guard; ties F → LW → R; none → 30 min) | PASS |
| U2 segment cuts (never split a seizure, cover the recording), top = 0 → no event, statistics R / B, MCD = independent `MinCovDet` | PASS |
| P1 `M2L_L2_REC`: G-raw, G-data, G-stats1, G-feat1, G-worker[smoke], G-k, R1.0-dev, G-chain (180 rows, 56 error pairs = record), G-split, PROJ, G-worker[build], G-struct[dev], G-worker[score_dev]; 1,080 rows; no .npz / EDF in the output | PASS (328 s) |
| P1 `M2L_L2_ROB`: the same + G-c | PASS (333 s) |
| R2 reader `--l2`: A0, A1, selection by the rule | PASS |
| P4 `M2L_L3_SHORT_A` / `_B` (segments 2, 3 / 4, 5 min in this world) and reader `--l3short` | PASS (735 s, 537 s) |
| P4 `M2L_L3_EVAL` (G-sel, G-raw incl. Siena, G-data, R1.0-test, GE, G-struct[test], G-struct[ext]) and reader `--l3` | PASS (207 s) |
| P2 (non-circular) PN01, one recording: per-recording record statistics = x1_external label-free statistics | PASS (mean 5.6e-18 of SD, SD 0) |
| P3 (non-circular) PN01: per-recording rows of R-LW-F = the V5 chain on the x1_external .npz at the same k | PASS |
| NEG1 RB1c constants edited → STOP at G-c · NEG2 committed chb08 statistics +0.1 % → STOP at G-feat1 · NEG3 k × 1.05 inside G-chain (test hook) → STOP at G-chain · NEG4 is_buffer flipped (R1.0 passes) → STOP at G-struct[dev] · NEG5 selection.json missing → STOP at G-sel · NEG6 edited module → STOP before the run | PASS (413 s) |

Full positive run 2,420 s; negatives re-run on the same world with `--neg-only` (the test script was restructured
between the two runs to allow that; the code under test is unchanged). Not covered: real amplitudes, runtime and memory
on Kaggle (the smoke measures them; PROJ stops above 10.5 h).
