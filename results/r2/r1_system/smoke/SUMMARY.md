# R1 smoke — gates and timing (no research number)

| gate | status | summary |
|---|---|---|
| G-data | PASS | 24 CHB-MIT + 15 external cases; G-feat re-read on 13 cases |
| G-const | PASS | max relative difference 0.00e+00 |
| G-count | PASS | 15 cases, clean windows = committed metas |
| R1.0-dev | PASS | p3c_freeze: 48 rows, 112 error pairs; 0 differ |
| R1.0-test | PASS | e23 16 rows + 55 error pairs, look #6 8 rows, run_budget consistency 0 differ; 0 differ from the record |
| GE | PASS | 16 rows, 16 exact, max |dtp| 0, max |dfp| 0 (tolerance 1 / 2) |
| G-vec | PASS | train_gae_v2.py --smoke vs tensor loop: max |weight difference| 0.000e+00 |
| R1.1-training-smoke | PASS | seeds [42, 1, 2, 3]: n_train 270758, 3,964 parameters, G2 PASS |

Phases (s): {"views": 27.3, "gate_data": 41.8, "gate_const_count": 1.6, "D_r10": 54.2, "score_r10": 30.3, "gate_vec": 3.6, "train_smoke": 206.3, "D_path_check": 69.5, "score_path_check": 22.1}

