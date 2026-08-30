# Report metrics — BASELINE v3.1 (equal-weight, canonical seed 42)

## Window-level (per-subject + macro)
| subject | n_inter | n_ictal | prevalence | AUROC | AUPRC |
|---|---|---|---|---|---|
| chb03 | 17204 | 106 | 0.0061 | 0.954 | 0.1715 |
| chb06 | 19826 | 45 | 0.0023 | 0.4371 | 0.0036 |
| chb13 | 12452 | 144 | 0.0114 | 0.8047 | 0.0375 |
| chb14 | 13983 | 49 | 0.0035 | 0.6257 | 0.0206 |
| chb15 | 17026 | 515 | 0.0294 | 0.8261 | 0.2179 |
| chb16 | 6428 | 28 | 0.0043 | 0.8707 | 0.104 |
| chb17 | 9304 | 74 | 0.0079 | 0.7467 | 0.0164 |
| chb18 | 14853 | 83 | 0.0056 | 0.9384 | 0.2014 |
| **MACRO** | | | | **0.7754** | **0.0966** |

_AUPRC baseline = prevalence (cot prevalence); AUPRC that vi su kien hiem, doc kem prevalence._

## Event-level (pooled, 8 sub / 76 con)
| operating point | mag/pen | Sensitivity (CI) | Precision (CI) | F1 | FP/day (CI) | TP/FN/FP |
|---|---|---|---|---|---|---|
| balanced - shared (held-out) | mag70/pen0.5 | 0.6316 [0.519, 0.731] | 0.097 [0.074, 0.126] | 0.1681 | 38.56 [35.07, 42.31] | 48/28/447 |
| balanced - calibrated (per-subject FP-budget) | per-subject | 0.6053 [0.493, 0.708] | 0.0924 [0.070, 0.121] | 0.1603 | 38.99 [35.48, 42.76] | 46/30/452 |
| high-sensitivity - shared (held-out) | mag55/pen0.3 | 0.7763 [0.671, 0.855] | 0.0654 [0.051, 0.083] | 0.1207 | 72.72 [67.89, 77.80] | 59/17/843 |
| high-sensitivity - calibrated (per-subject FP-budget) | per-subject | 0.7763 [0.671, 0.855] | 0.0654 [0.051, 0.083] | 0.1207 | 72.72 [67.89, 77.80] | 59/17/843 |

## Event-level (per-subject, tai 2 OP locked)
| operating point | subject | Sens | Prec | F1 | FP/day | TP/FN/FP |
|---|---|---|---|---|---|---|
| balanced | chb03 | 1.0 | 0.1167 | 0.209 | 33.58 | 7/0/53 |
| balanced | chb06 | 0.1 | 0.0139 | 0.0244 | 25.55 | 1/9/71 |
| balanced | chb13 | 0.8333 | 0.1923 | 0.3125 | 30.69 | 10/2/42 |
| balanced | chb14 | 0.25 | 0.0208 | 0.0385 | 86.94 | 2/6/94 |
| balanced | chb15 | 0.9 | 0.225 | 0.36 | 37.73 | 18/2/62 |
| balanced | chb16 | 0.3 | 0.0968 | 0.1463 | 35.42 | 3/7/28 |
| balanced | chb17 | 0.6667 | 0.0645 | 0.1176 | 33.27 | 2/1/29 |
| balanced | chb18 | 0.8333 | 0.0685 | 0.1266 | 45.92 | 5/1/68 |
| high-sensitivity | chb03 | 1.0 | 0.0603 | 0.1138 | 69.06 | 7/0/109 |
| high-sensitivity | chb06 | 0.3 | 0.0199 | 0.0373 | 53.27 | 3/7/148 |
| high-sensitivity | chb13 | 0.8333 | 0.1099 | 0.1942 | 59.2 | 10/2/81 |
| high-sensitivity | chb14 | 0.375 | 0.0203 | 0.0385 | 134.1 | 3/5/145 |
| high-sensitivity | chb15 | 0.95 | 0.131 | 0.2303 | 76.67 | 19/1/126 |
| high-sensitivity | chb16 | 0.9 | 0.1552 | 0.2647 | 61.99 | 9/1/49 |
| high-sensitivity | chb17 | 1.0 | 0.0469 | 0.0896 | 69.98 | 3/0/61 |
| high-sensitivity | chb18 | 0.8333 | 0.0388 | 0.0741 | 83.74 | 5/1/124 |