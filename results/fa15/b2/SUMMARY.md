# F-A1.5 data run b2 (fa15_asr f9a548e45cfed9a6; project verification, board R204)

| gate | status | summary |
|---|---|---|
| G-mod | PASS | closed modules from /tmp/Thesis/src; fa15_asr f9a548e45cfed9a6, v9_x6_asr 9cb96ecdc50b45e7 |
| mode | PASS | exact (versions vs R0's run_meta); asrpy 0.0.8 |
| R0.1-inventory | PASS | 159 files sha256 = PhysioNet (0 downloaded) |
| G-ref | PASS | 15 R0 reference files; 15 checked against the pin; missing []; differ [] |
| G-conv | PASS | 9 cases; worst relative difference 6.66e-04; beyond 0.01: [] |
| G-lab | PASS | labels / buffer / signal loss / file index / files = R0 in 9 of 9 cases |
| G-asr | FAIL | 13 V9-X6 files, 16 seizures; classes {'exact': 11, 'within_tol': 0, 'explained': 0, 'beyond': 2}; unexplained [('chb06', 'chb06_01.edf'), ('chb18', 'chb18_31.edf')]; max /diff/ at 60-s chunks 2.13e-01 |
| G-done | PASS | 9 of 9 cases written |
| G-worker-sha | PASS | 156 of 156 jobs ran fa15_asr f9a548e45cfed9a6; differ [] |
