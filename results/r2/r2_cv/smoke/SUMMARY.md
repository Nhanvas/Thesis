# R2 smoke -- gates and timing (no research number)

| gate | status | summary |
|---|---|---|
| G-data | PASS | 24 new .npz, sha256 = pinned R1_SMOKE hashes |
| D0' | PASS | 24 cases: n_ref = record; non-ictal hours = record (22) / record + added files (chb11, chb21); clean windows = expected |
| G-const | PASS |  |
| G-vec | PASS |  |
| G-mlp | PASS |  |
| R2.0-gae (GG0) | PASS | committed GAE fold models = results/v9_x3; [] |
| R2.0-if | PASS | 96 rows, 96 exact, max |dtp| 0, |dfp| 0, k rel 0.0e+00 (exact) |
| R2.0-hgb | PASS | 96 rows, 96 exact, max |dtp| 0, |dfp| 0, k rel 2.4e-11 (exact) |
| R2.0-svm | PASS | 20 rows, 20 exact, max |dtp| 0, |dfp| 0, k rel 0.0e+00 (exact) |
| R2.0-mlp | PASS | 96 rows, 96 exact, max |dtp| 0, |dfp| 0, k rel 0.0e+00 (tolerance) |
| R2.0-cnn | n/a | CNN checkpoints not in the pinned repository; not gated |

Phases (s): {"views": 6.1, "gate_data": 12.8, "gate_d0": 0.4, "gates_earlier": 18.2, "r20_read": 0.2}
