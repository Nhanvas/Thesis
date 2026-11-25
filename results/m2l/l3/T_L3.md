# T_L3 — SzScan 1.0 baseline: the per-recording protocol scored once

Arm B-MCD-F (k 9.914209), minimum recording length 30 min; V5 checkpoints, 4 seeds; per-patient means after the localizer; paired patient bootstrap. V5 = the record rows reproduced in the same session (test: e23; chb24 / Siena: V0 from the rebuilt external features). L0 (test) = EUR_9A label-free patient-level statistics. Test is descriptive (it entered earlier decisions); Siena is the external set.

| set | system | sensitivity ± seed SD | F1 | FP/day | Δ sens vs V5 | Δ F1 vs V5 | Δ FP/day vs V5 | Δ sens vs L0 |
|---|---|---|---|---|---|---|---|---|
| test | V5 | 0.567 ± 0.019 | 0.180 | 28.7 | — | — | — | — |
| test | L0 | 0.536 ± 0.027 | 0.175 | 27.9 | — | — | — | — |
| test | L3 | 0.562 ± 0.019 | 0.107 | 52.0 | -0.005 [-0.064, +0.047] | -0.073 [-0.117, -0.039] | +23.3 [+16.1, +30.7] | +0.027 [-0.039, +0.089] |
| test | L3-FX | 0.552 ± 0.024 | 0.111 | 48.1 | -0.015 [-0.075, +0.042] | -0.069 [-0.111, -0.035] | +19.4 [+13.3, +25.9] | — |
| chb24 | V5 | 0.844 ± 0.036 | 0.500 | 27.8 | — | — | — | — |
| chb24 | L3 | 0.984 ± 0.031 | 0.403 | 52.8 | +0.141 | -0.097 | +25.0 | — |
| chb24 | L3-FX | 0.953 ± 0.031 | 0.481 | 36.6 | +0.109 | -0.019 | +8.8 | — |
| siena | V5 | 0.645 ± 0.092 | 0.233 | 40.6 | — | — | — | — |
| siena | L3 | 0.540 ± 0.026 | 0.252 | 31.2 | -0.105 [-0.281, +0.036] | +0.019 [-0.065, +0.110] | -9.4 [-20.0, +1.8] | — |
| siena | L3-FX | 0.521 ± 0.018 | 0.250 | 29.5 | -0.124 [-0.295, +0.011] | +0.018 [-0.067, +0.110] | -11.1 [-22.4, +0.3] | — |

## Recordings under the minimum length (seed 42 rows)

| set | recordings | under the minimum | seizures in them | recordings with no event |
|---|---|---|---|---|
| chb24 | 22 | 1 | 0 | 0.045 |
| siena | 41 | 0 | 0 | 0.000 |
| test | 231 | 0 | 0 | 0.000 |
