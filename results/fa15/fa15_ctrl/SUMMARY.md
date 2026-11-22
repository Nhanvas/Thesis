# fa15_ctrl -- F-A1.5 / PC5 training and scoring (gates and timing; no research number; mode exact)

| gate | status | summary |
|---|---|---|
| G-mod | PASS | r2_r1 76cbe51ff0180d4a, r2_rp 5281446e6168312e (control's code), fa15_run effcdf70588ae6b1 |
| G-data | PASS | 63 files hashed = pinned R1_SMOKE hashes |
| G-const-new | PASS | constants max relative difference 0.0e+00; n_train 270758 |
| G-repro | PASS | mode exact: control seed 4 rescored = rp2 (456 rows, 456 exact, 0 mismatches; 0 error groups differ) |
| G-vec | PASS | train_gae_v2.py --smoke vs tensor loop: max /weight difference/ 0.000e+00 |
| R1.1-training | PASS | seeds [5, 6, 7]: n_train 270758, 3,964 parameters, G2 PASS |
| RUN-complete | PASS | 1368 rows (expected 1368); k per seed {'clean_seed5': 4.26799599116981, 'clean_seed6': 4.1994114667657065, 'clean_seed7': 4.169034492126537} |
| G-worker-sha | PASS | 4 of 4 workers imported r2_r1 76cbe51ff0180d4a, r2_rp 5281446e6168312e, fa15_run effcdf70588ae6b1 |

Phases (s): {"views": 21.4, "gate_data": 23.5, "gate_const_new": 0.8, "D_repro": 278.5, "score_repro": 178.0, "g_repro": 456.8, "gate_vec": 3.7, "train": 12982.8, "D_run": 504.6, "score_run": 811.0}

Tables: `python src/fa15_aggregate.py` (committed before this run).
