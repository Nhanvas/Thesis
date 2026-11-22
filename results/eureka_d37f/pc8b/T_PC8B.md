# Table T_PC8B — which input block keeps the detection on unseen patients (retraining, Kaggle CPU)

Design `results/eureka_d37f/DESIGN_PC8B.md` (written before the run). Arms retrained with the thesis recipe, 8 seeds each; P8c = the PC8 run (rows read); control R0 = PC7's primary seeds (N = 16; rows read; gates M0, M1). Per-patient means, own label-free point, after the localizer. Unseen = the 3 validation + 8 test patients (chb10, chb11, chb22, chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18; primary); development (15) secondary; validation, test, chb24, Siena descriptive. Two-level bootstrap (patient units, chb01 + chb21 one unit; seeds within each group), B = 10000.

Arms: P8d = connectivity row + the 7 absolute features (without the relative band powers); P8e = relative band powers + the 7 absolute features (without the connectivity row); P8c = the 7 absolute features only (PC8); 10a = without the 7 absolute features (PC1, 4 seeds); R0 = the full node input (control).

## Machines

| run | arm | CPU model | G-pc7rep | ms per step | runtime h | seeds skipped |
|---|---|---|---|---|---|---|
| pc8_d | P8d | Intel(R) Xeon(R) CPU @ 2.20GHz | DIFF | 8.04–8.40 | 8.581 | [] |
| pc8_e | P8e | Intel(R) Xeon(R) CPU @ 2.20GHz | DIFF | 8.20–8.79 | 8.826 | [] |
| pc8_c | P8c | Intel(R) Xeon(R) CPU @ 2.20GHz | DIFF | 8.66–9.44 | 9.42 | [] |

## R1 — arm − R0 (unseen primary)

| comparison | set | metric | patients | arm seeds | Δ [95 %] | reading | wording |
|---|---|---|---|---|---|---|---|
| 10a - R0 | unseen | sens | 11 | 4 | -0.235 [-0.448, -0.041] | descriptive | loses |
| P8c - R0 | unseen | sens | 11 | 8 | -0.163 [-0.323, -0.043] | descriptive | loses |
| P8d - R0 | unseen | sens | 11 | 8 | -0.013 [-0.130, +0.104] | primary | no measurable difference |
| P8e - R0 | unseen | sens | 11 | 8 | -0.123 [-0.235, -0.020] | primary | loses |
| 10a - R0 | unseen | f1 | 11 | 4 | -0.120 [-0.167, -0.074] | descriptive | loses |
| P8c - R0 | unseen | f1 | 11 | 8 | -0.027 [-0.076, +0.025] | descriptive | no measurable difference |
| P8d - R0 | unseen | f1 | 11 | 8 | -0.028 [-0.062, +0.005] | primary | no measurable difference |
| P8e - R0 | unseen | f1 | 11 | 8 | -0.037 [-0.077, +0.005] | primary | no measurable difference |
| 10a - R0 | unseen | fa | 11 | 4 | +26.0 [+20.2, +31.7] | descriptive | more false alarms |
| P8c - R0 | unseen | fa | 11 | 8 | -2.3 [-6.4, +2.0] | descriptive | no measurable difference |
| P8d - R0 | unseen | fa | 11 | 8 | +7.2 [+2.2, +13.1] | primary | more false alarms |
| P8e - R0 | unseen | fa | 11 | 8 | -1.2 [-5.6, +2.6] | primary | no measurable difference |
| 10a - R0 | development | sens | 15 | 4 | -0.290 [-0.412, -0.175] | descriptive | loses |
| P8c - R0 | development | sens | 15 | 8 | +0.013 [-0.088, +0.113] | descriptive | no measurable difference |
| P8d - R0 | development | sens | 15 | 8 | -0.035 [-0.093, +0.016] | secondary | no measurable difference |
| P8e - R0 | development | sens | 15 | 8 | -0.083 [-0.160, -0.020] | secondary | loses |
| 10a - R0 | development | f1 | 15 | 4 | -0.164 [-0.251, -0.102] | descriptive | loses |
| P8c - R0 | development | f1 | 15 | 8 | +0.031 [-0.014, +0.073] | descriptive | no measurable difference |
| P8d - R0 | development | f1 | 15 | 8 | -0.005 [-0.032, +0.020] | secondary | no measurable difference |
| P8e - R0 | development | f1 | 15 | 8 | -0.007 [-0.045, +0.030] | secondary | no measurable difference |
| 10a - R0 | development | fa | 15 | 4 | +27.1 [+21.7, +33.1] | descriptive | more false alarms |
| P8c - R0 | development | fa | 15 | 8 | -2.5 [-5.9, +1.4] | descriptive | no measurable difference |
| P8d - R0 | development | fa | 15 | 8 | +2.3 [+0.1, +4.8] | secondary | more false alarms |
| P8e - R0 | development | fa | 15 | 8 | -1.8 [-4.5, +1.3] | secondary | no measurable difference |
| 10a - R0 | validation | sens | 3 | 4 | -0.357 [-0.622, +0.000] | descriptive | no measurable difference |
| P8c - R0 | validation | sens | 3 | 8 | -0.129 [-0.363, +0.000] | descriptive | no measurable difference |
| P8d - R0 | validation | sens | 3 | 8 | -0.088 [-0.250, +0.000] | descriptive | no measurable difference |
| P8e - R0 | validation | sens | 3 | 8 | -0.146 [-0.413, +0.000] | descriptive | no measurable difference |
| 10a - R0 | validation | f1 | 3 | 4 | -0.171 [-0.216, -0.119] | descriptive | loses |
| P8c - R0 | validation | f1 | 3 | 8 | -0.057 [-0.130, +0.043] | descriptive | no measurable difference |
| P8d - R0 | validation | f1 | 3 | 8 | -0.061 [-0.099, -0.023] | descriptive | loses |
| P8e - R0 | validation | f1 | 3 | 8 | -0.075 [-0.139, -0.009] | descriptive | loses |
| 10a - R0 | validation | fa | 3 | 4 | +27.7 [+20.0, +37.7] | descriptive | more false alarms |
| P8c - R0 | validation | fa | 3 | 8 | +0.9 [-6.8, +10.1] | descriptive | no measurable difference |
| P8d - R0 | validation | fa | 3 | 8 | +4.1 [+0.9, +6.7] | descriptive | more false alarms |
| P8e - R0 | validation | fa | 3 | 8 | +3.5 [+0.5, +6.9] | descriptive | more false alarms |
| 10a - R0 | test | sens | 8 | 4 | -0.189 [-0.449, +0.030] | descriptive | no measurable difference |
| P8c - R0 | test | sens | 8 | 8 | -0.176 [-0.379, -0.029] | descriptive | loses |
| P8d - R0 | test | sens | 8 | 8 | +0.014 [-0.132, +0.164] | descriptive | no measurable difference |
| P8e - R0 | test | sens | 8 | 8 | -0.114 [-0.234, +0.004] | descriptive | no measurable difference |
| 10a - R0 | test | f1 | 8 | 4 | -0.101 [-0.158, -0.045] | descriptive | loses |
| P8c - R0 | test | f1 | 8 | 8 | -0.016 [-0.072, +0.045] | descriptive | no measurable difference |
| P8d - R0 | test | f1 | 8 | 8 | -0.015 [-0.057, +0.022] | descriptive | no measurable difference |
| P8e - R0 | test | f1 | 8 | 8 | -0.023 [-0.070, +0.025] | descriptive | no measurable difference |
| 10a - R0 | test | fa | 8 | 4 | +25.3 [+18.2, +32.6] | descriptive | more false alarms |
| P8c - R0 | test | fa | 8 | 8 | -3.5 [-8.0, +1.0] | descriptive | no measurable difference |
| P8d - R0 | test | fa | 8 | 8 | +8.4 [+1.4, +16.0] | descriptive | more false alarms |
| P8e - R0 | test | fa | 8 | 8 | -3.0 [-8.2, +1.6] | descriptive | no measurable difference |
| 10a - R0 | chb24 | sens | 1 | 4 | -0.566 [—, —] | descriptive | descriptive (one patient) |
| P8c - R0 | chb24 | sens | 1 | 8 | +0.199 [—, —] | descriptive | descriptive (one patient) |
| P8d - R0 | chb24 | sens | 1 | 8 | +0.059 [—, —] | descriptive | descriptive (one patient) |
| P8e - R0 | chb24 | sens | 1 | 8 | +0.191 [—, —] | descriptive | descriptive (one patient) |
| 10a - R0 | chb24 | f1 | 1 | 4 | -0.363 [—, —] | descriptive | descriptive (one patient) |
| P8c - R0 | chb24 | f1 | 1 | 8 | -0.145 [—, —] | descriptive | descriptive (one patient) |
| P8d - R0 | chb24 | f1 | 1 | 8 | +0.027 [—, —] | descriptive | descriptive (one patient) |
| P8e - R0 | chb24 | f1 | 1 | 8 | -0.115 [—, —] | descriptive | descriptive (one patient) |
| 10a - R0 | chb24 | fa | 1 | 4 | +18.4 [—, —] | descriptive | descriptive (one patient) |
| P8c - R0 | chb24 | fa | 1 | 8 | +43.4 [—, —] | descriptive | descriptive (one patient) |
| P8d - R0 | chb24 | fa | 1 | 8 | +0.7 [—, —] | descriptive | descriptive (one patient) |
| P8e - R0 | chb24 | fa | 1 | 8 | +33.8 [—, —] | descriptive | descriptive (one patient) |
| 10a - R0 | siena | sens | 14 | 4 | -0.074 [-0.218, +0.076] | descriptive | no measurable difference |
| P8c - R0 | siena | sens | 14 | 8 | -0.015 [-0.225, +0.179] | descriptive | no measurable difference |
| P8d - R0 | siena | sens | 14 | 8 | -0.146 [-0.324, +0.007] | descriptive | no measurable difference |
| P8e - R0 | siena | sens | 14 | 8 | -0.027 [-0.174, +0.131] | descriptive | no measurable difference |
| 10a - R0 | siena | f1 | 14 | 4 | -0.092 [-0.140, -0.047] | descriptive | loses |
| P8c - R0 | siena | f1 | 14 | 8 | -0.009 [-0.083, +0.061] | descriptive | no measurable difference |
| P8d - R0 | siena | f1 | 14 | 8 | -0.047 [-0.112, +0.008] | descriptive | no measurable difference |
| P8e - R0 | siena | f1 | 14 | 8 | -0.044 [-0.091, -0.002] | descriptive | loses |
| 10a - R0 | siena | fa | 14 | 4 | +25.3 [+17.7, +33.5] | descriptive | more false alarms |
| P8c - R0 | siena | fa | 14 | 8 | +3.2 [-6.8, +12.1] | descriptive | no measurable difference |
| P8d - R0 | siena | fa | 14 | 8 | -5.4 [-12.4, +0.6] | descriptive | no measurable difference |
| P8e - R0 | siena | fa | 14 | 8 | +6.6 [+0.7, +12.8] | descriptive | more false alarms |

## R5 — arm − P8c: what each block adds to the 7 absolute features (unseen primary)

| comparison | set | metric | patients | arm seeds | Δ [95 %] | reading | wording |
|---|---|---|---|---|---|---|---|
| R0 - P8c | unseen | sens | 11 | 16 | +0.163 [+0.040, +0.320] | descriptive | gains |
| P8d - P8c | unseen | sens | 11 | 8 | +0.150 [+0.058, +0.264] | primary | gains |
| P8e - P8c | unseen | sens | 11 | 8 | +0.041 [-0.029, +0.138] | primary | no measurable difference |
| R0 - P8c | unseen | f1 | 11 | 16 | +0.027 [-0.025, +0.074] | descriptive | no measurable difference |
| P8d - P8c | unseen | f1 | 11 | 8 | -0.001 [-0.046, +0.043] | primary | no measurable difference |
| P8e - P8c | unseen | f1 | 11 | 8 | -0.010 [-0.034, +0.015] | primary | no measurable difference |
| R0 - P8c | unseen | fa | 11 | 16 | +2.3 [-1.9, +6.5] | descriptive | no measurable difference |
| P8d - P8c | unseen | fa | 11 | 8 | +9.5 [+4.0, +15.8] | primary | more false alarms |
| P8e - P8c | unseen | fa | 11 | 8 | +1.1 [-3.4, +5.1] | primary | no measurable difference |
| R0 - P8c | development | sens | 15 | 16 | -0.013 [-0.114, +0.090] | descriptive | no measurable difference |
| P8d - P8c | development | sens | 15 | 8 | -0.048 [-0.150, +0.051] | secondary | no measurable difference |
| P8e - P8c | development | sens | 15 | 8 | -0.095 [-0.195, -0.001] | secondary | loses |
| R0 - P8c | development | f1 | 15 | 16 | -0.031 [-0.072, +0.014] | descriptive | no measurable difference |
| P8d - P8c | development | f1 | 15 | 8 | -0.036 [-0.075, +0.000] | secondary | no measurable difference |
| P8e - P8c | development | f1 | 15 | 8 | -0.038 [-0.087, +0.006] | secondary | no measurable difference |
| R0 - P8c | development | fa | 15 | 16 | +2.5 [-1.4, +5.8] | descriptive | no measurable difference |
| P8d - P8c | development | fa | 15 | 8 | +4.9 [+1.2, +8.4] | secondary | more false alarms |
| P8e - P8c | development | fa | 15 | 8 | +0.8 [-2.0, +3.6] | secondary | no measurable difference |
| R0 - P8c | validation | sens | 3 | 16 | +0.129 [+0.000, +0.375] | descriptive | no measurable difference |
| P8d - P8c | validation | sens | 3 | 8 | +0.042 [+0.000, +0.150] | descriptive | no measurable difference |
| P8e - P8c | validation | sens | 3 | 8 | -0.017 [-0.100, +0.025] | descriptive | no measurable difference |
| R0 - P8c | validation | f1 | 3 | 16 | +0.057 [-0.043, +0.130] | descriptive | no measurable difference |
| P8d - P8c | validation | f1 | 3 | 8 | -0.004 [-0.066, +0.048] | descriptive | no measurable difference |
| P8e - P8c | validation | f1 | 3 | 8 | -0.018 [-0.068, +0.037] | descriptive | no measurable difference |
| R0 - P8c | validation | fa | 3 | 16 | -0.9 [-10.2, +6.7] | descriptive | no measurable difference |
| P8d - P8c | validation | fa | 3 | 8 | +3.2 [-4.7, +11.4] | descriptive | no measurable difference |
| P8e - P8c | validation | fa | 3 | 8 | +2.6 [-4.4, +8.8] | descriptive | no measurable difference |
| R0 - P8c | test | sens | 8 | 16 | +0.176 [+0.031, +0.381] | descriptive | gains |
| P8d - P8c | test | sens | 8 | 8 | +0.190 [+0.075, +0.324] | descriptive | gains |
| P8e - P8c | test | sens | 8 | 8 | +0.062 [-0.029, +0.188] | descriptive | no measurable difference |
| R0 - P8c | test | f1 | 8 | 16 | +0.016 [-0.044, +0.071] | descriptive | no measurable difference |
| P8d - P8c | test | f1 | 8 | 8 | +0.000 [-0.057, +0.056] | descriptive | no measurable difference |
| P8e - P8c | test | f1 | 8 | 8 | -0.007 [-0.031, +0.019] | descriptive | no measurable difference |
| R0 - P8c | test | fa | 8 | 16 | +3.5 [-0.9, +8.0] | descriptive | no measurable difference |
| P8d - P8c | test | fa | 8 | 8 | +11.9 [+5.7, +19.6] | descriptive | more false alarms |
| P8e - P8c | test | fa | 8 | 8 | +0.5 [-4.8, +5.3] | descriptive | no measurable difference |
| R0 - P8c | chb24 | sens | 1 | 16 | -0.199 [—, —] | descriptive | descriptive (one patient) |
| P8d - P8c | chb24 | sens | 1 | 8 | -0.141 [—, —] | descriptive | descriptive (one patient) |
| P8e - P8c | chb24 | sens | 1 | 8 | -0.008 [—, —] | descriptive | descriptive (one patient) |
| R0 - P8c | chb24 | f1 | 1 | 16 | +0.145 [—, —] | descriptive | descriptive (one patient) |
| P8d - P8c | chb24 | f1 | 1 | 8 | +0.172 [—, —] | descriptive | descriptive (one patient) |
| P8e - P8c | chb24 | f1 | 1 | 8 | +0.030 [—, —] | descriptive | descriptive (one patient) |
| R0 - P8c | chb24 | fa | 1 | 16 | -43.4 [—, —] | descriptive | descriptive (one patient) |
| P8d - P8c | chb24 | fa | 1 | 8 | -42.7 [—, —] | descriptive | descriptive (one patient) |
| P8e - P8c | chb24 | fa | 1 | 8 | -9.6 [—, —] | descriptive | descriptive (one patient) |
| R0 - P8c | siena | sens | 14 | 16 | +0.015 [-0.180, +0.226] | descriptive | no measurable difference |
| P8d - P8c | siena | sens | 14 | 8 | -0.130 [-0.296, +0.017] | descriptive | no measurable difference |
| P8e - P8c | siena | sens | 14 | 8 | -0.012 [-0.171, +0.158] | descriptive | no measurable difference |
| R0 - P8c | siena | f1 | 14 | 16 | +0.009 [-0.062, +0.084] | descriptive | no measurable difference |
| P8d - P8c | siena | f1 | 14 | 8 | -0.038 [-0.091, +0.013] | descriptive | no measurable difference |
| P8e - P8c | siena | f1 | 14 | 8 | -0.034 [-0.101, +0.024] | descriptive | no measurable difference |
| R0 - P8c | siena | fa | 14 | 16 | -3.2 [-12.2, +6.4] | descriptive | no measurable difference |
| P8d - P8c | siena | fa | 14 | 8 | -8.6 [-16.8, -0.4] | descriptive | fewer false alarms |
| P8e - P8c | siena | fa | 14 | 8 | +3.4 [-3.7, +10.9] | descriptive | no measurable difference |

## R6 — share of P8c's gap to R0 recovered by the block (ratio of paired bootstrap draws; descriptive)

| arm | set | metric | R0 − P8c | share [95 %] |
|---|---|---|---|---|
| P8d | unseen | sens | +0.163 | 0.92 [0.44, 2.88] |
| P8e | unseen | sens | +0.163 | 0.25 [-0.30, 0.72] |
| P8d | unseen | f1 | +0.027 | -0.04 [-6.80, 7.17] |
| P8e | unseen | f1 | +0.027 | -0.38 [-6.49, 6.08] |
| P8d | unseen | fa | +2.3 | 4.18 [-28.70, 37.56] |
| P8e | unseen | fa | +2.3 | 0.47 [-5.01, 6.23] |
| P8d | development | sens | -0.013 | 3.80 [-10.98, 12.23] |
| P8e | development | sens | -0.013 | 7.58 [-25.93, 27.12] |
| P8d | development | f1 | -0.031 | 1.18 [-3.80, 5.85] |
| P8e | development | f1 | -0.031 | 1.23 [-4.34, 7.07] |
| P8d | development | fa | +2.5 | 1.92 [-8.13, 12.14] |
| P8e | development | fa | +2.5 | 0.31 [-3.40, 3.08] |

## R1m — arm − R0 with the machine-matched control (secondary)

Control seeds per arm: {"P8d": {"arm_rep": "DIFF", "control_seeds": ["clean_seed12", "clean_seed13", "clean_seed14", "clean_seed15", "clean_seed16", "clean_seed17", "clean_seed18", "clean_seed19"]}, "P8e": {"arm_rep": "DIFF", "control_seeds": ["clean_seed12", "clean_seed13", "clean_seed14", "clean_seed15", "clean_seed16", "clean_seed17", "clean_seed18", "clean_seed19"]}}

| comparison | set | metric | patients | arm seeds | Δ [95 %] | reading | wording |
|---|---|---|---|---|---|---|---|
| P8d - R0 (control DIFF) | unseen | sens | 11 | 8 | -0.003 [-0.118, +0.116] | secondary | no measurable difference |
| P8d - R0 (control DIFF) | unseen | f1 | 11 | 8 | -0.025 [-0.060, +0.010] | secondary | no measurable difference |
| P8d - R0 (control DIFF) | unseen | fa | 11 | 8 | +7.2 [+2.0, +13.0] | secondary | more false alarms |
| P8d - R0 (control DIFF) | development | sens | 15 | 8 | -0.022 [-0.083, +0.034] | secondary | no measurable difference |
| P8d - R0 (control DIFF) | development | f1 | 15 | 8 | -0.001 [-0.030, +0.027] | secondary | no measurable difference |
| P8d - R0 (control DIFF) | development | fa | 15 | 8 | +2.2 [-0.1, +4.7] | secondary | no measurable difference |
| P8d - R0 (control DIFF) | validation | sens | 3 | 8 | -0.083 [-0.250, +0.000] | secondary | no measurable difference |
| P8d - R0 (control DIFF) | validation | f1 | 3 | 8 | -0.060 [-0.104, -0.020] | secondary | loses |
| P8d - R0 (control DIFF) | validation | fa | 3 | 8 | +3.8 [-0.1, +6.6] | secondary | no measurable difference |
| P8d - R0 (control DIFF) | test | sens | 8 | 8 | +0.027 [-0.119, +0.173] | secondary | no measurable difference |
| P8d - R0 (control DIFF) | test | f1 | 8 | 8 | -0.012 [-0.055, +0.028] | secondary | no measurable difference |
| P8d - R0 (control DIFF) | test | fa | 8 | 8 | +8.4 [+1.6, +16.1] | secondary | more false alarms |
| P8d - R0 (control DIFF) | chb24 | sens | 1 | 8 | +0.078 [—, —] | secondary | descriptive (one patient) |
| P8d - R0 (control DIFF) | chb24 | f1 | 1 | 8 | +0.026 [—, —] | secondary | descriptive (one patient) |
| P8d - R0 (control DIFF) | chb24 | fa | 1 | 8 | +2.1 [—, —] | secondary | descriptive (one patient) |
| P8d - R0 (control DIFF) | siena | sens | 14 | 8 | -0.149 [-0.330, +0.006] | secondary | no measurable difference |
| P8d - R0 (control DIFF) | siena | f1 | 14 | 8 | -0.053 [-0.124, +0.007] | secondary | no measurable difference |
| P8d - R0 (control DIFF) | siena | fa | 14 | 8 | -3.8 [-10.4, +2.6] | secondary | no measurable difference |
| P8e - R0 (control DIFF) | unseen | sens | 11 | 8 | -0.112 [-0.221, -0.005] | secondary | loses |
| P8e - R0 (control DIFF) | unseen | f1 | 11 | 8 | -0.034 [-0.075, +0.008] | secondary | no measurable difference |
| P8e - R0 (control DIFF) | unseen | fa | 11 | 8 | -1.3 [-5.7, +2.6] | secondary | no measurable difference |
| P8e - R0 (control DIFF) | development | sens | 15 | 8 | -0.070 [-0.149, -0.007] | secondary | loses |
| P8e - R0 (control DIFF) | development | f1 | 15 | 8 | -0.002 [-0.041, +0.037] | secondary | no measurable difference |
| P8e - R0 (control DIFF) | development | fa | 15 | 8 | -1.9 [-4.7, +1.1] | secondary | no measurable difference |
| P8e - R0 (control DIFF) | validation | sens | 3 | 8 | -0.142 [-0.400, +0.000] | secondary | no measurable difference |
| P8e - R0 (control DIFF) | validation | f1 | 3 | 8 | -0.074 [-0.144, -0.006] | secondary | loses |
| P8e - R0 (control DIFF) | validation | fa | 3 | 8 | +3.2 [-0.3, +7.2] | secondary | no measurable difference |
| P8e - R0 (control DIFF) | test | sens | 8 | 8 | -0.101 [-0.223, +0.022] | secondary | no measurable difference |
| P8e - R0 (control DIFF) | test | f1 | 8 | 8 | -0.019 [-0.066, +0.029] | secondary | no measurable difference |
| P8e - R0 (control DIFF) | test | fa | 8 | 8 | -3.0 [-8.0, +1.6] | secondary | no measurable difference |
| P8e - R0 (control DIFF) | chb24 | sens | 1 | 8 | +0.211 [—, —] | secondary | descriptive (one patient) |
| P8e - R0 (control DIFF) | chb24 | f1 | 1 | 8 | -0.116 [—, —] | secondary | descriptive (one patient) |
| P8e - R0 (control DIFF) | chb24 | fa | 1 | 8 | +35.2 [—, —] | secondary | descriptive (one patient) |
| P8e - R0 (control DIFF) | siena | sens | 14 | 8 | -0.031 [-0.174, +0.131] | secondary | no measurable difference |
| P8e - R0 (control DIFF) | siena | f1 | 14 | 8 | -0.050 [-0.098, -0.006] | secondary | loses |
| P8e - R0 (control DIFF) | siena | fa | 14 | 8 | +8.3 [+2.2, +14.7] | secondary | more false alarms |

## Means over seeds

| set | variant | seeds | sensitivity | F1 | FP/day |
|---|---|---|---|---|---|
| unseen | V0 | 4 | 0.667 ± 0.028 | 0.198 ± 0.010 | 26.2 ± 1.0 |
| unseen | R0 | 16 | 0.638 ± 0.036 | 0.186 ± 0.012 | 26.8 ± 1.2 |
| unseen | 10a | 4 | 0.403 ± 0.039 | 0.066 ± 0.007 | 52.8 ± 1.3 |
| unseen | P8c | 8 | 0.475 ± 0.023 | 0.160 ± 0.012 | 24.5 ± 1.6 |
| unseen | P8d | 8 | 0.625 ± 0.041 | 0.159 ± 0.011 | 34.1 ± 1.2 |
| unseen | P8e | 8 | 0.516 ± 0.024 | 0.150 ± 0.009 | 25.6 ± 1.2 |
| development | V0 | 4 | 0.832 ± 0.014 | 0.225 ± 0.009 | 23.2 ± 0.6 |
| development | R0 | 16 | 0.803 ± 0.029 | 0.225 ± 0.012 | 22.7 ± 0.7 |
| development | 10a | 4 | 0.513 ± 0.018 | 0.061 ± 0.005 | 49.9 ± 0.5 |
| development | P8c | 8 | 0.816 ± 0.031 | 0.256 ± 0.012 | 20.2 ± 1.6 |
| development | P8d | 8 | 0.768 ± 0.043 | 0.220 ± 0.016 | 25.1 ± 1.5 |
| development | P8e | 8 | 0.720 ± 0.025 | 0.218 ± 0.012 | 21.0 ± 0.9 |
| validation | V0 | 4 | 0.933 ± 0.054 | 0.248 ± 0.017 | 19.4 ± 0.9 |
| validation | R0 | 16 | 0.946 ± 0.044 | 0.249 ± 0.025 | 19.4 ± 2.2 |
| validation | 10a | 4 | 0.589 ± 0.074 | 0.078 ± 0.011 | 47.1 ± 1.0 |
| validation | P8c | 8 | 0.817 ± 0.047 | 0.192 ± 0.027 | 20.3 ± 2.4 |
| validation | P8d | 8 | 0.858 ± 0.043 | 0.188 ± 0.017 | 23.5 ± 2.3 |
| validation | P8e | 8 | 0.800 ± 0.036 | 0.174 ± 0.016 | 22.9 ± 2.8 |
| test | V0 | 4 | 0.567 ± 0.019 | 0.180 ± 0.009 | 28.7 ± 1.3 |
| test | R0 | 16 | 0.523 ± 0.048 | 0.163 ± 0.015 | 29.6 ± 1.1 |
| test | 10a | 4 | 0.334 ± 0.029 | 0.062 ± 0.006 | 54.9 ± 1.7 |
| test | P8c | 8 | 0.347 ± 0.023 | 0.147 ± 0.010 | 26.1 ± 2.0 |
| test | P8d | 8 | 0.537 ± 0.052 | 0.148 ± 0.012 | 38.0 ± 1.2 |
| test | P8e | 8 | 0.409 ± 0.034 | 0.140 ± 0.010 | 26.6 ± 1.1 |
| chb24 | V0 | 4 | 0.844 ± 0.036 | 0.500 ± 0.013 | 27.8 ± 1.1 |
| chb24 | R0 | 16 | 0.801 ± 0.100 | 0.489 ± 0.045 | 26.7 ± 3.7 |
| chb24 | 10a | 4 | 0.234 ± 0.060 | 0.126 ± 0.031 | 45.1 ± 3.5 |
| chb24 | P8c | 8 | 1.000 ± 0.000 | 0.344 ± 0.031 | 70.1 ± 9.7 |
| chb24 | P8d | 8 | 0.859 ± 0.099 | 0.516 ± 0.049 | 27.4 ± 8.3 |
| chb24 | P8e | 8 | 0.992 ± 0.022 | 0.374 ± 0.025 | 60.5 ± 5.9 |
| siena | V0 | 4 | 0.645 ± 0.092 | 0.233 ± 0.029 | 40.6 ± 1.5 |
| siena | R0 | 16 | 0.643 ± 0.066 | 0.223 ± 0.018 | 41.1 ± 2.6 |
| siena | 10a | 4 | 0.568 ± 0.065 | 0.131 ± 0.009 | 66.4 ± 1.9 |
| siena | P8c | 8 | 0.627 ± 0.078 | 0.214 ± 0.028 | 44.3 ± 1.7 |
| siena | P8d | 8 | 0.497 ± 0.053 | 0.176 ± 0.020 | 35.6 ± 2.7 |
| siena | P8e | 8 | 0.615 ± 0.046 | 0.179 ± 0.018 | 47.7 ± 1.7 |

## R4 — events at each budget (CPD stage; per-seed means of the set sums)

| set | budget | variant | seeds | events | seizures found | false alarms | s per event | flagged time % | windows flagged % |
|---|---|---|---|---|---|---|---|---|---|
| development | fixed | 10a | 4 | 1186 | 35.5 / 94 | 1151 | 42.1 | 2.05 | 0.50 |
| development | fixed | P8c | 8 | 515 | 62.2 / 94 | 453 | 64.0 | 1.35 | 0.50 |
| development | fixed | P8d | 8 | 710 | 56.9 / 94 | 653 | 50.8 | 1.48 | 0.50 |
| development | fixed | P8e | 8 | 582 | 49.5 / 94 | 533 | 60.2 | 1.44 | 0.50 |
| development | fixed | R0 | 16 | 618 | 60.1 / 94 | 558 | 56.4 | 1.44 | 0.50 |
| development | fixed | V0 | 4 | 610 | 62.2 / 94 | 548 | 56.0 | 1.41 | 0.50 |
| development | own | 10a | 4 | 1465 | 37.8 / 94 | 1427 | 43.4 | 2.62 | 0.62 |
| development | own | P8c | 8 | 648 | 69.0 / 94 | 579 | 64.8 | 1.73 | 0.69 |
| development | own | P8d | 8 | 799 | 59.8 / 94 | 739 | 51.8 | 1.70 | 0.63 |
| development | own | P8e | 8 | 669 | 53.2 / 94 | 616 | 60.0 | 1.66 | 0.60 |
| development | own | R0 | 16 | 706 | 61.7 / 94 | 644 | 55.9 | 1.63 | 0.62 |
| development | own | V0 | 4 | 714 | 63.0 / 94 | 651 | 55.1 | 1.62 | 0.64 |
| siena | fixed | 10a | 4 | 222 | 15.8 / 47 | 206 | 48.7 | 2.12 | 0.50 |
| siena | fixed | P8c | 8 | 175 | 21.9 / 47 | 153 | 54.0 | 1.86 | 0.50 |
| siena | fixed | P8d | 8 | 164 | 19.1 / 47 | 145 | 55.3 | 1.78 | 0.50 |
| siena | fixed | P8e | 8 | 140 | 18.1 / 47 | 122 | 61.6 | 1.69 | 0.50 |
| siena | fixed | R0 | 16 | 143 | 20.8 / 47 | 122 | 60.7 | 1.71 | 0.50 |
| siena | fixed | V0 | 4 | 140 | 20.5 / 47 | 120 | 61.7 | 1.70 | 0.50 |
| siena | own | 10a | 4 | 421 | 23.0 / 47 | 398 | 59.0 | 4.89 | 1.47 |
| siena | own | P8c | 8 | 286 | 29.0 / 47 | 257 | 69.1 | 3.90 | 1.18 |
| siena | own | P8d | 8 | 239 | 22.5 / 47 | 217 | 57.7 | 2.72 | 0.79 |
| siena | own | P8e | 8 | 316 | 28.4 / 47 | 287 | 72.8 | 4.53 | 1.48 |
| siena | own | R0 | 16 | 282 | 28.4 / 47 | 254 | 65.8 | 3.65 | 1.25 |
| siena | own | V0 | 4 | 284 | 29.5 / 47 | 255 | 66.0 | 3.70 | 1.27 |
| unseen | fixed | 10a | 4 | 683 | 28.5 / 91 | 655 | 40.8 | 1.98 | 0.50 |
| unseen | fixed | P8c | 8 | 352 | 29.9 / 91 | 322 | 60.0 | 1.50 | 0.50 |
| unseen | fixed | P8d | 8 | 465 | 39.0 / 91 | 426 | 50.0 | 1.65 | 0.50 |
| unseen | fixed | P8e | 8 | 375 | 30.1 / 91 | 345 | 59.5 | 1.58 | 0.50 |
| unseen | fixed | R0 | 16 | 404 | 35.9 / 91 | 368 | 54.2 | 1.55 | 0.50 |
| unseen | fixed | V0 | 4 | 396 | 39.5 / 91 | 357 | 53.3 | 1.50 | 0.50 |
| unseen | own | 10a | 4 | 890 | 37.2 / 91 | 853 | 44.1 | 2.79 | 0.76 |
| unseen | own | P8c | 8 | 438 | 35.2 / 91 | 403 | 61.6 | 1.92 | 0.64 |
| unseen | own | P8d | 8 | 570 | 48.0 / 91 | 522 | 52.5 | 2.12 | 0.70 |
| unseen | own | P8e | 8 | 427 | 35.5 / 91 | 391 | 61.7 | 1.87 | 0.64 |
| unseen | own | R0 | 16 | 483 | 47.9 / 91 | 435 | 56.4 | 1.93 | 0.68 |
| unseen | own | V0 | 4 | 473 | 50.2 / 91 | 422 | 55.7 | 1.87 | 0.68 |

## R3 — seeds

| arm | seed | parameters | validation loss | training loss | ms per step | unseen sensitivity | unseen FP/day | dev sensitivity | Siena sensitivity |
|---|---|---|---|---|---|---|---|---|---|
| P8d | clean_seed1 | 3479 | 0.01969 | 0.01453 | 8.057 | 0.602 | 33.8 | 0.736 | 0.468 |
| P8d | clean_seed2 | 3479 | 0.01966 | 0.01451 | 8.053 | 0.649 | 33.1 | 0.759 | 0.482 |
| P8d | clean_seed3 | 3479 | 0.01970 | 0.01452 | 8.038 | 0.631 | 34.0 | 0.790 | 0.467 |
| P8d | clean_seed4 | 3479 | 0.01969 | 0.01450 | 8.37 | 0.685 | 35.1 | 0.831 | 0.610 |
| P8d | clean_seed5 | 3479 | 0.01966 | 0.01449 | 8.391 | 0.628 | 33.1 | 0.790 | 0.449 |
| P8d | clean_seed6 | 3479 | 0.01966 | 0.01450 | 8.393 | 0.542 | 33.6 | 0.792 | 0.487 |
| P8d | clean_seed7 | 3479 | 0.01968 | 0.01450 | 8.396 | 0.622 | 36.5 | 0.689 | 0.474 |
| P8d | clean_seed42 | 3479 | 0.01968 | 0.01451 | 8.039 | 0.639 | 33.1 | 0.754 | 0.539 |
| P8e | clean_seed1 | 2812 | 0.02594 | 0.01928 | 8.203 | 0.526 | 27.7 | 0.702 | 0.665 |
| P8e | clean_seed2 | 2812 | 0.02580 | 0.01928 | 8.222 | 0.529 | 25.9 | 0.714 | 0.548 |
| P8e | clean_seed3 | 2812 | 0.02569 | 0.01925 | 8.202 | 0.545 | 25.7 | 0.757 | 0.576 |
| P8e | clean_seed4 | 2812 | 0.02575 | 0.01926 | 8.786 | 0.517 | 25.2 | 0.737 | 0.686 |
| P8e | clean_seed5 | 2812 | 0.02573 | 0.01936 | 8.761 | 0.483 | 24.5 | 0.720 | 0.593 |
| P8e | clean_seed6 | 2812 | 0.02573 | 0.01928 | 8.789 | 0.476 | 25.5 | 0.675 | 0.619 |
| P8e | clean_seed7 | 2812 | 0.02580 | 0.01925 | 8.773 | 0.519 | 23.7 | 0.735 | 0.598 |
| P8e | clean_seed42 | 2812 | 0.02573 | 0.01926 | 8.196 | 0.530 | 26.6 | 0.722 | 0.637 |
| P8c | clean_seed1 | 2327 | 0.02743 | 0.01947 | 8.67 | 0.464 | 26.3 | 0.832 | 0.485 |
| P8c | clean_seed2 | 2327 | 0.02786 | 0.01964 | 8.656 | 0.506 | 23.0 | 0.859 | 0.727 |
| P8c | clean_seed3 | 2327 | 0.02736 | 0.01941 | 8.683 | 0.427 | 24.1 | 0.810 | 0.611 |
| P8c | clean_seed4 | 2327 | 0.02756 | 0.01951 | 9.394 | 0.479 | 26.8 | 0.784 | 0.630 |
| P8c | clean_seed5 | 2327 | 0.02854 | 0.01953 | 9.428 | 0.488 | 23.7 | 0.857 | 0.605 |
| P8c | clean_seed6 | 2327 | 0.02835 | 0.01949 | 9.403 | 0.469 | 22.2 | 0.802 | 0.646 |
| P8c | clean_seed7 | 2327 | 0.02710 | 0.01955 | 9.441 | 0.485 | 26.0 | 0.805 | 0.726 |
| P8c | clean_seed42 | 2327 | 0.02803 | 0.01948 | 8.692 | 0.482 | 24.1 | 0.776 | 0.587 |

Gates: {"m_gates": "PASS", "m0": "PASS", "m1": "PASS", "m2": "PASS", "m4": "PASS", "m5": "PASS", "m6": "PASS", "m7": "PASS"}; R0 k 4.138745506.
