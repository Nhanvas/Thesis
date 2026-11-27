# SzScan subjects scored outside the application (chat C5c, Step 2b)

Every AI event of every public subject of the application's database, before review, against the annotations (SzCORE event scoring, application-tier scorer of the thesis; `src/c5_score_app.py`). Private studies skipped: 2. Group values are per-patient means; they describe the demo database, not new thesis results (V5 stays the number source).

Gate S0 (test subjects, session mode = committed application-tier result `application_eval_v4`): **PASS** 

Gate S1 (reference seizures per file = F2-03's L3 rows): **PASS** 316 files compared 

| group | mode | subjects | hours | seizures | detected | sensitivity (mean) | F1 (mean) | FP/day (mean) |
|---|---|---|---|---|---|---|---|---|
| Siena | session | 14 | 141.0 | 47 | 33 | 0.748 | 0.280 | 40.7 |
| chb24 | file | 1 | 21.3 | 16 | 15 | 0.938 | 0.380 | 54.5 |
| chb24 | session | 1 | 21.3 | 16 | 14 | 0.875 | 0.509 | 28.4 |
| test | session | 8 | 279.4 | 76 | 33 | 0.528 | 0.175 | 26.9 |
| validation | session | 3 | 115.8 | 15 | 14 | 0.933 | 0.228 | 20.4 |

Sensitivity mean over subjects with at least one seizure; F1 'undefined' (no detection, no seizure) left out of the mean. A file the subject's annotation does not list counts as seizure-free (x1_external's convention, as F2-03's L3): 20 such file(s).

| subject | group | mode | files | hours | seizures | detected | false alarms | sensitivity | precision | F1 | FP/day | events crossing a file end |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PN00 | Siena | session | 5 | 3.24 | 5 | 5 | 1 | 1.000 | 0.833 | 0.909 | 7.6 | 0 |
| PN01 | Siena | session | 1 | 13.49 | 2 | 2 | 10 | 1.000 | 0.167 | 0.286 | 17.8 | 0 |
| PN03 | Siena | session | 2 | 24.23 | 2 | 2 | 53 | 1.000 | 0.036 | 0.070 | 52.7 | 0 |
| PN05 | Siena | session | 3 | 6.04 | 3 | 0 | 6 | 0.000 | 0.000 | undefined | 24.0 | 0 |
| PN06 | Siena | session | 5 | 12.07 | 5 | 3 | 38 | 0.600 | 0.073 | 0.130 | 76.0 | 0 |
| PN07 | Siena | session | 1 | 8.74 | 1 | 1 | 33 | 1.000 | 0.029 | 0.057 | 90.8 | 0 |
| PN09 | Siena | session | 3 | 6.85 | 3 | 1 | 6 | 0.333 | 0.143 | 0.200 | 21.2 | 0 |
| PN10 | Siena | session | 6 | 18.73 | 10 | 7 | 17 | 0.700 | 0.292 | 0.412 | 21.9 | 0 |
| PN11 | Siena | session | 1 | 2.41 | 1 | 1 | 3 | 1.000 | 0.250 | 0.400 | 30.1 | 0 |
| PN12 | Siena | session | 3 | 6.10 | 4 | 3 | 8 | 0.750 | 0.273 | 0.400 | 31.9 | 0 |
| PN13 | Siena | session | 3 | 8.66 | 3 | 1 | 10 | 0.333 | 0.091 | 0.143 | 27.9 | 0 |
| PN14 | Siena | session | 4 | 20.46 | 4 | 3 | 43 | 0.750 | 0.065 | 0.120 | 50.5 | 0 |
| PN16 | Siena | session | 2 | 4.88 | 2 | 2 | 15 | 1.000 | 0.118 | 0.211 | 74.8 | 0 |
| PN17 | Siena | session | 2 | 5.12 | 2 | 2 | 9 | 1.000 | 0.182 | 0.308 | 42.5 | 0 |
| chb03 | test | session | 38 | 38.00 | 7 | 6 | 20 | 0.857 | 0.231 | 0.364 | 12.7 | 0 |
| chb06 | test | session | 18 | 66.73 | 10 | 1 | 97 | 0.100 | 0.010 | 0.019 | 34.9 | 0 |
| chb10 | validation | session | 25 | 50.02 | 7 | 7 | 30 | 1.000 | 0.189 | 0.318 | 14.4 | 0 |
| chb11 | validation | session | 35 | 34.79 | 5 | 4 | 27 | 0.800 | 0.129 | 0.222 | 18.7 | 0 |
| chb13 | test | session | 33 | 33.00 | 12 | 1 | 41 | 0.083 | 0.024 | 0.037 | 30.0 | 0 |
| chb14 | test | session | 26 | 26.00 | 8 | 6 | 33 | 0.750 | 0.154 | 0.255 | 30.5 | 0 |
| chb15 | test | session | 40 | 40.01 | 20 | 10 | 59 | 0.500 | 0.145 | 0.225 | 35.9 | 0 |
| chb16 | test | session | 19 | 19.00 | 10 | 1 | 16 | 0.100 | 0.059 | 0.074 | 20.2 | 0 |
| chb17 | test | session | 21 | 21.01 | 3 | 3 | 27 | 1.000 | 0.100 | 0.182 | 31.0 | 0 |
| chb18 | test | session | 36 | 35.63 | 6 | 5 | 30 | 0.833 | 0.143 | 0.244 | 20.3 | 0 |
| chb22 | validation | session | 31 | 31.00 | 3 | 3 | 36 | 1.000 | 0.077 | 0.143 | 27.9 | 0 |
| chb24 | chb24 | session | 22 | 21.30 | 16 | 14 | 25 | 0.875 | 0.359 | 0.509 | 28.4 | 0 |
| chb24-file | chb24 | file | 22 | 21.30 | 16 | 15 | 48 | 0.938 | 0.238 | 0.380 | 54.5 | 0 |
