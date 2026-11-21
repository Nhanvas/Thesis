# Table T_PC7 — seed variance of the training recipe (R0 retrained, Kaggle CPU)

Design `results/eureka_d34f/DESIGN_PC7.md` (written before the run). Seeds reused from PC1: clean_seed1, clean_seed2, clean_seed3, clean_seed42; trained: clean_seed4, clean_seed5, clean_seed6, clean_seed7, clean_seed8, clean_seed9, clean_seed10, clean_seed11, clean_seed12, clean_seed13, clean_seed14, clean_seed15, clean_seed16, clean_seed17, clean_seed18, clean_seed19. Pooling rule: G-pc7plat / G-pc7rep {"pc7_A": {"G-pc7rep": "PASS", "G-pc7plat": "PASS"}, "pc7_B": {"G-pc7rep": "DIFF", "G-pc7plat": "PASS"}} -> **new seeds only, N = 16** in the primary reading. Per-patient means, own label-free point, after the localizer; development = 15 patients (primary).

## Seeds

| seed | origin | validation loss | training loss | dev sensitivity | dev F1 | dev FP/day | test sensitivity |
|---|---|---|---|---|---|---|---|
| clean_seed1 | PC1 (reused) (not in primary) | 0.02121 | 0.01582 | 0.821 | 0.238 | 22.4 | 0.562 |
| clean_seed2 | PC1 (reused) (not in primary) | 0.02124 | 0.01583 | 0.680 | 0.180 | 27.1 | 0.408 |
| clean_seed3 | PC1 (reused) (not in primary) | 0.02122 | 0.01583 | 0.841 | 0.227 | 22.7 | 0.511 |
| clean_seed42 | PC1 (reused) (not in primary) | 0.02133 | 0.01587 | 0.817 | 0.234 | 22.5 | 0.495 |
| clean_seed4 | pc7_A | 0.02127 | 0.01584 | 0.824 | 0.223 | 22.4 | 0.566 |
| clean_seed5 | pc7_A | 0.02130 | 0.01586 | 0.837 | 0.233 | 22.5 | 0.547 |
| clean_seed6 | pc7_A | 0.02125 | 0.01583 | 0.828 | 0.227 | 23.3 | 0.477 |
| clean_seed7 | pc7_A | 0.02130 | 0.01586 | 0.804 | 0.234 | 22.4 | 0.575 |
| clean_seed8 | pc7_A | 0.02123 | 0.01585 | 0.813 | 0.236 | 22.8 | 0.597 |
| clean_seed9 | pc7_A | 0.02129 | 0.01584 | 0.812 | 0.228 | 22.6 | 0.496 |
| clean_seed10 | pc7_A | 0.02123 | 0.01581 | 0.801 | 0.238 | 21.3 | 0.537 |
| clean_seed11 | pc7_A | 0.02132 | 0.01589 | 0.809 | 0.220 | 23.0 | 0.492 |
| clean_seed12 | pc7_B | 0.02126 | 0.01583 | 0.777 | 0.221 | 22.6 | 0.428 |
| clean_seed13 | pc7_B | 0.02124 | 0.01582 | 0.815 | 0.226 | 23.3 | 0.473 |
| clean_seed14 | pc7_B | 0.02123 | 0.01581 | 0.807 | 0.229 | 22.8 | 0.554 |
| clean_seed15 | pc7_B | 0.02126 | 0.01584 | 0.711 | 0.193 | 24.5 | 0.556 |
| clean_seed16 | pc7_B | 0.02121 | 0.01583 | 0.789 | 0.213 | 23.0 | 0.562 |
| clean_seed17 | pc7_B | 0.02123 | 0.01584 | 0.816 | 0.221 | 23.1 | 0.538 |
| clean_seed18 | pc7_B | 0.02124 | 0.01584 | 0.801 | 0.243 | 21.3 | 0.454 |
| clean_seed19 | pc7_B | 0.02126 | 0.01584 | 0.805 | 0.216 | 22.5 | 0.515 |

## Q1 — spread over seeds (R0; V0 = V5's four trainings)

| set | variant | metric | seeds | mean | SD [95 % interval] | min | median | max |
|---|---|---|---|---|---|---|---|---|
| development | R0 | sens | 16 | 0.803 | 0.029 [0.021, 0.044] | 0.711 | 0.808 | 0.837 |
| development | R0 | f1 | 16 | 0.225 | 0.012 [0.009, 0.018] | 0.193 | 0.227 | 0.243 |
| development | R0 | fa | 16 | 22.7 | 0.7 [0.6, 1.2] | 21.3 | 22.7 | 24.5 |
| development | R0s | sens | 16 | 0.808 | 0.019 [0.014, 0.030] | 0.754 | 0.810 | 0.837 |
| development | R0s | f1 | 16 | 0.223 | 0.017 [0.013, 0.026] | 0.184 | 0.226 | 0.247 |
| development | R0s | fa | 16 | 23.2 | 2.1 [1.5, 3.2] | 20.7 | 22.8 | 29.4 |
| development | V0 | sens | 4 | 0.832 | 0.014 [0.008, 0.051] | 0.816 | 0.832 | 0.847 |
| development | V0 | f1 | 4 | 0.225 | 0.009 [0.005, 0.033] | 0.215 | 0.225 | 0.237 |
| development | V0 | fa | 4 | 23.2 | 0.6 [0.3, 2.2] | 22.7 | 23.0 | 24.0 |
| test | R0 | sens | 16 | 0.523 | 0.048 [0.036, 0.075] | 0.428 | 0.538 | 0.597 |
| test | R0 | f1 | 16 | 0.163 | 0.015 [0.011, 0.023] | 0.129 | 0.165 | 0.185 |
| test | R0 | fa | 16 | 29.6 | 1.1 [0.8, 1.7] | 27.6 | 29.7 | 31.5 |
| test | R0s | sens | 16 | 0.523 | 0.046 [0.034, 0.072] | 0.428 | 0.531 | 0.581 |
| test | R0s | f1 | 16 | 0.161 | 0.016 [0.012, 0.025] | 0.121 | 0.161 | 0.185 |
| test | R0s | fa | 16 | 30.0 | 2.1 [1.6, 3.3] | 27.6 | 29.7 | 36.5 |
| test | V0 | sens | 4 | 0.567 | 0.019 [0.011, 0.071] | 0.545 | 0.568 | 0.588 |
| test | V0 | f1 | 4 | 0.180 | 0.009 [0.005, 0.033] | 0.169 | 0.181 | 0.190 |
| test | V0 | fa | 4 | 28.7 | 1.3 [0.7, 4.9] | 26.8 | 29.1 | 29.9 |
| chb24 | R0 | sens | 16 | 0.801 | 0.100 [0.074, 0.155] | 0.500 | 0.812 | 0.938 |
| chb24 | R0 | f1 | 16 | 0.489 | 0.045 [0.033, 0.070] | 0.390 | 0.477 | 0.571 |
| chb24 | R0 | fa | 16 | 26.7 | 3.7 [2.7, 5.7] | 19.3 | 26.1 | 34.1 |
| chb24 | R0s | sens | 16 | 0.824 | 0.061 [0.045, 0.095] | 0.688 | 0.812 | 0.938 |
| chb24 | R0s | f1 | 16 | 0.493 | 0.034 [0.025, 0.053] | 0.444 | 0.491 | 0.560 |
| chb24 | R0s | fa | 16 | 27.6 | 2.1 [1.5, 3.2] | 22.7 | 28.4 | 29.5 |
| chb24 | V0 | sens | 4 | 0.844 | 0.036 [0.020, 0.135] | 0.812 | 0.844 | 0.875 |
| chb24 | V0 | f1 | 4 | 0.500 | 0.013 [0.007, 0.049] | 0.481 | 0.505 | 0.509 |
| chb24 | V0 | fa | 4 | 27.8 | 1.1 [0.6, 4.2] | 26.1 | 28.4 | 28.4 |
| siena | R0 | sens | 16 | 0.643 | 0.066 [0.049, 0.102] | 0.537 | 0.627 | 0.783 |
| siena | R0 | f1 | 16 | 0.223 | 0.018 [0.013, 0.027] | 0.195 | 0.218 | 0.267 |
| siena | R0 | fa | 16 | 41.1 | 2.6 [1.9, 4.1] | 35.3 | 41.2 | 45.3 |
| siena | R0s | sens | 16 | 0.652 | 0.062 [0.046, 0.096] | 0.562 | 0.640 | 0.769 |
| siena | R0s | f1 | 16 | 0.221 | 0.018 [0.013, 0.028] | 0.195 | 0.216 | 0.262 |
| siena | R0s | fa | 16 | 42.8 | 4.0 [2.9, 6.2] | 36.2 | 42.1 | 53.0 |
| siena | V0 | sens | 4 | 0.645 | 0.092 [0.052, 0.343] | 0.569 | 0.620 | 0.771 |
| siena | V0 | f1 | 4 | 0.233 | 0.029 [0.016, 0.108] | 0.206 | 0.227 | 0.271 |
| siena | V0 | fa | 4 | 40.6 | 1.5 [0.8, 5.5] | 38.5 | 41.1 | 41.7 |

Variance components (patient x seed, R0): 

| set | metric | patients | seeds | SD seed (shared) | SD patient x seed | seed share of non-patient variance |
|---|---|---|---|---|---|---|
| development | sens | 15 | 16 | 0.020 | 0.079 | 0.06 |
| development | f1 | 15 | 16 | 0.008 | 0.035 | 0.05 |
| development | fa | 15 | 16 | 0.2 | 2.8 | 0.01 |
| test | sens | 8 | 16 | 0.033 | 0.100 | 0.10 |
| test | f1 | 8 | 16 | 0.009 | 0.033 | 0.07 |
| test | fa | 8 | 16 | 0.6 | 2.6 | 0.06 |
| siena | sens | 14 | 16 | 0.038 | 0.200 | 0.04 |
| siena | f1 | 14 | 16 | 0.007 | 0.060 | 0.01 |
| siena | fa | 14 | 16 | 2.0 | 6.2 | 0.10 |

## Q2 — does the loss pick the better detector?

| criterion | set | metric | Spearman rho [95 %] | selection gain, 4 seeds [95 %] | chosen >= subset median | reading | wording |
|---|---|---|---|---|---|---|---|
| val_loss | development | sens | +0.23 [-0.30, +0.67] | -0.001 [-0.012, +0.012] | 0.35 | primary | no evidence that it picks the better detector |
| val_loss | development | f1 | -0.13 [-0.66, +0.45] | +0.002 [-0.005, +0.009] | 0.58 | primary | no evidence that it picks the better detector |
| val_loss | test | sens | -0.14 [-0.61, +0.41] | +0.021 [-0.008, +0.041] | 0.66 | secondary | no evidence that it picks the better detector |
| val_loss | test | f1 | -0.22 [-0.74, +0.37] | +0.007 [-0.002, +0.012] | 0.75 | secondary | no evidence that it picks the better detector |
| val_loss | chb24 | sens | -0.39 [-0.72, +0.07] | +0.045 [-0.001, +0.087] | 0.85 | secondary | no evidence that it picks the better detector |
| val_loss | chb24 | f1 | -0.59 [-0.84, -0.15] | +0.025 [+0.000, +0.043] | 0.86 | secondary | picks the better detector |
| val_loss | siena | sens | -0.05 [-0.57, +0.47] | +0.007 [-0.023, +0.050] | 0.55 | secondary | no evidence that it picks the better detector |
| val_loss | siena | f1 | -0.06 [-0.58, +0.49] | +0.004 [-0.005, +0.016] | 0.52 | secondary | no evidence that it picks the better detector |
| train_loss | development | sens | +0.29 [-0.20, +0.66] | -0.001 [-0.012, +0.012] | 0.37 | secondary | no evidence that it picks the better detector |
| train_loss | development | f1 | +0.09 [-0.46, +0.60] | +0.002 [-0.005, +0.008] | 0.57 | secondary | no evidence that it picks the better detector |
| train_loss | test | sens | +0.25 [-0.27, +0.69] | -0.004 [-0.034, +0.019] | 0.41 | secondary | no evidence that it picks the better detector |
| train_loss | test | f1 | +0.17 [-0.41, +0.71] | -0.001 [-0.011, +0.005] | 0.47 | secondary | no evidence that it picks the better detector |
| train_loss | chb24 | sens | -0.22 [-0.61, +0.22] | +0.023 [-0.019, +0.063] | 0.74 | secondary | no evidence that it picks the better detector |
| train_loss | chb24 | f1 | -0.41 [-0.78, +0.09] | +0.016 [-0.006, +0.032] | 0.80 | secondary | no evidence that it picks the better detector |
| train_loss | siena | sens | -0.02 [-0.50, +0.49] | +0.005 [-0.028, +0.042] | 0.53 | secondary | no evidence that it picks the better detector |
| train_loss | siena | f1 | -0.25 [-0.77, +0.34] | +0.005 [-0.006, +0.017] | 0.67 | secondary | no evidence that it picks the better detector |

## Q3 — minimal detectable difference of an arm − control comparison (development; lower bounds)

| metric | seeds per arm | method | MDD 95 % | MDD 80 % power |
|---|---|---|---|---|
| sens | 4 | empirical (disjoint seed groups x patient bootstrap) | 0.048 | — |
| sens | 8 | empirical (disjoint seed groups x patient bootstrap) | 0.034 | — |
| sens | 4 | variance components | 0.040 | 0.056 |
| sens | 8 | variance components | 0.028 | 0.040 |
| sens | 12 | variance components | 0.023 | 0.033 |
| sens | 20 | variance components | 0.018 | 0.025 |
| f1 | 4 | empirical (disjoint seed groups x patient bootstrap) | 0.019 | — |
| f1 | 8 | empirical (disjoint seed groups x patient bootstrap) | 0.014 | — |
| f1 | 4 | variance components | 0.016 | 0.024 |
| f1 | 8 | variance components | 0.012 | 0.017 |
| f1 | 12 | variance components | 0.010 | 0.014 |
| f1 | 20 | variance components | 0.007 | 0.011 |
| fa | 4 | empirical (disjoint seed groups x patient bootstrap) | 1.4 | — |
| fa | 8 | empirical (disjoint seed groups x patient bootstrap) | 1.0 | — |
| fa | 4 | variance components | 1.0 | 1.5 |
| fa | 8 | variance components | 0.7 | 1.0 |
| fa | 12 | variance components | 0.6 | 0.9 |
| fa | 20 | variance components | 0.5 | 0.7 |

## Q4 — V5's four trainings in the distribution of 4-seed means of R0 (descriptive; other platform)

| set | metric | V5 | R0 mean | R0 4-seed means, central 95 % | V5 percentile |
|---|---|---|---|---|---|
| development | sens | 0.832 | 0.803 | 0.777 – 0.820 | 100 |
| development | f1 | 0.225 | 0.225 | 0.214 – 0.234 | 48 |
| development | fa | 23.2 | 22.7 | 22.1 – 23.4 | 90 |
| test | sens | 0.567 | 0.523 | 0.481 – 0.562 | 99 |
| test | f1 | 0.180 | 0.163 | 0.150 – 0.174 | 100 |
| test | fa | 28.7 | 29.6 | 28.6 – 30.5 | 4 |
| chb24 | sens | 0.844 | 0.801 | 0.703 – 0.875 | 91 |
| chb24 | f1 | 0.500 | 0.489 | 0.451 – 0.526 | 70 |
| chb24 | fa | 27.8 | 26.7 | 23.6 – 29.8 | 77 |
| siena | sens | 0.645 | 0.643 | 0.591 – 0.700 | 55 |
| siena | f1 | 0.233 | 0.223 | 0.210 – 0.240 | 90 |
| siena | fa | 40.6 | 41.1 | 38.8 – 43.2 | 33 |

## Q5 — PC1 re-read with the training variance (two-level bootstrap)

| comparison | set | metric | R0 seeds | Δ [95 %, patients + seeds] | PC1: Δ [95 %, patients only, 4 R0 seeds] | reading |
|---|---|---|---|---|---|---|
| 10a - R0 | development | sens | 16 | -0.290 [-0.415, -0.174] | -0.277 [-0.393, -0.163] | primary |
| 10a - R0 | development | f1 | 16 | -0.164 [-0.253, -0.102] | -0.159 [-0.250, -0.095] | primary |
| 10a - R0 | development | fa | 16 | 27.1 [21.6, 33.1] | 26.2 [20.7, 32.4] | primary |
| 10a - R0 | test | sens | 16 | -0.189 [-0.455, 0.030] | -0.160 [-0.398, 0.032] | descriptive |
| 10a - R0 | test | f1 | 16 | -0.101 [-0.159, -0.045] | -0.092 [-0.135, -0.047] | descriptive |
| 10a - R0 | test | fa | 16 | 25.3 [18.2, 32.4] | 24.9 [18.3, 31.8] | descriptive |
| 10a - R0 | chb24 | sens | 16 | -0.566 [—, —] | -0.594 [—, —] | descriptive |
| 10a - R0 | chb24 | f1 | 16 | -0.363 [—, —] | -0.385 [—, —] | descriptive |
| 10a - R0 | chb24 | fa | 16 | 18.4 [—, —] | 19.3 [—, —] | descriptive |
| 10a - R0 | siena | sens | 16 | -0.074 [-0.219, 0.077] | -0.102 [-0.276, 0.050] | descriptive |
| 10a - R0 | siena | f1 | 16 | -0.092 [-0.139, -0.047] | -0.099 [-0.146, -0.053] | descriptive |
| 10a - R0 | siena | fa | 16 | 25.3 [17.7, 33.3] | 27.2 [20.6, 33.5] | descriptive |
| 10b - R0 | development | sens | 16 | -0.001 [-0.038, 0.030] | 0.012 [-0.006, 0.033] | primary |
| 10b - R0 | development | f1 | 16 | 0.004 [-0.018, 0.022] | 0.009 [0.002, 0.016] | primary |
| 10b - R0 | development | fa | 16 | -0.6 [-2.0, 1.2] | -1.5 [-2.3, -0.6] | primary |
| 10b - R0 | test | sens | 16 | -0.011 [-0.084, 0.041] | 0.018 [-0.038, 0.079] | descriptive |
| 10b - R0 | test | f1 | 16 | 0.005 [-0.022, 0.030] | 0.015 [-0.013, 0.048] | descriptive |
| 10b - R0 | test | fa | 16 | -1.9 [-4.2, 0.3] | -2.3 [-4.1, -0.1] | descriptive |
| 10b - R0 | chb24 | sens | 16 | -0.098 [—, —] | -0.125 [—, —] | descriptive |
| 10b - R0 | chb24 | f1 | 16 | 0.017 [—, —] | -0.005 [—, —] | descriptive |
| 10b - R0 | chb24 | fa | 16 | -7.4 [—, —] | -6.5 [—, —] | descriptive |
| 10b - R0 | siena | sens | 16 | -0.069 [-0.192, 0.036] | -0.097 [-0.259, 0.020] | descriptive |
| 10b - R0 | siena | f1 | 16 | -0.008 [-0.043, 0.024] | -0.014 [-0.057, 0.023] | descriptive |
| 10b - R0 | siena | fa | 16 | -2.1 [-6.5, 2.2] | -0.3 [-3.1, 2.6] | descriptive |

## Q6 — k per seed (R0s) against the k of seed 42 (R0), development

| seed | sensitivity R0 | sensitivity R0s | F1 R0 | F1 R0s | FP/day R0 | FP/day R0s |
|---|---|---|---|---|---|---|
| clean_seed1 | 0.821 | 0.821 | 0.238 | 0.238 | 22.4 | 22.4 |
| clean_seed2 | 0.680 | 0.666 | 0.180 | 0.152 | 27.1 | 33.3 |
| clean_seed3 | 0.841 | 0.844 | 0.227 | 0.207 | 22.7 | 26.3 |
| clean_seed42 | 0.817 | 0.817 | 0.234 | 0.234 | 22.5 | 22.5 |
| clean_seed4 | 0.824 | 0.824 | 0.223 | 0.226 | 22.4 | 21.9 |
| clean_seed5 | 0.837 | 0.837 | 0.233 | 0.247 | 22.5 | 20.7 |
| clean_seed6 | 0.828 | 0.828 | 0.227 | 0.242 | 23.3 | 21.9 |
| clean_seed7 | 0.804 | 0.804 | 0.234 | 0.234 | 22.4 | 22.4 |
| clean_seed8 | 0.813 | 0.813 | 0.236 | 0.243 | 22.8 | 21.8 |
| clean_seed9 | 0.812 | 0.812 | 0.228 | 0.228 | 22.6 | 22.4 |
| clean_seed10 | 0.801 | 0.801 | 0.238 | 0.216 | 21.3 | 24.0 |
| clean_seed11 | 0.809 | 0.809 | 0.220 | 0.206 | 23.0 | 25.2 |
| clean_seed12 | 0.777 | 0.790 | 0.221 | 0.206 | 22.6 | 24.7 |
| clean_seed13 | 0.815 | 0.815 | 0.226 | 0.226 | 23.3 | 23.3 |
| clean_seed14 | 0.807 | 0.802 | 0.229 | 0.238 | 22.8 | 21.0 |
| clean_seed15 | 0.711 | 0.754 | 0.193 | 0.184 | 24.5 | 29.4 |
| clean_seed16 | 0.789 | 0.789 | 0.213 | 0.213 | 23.0 | 23.0 |
| clean_seed17 | 0.816 | 0.814 | 0.221 | 0.223 | 23.1 | 22.5 |
| clean_seed18 | 0.801 | 0.823 | 0.243 | 0.234 | 21.3 | 23.2 |
| clean_seed19 | 0.805 | 0.807 | 0.216 | 0.208 | 22.5 | 24.0 |
