# RP aggregate — main model of the final report (seeds 1-4, k per seed); descriptive

Gates: A0 PASS, A1 PASS (RP_RUN mode exact). Demo model: seed 3 (validation loss {"1": 0.020844111434912032, "2": 0.020848997497762697, "3": 0.020768452966321658, "4": 0.02080145203665401}).

## Per-patient means, CPD stage: 4-seed mean ± SD, patient bootstrap 95 % CI

| set | arm | subjects | n_ref | tp_mean | fp_mean | sens | sens_sd | sens_ci_lo | sens_ci_hi | prec | f1 | f1_sd | fa | fa_sd | fa_ci_lo | fa_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| test | final (per-patient budget) | 8 | 76 | 34.8 | 353.2 | 0.541 | 0.032 | 0.312 | 0.770 | 0.101 | 0.166 | 0.011 | 30.2 | 1.6 | 25.0 | 34.9 |
| test | held-out (0.5 %) | 8 | 76 | 23.5 | 291.2 | 0.466 | 0.028 | 0.217 | 0.729 | 0.089 | 0.144 | 0.013 | 25.3 | 1.0 | 18.7 | 31.5 |
| development | final (per-patient budget) | 15 | 94 | 63.0 | 678.2 | 0.817 | 0.020 | 0.677 | 0.945 | 0.141 | 0.219 | 0.010 | 23.7 | 0.9 | 18.3 | 28.5 |
| development | held-out (0.5 %) | 15 | 94 | 60.8 | 571.8 | 0.791 | 0.023 | 0.651 | 0.917 | 0.174 | 0.248 | 0.018 | 19.5 | 0.5 | 15.0 | 23.5 |
| chb24 | final (per-patient budget) | 1 | 16 | 13.8 | 25.0 | 0.859 | 0.031 | 0.859 | 0.859 | 0.355 | 0.502 | 0.016 | 28.4 | 0.9 | 28.4 | 28.4 |
| chb24 | held-out (0.5 %) | 1 | 16 | 9.8 | 12.5 | 0.609 | 0.094 | 0.609 | 0.609 | 0.437 | 0.508 | 0.061 | 14.2 | 0.7 | 14.2 | 14.2 |
| siena | final (per-patient budget) | 14 | 47 | 29.2 | 265.5 | 0.654 | 0.068 | 0.482 | 0.805 | 0.157 | 0.219 | 0.018 | 43.0 | 2.4 | 32.0 | 54.5 |
| siena | held-out (0.5 %) | 14 | 47 | 22.2 | 120.2 | 0.478 | 0.042 | 0.295 | 0.660 | 0.221 | 0.264 | 0.022 | 19.8 | 1.0 | 14.6 | 24.9 |

## Per seed (CPD stage)

| set | arm | seed | tp | n_ref | fp | s_sens | s_f1 | s_fa |
|---|---|---|---|---|---|---|---|---|
| test | L2f | clean_seed1 | 36 | 76 | 369 | 0.559 | 0.170 | 31.5 |
| test | L2f | clean_seed2 | 36 | 76 | 372 | 0.563 | 0.162 | 31.7 |
| test | L2f | clean_seed3 | 35 | 76 | 338 | 0.547 | 0.178 | 28.8 |
| test | L2f | clean_seed4 | 32 | 76 | 334 | 0.494 | 0.152 | 29.0 |
| test | L2f | clean_seed42 | 36 | 76 | 364 | 0.560 | 0.165 | 31.0 |
| test | frozen | clean_seed1 | 25 | 76 | 294 | 0.491 | 0.157 | 25.2 |
| test | frozen | clean_seed2 | 24 | 76 | 310 | 0.470 | 0.136 | 26.8 |
| test | frozen | clean_seed3 | 24 | 76 | 285 | 0.478 | 0.154 | 24.6 |
| test | frozen | clean_seed4 | 21 | 76 | 276 | 0.426 | 0.130 | 24.5 |
| test | frozen | clean_seed42 | 23 | 76 | 305 | 0.460 | 0.134 | 26.3 |
| development | L2f | clean_seed1 | 63 | 94 | 654 | 0.805 | 0.220 | 23.0 |
| development | L2f | clean_seed2 | 62 | 94 | 709 | 0.809 | 0.207 | 25.0 |
| development | L2f | clean_seed3 | 66 | 94 | 682 | 0.846 | 0.231 | 23.8 |
| development | L2f | clean_seed4 | 61 | 94 | 668 | 0.807 | 0.218 | 23.2 |
| development | L2f | clean_seed42 | 64 | 94 | 679 | 0.837 | 0.222 | 24.3 |
| development | frozen | clean_seed1 | 63 | 94 | 560 | 0.805 | 0.260 | 19.3 |
| development | frozen | clean_seed2 | 60 | 94 | 570 | 0.793 | 0.248 | 19.2 |
| development | frozen | clean_seed3 | 63 | 94 | 566 | 0.808 | 0.262 | 19.3 |
| development | frozen | clean_seed4 | 57 | 94 | 591 | 0.757 | 0.222 | 20.2 |
| development | frozen | clean_seed42 | 64 | 94 | 568 | 0.837 | 0.267 | 19.8 |
| chb24 | L2f | clean_seed1 | 13 | 16 | 25 | 0.812 | 0.481 | 28.4 |
| chb24 | L2f | clean_seed2 | 14 | 16 | 26 | 0.875 | 0.500 | 29.5 |
| chb24 | L2f | clean_seed3 | 14 | 16 | 25 | 0.875 | 0.509 | 28.4 |
| chb24 | L2f | clean_seed4 | 14 | 16 | 24 | 0.875 | 0.519 | 27.2 |
| chb24 | L2f | clean_seed42 | 15 | 16 | 34 | 0.938 | 0.462 | 38.6 |
| chb24 | frozen | clean_seed1 | 8 | 16 | 13 | 0.500 | 0.432 | 14.8 |
| chb24 | frozen | clean_seed2 | 11 | 16 | 12 | 0.688 | 0.564 | 13.6 |
| chb24 | frozen | clean_seed3 | 11 | 16 | 13 | 0.688 | 0.550 | 14.8 |
| chb24 | frozen | clean_seed4 | 9 | 16 | 12 | 0.562 | 0.486 | 13.6 |
| chb24 | frozen | clean_seed42 | 12 | 16 | 12 | 0.750 | 0.600 | 13.6 |
| siena | L2f | clean_seed1 | 27 | 47 | 272 | 0.633 | 0.203 | 44.0 |
| siena | L2f | clean_seed2 | 29 | 47 | 264 | 0.664 | 0.219 | 42.4 |
| siena | L2f | clean_seed3 | 28 | 47 | 250 | 0.576 | 0.211 | 39.9 |
| siena | L2f | clean_seed4 | 33 | 47 | 276 | 0.740 | 0.244 | 45.7 |
| siena | L2f | clean_seed42 | 32 | 47 | 275 | 0.760 | 0.249 | 44.9 |
| siena | frozen | clean_seed1 | 21 | 47 | 125 | 0.474 | 0.256 | 21.2 |
| siena | frozen | clean_seed2 | 22 | 47 | 116 | 0.433 | 0.241 | 18.9 |
| siena | frozen | clean_seed3 | 22 | 47 | 118 | 0.470 | 0.264 | 19.2 |
| siena | frozen | clean_seed4 | 24 | 47 | 122 | 0.535 | 0.294 | 19.8 |
| siena | frozen | clean_seed42 | 21 | 47 | 122 | 0.480 | 0.250 | 21.1 |

## Final − held-out (paired, CPD stage)

| set | metric | subjects | a | b | diff | ci_lo | ci_hi |
|---|---|---|---|---|---|---|---|
| chb24 | sens | 1 | 0.859 | 0.609 | +0.250 | +0.250 | +0.250 |
| chb24 | f1 | 1 | 0.502 | 0.508 | -0.006 | -0.006 | -0.006 |
| chb24 | fa | 1 | 28.381 | 14.190 | +14.190 | +14.190 | +14.190 |
| development | sens | 15 | 0.817 | 0.791 | +0.026 | +0.005 | +0.057 |
| development | f1 | 15 | 0.219 | 0.248 | -0.029 | -0.048 | -0.010 |
| development | fa | 15 | 23.737 | 19.520 | +4.217 | +1.715 | +7.051 |
| siena | sens | 14 | 0.654 | 0.478 | +0.176 | +0.068 | +0.298 |
| siena | f1 | 14 | 0.219 | 0.264 | -0.044 | -0.121 | +0.021 |
| siena | fa | 14 | 43.005 | 19.751 | +23.255 | +13.589 | +32.648 |
| test | sens | 8 | 0.541 | 0.466 | +0.075 | +0.000 | +0.209 |
| test | f1 | 8 | 0.166 | 0.144 | +0.021 | -0.022 | +0.087 |
| test | fa | 8 | 30.246 | 25.285 | +4.961 | +0.238 | +11.938 |

## k per seed; correction (seeds 1-3, own k − R1 k), arm final, CPD stage

| seed | k | k_r1 | median_dev_q_own_k | median_dev_q_r1_k |
|---|---|---|---|---|
| clean_seed42 | 3.7852 | 3.7852 | 0.0050 | 0.0050 |
| clean_seed1 | 4.1313 | 3.7852 | 0.0050 | 0.0065 |
| clean_seed2 | 3.9446 | 3.7852 | 0.0050 | 0.0062 |
| clean_seed3 | 4.0384 | 3.7852 | 0.0050 | 0.0056 |
| clean_seed4 | 4.0092 | 3.7852 | 0.0050 |  |

| set | metric | subjects | a | b | diff | ci_lo | ci_hi |
|---|---|---|---|---|---|---|---|
| chb24 | sens | 1 | 0.854 | 0.854 | +0.000 | +0.000 | +0.000 |
| chb24 | f1 | 1 | 0.497 | 0.486 | +0.011 | +0.011 | +0.011 |
| chb24 | fa | 1 | 28.759 | 30.273 | -1.514 | -1.514 | -1.514 |
| development | sens | 15 | 0.820 | 0.823 | -0.003 | -0.010 | +0.000 |
| development | f1 | 15 | 0.219 | 0.202 | +0.017 | +0.008 | +0.028 |
| development | fa | 15 | 23.916 | 26.612 | -2.696 | -3.770 | -1.623 |
| siena | sens | 14 | 0.625 | 0.679 | -0.054 | -0.119 | +0.000 |
| siena | f1 | 14 | 0.211 | 0.218 | -0.007 | -0.035 | +0.018 |
| siena | fa | 14 | 42.108 | 46.512 | -4.404 | -6.779 | -2.221 |
| test | sens | 8 | 0.557 | 0.580 | -0.023 | -0.047 | -0.006 |
| test | f1 | 8 | 0.170 | 0.164 | +0.006 | +0.001 | +0.014 |
| test | fa | 8 | 30.649 | 32.678 | -2.029 | -4.069 | -0.396 |

## Onset / offset errors (s), seeds 1-4 pooled, median |error|

| set | arm | pairs | med_abs_cpd_on | med_abs_cpd_off | med_abs_hyb_on | med_abs_hyb_off | med_cpd_off | med_hyb_off |
|---|---|---|---|---|---|---|---|---|
| chb24 | L2f | 55.0 | 4.0 | 4.0 | 4.0 | 4.0 | 0.0 | -4.0 |
| chb24 | frozen | 39.0 | 4.0 | 4.0 | 4.0 | 4.0 | 0.0 | -4.0 |
| development | L2f | 248.0 | 8.0 | 16.0 | 8.0 | 12.0 | 0.0 | 0.0 |
| development | frozen | 240.0 | 8.0 | 16.0 | 8.0 | 12.0 | 0.0 | 0.0 |
| siena | L2f | 117.0 | 20.0 | 32.0 | 20.0 | 20.0 | 20.0 | 0.0 |
| siena | frozen | 89.0 | 20.0 | 20.0 | 20.0 | 16.0 | 16.0 | 0.0 |
| test | L2f | 139.0 | 16.0 | 24.0 | 16.0 | 16.0 | 16.0 | 0.0 |
| test | frozen | 94.0 | 8.0 | 22.0 | 8.0 | 16.0 | 18.0 | 8.0 |

All arms and stages: `summary.csv`, `summary_per_seed.csv`; per subject: `per_subject*.csv`; review load: `review.csv`. Descriptive only (plan P2).
