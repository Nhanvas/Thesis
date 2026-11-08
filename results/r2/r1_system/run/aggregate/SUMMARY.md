# R1 aggregate — the thesis system rerun on complete data vs the record (descriptive)

Gates: A0 PASS, A1 PASS, A1-self PASS

k: record 4.067744, run 3.785202, cf 4.065955

Record rows matched: 1152; rows with tp different (rerun): 297, fp different: 1049

## Per-patient means (4 seeds; seed 42 in brackets), CPD stage, arms frozen and L2f

| set | arm | system | subjects | sens | sens_sd | sens42 | fa | fa_sd | fa42 | f1 | prec |
|---|---|---|---|---|---|---|---|---|---|---|---|
| development | L2f | record | 15 | 0.832 | 0.014 | 0.847 | 23.2 | 0.6 | 24.0 | 0.225 | 0.145 |
| development | L2f | cf_krec | 15 | 0.823 | 0.019 | 0.830 | 23.5 | 0.5 | 24.1 | 0.220 | 0.142 |
| development | L2f | cf | 15 | 0.823 | 0.019 | 0.830 | 23.5 | 0.5 | 24.1 | 0.220 | 0.142 |
| development | L2f | rerun | 15 | 0.827 | 0.019 | 0.837 | 26.0 | 1.2 | 24.3 | 0.207 | 0.131 |
| development | frozen | record | 15 | 0.822 | 0.009 | 0.834 | 19.2 | 0.5 | 19.4 | 0.262 | 0.181 |
| development | frozen | cf_krec | 15 | 0.813 | 0.012 | 0.817 | 19.3 | 0.5 | 19.6 | 0.258 | 0.178 |
| development | frozen | cf | 15 | 0.813 | 0.012 | 0.817 | 19.3 | 0.5 | 19.6 | 0.258 | 0.178 |
| development | frozen | rerun | 15 | 0.811 | 0.018 | 0.837 | 19.4 | 0.2 | 19.8 | 0.259 | 0.180 |
| test | L2f | record | 8 | 0.567 | 0.019 | 0.577 | 28.7 | 1.3 | 26.8 | 0.180 | 0.111 |
| test | L2f | cf_krec | 8 | 0.560 | 0.025 | 0.565 | 28.8 | 1.5 | 26.8 | 0.176 | 0.108 |
| test | L2f | cf | 8 | 0.560 | 0.025 | 0.565 | 28.8 | 1.5 | 26.8 | 0.176 | 0.108 |
| test | L2f | rerun | 8 | 0.575 | 0.017 | 0.560 | 32.3 | 1.9 | 31.0 | 0.164 | 0.099 |
| test | frozen | record | 8 | 0.498 | 0.010 | 0.508 | 23.8 | 1.3 | 21.8 | 0.161 | 0.100 |
| test | frozen | cf_krec | 8 | 0.494 | 0.020 | 0.496 | 23.8 | 1.5 | 21.6 | 0.159 | 0.098 |
| test | frozen | cf | 8 | 0.494 | 0.020 | 0.496 | 23.8 | 1.5 | 21.6 | 0.159 | 0.098 |
| test | frozen | rerun | 8 | 0.475 | 0.013 | 0.460 | 25.7 | 1.0 | 26.3 | 0.145 | 0.089 |
| chb24 | L2f | record | 1 | 0.828 | 0.060 | 0.875 | 28.4 | 1.6 | 29.5 | 0.488 | 0.346 |
| chb24 | L2f | cf_krec | 1 | 0.844 | 0.036 | 0.875 | 27.8 | 1.1 | 28.4 | 0.500 | 0.355 |
| chb24 | L2f | cf | 1 | 0.844 | 0.036 | 0.875 | 27.8 | 1.1 | 28.4 | 0.500 | 0.355 |
| chb24 | L2f | rerun | 1 | 0.875 | 0.051 | 0.938 | 32.4 | 4.8 | 38.6 | 0.480 | 0.331 |
| chb24 | frozen | cf_krec | 1 | 0.625 | 0.051 | 0.625 | 14.2 | 1.5 | 12.5 | 0.519 | 0.445 |
| chb24 | frozen | cf | 1 | 0.625 | 0.051 | 0.625 | 14.2 | 1.5 | 12.5 | 0.519 | 0.445 |
| chb24 | frozen | rerun | 1 | 0.656 | 0.108 | 0.750 | 14.2 | 0.7 | 13.6 | 0.537 | 0.454 |
| siena | L2f | record | 14 | 0.633 | 0.079 | 0.748 | 41.0 | 2.2 | 41.5 | 0.226 | 0.160 |
| siena | L2f | cf_krec | 14 | 0.645 | 0.092 | 0.771 | 40.6 | 1.5 | 40.6 | 0.233 | 0.165 |
| siena | L2f | cf | 14 | 0.645 | 0.092 | 0.771 | 40.6 | 1.5 | 40.6 | 0.233 | 0.165 |
| siena | L2f | rerun | 14 | 0.699 | 0.057 | 0.760 | 46.1 | 1.4 | 44.9 | 0.226 | 0.161 |
| siena | frozen | cf_krec | 14 | 0.418 | 0.046 | 0.485 | 20.1 | 2.0 | 17.7 | 0.231 | 0.195 |
| siena | frozen | cf | 14 | 0.418 | 0.046 | 0.485 | 20.1 | 2.0 | 17.7 | 0.231 | 0.195 |
| siena | frozen | rerun | 14 | 0.464 | 0.021 | 0.480 | 20.1 | 1.2 | 21.1 | 0.253 | 0.218 |

## Paired subject bootstrap (B = 10,000), CPD stage, arms frozen and L2f

| set | arm | step | metric | subjects | diff | ci_lo | ci_hi | subjects_changed |
|---|---|---|---|---|---|---|---|---|
| development | L2f | data (cf_krec - record) | f1 | 15 | -0.005 | -0.014 | +0.001 | 15 |
| development | L2f | data (cf_krec - record) | fa | 15 | +0.344 | -0.098 | +1.011 | 11 |
| development | L2f | data (cf_krec - record) | sens | 15 | -0.008 | -0.025 | +0.000 | 1 |
| development | L2f | k (cf - cf_krec) | f1 | 15 | -0.000 | -0.000 | +0.000 | 1 |
| development | L2f | k (cf - cf_krec) | fa | 15 | +0.006 | +0.000 | +0.018 | 1 |
| development | L2f | k (cf - cf_krec) | sens | 15 | +0.000 | +0.000 | +0.000 | 0 |
| development | L2f | new models (rerun - cf) | f1 | 15 | -0.013 | -0.025 | -0.002 | 15 |
| development | L2f | new models (rerun - cf) | fa | 15 | +2.482 | +0.928 | +4.106 | 15 |
| development | L2f | new models (rerun - cf) | sens | 15 | +0.003 | -0.011 | +0.017 | 5 |
| development | L2f | rerun - record | f1 | 15 | -0.018 | -0.034 | -0.004 | 15 |
| development | L2f | rerun - record | fa | 15 | +2.831 | +0.960 | +4.881 | 15 |
| development | L2f | rerun - record | sens | 15 | -0.005 | -0.036 | +0.017 | 5 |
| development | frozen | data (cf_krec - record) | f1 | 15 | -0.004 | -0.011 | +0.000 | 14 |
| development | frozen | data (cf_krec - record) | fa | 15 | +0.141 | -0.104 | +0.442 | 12 |
| development | frozen | data (cf_krec - record) | sens | 15 | -0.008 | -0.025 | +0.000 | 1 |
| development | frozen | k (cf - cf_krec) | f1 | 15 | +0.000 | +0.000 | +0.000 | 0 |
| development | frozen | k (cf - cf_krec) | fa | 15 | +0.000 | +0.000 | +0.000 | 0 |
| development | frozen | k (cf - cf_krec) | sens | 15 | +0.000 | +0.000 | +0.000 | 0 |
| development | frozen | new models (rerun - cf) | f1 | 15 | +0.002 | -0.010 | +0.015 | 15 |
| development | frozen | new models (rerun - cf) | fa | 15 | +0.081 | -0.708 | +1.018 | 15 |
| development | frozen | new models (rerun - cf) | sens | 15 | -0.003 | -0.022 | +0.018 | 5 |
| development | frozen | rerun - record | f1 | 15 | -0.003 | -0.015 | +0.012 | 15 |
| development | frozen | rerun - record | fa | 15 | +0.222 | -0.605 | +1.127 | 15 |
| development | frozen | rerun - record | sens | 15 | -0.011 | -0.043 | +0.016 | 5 |
| test | L2f | data (cf_krec - record) | f1 | 8 | -0.004 | -0.010 | +0.001 | 8 |
| test | L2f | data (cf_krec - record) | fa | 8 | +0.066 | -0.275 | +0.334 | 8 |
| test | L2f | data (cf_krec - record) | sens | 8 | -0.008 | -0.018 | +0.000 | 2 |
| test | L2f | k (cf - cf_krec) | f1 | 8 | +0.000 | +0.000 | +0.000 | 0 |
| test | L2f | k (cf - cf_krec) | fa | 8 | +0.000 | +0.000 | +0.000 | 0 |
| test | L2f | k (cf - cf_krec) | sens | 8 | +0.000 | +0.000 | +0.000 | 0 |
| test | L2f | new models (rerun - cf) | f1 | 8 | -0.012 | -0.020 | -0.005 | 8 |
| test | L2f | new models (rerun - cf) | fa | 8 | +3.462 | +2.241 | +4.882 | 8 |
| test | L2f | new models (rerun - cf) | sens | 8 | +0.015 | -0.008 | +0.036 | 6 |
| test | L2f | rerun - record | f1 | 8 | -0.016 | -0.027 | -0.006 | 8 |
| test | L2f | rerun - record | fa | 8 | +3.528 | +2.309 | +4.885 | 8 |
| test | L2f | rerun - record | sens | 8 | +0.008 | -0.016 | +0.031 | 6 |
| test | frozen | data (cf_krec - record) | f1 | 8 | -0.002 | -0.009 | +0.003 | 7 |
| test | frozen | data (cf_krec - record) | fa | 8 | +0.031 | -0.268 | +0.258 | 8 |
| test | frozen | data (cf_krec - record) | sens | 8 | -0.004 | -0.017 | +0.009 | 3 |
| test | frozen | k (cf - cf_krec) | f1 | 8 | +0.000 | +0.000 | +0.000 | 0 |
| test | frozen | k (cf - cf_krec) | fa | 8 | +0.000 | +0.000 | +0.000 | 0 |
| test | frozen | k (cf - cf_krec) | sens | 8 | +0.000 | +0.000 | +0.000 | 0 |
| test | frozen | new models (rerun - cf) | f1 | 8 | -0.014 | -0.025 | -0.004 | 7 |
| test | frozen | new models (rerun - cf) | fa | 8 | +1.908 | +1.295 | +2.468 | 8 |
| test | frozen | new models (rerun - cf) | sens | 8 | -0.019 | -0.053 | +0.005 | 3 |
| test | frozen | rerun - record | f1 | 8 | -0.016 | -0.026 | -0.006 | 7 |
| test | frozen | rerun - record | fa | 8 | +1.939 | +1.356 | +2.518 | 8 |
| test | frozen | rerun - record | sens | 8 | -0.023 | -0.048 | -0.001 | 5 |
| chb24 | L2f | data (cf_krec - record) | f1 | 1 | +0.012 | +0.012 | +0.012 | 1 |
| chb24 | L2f | data (cf_krec - record) | fa | 1 | -0.568 | -0.568 | -0.568 | 1 |
| chb24 | L2f | data (cf_krec - record) | sens | 1 | +0.016 | +0.016 | +0.016 | 1 |
| chb24 | L2f | k (cf - cf_krec) | f1 | 1 | +0.000 | +0.000 | +0.000 | 0 |
| chb24 | L2f | k (cf - cf_krec) | fa | 1 | +0.000 | +0.000 | +0.000 | 0 |
| chb24 | L2f | k (cf - cf_krec) | sens | 1 | +0.000 | +0.000 | +0.000 | 0 |
| chb24 | L2f | new models (rerun - cf) | f1 | 1 | -0.020 | -0.020 | -0.020 | 1 |
| chb24 | L2f | new models (rerun - cf) | fa | 1 | +4.541 | +4.541 | +4.541 | 1 |
| chb24 | L2f | new models (rerun - cf) | sens | 1 | +0.031 | +0.031 | +0.031 | 1 |
| chb24 | L2f | rerun - record | f1 | 1 | -0.008 | -0.008 | -0.008 | 1 |
| chb24 | L2f | rerun - record | fa | 1 | +3.973 | +3.973 | +3.973 | 1 |
| chb24 | L2f | rerun - record | sens | 1 | +0.047 | +0.047 | +0.047 | 1 |
| chb24 | frozen | k (cf - cf_krec) | f1 | 1 | +0.000 | +0.000 | +0.000 | 0 |
| chb24 | frozen | k (cf - cf_krec) | fa | 1 | +0.000 | +0.000 | +0.000 | 0 |
| chb24 | frozen | k (cf - cf_krec) | sens | 1 | +0.000 | +0.000 | +0.000 | 0 |
| chb24 | frozen | new models (rerun - cf) | f1 | 1 | +0.018 | +0.018 | +0.018 | 1 |
| chb24 | frozen | new models (rerun - cf) | fa | 1 | +0.000 | +0.000 | +0.000 | 0 |
| chb24 | frozen | new models (rerun - cf) | sens | 1 | +0.031 | +0.031 | +0.031 | 1 |
| siena | L2f | data (cf_krec - record) | f1 | 14 | +0.007 | -0.000 | +0.016 | 10 |
| siena | L2f | data (cf_krec - record) | fa | 14 | -0.417 | -0.996 | +0.071 | 10 |
| siena | L2f | data (cf_krec - record) | sens | 14 | +0.012 | +0.000 | +0.030 | 2 |
| siena | L2f | k (cf - cf_krec) | f1 | 14 | +0.000 | +0.000 | +0.000 | 0 |
| siena | L2f | k (cf - cf_krec) | fa | 14 | +0.000 | +0.000 | +0.000 | 0 |
| siena | L2f | k (cf - cf_krec) | sens | 14 | +0.000 | +0.000 | +0.000 | 0 |
| siena | L2f | new models (rerun - cf) | f1 | 14 | -0.007 | -0.021 | +0.008 | 13 |
| siena | L2f | new models (rerun - cf) | fa | 14 | +5.531 | +2.231 | +9.292 | 13 |
| siena | L2f | new models (rerun - cf) | sens | 14 | +0.054 | -0.012 | +0.140 | 6 |
| siena | L2f | rerun - record | f1 | 14 | -0.000 | -0.015 | +0.018 | 13 |
| siena | L2f | rerun - record | fa | 14 | +5.114 | +1.887 | +8.739 | 13 |
| siena | L2f | rerun - record | sens | 14 | +0.066 | -0.004 | +0.154 | 5 |
| siena | frozen | k (cf - cf_krec) | f1 | 14 | +0.000 | +0.000 | +0.000 | 0 |
| siena | frozen | k (cf - cf_krec) | fa | 14 | +0.000 | +0.000 | +0.000 | 0 |
| siena | frozen | k (cf - cf_krec) | sens | 14 | +0.000 | +0.000 | +0.000 | 0 |
| siena | frozen | new models (rerun - cf) | f1 | 14 | +0.022 | -0.019 | +0.071 | 11 |
| siena | frozen | new models (rerun - cf) | fa | 14 | +0.026 | -1.483 | +1.602 | 12 |
| siena | frozen | new models (rerun - cf) | sens | 14 | +0.046 | -0.032 | +0.143 | 8 |

All arms and stages: `summary.csv`, `bootstrap.csv`, `attribution.csv`; per row: `rows_vs_record.csv`; per subject: `per_subject.csv`; boundaries: `errors.csv`. Descriptive only (plan P2); no row replaces a locked number of the thesis.
