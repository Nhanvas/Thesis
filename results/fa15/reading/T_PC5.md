# PC5 / F-A1.5 — ASR in the preprocessing vs the control (reading; fa15_aggregate.py)

Per-patient means after the change point localizer; mean ± SD over seeds; ASR − control with a two-level bootstrap (patients as units, seeds within each arm; B = 10,000). Descriptive: no threshold (plan P2). Control seeds [42, 1, 2, 3, 4, 5, 6, 7], ASR seeds [42, 1, 2, 3, 4, 5, 6, 7].

| set | evaluation | metric | control | ASR | ASR − control [95 % CI] | patients | bootstrap |
|---|---|---|---|---|---|---|---|
| development | held-out | sens | 0.792 ± 0.028 | 0.694 ± 0.032 | -0.098 [-0.173, -0.023] | 15 | patients x seeds |
| development | held-out | f1 | 0.249 ± 0.017 | 0.174 ± 0.013 | -0.075 [-0.106, -0.043] | 15 | patients x seeds |
| development | held-out | fa | 19.2 ± 0.6 | 28.3 ± 1.1 | 9.1 [5.5, 13.1] | 15 | patients x seeds |
| development | held-out | prec | 0.175 ± 0.009 | 0.126 ± 0.010 | -0.050 [-0.070, -0.029] | 15 | patients x seeds |
| development | final | sens | 0.819 ± 0.016 | 0.727 ± 0.022 | -0.092 [-0.164, -0.017] | 15 | patients x seeds |
| development | final | f1 | 0.225 ± 0.011 | 0.133 ± 0.006 | -0.091 [-0.156, -0.044] | 15 | patients x seeds |
| development | final | fa | 23.2 ± 1.2 | 34.3 ± 1.3 | 11.1 [6.5, 15.8] | 15 | patients x seeds |
| development | final | prec | 0.146 ± 0.010 | 0.079 ± 0.004 | -0.067 [-0.126, -0.027] | 15 | patients x seeds |
| test | held-out | sens | 0.472 ± 0.025 | 0.368 ± 0.031 | -0.104 [-0.286, 0.074] | 8 | patients x seeds |
| test | held-out | f1 | 0.147 ± 0.012 | 0.117 ± 0.015 | -0.031 [-0.113, 0.068] | 8 | patients x seeds |
| test | held-out | fa | 25.3 ± 1.0 | 34.1 ± 1.2 | 8.8 [4.6, 13.2] | 8 | patients x seeds |
| test | held-out | prec | 0.091 ± 0.008 | 0.077 ± 0.010 | -0.014 [-0.073, 0.066] | 8 | patients x seeds |
| test | final | sens | 0.548 ± 0.025 | 0.428 ± 0.035 | -0.120 [-0.287, 0.026] | 8 | patients x seeds |
| test | final | f1 | 0.168 ± 0.009 | 0.108 ± 0.011 | -0.060 [-0.109, -0.017] | 8 | patients x seeds |
| test | final | fa | 30.3 ± 1.5 | 42.0 ± 2.3 | 11.7 [5.5, 17.7] | 8 | patients x seeds |
| test | final | prec | 0.103 ± 0.006 | 0.063 ± 0.007 | -0.040 [-0.073, -0.012] | 8 | patients x seeds |
| chb24 | held-out | sens | 0.648 ± 0.088 | 0.531 ± 0.067 | -0.117 [-0.188, -0.047] | 1 | seeds only (one patient) |
| chb24 | held-out | f1 | 0.529 ± 0.054 | 0.434 ± 0.061 | -0.095 [-0.148, -0.043] | 1 | seeds only (one patient) |
| chb24 | held-out | fa | 14.5 ± 0.8 | 16.7 ± 2.4 | 2.3 [0.7, 3.8] | 1 | seeds only (one patient) |
| chb24 | held-out | prec | 0.447 ± 0.036 | 0.368 ± 0.057 | -0.079 [-0.124, -0.037] | 1 | seeds only (one patient) |
| chb24 | final | sens | 0.844 ± 0.058 | 0.734 ± 0.073 | -0.109 [-0.172, -0.055] | 1 | seeds only (one patient) |
| chb24 | final | f1 | 0.502 ± 0.036 | 0.347 ± 0.022 | -0.156 [-0.185, -0.131] | 1 | seeds only (one patient) |
| chb24 | final | fa | 27.8 ± 5.6 | 45.4 ± 4.3 | 17.6 [12.8, 22.1] | 1 | seeds only (one patient) |
| chb24 | final | prec | 0.360 ± 0.041 | 0.227 ± 0.015 | -0.132 [-0.163, -0.107] | 1 | seeds only (one patient) |
| siena | held-out | sens | 0.468 ± 0.035 | 0.437 ± 0.065 | -0.032 [-0.195, 0.140] | 14 | patients x seeds |
| siena | held-out | f1 | 0.257 ± 0.020 | 0.192 ± 0.018 | -0.065 [-0.133, -0.009] | 14 | patients x seeds |
| siena | held-out | fa | 20.2 ± 1.0 | 30.0 ± 1.4 | 9.8 [4.4, 15.7] | 14 | patients x seeds |
| siena | held-out | prec | 0.217 ± 0.012 | 0.176 ± 0.020 | -0.041 [-0.104, 0.016] | 14 | patients x seeds |
| siena | final | sens | 0.671 ± 0.068 | 0.596 ± 0.070 | -0.075 [-0.226, 0.057] | 14 | patients x seeds |
| siena | final | f1 | 0.228 ± 0.019 | 0.171 ± 0.010 | -0.056 [-0.111, -0.011] | 14 | patients x seeds |
| siena | final | fa | 42.5 ± 2.5 | 53.2 ± 3.4 | 10.7 [0.7, 21.2] | 14 | patients x seeds |
| siena | final | prec | 0.164 ± 0.011 | 0.115 ± 0.008 | -0.049 [-0.083, -0.020] | 14 | patients x seeds |

Training data (clean windows of the 12 training patients): fa15_asr_a: ASR 219055 vs R0 270758; fa15_asr_b: ASR 219055 vs R0 270758

Gates: A0 PASS, A1 PASS, A2 PASS.

Files: t1.csv (this table), t2_seeds.csv, t3_patients.csv, t4_boundaries.csv, t5_data.csv.
