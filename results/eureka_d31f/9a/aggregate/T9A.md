# Table T9A — V5 with label-free z-score statistics (EUR_9A)

k: label-free 4.0978, record 4.0677. Per-patient mean after the change point localizer, 4 seeds (sensitivity ± SD over seeds, F1, FP/day). Paired patient bootstrap of the difference with V5 (95 % interval; chb01 + chb21 one unit). REBUILD = record statistics with features rebuilt from the verified EDF (R0), 21 cases with an unchanged file set: the size of the numerical rebuild difference that LF also carries (its level row covers those 21 cases only; its Δ is paired on them). Descriptive; no threshold.

## Arm: each patient's label-free budget (V5's operating point)

| set | system | sensitivity ± SD | F1 | FP/day | seizures detected (4-seed mean, range) | Δ sensitivity vs V5 | Δ F1 vs V5 | Δ FP/day vs V5 |
|---|---|---|---|---|---|---|---|---|
| development | V5 | 0.832 ± 0.014 | 0.225 | 23.2 | 63.00 of 94 (61–64) | — | — | — |
| development | LF | 0.838 ± 0.012 | 0.227 | 22.7 | 63.50 of 94 (62–65) | +0.006 [+0.000, +0.015] | +0.001 [-0.007, +0.009] | -0.5 [-1.1, +0.1] |
| development | LF_krec | 0.838 ± 0.012 | 0.225 | 22.9 | 63.50 of 94 (62–65) | +0.006 [+0.000, +0.014] | -0.001 [-0.010, +0.007] | -0.3 [-0.9, +0.2] |
| development | REBUILD | 0.864 ± 0.011 | 0.236 | 22.0 | 57.25 of 85 (56–58) | +0.000 [+0.000, +0.000] | +0.000 [-0.001, +0.002] | +0.1 [-0.1, +0.3] |
| test | V5 | 0.567 ± 0.019 | 0.180 | 28.7 | 36.25 of 76 (34–38) | — | — | — |
| test | LF | 0.536 ± 0.027 | 0.175 | 27.9 | 34.00 of 76 (31–37) | -0.032 [-0.055, -0.009] | -0.005 [-0.021, +0.010] | -0.9 [-2.2, +0.4] |
| test | LF_krec | 0.536 ± 0.027 | 0.174 | 28.1 | 34.00 of 76 (31–37) | -0.032 [-0.055, -0.009] | -0.006 [-0.023, +0.009] | -0.7 [-2.0, +0.5] |
| test | REBUILD | 0.560 ± 0.025 | 0.176 | 28.8 | 35.75 of 76 (33–38) | -0.008 [-0.018, +0.000] | -0.004 [-0.009, +0.001] | +0.1 [-0.3, +0.3] |

## Arm: fixed 0.5 % budget

| set | system | sensitivity ± SD | F1 | FP/day | seizures detected (4-seed mean, range) | Δ sensitivity vs V5 | Δ F1 vs V5 | Δ FP/day vs V5 |
|---|---|---|---|---|---|---|---|---|
| development | V5 | 0.822 ± 0.009 | 0.262 | 19.2 | 62.25 of 94 (61–63) | — | — | — |
| development | LF | 0.803 ± 0.016 | 0.256 | 19.2 | 61.25 of 94 (60–63) | -0.018 [-0.053, +0.008] | -0.006 [-0.015, +0.002] | -0.0 [-0.4, +0.4] |
| development | LF_krec | 0.803 ± 0.016 | 0.256 | 19.2 | 61.25 of 94 (60–63) | -0.018 [-0.053, +0.008] | -0.006 [-0.016, +0.002] | -0.0 [-0.4, +0.4] |
| development | REBUILD | 0.853 ± 0.009 | 0.275 | 17.6 | 56.50 of 85 (55–57) | +0.000 [+0.000, +0.000] | -0.000 [-0.002, +0.001] | +0.1 [-0.0, +0.2] |
| test | V5 | 0.498 ± 0.010 | 0.161 | 23.8 | 25.50 of 76 (25–26) | — | — | — |
| test | LF | 0.462 ± 0.022 | 0.149 | 23.8 | 23.00 of 76 (21–25) | -0.035 [-0.062, -0.009] | -0.012 [-0.026, -0.002] | +0.0 [-0.8, +0.9] |
| test | LF_krec | 0.462 ± 0.022 | 0.149 | 23.8 | 23.00 of 76 (21–25) | -0.035 [-0.062, -0.009] | -0.012 [-0.026, -0.002] | +0.0 [-0.8, +0.9] |
| test | REBUILD | 0.494 ± 0.020 | 0.159 | 23.8 | 25.25 of 76 (24–27) | -0.004 [-0.017, +0.009] | -0.002 [-0.009, +0.003] | +0.0 [-0.3, +0.3] |

## Change of the statistics (label-free vs record), per case

| case | median relative change of channel SD | largest |change| | median mean shift (record SD) |
|---|---|---|---|
| chb01 | -0.578% | 3.741% | -0.0010 |
| chb02 | +0.473% | 7.022% | -0.0001 |
| chb03 | +2.667% | 9.848% | -0.0001 |
| chb04 | -1.866% | 4.666% | -0.0001 |
| chb05 | +1.824% | 4.158% | +0.0000 |
| chb06 | +5.032% | 11.523% | -0.0003 |
| chb07 | +1.581% | 3.131% | +0.0000 |
| chb08 | +5.407% | 12.113% | -0.0000 |
| chb09 | -0.583% | 3.614% | -0.0000 |
| chb10 | +0.528% | 3.473% | -0.0000 |
| chb11 | +2.987% | 8.649% | -0.0002 |
| chb12 | -0.641% | 2.438% | -0.0002 |
| chb13 | +0.563% | 4.735% | -0.0004 |
| chb14 | -0.073% | 1.045% | +0.0007 |
| chb15 | +1.356% | 5.454% | -0.0012 |
| chb16 | +0.917% | 8.778% | +0.0003 |
| chb17 | -2.899% | 11.602% | +0.0001 |
| chb18 | +23.668% | 57.977% | +0.0000 |
| chb19 | +11.394% | 16.003% | -0.0001 |
| chb20 | -3.356% | 6.451% | -0.0004 |
| chb21 | +0.896% | 3.271% | -0.0001 |
| chb22 | +0.277% | 2.046% | -0.0003 |
| chb23 | -2.623% | 7.415% | -0.0001 |
