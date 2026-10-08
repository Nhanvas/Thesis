# Seizure visibility with and without high-amplitude windows in the reference

e = share of reference windows whose smoothed score is >= the seizure's peak (smaller = more visible).

| set | subject | seizures | median e_all | median e_clean | e_all <= 5% | e_clean <= 5% | e_all <= 2% | e_clean <= 2% |
|---|---|---|---|---|---|---|---|---|
| test | chb03 | 7 | 0.045 | 0.005 | 4 | 7 | 0 | 6 |
| test | chb06 | 10 | 0.507 | 0.416 | 0 | 0 | 0 | 0 |
| test | chb13 | 12 | 0.367 | 0.118 | 0 | 4 | 0 | 1 |
| test | chb14 | 8 | 0.148 | 0.097 | 3 | 3 | 1 | 3 |
| test | chb15 | 20 | 0.127 | 0.023 | 1 | 15 | 0 | 9 |
| test | chb16 | 10 | 0.410 | 0.235 | 0 | 0 | 0 | 0 |
| test | chb17 | 3 | 0.164 | 0.048 | 0 | 2 | 0 | 0 |
| test | chb18 | 6 | 0.068 | 0.008 | 2 | 5 | 0 | 5 |
| val | chb10 | 7 | 0.044 | 0.008 | 4 | 6 | 1 | 4 |
| val | chb11 | 3 | 0.049 | 0.007 | 2 | 3 | 1 | 2 |
| val | chb22 | 3 | 0.008 | 0.001 | 3 | 3 | 2 | 3 |
| test | ALL | 76 | 0.200 | 0.061 | 10 | 36 | 1 | 24 |
| val | ALL | 13 | 0.040 | 0.007 | 9 | 12 | 4 | 9 |

Counts of seizures are over contiguous ictal runs, which can differ slightly from the annotated seizure count where a seizure crosses a file boundary. Descriptive only.