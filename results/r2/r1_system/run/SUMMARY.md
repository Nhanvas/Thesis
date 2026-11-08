# R1 run — gates and timing (no research number)

| gate | status | summary |
|---|---|---|
| G-data | PASS | 24 CHB-MIT + 15 external cases; G-feat re-read on 21 cases |
| G-const | PASS | max relative difference 0.00e+00 |
| G-count | PASS | 15 cases, clean windows = committed metas |
| G-k | PASS | k 4.067744299 vs record 4.067744299 (relative 0.0e+00) |
| R1.0-dev | PASS | p3c_freeze: 720 rows, 987 error pairs; 0 differ |
| R1.0-test | PASS | e23 128 rows + 296 error pairs, look #6 64 rows, run_budget consistency 0 differ; 0 differ from the record |
| GE | PASS | 240 rows, 148 exact, max |dtp| 1, max |dfp| 2 (tolerance 1 / 2) |
| G-vec | PASS | train_gae_v2.py --smoke vs tensor loop: max |weight difference| 0.000e+00 |
| R1.1-training | PASS | seeds [42, 1, 2, 3]: n_train 270758, 3,964 parameters, G2 PASS |

Phases (s): {"views": 26.9, "gate_data": 51.6, "gate_const_count": 1.9, "D_r10": 535.5, "score_r10": 243.3, "gate_vec": 3.3, "train": 14052.9, "D_run": 550.8, "score_run": 200.5, "D_cf": 548.1, "score_cf": 198.2, "counterfactual": 947.2}

