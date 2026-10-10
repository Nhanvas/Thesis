# T1 -- demo rebuilt on the final system: identity gate on chb03 (seed 42, balanced point)

Frozen code integrity:
- src/p2_scalars.py: unchanged since p3-frozen
- src/e16_recording_baseline.py: unchanged since p3-frozen
- src/e17b_latent_family.py: unchanged since p3-frozen
- src/e18_cpd_localizer.py: unchanged since p3-frozen
- src/e22_test_oneshot.py: unchanged since p3-frozen
- src/p3_levers.py: unchanged since p3-frozen
- src/p3c_freeze.py: unchanged since p3-frozen
- src/e23_test_look7.py: unchanged since p3-frozen
- src/c1b_build_trainset.py: unchanged since p3-frozen
- src/p2_dump_seeds23.py: unchanged since p3-frozen
- src/retrain/train_gae_v2.py: unchanged since p3-frozen
- src/x1_external.py: unchanged since x1-prereg-v2
- results/p3c_freeze/freeze.json: unchanged since p3-frozen

## Gate (thesis statistics)

```
detector   demo tp/fp 7/23  look #7 7/23
localized  demo tp/fp 7/22  look #7 7/22
alarm budget top 0.005175 (look #7 0.005175), q 0.005175
windows per file equal True, signal-loss flags equal True
per-channel distance max relative diff 1.34e-06 (share > 1e-4: 0.0000)
ensemble score max |diff| 7.31e-06
```

**GATE PASS**

## Label-free statistics (what the demo runs)

```
detector   tp/fp 6/21
localized  tp/fp 6/20   (n_ref 7)
alarm budget top 0.005175, q 0.005175
z-score std relative diff per channel vs thesis statistics: [0.0225, 0.0224, 0.0985, 0.0108, 0.0304, 0.0042, -0.0123, -0.0236, 0.0261, 0.0272, 0.0327, 0.0039, 0.0306, 0.0414, 0.0764, 0.0308, -0.0011, 0.0732]
z-score mean max |diff| 0.030 uV
per-channel distance max relative diff 1.00e+01
ensemble score max |diff| 5.86e-01
```

Elapsed 669 s (demo run with thesis statistics: 413.1 s for 38.001 h).