# F-A1.5 data run a (fa15_asr 0f9843dcfa3162a7; project verification, board R204)

| gate | status | summary |
|---|---|---|
| G-mod | PASS | closed modules from /tmp/Thesis/src; fa15_asr 0f9843dcfa3162a7, v9_x6_asr 9cb96ecdc50b45e7 |
| mode | PASS | exact (versions vs R0's run_meta); asrpy 0.0.8 |
| R0.1-inventory | PASS | 402 files sha256 = PhysioNet (1 downloaded) |
| G-ref | PASS | 30 R0 reference files; 30 checked against the pin; missing []; differ [] |
| G-conv-pad | PASS | chb16: 30 s 0.0e+00, 3 s 1.5e-04; PN00: 30 s 3.4e-14, 3 s 1.3e-03 |
| G-conv | PASS | 19 cases; worst relative difference 1.32e-03; beyond 0.01: [] |
| G-lab | PASS | labels / buffer / signal loss / file index / files = R0 in 19 of 19 cases |
| G-asr | FAIL | 57 V9-X6 files, 76 seizures; classes {'exact': 48, 'within_tol': 0, 'explained': 0, 'beyond': 9}; unexplained [('chb03', 'chb03_01.edf'), ('chb03', 'chb03_02.edf'), ('chb15', 'chb15_10.edf'), ('chb15', 'chb15_20.edf'), ('chb15', 'chb15_62.edf'), ('chb16', 'chb16_11.edf'), ('chb16', 'chb16_16.edf'), ('chb16', 'chb16_18.edf'), ('chb24', 'chb24_14.edf')]; max /diff/ at 60-s chunks 3.42e-01 |
| G-done | PASS | 19 of 19 cases written |
| G-worker-sha | PASS | 402 of 402 jobs ran fa15_asr 0f9843dcfa3162a7; differ [] |
