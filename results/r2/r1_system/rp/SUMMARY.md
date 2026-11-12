# RP_RUN — gates and timing (no research number; mode exact)

| gate | status | summary |
|---|---|---|
| G-data | PASS | 63 files hashed = pinned R1_SMOKE hashes |
| G-const-new | PASS | constants max relative difference 0.0e+00; n_train 270758 |
| RP.0 | PASS | mode exact: 1824 rows (1824 exact), 2210 error pairs (0 groups differ), q 0 differ, k relative 0.0e+00 |
| G-vec | PASS | train_gae_v2.py --smoke vs tensor loop: max |weight difference| 0.000e+00 |
| G-val | PASS | validation loss of the 4 R1 checkpoints recomputed: max relative difference 0.0e+00 |
| R1.1-training | PASS | seeds [4]: n_train 270758, 3,964 parameters, G2 PASS |
| RP2-complete | PASS | 2280 rows (expected 2280); per-window scores of 23 cases |
| RP3-demo | PASS | demo model = seed 3 (validation losses {"1": 0.020844111434912032, "2": 0.020848997497762697, "3": 0.020768452966321658, "4": 0.02080145203665401}) |

Phases (s): {"views": 45.0, "gate_data": 31.2, "gate_const_new": 0.8, "D_rp0": 576.0, "score_rp0": 218.5, "rp0": 872.0, "gate_vec": 3.9, "gate_val": 21.8, "train": 9175.2, "D_s4": 297.1, "merge_rp": 2.0, "score_rp": 250.4, "rp2": 633.9}

Tables: `python src/r2_rp_aggregate.py --rp results/r2/r1_system/rp` (committed before this run).
