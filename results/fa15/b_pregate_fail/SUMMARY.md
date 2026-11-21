# F-A1.5 data run b (fa15_asr 0f9843dcfa3162a7; project verification, board R204)

| gate | status | summary |
|---|---|---|
| G-mod | PASS | closed modules from /tmp/Thesis/src; fa15_asr 0f9843dcfa3162a7, v9_x6_asr 9cb96ecdc50b45e7 |
| mode | PASS | exact (versions vs R0's run_meta); asrpy 0.0.8 |
| R0.1-inventory | PASS | 363 files sha256 = PhysioNet (0 downloaded) |
| G-ref | PASS | 31 R0 reference files; 31 checked against the pin; missing []; differ [] |
| G-conv-pad | PASS | chb08: 30 s 0.0e+00, 3 s 1.6e-04; PN16: 30 s 9.0e-14, 3 s 4.1e-04 |
| G-asr-pre | FAIL | 1 file(s) with the record's chunking vs results/v9_x6: [('chb06_01.edf', 49, 'FAIL')] |
| G-done | FAIL | skipped: a pre-gate failed |
