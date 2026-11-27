# SzScan verification after Step 2 (gate G9, chat C5c)

Code `src/c5_verify2.py` (helpers of the Step 1 record module `src/c5_szscan_verify.py`); commit `a896f4b94d1cf798f3f8ee0052093e1bb9e2dfc4` (uncommitted changes in web_demo/ or src/: no); 407 files, 578.8 h of EEG, subjects PN00, PN01, PN03, PN05, PN06, PN07, PN09, PN10, PN11, PN12, PN13, PN14, PN16, PN17, chb03, chb06, chb10, chb11, chb13, chb14, chb15, chb16, chb17, chb18, chb22, chb24, chb24-file; run 7630 s; peak private memory per file 1882 MB. Read only. Private studies: 2 recording(s) checked, report in the private inbox.

| check | result | detail |
|---|---|---|
| V1 source (sha256; cache = independent reader) | PASS | 407 / 407 files; largest difference 4.66e-04 µV (tolerance 0.001) |
| V2 channels (18 names, order, derivation) | PASS | 407 / 407 files; app list = thesis list True |
| V3 µV on screen (endpoint function, whole file) | PASS | raw 0.006, filtered 0.006 µV (tolerance 0.006) |
| V4 time and events | PASS | 407 / 407 files; UI formatter 1221 cases, all equal |
| V5 filter at the study's mains | PASS | largest difference 4.65e-04 µV; UI label template True; API carries the study's mains True |
| V6 events = committed export (test subjects, session) | PASS | 231 equal, 0 differ, 176 without a committed reference |

## By subject

| subject | mode | mains | montage | input Hz | files | hours | V1 | V2 | V3 | V4 | V5 | V6 | AI events | peak MB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PN00 | session | 50 | referential | 512 | 5 | 3.2 | 5 | 5 | 5 | 5 | 5 | — | 6 | 1025 |
| PN01 | session | 50 | referential | 512 | 1 | 13.5 | 1 | 1 | 1 | 1 | 1 | — | 12 | 1882 |
| PN03 | session | 50 | referential | 512 | 2 | 24.2 | 2 | 2 | 2 | 2 | 2 | — | 53 | 1846 |
| PN05 | session | 50 | referential | 512 | 3 | 6.0 | 3 | 3 | 3 | 3 | 3 | — | 6 | 1134 |
| PN06 | session | 50 | referential | 512 | 5 | 12.1 | 5 | 5 | 5 | 5 | 5 | — | 41 | 1197 |
| PN07 | session | 50 | referential | 512 | 1 | 8.7 | 1 | 1 | 1 | 1 | 1 | — | 32 | 1556 |
| PN09 | session | 50 | referential | 512 | 3 | 6.8 | 3 | 3 | 3 | 3 | 3 | — | 7 | 1119 |
| PN10 | session | 50 | referential | 512 | 6 | 18.7 | 6 | 6 | 6 | 6 | 6 | — | 24 | 1273 |
| PN11 | session | 50 | referential | 512 | 1 | 2.4 | 1 | 1 | 1 | 1 | 1 | — | 4 | 1124 |
| PN12 | session | 50 | referential | 512 | 3 | 6.1 | 3 | 3 | 3 | 3 | 3 | — | 10 | 1153 |
| PN13 | session | 50 | referential | 512 | 3 | 8.7 | 3 | 3 | 3 | 3 | 3 | — | 10 | 1196 |
| PN14 | session | 50 | referential | 512 | 4 | 20.5 | 4 | 4 | 4 | 4 | 4 | — | 45 | 1758 |
| PN16 | session | 50 | referential | 512 | 2 | 4.9 | 2 | 2 | 2 | 2 | 2 | — | 17 | 1135 |
| PN17 | session | 50 | referential | 512 | 2 | 5.1 | 2 | 2 | 2 | 2 | 2 | — | 11 | 1135 |
| chb03 | session | 60 | bipolar | 256 | 38 | 38.0 | 38 | 38 | 38 | 38 | 38 | 38 | 26 | 1031 |
| chb06 | session | 60 | bipolar | 256 | 18 | 66.7 | 18 | 18 | 18 | 18 | 18 | 18 | 97 | 1144 |
| chb10 | session | 60 | bipolar | 256 | 25 | 50.0 | 25 | 25 | 25 | 25 | 25 | — | 37 | 1054 |
| chb11 | session | 60 | bipolar | 256 | 35 | 34.8 | 35 | 35 | 35 | 35 | 35 | — | 31 | 1030 |
| chb13 | session | 60 | bipolar | 256 | 33 | 33.0 | 33 | 33 | 33 | 33 | 33 | 33 | 42 | 1030 |
| chb14 | session | 60 | bipolar | 256 | 26 | 26.0 | 26 | 26 | 26 | 26 | 26 | 26 | 39 | 1031 |
| chb15 | session | 60 | bipolar | 256 | 40 | 40.0 | 40 | 40 | 40 | 40 | 40 | 40 | 65 | 1034 |
| chb16 | session | 60 | bipolar | 256 | 19 | 19.0 | 19 | 19 | 19 | 19 | 19 | 19 | 16 | 1031 |
| chb17 | session | 60 | bipolar | 256 | 21 | 21.0 | 21 | 21 | 21 | 21 | 21 | 21 | 30 | 1031 |
| chb18 | session | 60 | bipolar | 256 | 36 | 35.6 | 36 | 36 | 36 | 36 | 36 | 36 | 35 | 1031 |
| chb22 | session | 60 | bipolar | 256 | 31 | 31.0 | 31 | 31 | 31 | 31 | 31 | — | 39 | 1032 |
| chb24 | session | 60 | bipolar | 256 | 22 | 21.3 | 22 | 22 | 22 | 22 | 22 | — | 39 | 1032 |
| chb24-file | file | 60 | bipolar | 256 | 22 | 21.3 | 22 | 22 | 22 | 22 | 22 | — | 63 | 1032 |

Not covered: the resampler for inputs not at 256 Hz is scipy's resample_poly, the same function as the app (not independent); derivations with an interpolated electrode are not compared (test E10); upload paths (Step 1 V7) are covered by the synthetic test E7 and the backend tests, not re-run here; file-mode events against the per-recording protocol = gate G2.

Per file: `per_file.csv`; per channel: `channels.csv`; gates: `gates.json`.
