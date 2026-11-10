# R2 p1 -- gates and timing (no research number)

| gate | status | summary |
|---|---|---|
| G-data | PASS | 24 new .npz, sha256 = pinned R1_SMOKE hashes |
| D0' | PASS | 24 cases: n_ref = record; non-ictal hours = record (22) / record + added files (chb11, chb21); clean windows = expected |
| R3-projection | PASS | computed estimate 8.67 h on 4 workers + 0.03 h elapsed <= 10.5 h |
| G-const | PASS |  |
| G-vec | PASS |  |
| G-mlp | PASS |  |
| G-const-p | PASS | partition 1: fold constants on the earlier data = the F1 checkpoints' (max rel 0.0e+00); cases, seed, clean counts identical |
| R3.0-gae | PASS | 96 rows, 96 exact, max |dtp| 0, |dfp| 0, own-point k rel 0.0e+00, caught flags differing 0/185 |
| R3.0-mlp | PASS | 96 rows, 96 exact, max |dtp| 0, |dfp| 0, own-point k rel 0.0e+00, caught flags differing 0/185 |

Phases (s): {"views": 4.7, "gate_data": 13.3, "gate_d0": 0.4, "gates_earlier": 15.3, "gate_const_p": 3.8, "r30_read": 0.1}
