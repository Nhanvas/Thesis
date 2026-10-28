# V9-E1b -- fair per-arm calibration of the per-patient budget, then one evaluation

Full tables: `results/v9_e1b/*.csv`. Code: `src/v9_e1b_calibrate.py` (new; reuses src/v9_e1_baselines.py and every frozen script it calls, read-only; v9_e1_baselines.EXT/SIENA_MISSING are widened at runtime -- a module-attribute patch, not a file edit -- now that V9-T4 built the raw-feature cache for all 14 Siena patients).

k calibrated with `p3_levers.calibrate()` UNCHANGED (median over the 15 development patients, seed 42, of q_i(k) = 0.005), applied to each arm's OWN per-patient budget signal: k_G = 4.067744 (reproduces freeze.json exactly), k_B4 = 11.618333, k_F = 1.864051. Same floor/cap for every arm (clip(q_i(k), 0.005, 0.02)), same smoothing (5), same merge (90 s), same kernel-CPD localizer. Calibrated on development only -- nothing on CHB-MIT test, chb24 or Siena influenced k.

Full detail of the calibration construction (B4's and F's own 'member mean z' budget signal, the natural generalisation of G's): see the module docstring of `src/v9_e1b_calibrate.py`.


## Development (train + validation) (15 patients)

### Each arm's OWN calibrated balanced point (floor 0.005 / cap 0.02, k per arm), after the CPD localizer

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   64.0/  94  657.0  0.681  0.089  0.157   23.46 | 0.847  0.144  0.225  23.99  || 4-seed mean sens 0.670+-0.015 FA/day 23.25+-0.24 subj-mean 0.832+-0.014
B4 (features + kNN)                     70.0/  94  446.0  0.745  0.136  0.230   15.92 | 0.866  0.227  0.325  14.18
F (fusion: G + best of B1-B4)           67.0/  94  541.0  0.713  0.110  0.191   19.31 | 0.899  0.174  0.270  18.10  || 4-seed mean sens 0.707+-0.028 FA/day 18.51+-0.77 subj-mean 0.886+-0.020
```

### Sensitivity by seizure duration bin (localized stage; headline seed 42 for G/F)

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  8/12       47/120     76/116     116/124  
B4 (features + kNN)                    0/3        17/30      23/29      29/31    
F (fusion: G + best of B1-B4)          8/12       49/120     87/116     118/124  
```

### Patient bootstrap 95% CI for the per-patient-mean sensitivity (headline seed 42, B = 10,000)

```
G (frozen GAE latent)                  0.847  [0.707, 0.967]
B4 (features + kNN)                    0.866  [0.720, 0.978]
F (fusion: G + best of B1-B4)          0.899  [0.765, 1.000]
```

### Localizer onset/offset |error| (median seconds, pooled matched events, all seeds)

```
G (frozen GAE latent)                  onset median   4.0 s IQR [4.0, 12.0] bias  +4.0 | offset median  16.0 s IQR [4.0, 48.0] bias  +4.0
B4 (features + kNN)                    onset median   4.0 s IQR [0.0, 12.0] bias  +0.0 | offset median  32.0 s IQR [12.0, 48.0] bias +28.0
F (fusion: G + best of B1-B4)          onset median   4.0 s IQR [4.0, 12.0] bias  +4.0 | offset median  20.0 s IQR [4.0, 44.0] bias  +8.0
```

### System-stage curve (sweep k, per-patient budget + CPD localizer every point): per-patient-mean sensitivity @ FP/day 20.0, 27.5, 44.0

```
G (frozen GAE latent)                  20.0:0.829+-0.017  27.5:0.837+-0.010  44.0:0.858+-0.008
B4 (features + kNN)                    20.0:0.877+-0.000  27.5:0.919+-0.000  44.0:0.979+-0.000
F (fusion: G + best of B1-B4)          20.0:0.889+-0.020  27.5:0.902+-0.015  44.0:0.932+-0.008
```

## CHB-MIT held-out test (8 patients)

### Each arm's OWN calibrated balanced point (floor 0.005 / cap 0.02, k per arm), after the CPD localizer

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   37.0/  76  318.0  0.487  0.104  0.172   27.49 | 0.577  0.118  0.190  26.84  || 4-seed mean sens 0.477+-0.022 FA/day 29.15+-1.26 subj-mean 0.567+-0.019
B4 (features + kNN)                     31.0/  76  211.0  0.408  0.128  0.195   18.24 | 0.552  0.133  0.205  19.44
F (fusion: G + best of B1-B4)           37.0/  76  307.0  0.487  0.108  0.176   26.54 | 0.588  0.128  0.203  27.03  || 4-seed mean sens 0.497+-0.013 FA/day 26.54+-0.63 subj-mean 0.598+-0.011
```

### Sensitivity by seizure duration bin (localized stage; headline seed 42 for G/F)

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  26/96      15/48      64/108     41/52    
B4 (features + kNN)                    7/24       3/12       14/27      7/13     
F (fusion: G + best of B1-B4)          36/96      16/48      64/108     35/52    
```

### Patient bootstrap 95% CI for the per-patient-mean sensitivity (headline seed 42, B = 10,000)

```
G (frozen GAE latent)                  0.577  [0.329, 0.817]
B4 (features + kNN)                    0.552  [0.256, 0.846]
F (fusion: G + best of B1-B4)          0.588  [0.362, 0.817]
```

### Localizer onset/offset |error| (median seconds, pooled matched events, all seeds)

```
G (frozen GAE latent)                  onset median  12.0 s IQR [4.0, 28.0] bias  +8.0 | offset median  24.0 s IQR [8.0, 52.0] bias +16.0
B4 (features + kNN)                    onset median   4.0 s IQR [4.0, 16.0] bias  +0.0 | offset median  16.0 s IQR [6.0, 30.0] bias  +8.0
F (fusion: G + best of B1-B4)          onset median   4.0 s IQR [4.0, 20.0] bias  +4.0 | offset median  24.0 s IQR [12.0, 48.0] bias +16.0
```

### System-stage curve (sweep k, per-patient budget + CPD localizer every point): per-patient-mean sensitivity @ FP/day 20.0, 27.5, 44.0

```
G (frozen GAE latent)                  20.0:NA  27.5:0.554+-0.020  44.0:0.601+-0.015
B4 (features + kNN)                    20.0:0.564+-0.000  27.5:0.607+-0.000  44.0:0.666+-0.000
F (fusion: G + best of B1-B4)          20.0:NA  27.5:0.601+-0.011  44.0:0.646+-0.011
```

## chb24 (all 14 Siena + chb24 now fully recomputed) (1 patients)

### Each arm's OWN calibrated balanced point (floor 0.005 / cap 0.02, k per arm), after the CPD localizer

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   14.0/  16   25.0  0.875  0.359  0.509   28.38 | 0.875  0.359  0.509  28.38  || 4-seed mean sens 0.828+-0.060 FA/day 27.53+-1.70 subj-mean 0.828+-0.060
B4 (features + kNN)                     13.0/  16   16.0  0.812  0.448  0.578   18.16 | 0.812  0.448  0.578  18.16
F (fusion: G + best of B1-B4)           14.0/  16   12.0  0.875  0.538  0.667   13.62 | 0.875  0.538  0.667  13.62  || 4-seed mean sens 0.859+-0.031 FA/day 14.19+-0.66 subj-mean 0.859+-0.031
```

### Sensitivity by seizure duration bin (localized stage; headline seed 42 for G/F)

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  8/16       33/36      12/12      -        
B4 (features + kNN)                    2/4        8/9        3/3        -        
F (fusion: G + best of B1-B4)          8/16       35/36      12/12      -        
```

### Patient bootstrap 95% CI for the per-patient-mean sensitivity (headline seed 42, B = 10,000)

```
G (frozen GAE latent)                  0.875  [0.875, 0.875]
B4 (features + kNN)                    0.812  [0.812, 0.812]
F (fusion: G + best of B1-B4)          0.875  [0.875, 0.875]
```

### Localizer onset/offset |error| (median seconds, pooled matched events, all seeds)

```
G (frozen GAE latent)                  onset median   4.0 s IQR [4.0, 12.0] bias  +4.0 | offset median   4.0 s IQR [0.0, 12.0] bias  +0.0
B4 (features + kNN)                    onset median   4.0 s IQR [4.0, 8.0] bias  +4.0 | offset median   8.0 s IQR [0.0, 20.0] bias  +4.0
F (fusion: G + best of B1-B4)          onset median   4.0 s IQR [4.0, 4.0] bias  +4.0 | offset median   4.0 s IQR [0.0, 8.0] bias  +0.0
```

### System-stage curve (sweep k, per-patient budget + CPD localizer every point): per-patient-mean sensitivity @ FP/day 20.0, 27.5, 44.0

```
G (frozen GAE latent)                  20.0:0.717+-0.078  27.5:0.820+-0.058  44.0:0.885+-0.012
B4 (features + kNN)                    20.0:0.812+-0.000  27.5:0.830+-0.000  44.0:0.900+-0.000
F (fusion: G + best of B1-B4)          20.0:0.883+-0.025  27.5:0.913+-0.020  44.0:0.980+-0.008
```

## Siena, all 14 patients (14 patients)

### Each arm's OWN calibrated balanced point (floor 0.005 / cap 0.02, k per arm), after the CPD localizer

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   33.0/  47  257.0  0.702  0.114  0.196   44.01 | 0.754  0.179  0.257  41.41  || 4-seed mean sens 0.617+-0.067 FA/day 43.89+-1.82 subj-mean 0.635+-0.083
B4 (features + kNN)                     25.0/  47  112.0  0.532  0.182  0.272   19.18 | 0.579  0.251  0.306  19.99
F (fusion: G + best of B1-B4)           26.0/  47  159.0  0.553  0.141  0.224   27.23 | 0.546  0.181  0.247  26.59  || 4-seed mean sens 0.537+-0.020 FA/day 26.67+-1.25 subj-mean 0.544+-0.014
```

### Sensitivity by seizure duration bin (localized stage; headline seed 42 for G/F)

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  8/20       8/24       75/108     25/36    
B4 (features + kNN)                    2/5        3/6        13/27      7/9      
F (fusion: G + best of B1-B4)          8/20       8/24       51/108     34/36    
```

### Patient bootstrap 95% CI for the per-patient-mean sensitivity (headline seed 42, B = 10,000)

```
G (frozen GAE latent)                  0.754  [0.586, 0.899]
B4 (features + kNN)                    0.579  [0.376, 0.774]
F (fusion: G + best of B1-B4)          0.546  [0.350, 0.733]
```

### Localizer onset/offset |error| (median seconds, pooled matched events, all seeds)

```
G (frozen GAE latent)                  onset median  20.0 s IQR [4.0, 34.0] bias +20.0 | offset median  28.0 s IQR [8.0, 128.0] bias +20.0
B4 (features + kNN)                    onset median  12.0 s IQR [4.0, 24.0] bias  +8.0 | offset median  12.0 s IQR [4.0, 52.0] bias  +0.0
F (fusion: G + best of B1-B4)          onset median  16.0 s IQR [4.0, 32.0] bias +16.0 | offset median  20.0 s IQR [4.0, 60.0] bias  +8.0
```

### System-stage curve (sweep k, per-patient budget + CPD localizer every point): per-patient-mean sensitivity @ FP/day 20.0, 27.5, 44.0

```
G (frozen GAE latent)                  20.0:0.413+-0.040  27.5:0.492+-0.046  44.0:0.642+-0.075
B4 (features + kNN)                    20.0:0.580+-0.000  27.5:0.595+-0.000  44.0:0.745+-0.000
F (fusion: G + best of B1-B4)          20.0:0.497+-0.020  27.5:0.553+-0.019  44.0:0.726+-0.014
```

## Runtime measured
calibrate(): 96s. Per-subject eval timing: see each --eval-one call's own stdout (printed elapsed seconds + peak RAM); every step is resumable (per-subject part file under results/v9_e1b/_parts/).