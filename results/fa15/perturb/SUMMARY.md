# F-A1.5 T2 -- ASR sensitivity to a relative input perturbation of 9.095e-13 (fa15_asr f9a548e45cfed9a6)

Machine: {'cpu_model': 'Intel(R) Xeon(R) CPU @ 2.20GHz', 'avx512f': False, 'blas': 'scipy-openblas 0.3.27'}. Files: 70 of 70. ASR wall time P0 0.67 h, P1 0.68 h.

| gate | status | summary |
|---|---|---|
| G-mod | PASS | closed modules from /tmp/Thesis/src; fa15_asr f9a548e45cfed9a6 |
| mode | PASS | exact (versions vs R0's run_meta); asrpy 0.0.8 |
| R0.1-inventory | PASS | 262 files sha256 = PhysioNet |
| G-ref | PASS | 17 R0 reference files; 17 checked against the pin; missing []; differ [] |
| G-done | PASS | 70 of 70 files, both arms |
| G-worker-sha | PASS | 140 of 140 subprocesses ran fa15_asr f9a548e45cfed9a6 |

## Differs from the V9-X6 record (rows) x moves under the perturbation (columns), files

```
moves_under_perturbation  False  True 
differs_from_record                   
False                        57      2
True                          1     10
```

Kaggle P0 vs the data run's committed Measure 1 (same code, another session): 58 files compared, 0 differ beyond 1e-9.

## Files that move under the perturbation

```
subject         file  max_pert  max_vs_record  max_vs_prior  power_removed_p0
  chb03 chb03_01.edf  0.051805   2.833624e-03           0.0          0.903929
  chb03 chb03_02.edf  0.013973   7.320498e-02           0.0          0.891370
  chb15 chb15_10.edf  0.026326   2.632578e-02           0.0          0.087946
  chb15 chb15_20.edf  0.129252   1.292524e-01           0.0          0.788148
  chb15 chb15_62.edf  0.342192   3.421922e-01           0.0          0.235234
  chb16 chb16_11.edf  0.006250   2.019444e-03           0.0          0.835229
  chb16 chb16_16.edf  0.071373   7.137295e-02           0.0          0.724458
  chb16 chb16_18.edf  0.040700   1.683027e-02           0.0          0.648901
  chb18 chb18_31.edf  0.199646   2.132749e-01           NaN          0.854086
  chb18 chb18_32.edf  0.020627   6.239453e-14           NaN          0.953319
  chb24 chb24_13.edf  0.069874   2.056133e-13           0.0          0.370328
  chb24 chb24_14.edf  0.143299   1.432986e-01           0.0          0.396716
```
