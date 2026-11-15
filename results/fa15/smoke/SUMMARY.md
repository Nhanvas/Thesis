# F-A1.5 data run smoke (fa15_asr 132d6179a1c77723; project verification, board R204)

| gate | status | summary |
|---|---|---|
| G-mod | PASS | closed modules from /tmp/Thesis/src; fa15_asr 132d6179a1c77723, v9_x6_asr 9cb96ecdc50b45e7 |
| mode | PASS | exact (versions vs R0's run_meta); asrpy 0.0.8 |
| R0.1-inventory | PASS | 70 files sha256 = PhysioNet (0 downloaded) |
| G-ref | PASS | 3 R0 reference files; 3 checked against the pin; missing []; differ [] |
| G-ref | PASS | 2 R0 reference files; 2 checked against the pin; missing []; differ [] |
| G-ref | PASS | 1 R0 reference files; 1 checked against the pin; missing []; differ [] |
| G-conv | FAIL | 2 cases; worst relative difference 1.32e-03; beyond 0.001: ['PN00'] |
| G-lab | PASS | labels / buffer / signal loss / file index / files = R0 in 2 of 2 cases |
| G-asr | FAIL | 5 V9-X6 files, 8 seizures; max /diff/ {'share_seizure': 3.999586459602078e-05, 'share_preictal60': 0.0038673787443492813, 'contrast_before': 4.618527782440651e-14, 'contrast_after': 0.001050765908599094, 'highamp_share': 2.1328567972767054e-05, 'background_share_sorted': 8.448797217397441e-14}; windows in one set only 0 |
| G-done | PASS | 2 of 2 cases written |
| G-ident | PASS | mode off -> R0 .npz bit for bit: [('chb17', 'PASS'), ('PN00', 'PASS')] |
