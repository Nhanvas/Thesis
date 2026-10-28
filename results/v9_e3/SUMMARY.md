# V9-E3 -- short-seizure branch (multi-scale score)

Full tables: `results/v9_e3/*.csv`, `results/v9_e3/paired/*.csv`. Code: `src/v9_e3_short.py` (new; reuses src/v9_e1_baselines.py, src/v9_e1b_calibrate.py, src/p3_levers.py, src/p2_scalars.py, src/e18_cpd_localizer.py and (for the veto fast path) src/v9_e2_veto.py, all read-only).

S1 = max(pct(smoothed(x,5)), pct(smoothed(x,2))) per window, x = the frozen ensemble score before any smoothing (v9_e1_baselines.final_scalar_from_D for G, v9_e1b_calibrate.f_signals for F); fed into the SAME budget (k_G/k_F reused unchanged from v9_e1b, reproduction gated below), merge 90s, kernel-CPD localizer. See the module docstring of src/v9_e3_short.py for exactly where smoothing happens in the frozen chain and why S1 uses smooth=1 downstream of its own two-branch smoothing (no double smoothing).

Gate: recalibrating on the SAME budget signal m(t) reproduces k_G = 4.067744, k_F = 1.864051 (results/v9_e1b/calibration.json) exactly -- S1 does not retune the budget, only the detection scalar x.

S1 + veto: V9-E2's selected feature is **f5** (event duration -- no raw EEG needed; applied directly to S1 own event boundaries), threshold unchanged, fast path used for every subject: True.


## Development (15 patients)


### S1 (multi-scale max fusion)

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   64.0/  94  798.0  0.681  0.074  0.134   28.49 | 0.822  0.117  0.188  29.09  || 4-seed mean sens 0.678+-0.005 FA/day 27.93+-0.40 subj-mean 0.810+-0.012
F (fusion: G + best of B1-B4)           65.0/  94  659.0  0.691  0.090  0.159   23.53 | 0.855  0.132  0.215  23.06  || 4-seed mean sens 0.702+-0.009 FA/day 23.37+-0.51 subj-mean 0.861+-0.010
```

### S1 + veto (V9-E2 threshold, unchanged)

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   61.0/  94  529.0  0.649  0.103  0.178   18.89 | 0.791  0.166  0.245  18.84  || 4-seed mean sens 0.657+-0.010 FA/day 18.60+-0.29 subj-mean 0.793+-0.006
F (fusion: G + best of B1-B4)           60.0/  94  399.0  0.638  0.131  0.217   14.24 | 0.796  0.186  0.280  14.31  || 4-seed mean sens 0.654+-0.011 FA/day 14.27+-0.30 subj-mean 0.810+-0.012
```

### Sensitivity by seizure duration bin, S1, seed 42 (E1 overlap rule)

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  2/3        14/30      20/29      28/31    
F (fusion: G + best of B1-B4)          2/3        11/30      20/29      30/31    
```

### Sensitivity by seizure duration bin, S1 + veto, seed 42

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  2/3        11/30      20/29      28/31    
F (fusion: G + best of B1-B4)          1/3        7/30       20/29      30/31    
```

## CHB-MIT held-out test (8 patients)


### S1 (multi-scale max fusion)

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   31.0/  76  404.0  0.408  0.071  0.121   34.92 | 0.516  0.084  0.140  34.06  || 4-seed mean sens 0.401+-0.027 FA/day 35.55+-1.04 subj-mean 0.498+-0.042
F (fusion: G + best of B1-B4)           32.0/  76  384.0  0.421  0.077  0.130   33.20 | 0.552  0.096  0.161  33.81  || 4-seed mean sens 0.434+-0.011 FA/day 32.53+-0.82 subj-mean 0.568+-0.012
```

### S1 + veto (V9-E2 threshold, unchanged)

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   28.0/  76  274.0  0.368  0.093  0.148   23.69 | 0.476  0.111  0.173  23.65  || 4-seed mean sens 0.362+-0.017 FA/day 23.12+-0.59 subj-mean 0.469+-0.031
F (fusion: G + best of B1-B4)           29.0/  76  246.0  0.382  0.105  0.165   21.27 | 0.515  0.129  0.200  21.98  || 4-seed mean sens 0.398+-0.013 FA/day 20.36+-1.10 subj-mean 0.531+-0.014
```

### Sensitivity by seizure duration bin, S1, seed 42 (E1 overlap rule)

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  4/24       3/12       16/27      8/13     
F (fusion: G + best of B1-B4)          7/24       4/12       15/27      6/13     
```

### Sensitivity by seizure duration bin, S1 + veto, seed 42

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  4/24       2/12       14/27      8/13     
F (fusion: G + best of B1-B4)          6/24       3/12       15/27      5/13     
```

## chb24 (1 patients)


### S1 (multi-scale max fusion)

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   16.0/  16   30.0  1.000  0.348  0.516   34.06 | 1.000  0.348  0.516  34.06  || 4-seed mean sens 1.000+-0.000 FA/day 31.22+-3.41 subj-mean 1.000+-0.000
F (fusion: G + best of B1-B4)           16.0/  16   10.0  1.000  0.615  0.762   11.35 | 1.000  0.615  0.762  11.35  || 4-seed mean sens 1.000+-0.000 FA/day 11.07+-0.57 subj-mean 1.000+-0.000
```

### S1 + veto (V9-E2 threshold, unchanged)

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   14.0/  16   17.0  0.875  0.452  0.596   19.30 | 0.875  0.452  0.596  19.30  || 4-seed mean sens 0.812+-0.051 FA/day 18.16+-2.27 subj-mean 0.812+-0.051
F (fusion: G + best of B1-B4)            9.0/  16    6.0  0.562  0.600  0.581    6.81 | 0.562  0.600  0.581   6.81  || 4-seed mean sens 0.609+-0.060 FA/day 6.81+-0.93 subj-mean 0.609+-0.060
```

### Sensitivity by seizure duration bin, S1, seed 42 (E1 overlap rule)

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  4/4        9/9        3/3        -        
F (fusion: G + best of B1-B4)          4/4        9/9        3/3        -        
```

### Sensitivity by seizure duration bin, S1 + veto, seed 42

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  4/4        8/9        2/3        -        
F (fusion: G + best of B1-B4)          2/4        5/9        2/3        -        
```

## Siena, all 14 patients (14 patients)


### S1 (multi-scale max fusion)

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   32.0/  47  356.0  0.681  0.082  0.147   60.97 | 0.776  0.126  0.199  60.22  || 4-seed mean sens 0.612+-0.053 FA/day 60.41+-1.63 subj-mean 0.678+-0.085
F (fusion: G + best of B1-B4)           25.0/  47  207.0  0.532  0.108  0.179   35.45 | 0.532  0.131  0.199  37.16  || 4-seed mean sens 0.521+-0.044 FA/day 34.55+-1.46 subj-mean 0.521+-0.027
```

### S1 + veto (V9-E2 threshold, unchanged)

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   26.0/  47  238.0  0.553  0.098  0.167   40.76 | 0.643  0.141  0.212  40.38  || 4-seed mean sens 0.505+-0.044 FA/day 39.18+-2.14 subj-mean 0.557+-0.073
F (fusion: G + best of B1-B4)           19.0/  47  123.0  0.404  0.134  0.201   21.06 | 0.408  0.133  0.191  22.55  || 4-seed mean sens 0.410+-0.040 FA/day 20.81+-0.80 subj-mean 0.411+-0.028
```

### Sensitivity by seizure duration bin, S1, seed 42 (E1 overlap rule)

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  1/5        3/6        21/27      7/9      
F (fusion: G + best of B1-B4)          2/5        2/6        13/27      8/9      
```

### Sensitivity by seizure duration bin, S1 + veto, seed 42

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  1/5        1/6        19/27      5/9      
F (fusion: G + best of B1-B4)          2/5        1/6        10/27      6/9      
```

## Paired bootstrap (B=10,000): per-patient-mean sensitivity difference, S1 minus the SAME arm WITHOUT the short branch (system-stage curve, matched FP/day)
```
dev        G    fa_target=20 mean diff +nan  95% CI [+nan, +nan]  P(diff>0) nan  (n=0)
dev        G    fa_target=27.5 mean diff -0.028  95% CI [-0.089, +0.018]  P(diff>0) 0.152  (n=15)
dev        G    fa_target=44 mean diff -0.019  95% CI [-0.070, +0.015]  P(diff>0) 0.254  (n=15)
dev        F    fa_target=20 mean diff +nan  95% CI [+nan, +nan]  P(diff>0) nan  (n=0)
dev        F    fa_target=27.5 mean diff -0.035  95% CI [-0.092, -0.001]  P(diff>0) 0.012  (n=15)
dev        F    fa_target=44 mean diff -0.040  95% CI [-0.083, -0.006]  P(diff>0) 0.006  (n=15)
test       G    fa_target=20 mean diff +nan  95% CI [+nan, +nan]  P(diff>0) nan  (n=0)
test       G    fa_target=27.5 mean diff +nan  95% CI [+nan, +nan]  P(diff>0) nan  (n=0)
test       G    fa_target=44 mean diff -0.068  95% CI [-0.112, -0.018]  P(diff>0) 0.004  (n=8)
test       F    fa_target=20 mean diff +nan  95% CI [+nan, +nan]  P(diff>0) nan  (n=0)
test       F    fa_target=27.5 mean diff +nan  95% CI [+nan, +nan]  P(diff>0) nan  (n=0)
test       F    fa_target=44 mean diff -0.040  95% CI [-0.092, +0.012]  P(diff>0) 0.074  (n=8)
siena14    G    fa_target=20 mean diff +nan  95% CI [+nan, +nan]  P(diff>0) nan  (n=0)
siena14    G    fa_target=27.5 mean diff -0.043  95% CI [-0.223, +0.113]  P(diff>0) 0.320  (n=14)
siena14    G    fa_target=44 mean diff -0.104  95% CI [-0.212, +0.003]  P(diff>0) 0.028  (n=14)
siena14    F    fa_target=20 mean diff +nan  95% CI [+nan, +nan]  P(diff>0) nan  (n=0)
siena14    F    fa_target=27.5 mean diff -0.088  95% CI [-0.174, -0.018]  P(diff>0) 0.004  (n=14)
siena14    F    fa_target=44 mean diff -0.126  95% CI [-0.227, -0.034]  P(diff>0) 0.002  (n=14)
```

## Paired bootstrap (B=10,000): per-patient-mean F1 difference, S1 minus no-S1, each arm's OWN calibrated point
```
dev        G    mean diff -0.037  95% CI [-0.065, -0.012]  P(diff>0) 0.003  (n=15)
dev        F    mean diff -0.055  95% CI [-0.090, -0.025]  P(diff>0) 0.000  (n=15)
test       G    mean diff -0.050  95% CI [-0.071, -0.024]  P(diff>0) 0.000  (n=8)
test       F    mean diff -0.042  95% CI [-0.077, -0.006]  P(diff>0) 0.012  (n=8)
siena14    G    mean diff -0.058  95% CI [-0.136, +0.007]  P(diff>0) 0.043  (n=14)
siena14    F    mean diff -0.047  95% CI [-0.097, -0.010]  P(diff>0) 0.000  (n=14)
```

### Localizer onset/offset |error| (median seconds, pooled matched events, all seeds, S1)

```
G (frozen GAE latent)                  onset median   8.0 s IQR [4.0, 20.0] bias  +4.0 | offset median  32.0 s IQR [8.0, 64.0] bias +20.0
F (fusion: G + best of B1-B4)          onset median   8.0 s IQR [4.0, 16.0] bias  +4.0 | offset median  28.0 s IQR [8.0, 52.0] bias +20.0
```

## Adoption verdict (fixed rule: dev paired-sens-diff @ 27.5 FP/day 95% CI lower bound >= -0.05 AND pooled test+chb24+Siena-14 <=20s detections increase vs the no-S1 seed42 baseline)

- G (frozen GAE latent): dev sens-diff CI lower bound -0.089 (FAIL >= -0.05); pooled <=20s caught 9 (S1) vs 12 (no-S1) (FAIL increase) -> **NOT adopted**
- F (fusion: G + best of B1-B4): dev sens-diff CI lower bound -0.092 (FAIL >= -0.05); pooled <=20s caught 13 (S1) vs 12 (no-S1) (pass increase) -> **NOT adopted**