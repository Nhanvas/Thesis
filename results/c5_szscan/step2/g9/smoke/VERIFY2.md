# SzScan verification after Step 2 (gate G9, chat C5c) — SMOKE

Code `src/c5_verify2.py` (helpers of the Step 1 record module `src/c5_szscan_verify.py`); commit `76665ce67d2ff4206983b46f74cdb422ed7c88b6` (uncommitted changes in web_demo/ or src/: no); 1 files, 13.5 h of EEG, subjects PN01; run 302 s; peak private memory per file 1882 MB. Read only. Private studies: not checked in this run.

| check | result | detail |
|---|---|---|
| V1 source (sha256; cache = independent reader) | PASS | 1 / 1 files; largest difference 1.16e-04 µV (tolerance 0.001) |
| V2 channels (18 names, order, derivation) | PASS | 1 / 1 files; app list = thesis list True |
| V3 µV on screen (endpoint function, whole file) | PASS | raw 0.005, filtered 0.005 µV (tolerance 0.006) |
| V4 time and events | PASS | 1 / 1 files; UI formatter 3 cases, all equal |
| V5 filter at the study's mains | PASS | largest difference 5.81e-05 µV; UI label template True; API carries the study's mains True |
| V6 events = committed export (test subjects, session) | not run | 0 equal, 0 differ, 1 without a committed reference |

## By subject

| subject | mode | mains | montage | input Hz | files | hours | V1 | V2 | V3 | V4 | V5 | V6 | AI events | peak MB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PN01 | session | 50 | referential | 512 | 1 | 13.5 | 1 | 1 | 1 | 1 | 1 | — | 12 | 1882 |

Not covered: the resampler for inputs not at 256 Hz is scipy's resample_poly, the same function as the app (not independent); derivations with an interpolated electrode are not compared (test E10); upload paths (Step 1 V7) are covered by the synthetic test E7 and the backend tests, not re-run here; file-mode events against the per-recording protocol = gate G2.

Per file: `per_file.csv`; per channel: `channels.csv`; gates: `gates.json`.
