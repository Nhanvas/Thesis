# Table T_PC6 — edge type of the graph (retraining, Kaggle CPU)

Design `results/eureka_d37f/DESIGN_PC6.md` (written before the run). 11a = graph of wPLI only, 11b = graph of AEC only (top 20 %), retrained with the thesis recipe, 8 seeds each; control R0 = PC7's primary seeds (N = 16; rows read). Per-patient means, own label-free point, after the localizer; development primary. Two-level bootstrap, B = 10000.

## Machines

| run | arm | CPU model | G-pc7rep | ms per step | runtime h | seeds skipped |
|---|---|---|---|---|---|---|
| pc6_11a | 11a | Intel(R) Xeon(R) CPU @ 2.20GHz | DIFF | 8.15–8.62 | 8.751 | [] |
| pc6_11b | 11b | Intel(R) Xeon(R) CPU @ 2.20GHz | DIFF | 8.02–8.48 | 8.592 | [] |

## R1 — arm − R0 (development primary)

| comparison | set | metric | seeds | Δ [95 %] | reading | wording |
|---|---|---|---|---|---|---|
| 11a - R0 | development | sens | 8 / 16 | -0.086 [-0.161, -0.021] | primary | loses |
| 11b - R0 | development | sens | 8 / 16 | -0.030 [-0.087, +0.026] | primary | no measurable difference |
| 11a - R0 | development | f1 | 8 / 16 | -0.112 [-0.169, -0.066] | primary | loses |
| 11b - R0 | development | f1 | 8 / 16 | -0.013 [-0.040, +0.014] | primary | no measurable difference |
| 11a - R0 | development | fa | 8 / 16 | +18.0 [+13.1, +23.9] | primary | more false alarms |
| 11b - R0 | development | fa | 8 / 16 | +1.9 [-1.0, +5.7] | primary | no measurable difference |
| 11a - R0 | test | sens | 8 / 16 | -0.144 [-0.286, -0.010] | descriptive | loses |
| 11b - R0 | test | sens | 8 / 16 | -0.047 [-0.183, +0.080] | descriptive | no measurable difference |
| 11a - R0 | test | f1 | 8 / 16 | -0.073 [-0.117, -0.030] | descriptive | loses |
| 11b - R0 | test | f1 | 8 / 16 | -0.032 [-0.067, +0.001] | descriptive | no measurable difference |
| 11a - R0 | test | fa | 8 / 16 | +12.7 [+8.5, +17.3] | descriptive | more false alarms |
| 11b - R0 | test | fa | 8 / 16 | +3.1 [-0.3, +6.6] | descriptive | no measurable difference |
| 11a - R0 | chb24 | sens | 8 / 16 | -0.191 [—, —] | descriptive | descriptive (one patient) |
| 11b - R0 | chb24 | sens | 8 / 16 | +0.137 [—, —] | descriptive | descriptive (one patient) |
| 11a - R0 | chb24 | f1 | 8 / 16 | -0.169 [—, —] | descriptive | descriptive (one patient) |
| 11b - R0 | chb24 | f1 | 8 / 16 | +0.053 [—, —] | descriptive | descriptive (one patient) |
| 11a - R0 | chb24 | fa | 8 / 16 | +13.5 [—, —] | descriptive | descriptive (one patient) |
| 11b - R0 | chb24 | fa | 8 / 16 | +1.0 [—, —] | descriptive | descriptive (one patient) |
| 11a - R0 | siena | sens | 8 / 16 | -0.051 [-0.164, +0.084] | descriptive | no measurable difference |
| 11b - R0 | siena | sens | 8 / 16 | -0.045 [-0.169, +0.092] | descriptive | no measurable difference |
| 11a - R0 | siena | f1 | 8 / 16 | -0.084 [-0.127, -0.047] | descriptive | loses |
| 11b - R0 | siena | f1 | 8 / 16 | -0.030 [-0.071, +0.010] | descriptive | no measurable difference |
| 11a - R0 | siena | fa | 8 / 16 | +16.2 [+9.2, +23.6] | descriptive | more false alarms |
| 11b - R0 | siena | fa | 8 / 16 | +3.9 [+0.4, +7.6] | descriptive | more false alarms |

## R1m — arm − R0 with the machine-matched control (secondary)

| comparison | set | metric | seeds | Δ [95 %] | reading | wording |
|---|---|---|---|---|---|---|
| 11a - R0 (control DIFF) | development | sens | 8 / 8 | -0.073 [-0.147, -0.010] | secondary | loses |
| 11a - R0 (control DIFF) | development | f1 | 8 / 8 | -0.107 [-0.166, -0.061] | secondary | loses |
| 11a - R0 (control DIFF) | development | fa | 8 / 8 | +17.8 [+13.0, +23.7] | secondary | more false alarms |
| 11a - R0 (control DIFF) | test | sens | 8 / 8 | -0.131 [-0.281, +0.009] | secondary | no measurable difference |
| 11a - R0 (control DIFF) | test | f1 | 8 / 8 | -0.069 [-0.115, -0.025] | secondary | loses |
| 11a - R0 (control DIFF) | test | fa | 8 / 8 | +12.7 [+8.4, +17.3] | secondary | more false alarms |
| 11a - R0 (control DIFF) | chb24 | sens | 8 / 8 | -0.172 [—, —] | secondary | descriptive (one patient) |
| 11a - R0 (control DIFF) | chb24 | f1 | 8 / 8 | -0.170 [—, —] | secondary | descriptive (one patient) |
| 11a - R0 (control DIFF) | chb24 | fa | 8 / 8 | +14.9 [—, —] | secondary | descriptive (one patient) |
| 11a - R0 (control DIFF) | siena | sens | 8 / 8 | -0.055 [-0.178, +0.082] | secondary | no measurable difference |
| 11a - R0 (control DIFF) | siena | f1 | 8 / 8 | -0.090 [-0.141, -0.046] | secondary | loses |
| 11a - R0 (control DIFF) | siena | fa | 8 / 8 | +17.9 [+10.6, +25.8] | secondary | more false alarms |
| 11b - R0 (control DIFF) | development | sens | 8 / 8 | -0.017 [-0.075, +0.040] | secondary | no measurable difference |
| 11b - R0 (control DIFF) | development | f1 | 8 / 8 | -0.008 [-0.038, +0.023] | secondary | no measurable difference |
| 11b - R0 (control DIFF) | development | fa | 8 / 8 | +1.8 [-1.2, +5.4] | secondary | no measurable difference |
| 11b - R0 (control DIFF) | test | sens | 8 / 8 | -0.034 [-0.171, +0.097] | secondary | no measurable difference |
| 11b - R0 (control DIFF) | test | f1 | 8 / 8 | -0.028 [-0.065, +0.007] | secondary | no measurable difference |
| 11b - R0 (control DIFF) | test | fa | 8 / 8 | +3.1 [-0.3, +6.7] | secondary | no measurable difference |
| 11b - R0 (control DIFF) | chb24 | sens | 8 / 8 | +0.156 [—, —] | secondary | descriptive (one patient) |
| 11b - R0 (control DIFF) | chb24 | f1 | 8 / 8 | +0.052 [—, —] | secondary | descriptive (one patient) |
| 11b - R0 (control DIFF) | chb24 | fa | 8 / 8 | +2.4 [—, —] | secondary | descriptive (one patient) |
| 11b - R0 (control DIFF) | siena | sens | 8 / 8 | -0.048 [-0.174, +0.089] | secondary | no measurable difference |
| 11b - R0 (control DIFF) | siena | f1 | 8 / 8 | -0.037 [-0.079, +0.003] | secondary | no measurable difference |
| 11b - R0 (control DIFF) | siena | fa | 8 / 8 | +5.6 [+1.8, +9.6] | secondary | more false alarms |

## R5 — 11a − 11b (descriptive)

| comparison | set | metric | seeds | Δ [95 %] | reading | wording |
|---|---|---|---|---|---|---|
| 11a - 11b | development | sens | 8 / 8 | -0.056 [-0.124, -0.002] | descriptive | loses |
| 11a - 11b | development | f1 | 8 / 8 | -0.099 [-0.158, -0.046] | descriptive | loses |
| 11a - 11b | development | fa | 8 / 8 | +16.1 [+8.6, +23.3] | descriptive | more false alarms |
| 11a - 11b | test | sens | 8 / 8 | -0.098 [-0.294, +0.075] | descriptive | no measurable difference |
| 11a - 11b | test | f1 | 8 / 8 | -0.041 [-0.093, +0.009] | descriptive | no measurable difference |
| 11a - 11b | test | fa | 8 / 8 | +9.6 [+4.1, +15.6] | descriptive | more false alarms |
| 11a - 11b | chb24 | sens | 8 / 8 | -0.328 [—, —] | descriptive | descriptive (one patient) |
| 11a - 11b | chb24 | f1 | 8 / 8 | -0.223 [—, —] | descriptive | descriptive (one patient) |
| 11a - 11b | chb24 | fa | 8 / 8 | +12.5 [—, —] | descriptive | descriptive (one patient) |
| 11a - 11b | siena | sens | 8 / 8 | -0.007 [-0.137, +0.120] | descriptive | no measurable difference |
| 11a - 11b | siena | f1 | 8 / 8 | -0.054 [-0.115, -0.005] | descriptive | loses |
| 11a - 11b | siena | fa | 8 / 8 | +12.3 [+4.7, +20.3] | descriptive | more false alarms |

Machine-matched control: {"11a": {"arm_rep": "DIFF", "control_seeds": ["clean_seed12", "clean_seed13", "clean_seed14", "clean_seed15", "clean_seed16", "clean_seed17", "clean_seed18", "clean_seed19"]}, "11b": {"arm_rep": "DIFF", "control_seeds": ["clean_seed12", "clean_seed13", "clean_seed14", "clean_seed15", "clean_seed16", "clean_seed17", "clean_seed18", "clean_seed19"]}}

## Means over seeds

| set | variant | seeds | sensitivity | F1 | FP/day |
|---|---|---|---|---|---|
| development | V0 | 4 | 0.832 ± 0.014 | 0.225 ± 0.009 | 23.2 ± 0.6 |
| development | R0 | 16 | 0.803 ± 0.029 | 0.225 ± 0.012 | 22.7 ± 0.7 |
| development | 11a | 8 | 0.717 ± 0.025 | 0.113 ± 0.006 | 40.8 ± 1.2 |
| development | 11b | 8 | 0.773 ± 0.032 | 0.212 ± 0.009 | 24.7 ± 1.3 |
| test | V0 | 4 | 0.567 ± 0.019 | 0.180 ± 0.009 | 28.7 ± 1.3 |
| test | R0 | 16 | 0.523 ± 0.048 | 0.163 ± 0.015 | 29.6 ± 1.1 |
| test | 11a | 8 | 0.379 ± 0.060 | 0.090 ± 0.010 | 42.3 ± 1.5 |
| test | 11b | 8 | 0.476 ± 0.046 | 0.131 ± 0.012 | 32.7 ± 1.2 |
| chb24 | V0 | 4 | 0.844 ± 0.036 | 0.500 ± 0.013 | 27.8 ± 1.1 |
| chb24 | R0 | 16 | 0.801 ± 0.100 | 0.489 ± 0.045 | 26.7 ± 3.7 |
| chb24 | 11a | 8 | 0.609 ± 0.110 | 0.320 ± 0.055 | 40.2 ± 6.1 |
| chb24 | 11b | 8 | 0.938 ± 0.067 | 0.542 ± 0.028 | 27.7 ± 3.6 |
| siena | V0 | 4 | 0.645 ± 0.092 | 0.233 ± 0.029 | 40.6 ± 1.5 |
| siena | R0 | 16 | 0.643 ± 0.066 | 0.223 ± 0.018 | 41.1 ± 2.6 |
| siena | 11a | 8 | 0.591 ± 0.039 | 0.139 ± 0.010 | 57.3 ± 3.7 |
| siena | 11b | 8 | 0.598 ± 0.042 | 0.193 ± 0.019 | 45.0 ± 1.8 |

## R4 — events at each budget (CPD stage; per-seed means)

| set | budget | variant | seeds | events | seizures found | false alarms | s per event | flagged time % |
|---|---|---|---|---|---|---|---|---|
| development | fixed | 11a | 8 | 947 | 53.4 / 94 | 894 | 44.4 | 1.73 |
| development | fixed | 11b | 8 | 613 | 53.6 / 94 | 559 | 56.0 | 1.41 |
| development | fixed | R0 | 16 | 618 | 60.1 / 94 | 558 | 56.4 | 1.44 |
| development | fixed | V0 | 4 | 610 | 62.2 / 94 | 548 | 56.0 | 1.41 |
| development | own | 11a | 8 | 1215 | 55.0 / 94 | 1160 | 45.3 | 2.27 |
| development | own | 11b | 8 | 747 | 58.8 / 94 | 688 | 56.8 | 1.75 |
| development | own | R0 | 16 | 706 | 61.7 / 94 | 644 | 55.9 | 1.63 |
| development | own | V0 | 4 | 714 | 63.0 / 94 | 651 | 55.1 | 1.62 |
| test | fixed | 11a | 8 | 352 | 14.4 / 76 | 338 | 50.2 | 1.76 |
| test | fixed | 11b | 8 | 298 | 20.4 / 76 | 278 | 57.0 | 1.69 |
| test | fixed | R0 | 16 | 309 | 21.9 / 76 | 287 | 54.8 | 1.68 |
| test | fixed | V0 | 4 | 302 | 25.5 / 76 | 276 | 54.0 | 1.62 |
| test | own | 11a | 8 | 516 | 25.9 / 76 | 490 | 50.6 | 2.59 |
| test | own | 11b | 8 | 403 | 29.2 / 76 | 374 | 60.6 | 2.43 |
| test | own | R0 | 16 | 384 | 33.8 / 76 | 350 | 57.5 | 2.19 |
| test | own | V0 | 4 | 374 | 36.2 / 76 | 337 | 57.1 | 2.12 |

## R3 — seeds

| arm | seed | validation loss | training loss | ms per step | dev sensitivity | dev F1 | dev FP/day | test sensitivity |
|---|---|---|---|---|---|---|---|---|
| 11a | clean_seed1 | 0.04130 | 0.02673 | 8.152 | 0.714 | 0.120 | 39.5 | 0.351 |
| 11a | clean_seed2 | 0.04135 | 0.02671 | 8.159 | 0.679 | 0.110 | 40.0 | 0.358 |
| 11a | clean_seed3 | 0.04141 | 0.02675 | 8.176 | 0.745 | 0.112 | 41.7 | 0.494 |
| 11a | clean_seed4 | 0.04140 | 0.02674 | 8.612 | 0.715 | 0.115 | 39.8 | 0.331 |
| 11a | clean_seed5 | 0.04127 | 0.02673 | 8.592 | 0.705 | 0.110 | 42.7 | 0.319 |
| 11a | clean_seed6 | 0.04130 | 0.02665 | 8.6 | 0.694 | 0.105 | 41.4 | 0.339 |
| 11a | clean_seed7 | 0.04139 | 0.02675 | 8.618 | 0.754 | 0.122 | 39.6 | 0.407 |
| 11a | clean_seed42 | 0.04135 | 0.02673 | 8.177 | 0.729 | 0.111 | 41.4 | 0.430 |
| 11b | clean_seed1 | 0.01772 | 0.01667 | 8.029 | 0.735 | 0.206 | 24.5 | 0.536 |
| 11b | clean_seed2 | 0.01777 | 0.01672 | 8.031 | 0.762 | 0.210 | 22.8 | 0.484 |
| 11b | clean_seed3 | 0.01771 | 0.01664 | 8.023 | 0.767 | 0.207 | 24.8 | 0.436 |
| 11b | clean_seed4 | 0.01775 | 0.01670 | 8.481 | 0.835 | 0.225 | 26.4 | 0.478 |
| 11b | clean_seed5 | 0.01773 | 0.01669 | 8.485 | 0.789 | 0.218 | 25.4 | 0.479 |
| 11b | clean_seed6 | 0.01772 | 0.01665 | 8.465 | 0.787 | 0.214 | 24.5 | 0.401 |
| 11b | clean_seed7 | 0.01778 | 0.01671 | 8.473 | 0.764 | 0.196 | 26.0 | 0.457 |
| 11b | clean_seed42 | 0.01780 | 0.01672 | 8.027 | 0.742 | 0.219 | 23.0 | 0.537 |

Gates: {"m_gates": "PASS", "m0": "PASS", "m1": "PASS", "m2": "PASS", "m4": "PASS"}; R0 k 4.138745506.
