# SzScan verification (chat C5, Step 1)

Code `src/c5_szscan_verify.py`; repository commit `2a06a7772d22c8106cf7021a20e8dcf6e6ad36f0` (uncommitted changes in web_demo/ or src/: no); run time 4283 s; subjects chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18; files 231; 279.39 h of EEG. Read only on the application's database and upload cache. Every check covers every file, every one of the 18 channels and the whole recording of every subject in the database.

| check | result | detail |
|---|---|---|
| V1 source (sha256, cached signal = independent EDF reader) | PASS | 231 / 231 files; largest difference 2.33e-04 µV (tolerance 0.001 µV) |
| V2 channels (18 names, order, label match) | PASS | app list = thesis list: True; 231 / 231 files |
| V3 amplitude in µV (endpoint function, whole file) | PASS | largest bucket difference raw 0.005 µV, filtered 0.005 µV (tolerance 0.006 µV); static checks 5 / 5 |
| V4 time (start, duration, events, UI formatter) | PASS | 231 / 231 files; UI formatter 693 cases, all equal |
| V5 filter (data + label) | PASS | largest difference 2.30e-04 µV; UI label '0.5-60 Hz + 60 Hz notch'; code notch 60.0 Hz |
| V6 events = committed application-tier export | PASS | 231 files equal, 0 differ, 0 without a committed reference |
| V7 upload paths | see table | 10 cases; not as expected: none |

## Facts recorded (not pass / fail)

- Labels present more than once in the EDF (the app uses the first): ['T8-P8'] in 204 files; largest difference between the copies 1657.631 µV.
- Dropped tail (shorter than one 4-s window): up to 3 s per file.
- Events in the database: 350 AI (9 already reviewed), 3 human.
- Frequency response of band-pass x notch, zero-phase (dB): {0.25: -48.55, 0.5: -6.02, 1.0: -0.03, 45.0: -0.4, 50.0: -1.13, 59.0: -11.2, 60.0: -591.31, 61.0: -12.96, 70.0: -18.48}.
- The amplitude control sets µV per half channel row (`EegPanel.jsx`: pxPerUv = (rowHeight/2 − 3) / amplitude), not µV/mm as on clinical viewers (information).

## V7 — upload paths (temporary database and upload folder)

| case | what | expected (written before the run) | observed | as expected |
|---|---|---|---|---|
| U1 | start a session with project id chb01 (the defense case) | rejected: 422 'This demo is restricted to the held-out test subjects.' | 422 This demo is restricted to the held-out test subjects. | yes |
| U2 | project id chb03, upload chb01_01.edf (no seizure) | accepted (Phase A ok): the app does not check that a file belongs to the subject | 200; uploaded | yes |
| U3 | same session, upload chb01_03.edf (with a seizure) | accepted (Phase A ok) | 200; uploaded | yes |
| U4 | Phase B of that session (two chb01 files under chb03) | runs (GAE + distances); nothing written to the real database | phase_b_done=True error=None after 86 s | yes |
| U5 | upload a file named .txt | rejected: 422 'File rejected — unsupported format or channel configuration.' | 422 File rejected — unsupported format or channel configuration. | yes |
| U6 | referential EDF, 19 electrodes named 'EEG Fp1-REF' …, 256 Hz | file error 'File rejected — unsupported format or channel configuration.' | error: File rejected — unsupported format or channel configuration. | yes |
| U7 | bipolar EDF with the 18 names at 512 Hz | file error 'File rejected …' | error: File rejected — unsupported format or channel configuration. | yes |
| U9 | garbage bytes named .edf | file error 'File rejected …' | error: File rejected — unsupported format or channel configuration. | yes |
| U8 | chb01_01.edf truncated to half its data, header unchanged | not specified in advance: observed behaviour reported | uploaded; header says 3600 s, file holds 1800 s, app windows 450, app duration 1800 s |  |
| U10 | memory: bytes held by the upload handler; tracemalloc peak of Phase A on chb01_01 | measured | upload handler holds the whole file in memory (main.py `await file.read()`): 42.4 MB for 1.00 h x 23 signals; Phase A traced peak 797 MB (797 MB per hour of EEG, 18 channels) |  |

Per-file values: `per_file.csv`; per channel: `channels.csv`; gates: `gates.json`.
