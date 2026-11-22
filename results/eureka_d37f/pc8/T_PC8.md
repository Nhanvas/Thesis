# Table T_PC8 — decomposition of the 7 absolute features (retraining, Kaggle CPU)

Design `results/eureka_d37f/DESIGN_PC8.md` (written before the run). Arms retrained with the thesis recipe, 8 seeds each; control R0 = PC7's primary seeds (N = 16; rows read, scored with the same chain and k; gates M0, M1). Per-patient means, own label-free point, after the localizer; development = 15 patients (primary); test, chb24, Siena descriptive. Two-level bootstrap (patient units, chb01 + chb21 one unit; seeds within each group), B = 10000.

## Machines

| run | arm | CPU model | G-pc7rep | ms per step | runtime h | seeds skipped |
|---|---|---|---|---|---|---|
| pc8_a | P8a | Intel(R) Xeon(R) CPU @ 2.20GHz | DIFF | 8.74–9.40 | 9.44 | [] |
| pc8_b | P8b | Intel(R) Xeon(R) CPU @ 2.20GHz | DIFF | 8.81–9.58 | 9.559 | [] |
| pc8_c | P8c | Intel(R) Xeon(R) CPU @ 2.20GHz | DIFF | 8.66–9.44 | 9.42 | [] |

## R1 — arm − R0 (development primary)

| comparison | set | metric | arm seeds | Δ [95 %] | reading | wording |
|---|---|---|---|---|---|---|
| 10a - R0 (without the 7 absolute features (PC1, 4 seeds)) | development | sens | 4 | -0.290 [-0.410, -0.172] | descriptive | loses |
| P8a - R0 (without the 5 log band powers) | development | sens | 8 | -0.124 [-0.217, -0.039] | primary | loses |
| P8b - R0 (without log line length + kurtosis) | development | sens | 8 | +0.015 [-0.040, +0.064] | primary | no measurable difference |
| P8c - R0 (the 7 absolute features only) | development | sens | 8 | +0.013 [-0.091, +0.114] | primary | no measurable difference |
| 10a - R0 (without the 7 absolute features (PC1, 4 seeds)) | development | f1 | 4 | -0.164 [-0.251, -0.103] | descriptive | loses |
| P8a - R0 (without the 5 log band powers) | development | f1 | 8 | -0.101 [-0.143, -0.068] | primary | loses |
| P8b - R0 (without log line length + kurtosis) | development | f1 | 8 | -0.095 [-0.143, -0.055] | primary | loses |
| P8c - R0 (the 7 absolute features only) | development | f1 | 8 | +0.031 [-0.014, +0.073] | primary | no measurable difference |
| 10a - R0 (without the 7 absolute features (PC1, 4 seeds)) | development | fa | 4 | +27.1 [+21.5, +33.3] | descriptive | more false alarms |
| P8a - R0 (without the 5 log band powers) | development | fa | 8 | +13.1 [+9.4, +17.8] | primary | more false alarms |
| P8b - R0 (without log line length + kurtosis) | development | fa | 8 | +23.8 [+18.5, +29.6] | primary | more false alarms |
| P8c - R0 (the 7 absolute features only) | development | fa | 8 | -2.5 [-5.8, +1.4] | primary | no measurable difference |
| 10a - R0 (without the 7 absolute features (PC1, 4 seeds)) | test | sens | 4 | -0.189 [-0.452, +0.032] | descriptive | no measurable difference |
| P8a - R0 (without the 5 log band powers) | test | sens | 8 | -0.109 [-0.274, +0.016] | descriptive | no measurable difference |
| P8b - R0 (without log line length + kurtosis) | test | sens | 8 | +0.055 [+0.003, +0.126] | descriptive | gains |
| P8c - R0 (the 7 absolute features only) | test | sens | 8 | -0.176 [-0.374, -0.031] | descriptive | loses |
| 10a - R0 (without the 7 absolute features (PC1, 4 seeds)) | test | f1 | 4 | -0.101 [-0.159, -0.045] | descriptive | loses |
| P8a - R0 (without the 5 log band powers) | test | f1 | 8 | -0.068 [-0.103, -0.034] | descriptive | loses |
| P8b - R0 (without log line length + kurtosis) | test | f1 | 8 | -0.053 [-0.105, -0.013] | descriptive | loses |
| P8c - R0 (the 7 absolute features only) | test | f1 | 8 | -0.016 [-0.072, +0.045] | descriptive | no measurable difference |
| 10a - R0 (without the 7 absolute features (PC1, 4 seeds)) | test | fa | 4 | +25.3 [+18.1, +32.5] | descriptive | more false alarms |
| P8a - R0 (without the 5 log band powers) | test | fa | 8 | +11.2 [+5.5, +17.7] | descriptive | more false alarms |
| P8b - R0 (without log line length + kurtosis) | test | fa | 8 | +20.4 [+11.5, +30.0] | descriptive | more false alarms |
| P8c - R0 (the 7 absolute features only) | test | fa | 8 | -3.5 [-7.9, +1.0] | descriptive | no measurable difference |
| 10a - R0 (without the 7 absolute features (PC1, 4 seeds)) | chb24 | sens | 4 | -0.566 [—, —] | descriptive | descriptive (one patient) |
| P8a - R0 (without the 5 log band powers) | chb24 | sens | 8 | -0.309 [—, —] | descriptive | descriptive (one patient) |
| P8b - R0 (without log line length + kurtosis) | chb24 | sens | 8 | +0.121 [—, —] | descriptive | descriptive (one patient) |
| P8c - R0 (the 7 absolute features only) | chb24 | sens | 8 | +0.199 [—, —] | descriptive | descriptive (one patient) |
| 10a - R0 (without the 7 absolute features (PC1, 4 seeds)) | chb24 | f1 | 4 | -0.363 [—, —] | descriptive | descriptive (one patient) |
| P8a - R0 (without the 5 log band powers) | chb24 | f1 | 8 | -0.189 [—, —] | descriptive | descriptive (one patient) |
| P8b - R0 (without log line length + kurtosis) | chb24 | f1 | 8 | -0.105 [—, —] | descriptive | descriptive (one patient) |
| P8c - R0 (the 7 absolute features only) | chb24 | f1 | 8 | -0.145 [—, —] | descriptive | descriptive (one patient) |
| 10a - R0 (without the 7 absolute features (PC1, 4 seeds)) | chb24 | fa | 4 | +18.4 [—, —] | descriptive | descriptive (one patient) |
| P8a - R0 (without the 5 log band powers) | chb24 | fa | 8 | +4.5 [—, —] | descriptive | descriptive (one patient) |
| P8b - R0 (without log line length + kurtosis) | chb24 | fa | 8 | +26.1 [—, —] | descriptive | descriptive (one patient) |
| P8c - R0 (the 7 absolute features only) | chb24 | fa | 8 | +43.4 [—, —] | descriptive | descriptive (one patient) |
| 10a - R0 (without the 7 absolute features (PC1, 4 seeds)) | siena | sens | 4 | -0.074 [-0.220, +0.077] | descriptive | no measurable difference |
| P8a - R0 (without the 5 log band powers) | siena | sens | 8 | -0.113 [-0.225, +0.010] | descriptive | no measurable difference |
| P8b - R0 (without log line length + kurtosis) | siena | sens | 8 | +0.128 [+0.033, +0.242] | descriptive | gains |
| P8c - R0 (the 7 absolute features only) | siena | sens | 8 | -0.015 [-0.225, +0.177] | descriptive | no measurable difference |
| 10a - R0 (without the 7 absolute features (PC1, 4 seeds)) | siena | f1 | 4 | -0.092 [-0.139, -0.049] | descriptive | loses |
| P8a - R0 (without the 5 log band powers) | siena | f1 | 8 | -0.095 [-0.143, -0.050] | descriptive | loses |
| P8b - R0 (without log line length + kurtosis) | siena | f1 | 8 | -0.011 [-0.051, +0.039] | descriptive | no measurable difference |
| P8c - R0 (the 7 absolute features only) | siena | f1 | 8 | -0.009 [-0.084, +0.064] | descriptive | no measurable difference |
| 10a - R0 (without the 7 absolute features (PC1, 4 seeds)) | siena | fa | 4 | +25.3 [+17.8, +33.3] | descriptive | more false alarms |
| P8a - R0 (without the 5 log band powers) | siena | fa | 8 | +16.3 [+11.3, +21.6] | descriptive | more false alarms |
| P8b - R0 (without log line length + kurtosis) | siena | fa | 8 | +17.2 [+11.7, +22.9] | descriptive | more false alarms |
| P8c - R0 (the 7 absolute features only) | siena | fa | 8 | +3.2 [-6.7, +12.2] | descriptive | no measurable difference |

## R1m — arm − R0 with the machine-matched control (secondary; addendum of 22/11, written before the reading)

Control seeds per arm: {"P8a": {"arm_rep": "DIFF", "control_seeds": ["clean_seed12", "clean_seed13", "clean_seed14", "clean_seed15", "clean_seed16", "clean_seed17", "clean_seed18", "clean_seed19"]}, "P8b": {"arm_rep": "DIFF", "control_seeds": ["clean_seed12", "clean_seed13", "clean_seed14", "clean_seed15", "clean_seed16", "clean_seed17", "clean_seed18", "clean_seed19"]}, "P8c": {"arm_rep": "DIFF", "control_seeds": ["clean_seed12", "clean_seed13", "clean_seed14", "clean_seed15", "clean_seed16", "clean_seed17", "clean_seed18", "clean_seed19"]}}

| comparison | set | metric | arm / control seeds | Δ [95 %] | wording |
|---|---|---|---|---|---|
| P8a - R0 (control DIFF) | development | sens | 8 / 8 | -0.111 [-0.205, -0.030] | loses |
| P8a - R0 (control DIFF) | development | f1 | 8 / 8 | -0.096 [-0.143, -0.060] | loses |
| P8a - R0 (control DIFF) | development | fa | 8 / 8 | +12.9 [+9.3, +17.5] | more false alarms |
| P8a - R0 (control DIFF) | test | sens | 8 / 8 | -0.096 [-0.262, +0.031] | no measurable difference |
| P8a - R0 (control DIFF) | test | f1 | 8 / 8 | -0.064 [-0.100, -0.028] | loses |
| P8a - R0 (control DIFF) | test | fa | 8 / 8 | +11.2 [+5.6, +17.6] | more false alarms |
| P8a - R0 (control DIFF) | chb24 | sens | 8 / 8 | -0.289 [—, —] | descriptive (one patient) |
| P8a - R0 (control DIFF) | chb24 | f1 | 8 / 8 | -0.190 [—, —] | descriptive (one patient) |
| P8a - R0 (control DIFF) | chb24 | fa | 8 / 8 | +6.0 [—, —] | descriptive (one patient) |
| P8a - R0 (control DIFF) | siena | sens | 8 / 8 | -0.117 [-0.235, +0.007] | no measurable difference |
| P8a - R0 (control DIFF) | siena | f1 | 8 / 8 | -0.101 [-0.152, -0.052] | loses |
| P8a - R0 (control DIFF) | siena | fa | 8 / 8 | +17.9 [+12.8, +23.3] | more false alarms |
| P8b - R0 (control DIFF) | development | sens | 8 / 8 | +0.028 [-0.028, +0.084] | no measurable difference |
| P8b - R0 (control DIFF) | development | f1 | 8 / 8 | -0.091 [-0.142, -0.048] | loses |
| P8b - R0 (control DIFF) | development | fa | 8 / 8 | +23.6 [+18.4, +29.5] | more false alarms |
| P8b - R0 (control DIFF) | test | sens | 8 / 8 | +0.068 [+0.010, +0.148] | gains |
| P8b - R0 (control DIFF) | test | f1 | 8 / 8 | -0.049 [-0.105, -0.007] | loses |
| P8b - R0 (control DIFF) | test | fa | 8 / 8 | +20.4 [+11.7, +29.8] | more false alarms |
| P8b - R0 (control DIFF) | chb24 | sens | 8 / 8 | +0.141 [—, —] | descriptive (one patient) |
| P8b - R0 (control DIFF) | chb24 | f1 | 8 / 8 | -0.106 [—, —] | descriptive (one patient) |
| P8b - R0 (control DIFF) | chb24 | fa | 8 / 8 | +27.5 [—, —] | descriptive (one patient) |
| P8b - R0 (control DIFF) | siena | sens | 8 / 8 | +0.124 [+0.023, +0.251] | gains |
| P8b - R0 (control DIFF) | siena | f1 | 8 / 8 | -0.017 [-0.063, +0.039] | no measurable difference |
| P8b - R0 (control DIFF) | siena | fa | 8 / 8 | +18.9 [+13.3, +24.5] | more false alarms |
| P8c - R0 (control DIFF) | development | sens | 8 / 8 | +0.026 [-0.081, +0.132] | no measurable difference |
| P8c - R0 (control DIFF) | development | f1 | 8 / 8 | +0.035 [-0.012, +0.080] | no measurable difference |
| P8c - R0 (control DIFF) | development | fa | 8 / 8 | -2.7 [-6.2, +1.2] | no measurable difference |
| P8c - R0 (control DIFF) | test | sens | 8 / 8 | -0.163 [-0.362, -0.016] | loses |
| P8c - R0 (control DIFF) | test | f1 | 8 / 8 | -0.012 [-0.068, +0.049] | no measurable difference |
| P8c - R0 (control DIFF) | test | fa | 8 / 8 | -3.5 [-8.2, +1.1] | no measurable difference |
| P8c - R0 (control DIFF) | chb24 | sens | 8 / 8 | +0.219 [—, —] | descriptive (one patient) |
| P8c - R0 (control DIFF) | chb24 | f1 | 8 / 8 | -0.146 [—, —] | descriptive (one patient) |
| P8c - R0 (control DIFF) | chb24 | fa | 8 / 8 | +44.8 [—, —] | descriptive (one patient) |
| P8c - R0 (control DIFF) | siena | sens | 8 / 8 | -0.019 [-0.226, +0.178] | no measurable difference |
| P8c - R0 (control DIFF) | siena | f1 | 8 / 8 | -0.016 [-0.097, +0.060] | no measurable difference |
| P8c - R0 (control DIFF) | siena | fa | 8 / 8 | +4.9 [-5.0, +14.0] | no measurable difference |

## R2 — share of 10a's loss, development (descriptive; ratio of paired bootstrap draws)

| arm | metric | share [95 %] |
|---|---|---|
| P8a | sens | 0.43 [0.15, 0.78] |
| P8b | sens | -0.05 [-0.24, 0.14] |
| P8c | sens | -0.04 [-0.51, 0.27] |
| P8a | f1 | 0.62 [0.50, 0.78] |
| P8b | f1 | 0.58 [0.43, 0.76] |
| P8c | f1 | -0.19 [-0.55, 0.09] |
| P8a | fa | 0.48 [0.36, 0.63] |
| P8b | fa | 0.88 [0.67, 1.14] |
| P8c | fa | -0.09 [-0.23, 0.05] |

## Means over seeds

| set | variant | seeds | sensitivity | F1 | FP/day |
|---|---|---|---|---|---|
| development | V0 | 4 | 0.832 ± 0.014 | 0.225 ± 0.009 | 23.2 ± 0.6 |
| development | R0 | 16 | 0.803 ± 0.029 | 0.225 ± 0.012 | 22.7 ± 0.7 |
| development | 10a | 4 | 0.513 ± 0.018 | 0.061 ± 0.005 | 49.9 ± 0.5 |
| development | P8a | 8 | 0.679 ± 0.062 | 0.124 ± 0.013 | 35.8 ± 3.3 |
| development | P8b | 8 | 0.818 ± 0.056 | 0.130 ± 0.008 | 46.5 ± 4.8 |
| development | P8c | 8 | 0.816 ± 0.031 | 0.256 ± 0.012 | 20.2 ± 1.6 |
| test | V0 | 4 | 0.567 ± 0.019 | 0.180 ± 0.009 | 28.7 ± 1.3 |
| test | R0 | 16 | 0.523 ± 0.048 | 0.163 ± 0.015 | 29.6 ± 1.1 |
| test | 10a | 4 | 0.334 ± 0.029 | 0.062 ± 0.006 | 54.9 ± 1.7 |
| test | P8a | 8 | 0.414 ± 0.090 | 0.095 ± 0.018 | 40.8 ± 2.6 |
| test | P8b | 8 | 0.578 ± 0.025 | 0.110 ± 0.006 | 50.0 ± 3.5 |
| test | P8c | 8 | 0.347 ± 0.023 | 0.147 ± 0.010 | 26.1 ± 2.0 |
| chb24 | V0 | 4 | 0.844 ± 0.036 | 0.500 ± 0.013 | 27.8 ± 1.1 |
| chb24 | R0 | 16 | 0.801 ± 0.100 | 0.489 ± 0.045 | 26.7 ± 3.7 |
| chb24 | 10a | 4 | 0.234 ± 0.060 | 0.126 ± 0.031 | 45.1 ± 3.5 |
| chb24 | P8a | 8 | 0.492 ± 0.212 | 0.300 ± 0.110 | 31.2 ± 4.1 |
| chb24 | P8b | 8 | 0.922 ± 0.055 | 0.384 ± 0.028 | 52.8 ± 8.3 |
| chb24 | P8c | 8 | 1.000 ± 0.000 | 0.344 ± 0.031 | 70.1 ± 9.7 |
| siena | V0 | 4 | 0.645 ± 0.092 | 0.233 ± 0.029 | 40.6 ± 1.5 |
| siena | R0 | 16 | 0.643 ± 0.066 | 0.223 ± 0.018 | 41.1 ± 2.6 |
| siena | 10a | 4 | 0.568 ± 0.065 | 0.131 ± 0.009 | 66.4 ± 1.9 |
| siena | P8a | 8 | 0.529 ± 0.054 | 0.128 ± 0.016 | 57.3 ± 2.2 |
| siena | P8b | 8 | 0.771 ± 0.033 | 0.212 ± 0.006 | 58.2 ± 1.8 |
| siena | P8c | 8 | 0.627 ± 0.078 | 0.214 ± 0.028 | 44.3 ± 1.7 |

## R4 — events at each budget (CPD stage; per-seed means of the set sums)

| set | budget | variant | seeds | events | seizures found | false alarms | s per event | flagged time % | windows flagged % |
|---|---|---|---|---|---|---|---|---|---|
| development | fixed | 10a | 4 | 1186 | 35.5 / 94 | 1151 | 42.1 | 2.05 | 0.50 |
| development | fixed | P8a | 8 | 841 | 45.5 / 94 | 795 | 48.0 | 1.66 | 0.50 |
| development | fixed | P8b | 8 | 724 | 58.4 / 94 | 666 | 53.2 | 1.57 | 0.50 |
| development | fixed | P8c | 8 | 515 | 62.2 / 94 | 453 | 64.0 | 1.35 | 0.50 |
| development | fixed | R0 | 16 | 618 | 60.1 / 94 | 558 | 56.4 | 1.44 | 0.50 |
| development | fixed | V0 | 4 | 610 | 62.2 / 94 | 548 | 56.0 | 1.41 | 0.50 |
| development | own | 10a | 4 | 1465 | 37.8 / 94 | 1427 | 43.4 | 2.62 | 0.62 |
| development | own | P8a | 8 | 1045 | 50.0 / 94 | 995 | 48.5 | 2.09 | 0.69 |
| development | own | P8b | 8 | 1461 | 65.8 / 94 | 1396 | 52.1 | 3.14 | 1.01 |
| development | own | P8c | 8 | 648 | 69.0 / 94 | 579 | 64.8 | 1.73 | 0.69 |
| development | own | R0 | 16 | 706 | 61.7 / 94 | 644 | 55.9 | 1.63 | 0.62 |
| development | own | V0 | 4 | 714 | 63.0 / 94 | 651 | 55.1 | 1.62 | 0.64 |
| test | fixed | 10a | 4 | 502 | 18.8 / 76 | 484 | 40.0 | 2.00 | 0.50 |
| test | fixed | P8a | 8 | 331 | 13.5 / 76 | 318 | 52.6 | 1.73 | 0.50 |
| test | fixed | P8b | 8 | 337 | 22.6 / 76 | 314 | 52.0 | 1.73 | 0.50 |
| test | fixed | P8c | 8 | 248 | 17.5 / 76 | 230 | 62.4 | 1.53 | 0.50 |
| test | fixed | R0 | 16 | 309 | 21.9 / 76 | 287 | 54.8 | 1.68 | 0.50 |
| test | fixed | V0 | 4 | 302 | 25.5 / 76 | 276 | 54.0 | 1.62 | 0.50 |
| test | own | 10a | 4 | 669 | 27.2 / 76 | 642 | 44.0 | 2.93 | 0.81 |
| test | own | P8a | 8 | 490 | 27.0 / 76 | 463 | 53.4 | 2.60 | 0.88 |
| test | own | P8b | 8 | 600 | 36.6 / 76 | 563 | 54.3 | 3.24 | 1.09 |
| test | own | P8c | 8 | 328 | 23.0 / 76 | 306 | 63.6 | 2.07 | 0.69 |
| test | own | R0 | 16 | 384 | 33.8 / 76 | 350 | 57.5 | 2.19 | 0.73 |
| test | own | V0 | 4 | 374 | 36.2 / 76 | 337 | 57.1 | 2.12 | 0.73 |

## R3 — seeds

| arm | seed | parameters | validation loss | training loss | ms per step | dev sensitivity | dev F1 | dev FP/day | test sensitivity |
|---|---|---|---|---|---|---|---|---|---|
| P8a | clean_seed1 | 3479 | 0.02244 | 0.01668 | 8.753 | 0.747 | 0.143 | 34.3 | 0.454 |
| P8a | clean_seed2 | 3479 | 0.02248 | 0.01669 | 8.775 | 0.721 | 0.117 | 40.8 | 0.518 |
| P8a | clean_seed3 | 3479 | 0.02247 | 0.01668 | 8.741 | 0.686 | 0.117 | 38.4 | 0.395 |
| P8a | clean_seed4 | 3479 | 0.02242 | 0.01668 | 9.36 | 0.712 | 0.142 | 34.7 | 0.492 |
| P8a | clean_seed5 | 3479 | 0.02242 | 0.01669 | 9.38 | 0.597 | 0.117 | 32.7 | 0.300 |
| P8a | clean_seed6 | 3479 | 0.02247 | 0.01667 | 9.403 | 0.610 | 0.107 | 33.4 | 0.299 |
| P8a | clean_seed7 | 3479 | 0.02245 | 0.01668 | 9.389 | 0.743 | 0.131 | 39.6 | 0.503 |
| P8a | clean_seed42 | 3479 | 0.02248 | 0.01667 | 8.755 | 0.616 | 0.117 | 32.6 | 0.352 |
| P8b | clean_seed1 | 3770 | 0.02156 | 0.01605 | 8.808 | 0.832 | 0.132 | 45.1 | 0.581 |
| P8b | clean_seed2 | 3770 | 0.02152 | 0.01606 | 8.835 | 0.854 | 0.121 | 52.3 | 0.605 |
| P8b | clean_seed3 | 3770 | 0.02154 | 0.01604 | 8.807 | 0.829 | 0.124 | 50.0 | 0.596 |
| P8b | clean_seed4 | 3770 | 0.02155 | 0.01605 | 9.544 | 0.862 | 0.122 | 52.1 | 0.588 |
| P8b | clean_seed5 | 3770 | 0.02148 | 0.01603 | 9.566 | 0.769 | 0.132 | 42.6 | 0.588 |
| P8b | clean_seed6 | 3770 | 0.02147 | 0.01600 | 9.584 | 0.800 | 0.143 | 41.1 | 0.574 |
| P8b | clean_seed7 | 3770 | 0.02155 | 0.01609 | 9.575 | 0.881 | 0.137 | 48.2 | 0.572 |
| P8b | clean_seed42 | 3770 | 0.02153 | 0.01605 | 8.823 | 0.712 | 0.126 | 40.9 | 0.522 |
| P8c | clean_seed1 | 2327 | 0.02743 | 0.01947 | 8.67 | 0.832 | 0.260 | 20.1 | 0.338 |
| P8c | clean_seed2 | 2327 | 0.02786 | 0.01964 | 8.656 | 0.859 | 0.265 | 20.1 | 0.371 |
| P8c | clean_seed3 | 2327 | 0.02736 | 0.01941 | 8.683 | 0.810 | 0.240 | 22.5 | 0.312 |
| P8c | clean_seed4 | 2327 | 0.02756 | 0.01951 | 9.394 | 0.784 | 0.240 | 20.9 | 0.359 |
| P8c | clean_seed5 | 2327 | 0.02854 | 0.01953 | 9.428 | 0.857 | 0.268 | 19.8 | 0.371 |
| P8c | clean_seed6 | 2327 | 0.02835 | 0.01949 | 9.403 | 0.802 | 0.267 | 18.0 | 0.319 |
| P8c | clean_seed7 | 2327 | 0.02710 | 0.01955 | 9.441 | 0.805 | 0.246 | 21.9 | 0.367 |
| P8c | clean_seed42 | 2327 | 0.02803 | 0.01948 | 8.692 | 0.776 | 0.261 | 18.1 | 0.338 |

Gates: {"m_gates": "PASS", "m0": "PASS", "m1": "PASS", "m2": "PASS", "m4": "PASS"}; R0 k 4.138745506.
