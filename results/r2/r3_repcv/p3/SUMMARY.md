# R2 p3 -- gates and timing (no research number)

| gate | status | summary |
|---|---|---|
| G-data | PASS | 24 new .npz, sha256 = pinned R1_SMOKE hashes |
| D0' | PASS | 24 cases: n_ref = record; non-ictal hours = record (22) / record + added files (chb11, chb21); clean windows = expected |
| R3-projection | PASS | computed estimate 8.75 h on 4 workers + 0.02 h elapsed <= 10.5 h |
| G-const | PASS |  |
| G-vec | PASS |  |
| G-mlp | PASS |  |
| G-const-p | PASS | partition 3: fold constants on the earlier data = the F1 checkpoints' (max rel 0.0e+00); cases, seed, clean counts identical |
| R3.0-gae | PASS | 96 rows, 96 exact, max |dtp| 0, |dfp| 0, own-point k rel 0.0e+00, caught flags differing 0/185 |
| R3.0-mlp | PASS | 96 rows, 96 exact, max |dtp| 0, |dfp| 0, own-point k rel 0.0e+00, caught flags differing 0/185 |

Phases (s): {"views": 5.3, "gate_data": 15.6, "gate_d0": 0.3, "gates_earlier": 17.8, "gate_const_p": 3.4, "r30_read": 0.1}
