# V9-E1 -- does the graph autoencoder help? Non-graph baselines on the identical pipeline

Full tables: `results/v9_e1/*.csv`. Code: `src/v9_e1_baselines.py` (new; every frozen script it calls -- p2_scalars, e16_recording_baseline, e17b_latent_family, e18_cpd_localizer, p3_levers, e22_test_oneshot, e23_test_look7, x1_external, v9_anatomy -- is read-only and unmodified).

System held fixed for every arm: k = 4.067744, smoothing 5, budget clip(q_i, 0.005, 0.02), merge 90 s, kernel-CPD localizer (freeze.json's choice). Only the per-channel anomaly score feeding e17b's order statistics (6/9/12 + channel mean) changes between arms. B3/B4 use a fixed random_state=42, no tuning; B4's 12 raw features are robust-z'd per channel per patient (label-free) before the Euclidean kNN distance, so unit differences between log-power, log-line-length and kurtosis do not by themselves dominate the distance -- the one preprocessing choice this script makes beyond the prompt's literal spec, disclosed here.

Reproduction gate: evaluate_arm(G) reproduces results/p3c_freeze/per_subject.csv (L2f) and results/e23_test_look7/per_subject_seed.csv (balanced) exactly -- checked, and would STOP the run, every invocation (see the script's own stdout).

Fusion F = rank-mean(G, B4); B4 was chosen as the best of B1-B4 on development only (pooled sensitivity at the balanced point, ties -> lower FP/day), per the prompt's rule.

## Development (train + validation) (15 patients)

### Balanced operating point (clip(q_i(k), 0.005, 0.02)), after the CPD localizer

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   64.0/  94  657.0  0.681  0.089  0.157   23.46 | 0.847  0.144  0.225  23.99  || 4-seed mean sens 0.670+-0.015 FA/day 23.25+-0.24 subj-mean 0.832+-0.014
B1 (features + Mahalanobis)             87.0/  94  1648.0  0.926  0.050  0.095   58.83 | 0.926  0.070  0.122  59.78
B2 (adjacency + Mahalanobis)            54.0/  94  2061.0  0.574  0.026  0.049   73.58 | 0.594  0.045  0.079  67.96
B3 (features + IsolationForest)         84.0/  94  1526.0  0.894  0.052  0.099   54.48 | 0.946  0.075  0.130  54.00
B4 (features + kNN)                     93.0/  94  1628.0  0.989  0.054  0.102   58.12 | 0.997  0.081  0.138  56.03
F (fusion: G + best of B1-B4)           66.0/  94  598.0  0.702  0.099  0.174   21.35 | 0.886  0.160  0.252  19.94  || 4-seed mean sens 0.705+-0.028 FA/day 20.37+-0.92 subj-mean 0.883+-0.018
```

### Sensitivity by seizure duration bin (headline seed 42, after the localizer; E1 overlap rule)

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  2/3        13/30      19/29      29/31    
B1 (features + Mahalanobis)            2/3        28/30      27/29      28/31    
B2 (adjacency + Mahalanobis)           0/3        14/30      15/29      24/31    
B3 (features + IsolationForest)        2/3        23/30      27/29      30/31    
B4 (features + kNN)                    3/3        29/30      29/29      31/31    
F (fusion: G + best of B1-B4)          2/3        12/30      21/29      30/31    
```

### Matched operating point (global budget sweep, detector stage): sensitivity @ FP/day 20.0, 27.5, 44.0

```
G (frozen GAE latent)                  20.0:0.665+-0.011  27.5:0.690+-0.009  44.0:0.726+-0.017
B1 (features + Mahalanobis)            20.0:0.682+-0.000  27.5:0.772+-0.000  44.0:0.845+-0.000
B2 (adjacency + Mahalanobis)           20.0:0.244+-0.000  27.5:0.274+-0.000  44.0:0.354+-0.000
B3 (features + IsolationForest)        20.0:0.633+-0.000  27.5:0.694+-0.000  44.0:0.834+-0.000
B4 (features + kNN)                    20.0:0.801+-0.000  27.5:0.857+-0.000  44.0:0.942+-0.000
F (fusion: G + best of B1-B4)          20.0:0.723+-0.016  27.5:0.753+-0.027  44.0:0.794+-0.009
```

### Patient bootstrap 95% CI for the per-patient-mean sensitivity (headline seed 42, B = 10,000)

```
G (frozen GAE latent)                  0.847  [0.707, 0.967]
B1 (features + Mahalanobis)            0.926  [0.785, 1.000]
B2 (adjacency + Mahalanobis)           0.594  [0.442, 0.735]
B3 (features + IsolationForest)        0.946  [0.859, 1.000]
B4 (features + kNN)                    0.997  [0.992, 1.000]
F (fusion: G + best of B1-B4)          0.886  [0.751, 0.983]
```

## CHB-MIT held-out test (8 patients)

### Balanced operating point (clip(q_i(k), 0.005, 0.02)), after the CPD localizer

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   37.0/  76  318.0  0.487  0.104  0.172   27.49 | 0.577  0.118  0.190  26.84  || 4-seed mean sens 0.477+-0.022 FA/day 29.15+-1.26 subj-mean 0.567+-0.019
B1 (features + Mahalanobis)             43.0/  76  805.0  0.566  0.051  0.093   69.59 | 0.690  0.060  0.106  68.56
B2 (adjacency + Mahalanobis)            24.0/  76  724.0  0.316  0.032  0.058   62.59 | 0.312  0.036  0.064  66.67
B3 (features + IsolationForest)         39.0/  76  623.0  0.513  0.059  0.106   53.86 | 0.631  0.071  0.123  53.32
B4 (features + kNN)                     51.0/  76  661.0  0.671  0.072  0.129   57.14 | 0.756  0.087  0.150  54.08
F (fusion: G + best of B1-B4)           38.0/  76  323.0  0.500  0.105  0.174   27.92 | 0.594  0.128  0.203  28.53  || 4-seed mean sens 0.507+-0.013 FA/day 27.92+-1.00 subj-mean 0.603+-0.011
```

### Sensitivity by seizure duration bin (headline seed 42, after the localizer; E1 overlap rule)

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  7/24       4/12       16/27      11/13    
B1 (features + Mahalanobis)            14/24      6/12       17/27      6/13     
B2 (adjacency + Mahalanobis)           4/24       3/12       13/27      4/13     
B3 (features + IsolationForest)        11/24      3/12       17/27      8/13     
B4 (features + kNN)                    18/24      4/12       18/27      11/13    
F (fusion: G + best of B1-B4)          8/24       4/12       17/27      9/13     
```

### Matched operating point (global budget sweep, detector stage): sensitivity @ FP/day 20.0, 27.5, 44.0

```
G (frozen GAE latent)                  20.0:0.292+-0.018  27.5:0.342+-0.011  44.0:0.360+-0.008
B1 (features + Mahalanobis)            20.0:0.193+-0.000  27.5:0.242+-0.000  44.0:0.362+-0.000
B2 (adjacency + Mahalanobis)           20.0:0.072+-0.000  27.5:0.106+-0.000  44.0:0.200+-0.000
B3 (features + IsolationForest)        20.0:0.246+-0.000  27.5:0.301+-0.000  44.0:0.404+-0.000
B4 (features + kNN)                    20.0:0.407+-0.000  27.5:0.467+-0.000  44.0:0.588+-0.000
F (fusion: G + best of B1-B4)          20.0:0.355+-0.008  27.5:0.396+-0.007  44.0:0.464+-0.014
```

### Patient bootstrap 95% CI for the per-patient-mean sensitivity (headline seed 42, B = 10,000)

```
G (frozen GAE latent)                  0.577  [0.329, 0.817]
B1 (features + Mahalanobis)            0.690  [0.458, 0.896]
B2 (adjacency + Mahalanobis)           0.312  [0.208, 0.423]
B3 (features + IsolationForest)        0.631  [0.398, 0.871]
B4 (features + kNN)                    0.756  [0.560, 0.923]
F (fusion: G + best of B1-B4)          0.594  [0.371, 0.819]
```

## Winner rule (fixed in the prompt): an arm 'beats G' only if it is better than G on development AND on CHB-MIT test (balanced-point pooled sensitivity) AND at the matched FP/day operating point (interpolated sensitivity >= G's at every one of [20.0, 27.5, 44.0] where both curves are defined, on both sets); otherwise 'no better' or 'mixed'.

- B1 (features + Mahalanobis): dev sens 0.926 vs G 0.670 (pass); test sens 0.566 vs G 0.477 (pass); matched-FP FAIL -> **mixed**
- B2 (adjacency + Mahalanobis): dev sens 0.574 vs G 0.670 (FAIL); test sens 0.316 vs G 0.477 (FAIL); matched-FP FAIL -> **no better**
- B3 (features + IsolationForest): dev sens 0.894 vs G 0.670 (pass); test sens 0.513 vs G 0.477 (pass); matched-FP FAIL -> **mixed**
- B4 (features + kNN): dev sens 0.989 vs G 0.670 (pass); test sens 0.671 vs G 0.477 (pass); matched-FP pass -> **BEATS G**
- F (fusion: G + best of B1-B4): dev sens 0.705 vs G 0.670 (pass); test sens 0.507 vs G 0.477 (pass); matched-FP pass -> **BEATS G**

## Part C -- re-reporting G (seed 42, frozen balanced point, after the localizer) under other papers' protocols on CHB-MIT test (secondary analysis, never the headline)

- full 8-patient test set: tp 37/76, FP 318, sens 0.487, FP/day 27.49
- secondary analysis under the protocol of [excluding chb06/chb14/chb16 (Clin Exp Pediatr 2026, DOI 10.3345/cep.2026.01011, mean seizure duration < 30 s)]: tp 27/48, FP 178, sens 0.562, FP/day 25.73
- secondary analysis under the protocol of [seizures >= 30 s only]: tp 28/45, FP 327, sens 0.622, FP/day n/a (ref-filtered only)

## chb24 and Siena

- chb24 (full, G only, from results/x1_external, balanced point, localized, 4-seed pooled): tp 53/64, FP 100, sens 0.828, FP/day 28.38 -- committed reference; recomputed below (all arms) where the raw-feature cache allows it.
- Siena, all 14 patients (G only, from results/x1_external, balanced point, localized, 4-seed pooled): tp 116/188, FP 1023, sens 0.617, FP/day 43.80 -- committed reference only (B1-F need raw features not cached for 11/14 patients).

Raw-feature cache available locally (results/v9_anatomy/xcache/) for chb24 and 3/14 Siena patients (PN00, PN10, PN11); the other 11 Siena patients (PN01, PN03, PN05, PN06, PN07, PN09, PN12, PN13, PN14, PN16, PN17) have no raw EDF in this checkout (documented in results/v9_anatomy/SUMMARY.md) -- B1-B4/F are refused there, not estimated.


## chb24 (recomputed locally, all arms) (1 patients)

### Balanced operating point (clip(q_i(k), 0.005, 0.02)), after the CPD localizer

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   14.0/  16   25.0  0.875  0.359  0.509   28.38 | 0.875  0.359  0.509  28.38  || 4-seed mean sens 0.828+-0.060 FA/day 27.53+-1.70 subj-mean 0.828+-0.060
B1 (features + Mahalanobis)             16.0/  16   55.0  1.000  0.225  0.368   62.44 | 1.000  0.225  0.368  62.44
B2 (adjacency + Mahalanobis)            16.0/  16   73.0  1.000  0.180  0.305   82.87 | 1.000  0.180  0.305  82.87
B3 (features + IsolationForest)         14.0/  16   53.0  0.875  0.209  0.337   60.17 | 0.875  0.209  0.337  60.17
B4 (features + kNN)                     16.0/  16   54.0  1.000  0.229  0.372   61.30 | 1.000  0.229  0.372  61.30
F (fusion: G + best of B1-B4)           16.0/  16   36.0  1.000  0.308  0.471   40.87 | 1.000  0.308  0.471  40.87  || 4-seed mean sens 0.984+-0.031 FA/day 37.46+-2.78 subj-mean 0.984+-0.031
```

### Sensitivity by seizure duration bin (headline seed 42, after the localizer; E1 overlap rule)

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  2/4        9/9        3/3        -        
B1 (features + Mahalanobis)            4/4        9/9        3/3        -        
B2 (adjacency + Mahalanobis)           4/4        9/9        3/3        -        
B3 (features + IsolationForest)        3/4        8/9        3/3        -        
B4 (features + kNN)                    4/4        9/9        3/3        -        
F (fusion: G + best of B1-B4)          4/4        9/9        3/3        -        
```

### Matched operating point (global budget sweep, detector stage): sensitivity @ FP/day 20.0, 27.5, 44.0

```
G (frozen GAE latent)                  20.0:0.681+-0.043  27.5:0.817+-0.043  44.0:0.898+-0.028
B1 (features + Mahalanobis)            20.0:0.764+-0.000  27.5:0.790+-0.000  44.0:0.840+-0.000
B2 (adjacency + Mahalanobis)           20.0:0.850+-0.000  27.5:0.919+-0.000  44.0:0.938+-0.000
B3 (features + IsolationForest)        20.0:0.812+-0.000  27.5:0.812+-0.000  44.0:0.858+-0.000
B4 (features + kNN)                    20.0:0.812+-0.000  27.5:0.830+-0.000  44.0:0.914+-0.000
F (fusion: G + best of B1-B4)          20.0:0.917+-0.037  27.5:0.970+-0.034  44.0:0.993+-0.014
```

### Patient bootstrap 95% CI for the per-patient-mean sensitivity (headline seed 42, B = 10,000)

```
G (frozen GAE latent)                  0.875  [0.875, 0.875]
B1 (features + Mahalanobis)            1.000  [1.000, 1.000]
B2 (adjacency + Mahalanobis)           1.000  [1.000, 1.000]
B3 (features + IsolationForest)        0.875  [0.875, 0.875]
B4 (features + kNN)                    1.000  [1.000, 1.000]
F (fusion: G + best of B1-B4)          1.000  [1.000, 1.000]
```

## Siena, 3/14 patients with a local raw-feature cache (3 patients)

### Balanced operating point (clip(q_i(k), 0.005, 0.02)), after the CPD localizer

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   13.0/  16   22.0  0.812  0.371  0.510   21.88 | 0.900  0.454  0.570  20.32  || 4-seed mean sens 0.672+-0.107 FA/day 25.61+-2.86 subj-mean 0.783+-0.088
B1 (features + Mahalanobis)             14.0/  16   64.0  0.875  0.179  0.298   63.65 | 0.900  0.229  0.331  70.13
B2 (adjacency + Mahalanobis)            12.0/  16   79.0  0.750  0.132  0.224   78.57 | 0.500  0.134  0.200  80.01
B3 (features + IsolationForest)         12.0/  16   45.0  0.750  0.211  0.329   44.76 | 0.800  0.232  0.332  50.31
B4 (features + kNN)                     12.0/  16   61.0  0.750  0.164  0.270   60.67 | 0.800  0.197  0.292  62.22
F (fusion: G + best of B1-B4)           11.0/  16   21.0  0.688  0.344  0.458   20.89 | 0.800  0.396  0.501  22.00  || 4-seed mean sens 0.594+-0.062 FA/day 24.62+-2.86 subj-mean 0.700+-0.067
```

### Sensitivity by seizure duration bin (headline seed 42, after the localizer; E1 overlap rule)

```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  2/4        1/2        10/10      -        
B1 (features + Mahalanobis)            3/4        2/2        9/10       -        
B2 (adjacency + Mahalanobis)           3/4        2/2        7/10       -        
B3 (features + IsolationForest)        2/4        2/2        8/10       -        
B4 (features + kNN)                    2/4        2/2        8/10       -        
F (fusion: G + best of B1-B4)          1/4        1/2        9/10       -        
```

### Matched operating point (global budget sweep, detector stage): sensitivity @ FP/day 20.0, 27.5, 44.0

```
G (frozen GAE latent)                  20.0:0.483+-0.098  27.5:0.584+-0.069  44.0:0.743+-0.040
B1 (features + Mahalanobis)            20.0:0.548+-0.000  27.5:0.651+-0.000  44.0:0.701+-0.000
B2 (adjacency + Mahalanobis)           20.0:0.576+-0.000  27.5:0.623+-0.000  44.0:0.731+-0.000
B3 (features + IsolationForest)        20.0:0.520+-0.000  27.5:0.654+-0.000  44.0:0.750+-0.000
B4 (features + kNN)                    20.0:0.517+-0.000  27.5:0.625+-0.000  44.0:0.645+-0.000
F (fusion: G + best of B1-B4)          20.0:0.440+-0.090  27.5:0.580+-0.131  44.0:0.832+-0.039
```

### Patient bootstrap 95% CI for the per-patient-mean sensitivity (headline seed 42, B = 10,000)

```
G (frozen GAE latent)                  0.900  [0.700, 1.000]
B1 (features + Mahalanobis)            0.900  [0.800, 1.000]
B2 (adjacency + Mahalanobis)           0.500  [0.000, 0.900]
B3 (features + IsolationForest)        0.800  [0.600, 1.000]
B4 (features + kNN)                    0.800  [0.600, 1.000]
F (fusion: G + best of B1-B4)          0.800  [0.600, 1.000]
```

## Runtime measured
See the script's own stdout (printed elapsed seconds) for the --full and --ext runs; both are resumable (per-subject cache under results/v9_e1/cache/).