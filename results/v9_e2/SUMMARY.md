# V9-E2 -- paired comparison + competing-anomaly (artifact) veto

Full tables: `results/v9_e2/*.csv`, `results/v9_e2/paired/*.csv`. Code: `src/v9_e2_veto.py` (new; reuses src/v9_e1b_calibrate.py, src/v9_e1_baselines.py, src/v9_anatomy.py and every frozen script they call, read-only).

## Part 0 -- fixes and paired statistics on the existing V9-E1b outputs

### Duration-bin tables, seed 42 only for every arm (B4 is deterministic; results/v9_e1b's own table summed G/F over 4 seeds, not comparable to B4's one)


**development**
```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  2/3        13/30      19/29      29/31    
B4 (features + kNN)                    0/3        17/30      23/29      29/31    
F (fusion: G + best of B1-B4)          2/3        12/30      21/29      30/31    
```

**CHB-MIT test**
```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  7/24       4/12       16/27      11/13    
B4 (features + kNN)                    7/24       3/12       14/27      7/13     
F (fusion: G + best of B1-B4)          8/24       4/12       16/27      9/13     
```

**chb24**
```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  2/4        9/9        3/3        -        
B4 (features + kNN)                    2/4        8/9        3/3        -        
F (fusion: G + best of B1-B4)          2/4        9/9        3/3        -        
```

**Siena-14**
```
arm                                    <=20s      21-40s     41-80s     >80s
G (frozen GAE latent)                  3/5        2/6        21/27      7/9      
B4 (features + kNN)                    2/5        3/6        13/27      7/9      
F (fusion: G + best of B1-B4)          2/5        2/6        14/27      8/9      
```

### Paired bootstrap (B=10,000): per-patient-mean sensitivity difference at matched FP/day, system-stage curve (chb24 excluded, n=1)
```
dev        B4-G   fa_target=20 mean diff +0.048  95% CI [-0.053, +0.161]  P(diff>0) 0.808  (n=15)
dev        B4-G   fa_target=27.5 mean diff +0.082  95% CI [+0.004, +0.181]  P(diff>0) 0.981  (n=15)
dev        B4-G   fa_target=44 mean diff +0.122  95% CI [+0.031, +0.226]  P(diff>0) 0.998  (n=15)
dev        F-G    fa_target=20 mean diff +0.060  95% CI [+0.005, +0.138]  P(diff>0) 0.992  (n=15)
dev        F-G    fa_target=27.5 mean diff +0.066  95% CI [+0.004, +0.156]  P(diff>0) 0.990  (n=15)
dev        F-G    fa_target=44 mean diff +0.075  95% CI [+0.000, +0.171]  P(diff>0) 0.979  (n=15)
test       B4-G   fa_target=20 mean diff +nan  95% CI [+nan, +nan]  P(diff>0) nan  (n=0)
test       B4-G   fa_target=27.5 mean diff +0.053  95% CI [-0.020, +0.143]  P(diff>0) 0.911  (n=8)
test       B4-G   fa_target=44 mean diff +0.065  95% CI [-0.048, +0.208]  P(diff>0) 0.812  (n=8)
test       F-G    fa_target=20 mean diff +nan  95% CI [+nan, +nan]  P(diff>0) nan  (n=0)
test       F-G    fa_target=27.5 mean diff +0.047  95% CI [+0.013, +0.086]  P(diff>0) 0.998  (n=8)
test       F-G    fa_target=44 mean diff +0.045  95% CI [-0.025, +0.110]  P(diff>0) 0.894  (n=8)
siena14    B4-G   fa_target=20 mean diff +0.168  95% CI [-0.014, +0.385]  P(diff>0) 0.962  (n=14)
siena14    B4-G   fa_target=27.5 mean diff +0.104  95% CI [-0.128, +0.339]  P(diff>0) 0.814  (n=14)
siena14    B4-G   fa_target=44 mean diff +0.104  95% CI [-0.053, +0.265]  P(diff>0) 0.898  (n=14)
siena14    F-G    fa_target=20 mean diff +0.084  95% CI [-0.042, +0.257]  P(diff>0) 0.867  (n=14)
siena14    F-G    fa_target=27.5 mean diff +0.061  95% CI [-0.132, +0.247]  P(diff>0) 0.744  (n=14)
siena14    F-G    fa_target=44 mean diff +0.084  95% CI [-0.039, +0.210]  P(diff>0) 0.912  (n=14)
```

### Paired bootstrap (B=10,000): per-patient-mean F1 difference, each arm's OWN calibrated point (chb24 excluded, n=1)
```
dev        B4-G   mean diff +0.100  95% CI [+0.035, +0.176]  P(diff>0) 0.999  (n=15)
dev        F-G    mean diff +0.045  95% CI [+0.020, +0.072]  P(diff>0) 1.000  (n=15)
test       B4-G   mean diff +0.016  95% CI [-0.032, +0.060]  P(diff>0) 0.747  (n=8)
test       F-G    mean diff +0.013  95% CI [-0.012, +0.037]  P(diff>0) 0.844  (n=8)
siena14    B4-G   mean diff +0.048  95% CI [-0.125, +0.216]  P(diff>0) 0.709  (n=14)
siena14    F-G    mean diff -0.011  95% CI [-0.105, +0.077]  P(diff>0) 0.414  (n=14)
```

## Part A -- veto of competing anomalies (pre-registered on development, applied once)

Selected feature: **f5** (direction: veto events where the feature is LOW; mean AUROC power 0.790, mean signed AUROC 0.790, averaged over G/B4/F on development). Threshold per arm (development, keeps >=95% of that arm's own true detections): {"G": 28.0, "B4": 33.8, "F": 36.0}.

Disclosure: the threshold uses development LABELS (a validation-set hyperparameter, same status as k/floor/cap/smoothing/merge elsewhere in this pipeline); the anomaly-detection model itself never sees a seizure label.


### AUROC table, every candidate feature, development (TP vs FP, pooled per arm)

```
arm         B4      F      G
feature                     
f1       0.238  0.303  0.424
f2       0.488  0.472  0.483
f3       0.459  0.462  0.446
f4       0.293  0.262  0.258
f5       0.790  0.803  0.778
```

### Same AUROCs measured on CHB-MIT test + Siena-14 (descriptive only, NOT used to pick the feature or threshold)

```
arm         B4      F      G
feature                     
f1       0.424  0.449  0.524
f2       0.486  0.492  0.492
f3       0.589  0.629  0.624
f4       0.467  0.434  0.461
f5       0.628  0.647  0.660
```

## Development (15 patients)

### before veto

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   64.0/  94  657.0  0.681  0.089  0.157   23.46 | 0.847  0.144  0.225  23.99  || 4-seed mean sens 0.670+-0.015 FA/day 23.25+-0.24 subj-mean 0.832+-0.014
B4 (features + kNN)                     70.0/  94  446.0  0.745  0.136  0.230   15.92 | 0.866  0.227  0.325  14.18
F (fusion: G + best of B1-B4)           67.0/  94  541.0  0.713  0.110  0.191   19.31 | 0.899  0.174  0.270  18.10  || 4-seed mean sens 0.707+-0.028 FA/day 18.51+-0.77 subj-mean 0.886+-0.020
```
### after veto

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   62.0/  94  414.0  0.660  0.130  0.218   14.78 | 0.825  0.195  0.286  14.38  || 4-seed mean sens 0.646+-0.010 FA/day 15.01+-0.84 subj-mean 0.809+-0.011
B4 (features + kNN)                     66.0/  94  289.0  0.702  0.186  0.294   10.32 | 0.838  0.277  0.377   9.38
F (fusion: G + best of B1-B4)           63.0/  94  301.0  0.670  0.173  0.275   10.75 | 0.866  0.251  0.350  10.33  || 4-seed mean sens 0.676+-0.025 FA/day 10.06+-0.50 subj-mean 0.858+-0.019
```

## CHB-MIT held-out test (8 patients)

### before veto

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   37.0/  76  318.0  0.487  0.104  0.172   27.49 | 0.577  0.118  0.190  26.84  || 4-seed mean sens 0.477+-0.022 FA/day 29.15+-1.26 subj-mean 0.567+-0.019
B4 (features + kNN)                     31.0/  76  211.0  0.408  0.128  0.195   18.24 | 0.552  0.133  0.205  19.44
F (fusion: G + best of B1-B4)           37.0/  76  307.0  0.487  0.108  0.176   26.54 | 0.588  0.128  0.203  27.03  || 4-seed mean sens 0.497+-0.013 FA/day 26.54+-0.63 subj-mean 0.598+-0.011
```
### after veto

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   33.0/  76  210.0  0.434  0.136  0.207   18.15 | 0.492  0.148  0.221  17.86  || 4-seed mean sens 0.395+-0.028 FA/day 18.59+-0.76 subj-mean 0.473+-0.017
B4 (features + kNN)                     27.0/  76  133.0  0.355  0.169  0.229   11.50 | 0.496  0.169  0.236  12.56
F (fusion: G + best of B1-B4)           28.0/  76  175.0  0.368  0.138  0.201   15.13 | 0.455  0.158  0.226  15.47  || 4-seed mean sens 0.382+-0.011 FA/day 14.29+-0.93 subj-mean 0.481+-0.024
```

## chb24 (1 patients)

### before veto

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   14.0/  16   25.0  0.875  0.359  0.509   28.38 | 0.875  0.359  0.509  28.38  || 4-seed mean sens 0.828+-0.060 FA/day 27.53+-1.70 subj-mean 0.828+-0.060
B4 (features + kNN)                     13.0/  16   16.0  0.812  0.448  0.578   18.16 | 0.812  0.448  0.578  18.16
F (fusion: G + best of B1-B4)           14.0/  16   12.0  0.875  0.538  0.667   13.62 | 0.875  0.538  0.667  13.62  || 4-seed mean sens 0.859+-0.031 FA/day 14.19+-0.66 subj-mean 0.859+-0.031
```
### after veto

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                    7.0/  16   18.0  0.438  0.280  0.341   20.43 | 0.438  0.280  0.341  20.43  || 4-seed mean sens 0.406+-0.081 FA/day 20.43+-0.93 subj-mean 0.406+-0.081
B4 (features + kNN)                      7.0/  16    8.0  0.438  0.467  0.452    9.08 | 0.438  0.467  0.452   9.08
F (fusion: G + best of B1-B4)            5.0/  16    8.0  0.312  0.385  0.345    9.08 | 0.312  0.385  0.345   9.08  || 4-seed mean sens 0.328+-0.031 FA/day 6.81+-1.61 subj-mean 0.328+-0.031
```

## Siena, all 14 patients (14 patients)

### before veto

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   33.0/  47  257.0  0.702  0.114  0.196   44.01 | 0.754  0.179  0.257  41.41  || 4-seed mean sens 0.617+-0.067 FA/day 43.89+-1.82 subj-mean 0.635+-0.083
B4 (features + kNN)                     25.0/  47  112.0  0.532  0.182  0.272   19.18 | 0.579  0.251  0.306  19.99
F (fusion: G + best of B1-B4)           26.0/  47  159.0  0.553  0.141  0.224   27.23 | 0.546  0.181  0.247  26.59  || 4-seed mean sens 0.537+-0.020 FA/day 26.67+-1.25 subj-mean 0.544+-0.014
```
### after veto

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
G (frozen GAE latent)                   29.0/  47  184.0  0.617  0.136  0.223   31.51 | 0.650  0.199  0.269  31.31  || 4-seed mean sens 0.553+-0.046 FA/day 29.76+-1.91 subj-mean 0.561+-0.060
B4 (features + kNN)                     17.0/  47   65.0  0.362  0.207  0.264   11.13 | 0.439  0.260  0.292  11.93
F (fusion: G + best of B1-B4)           20.0/  47   97.0  0.426  0.171  0.244   16.61 | 0.418  0.198  0.243  18.54  || 4-seed mean sens 0.367+-0.047 FA/day 15.97+-0.94 subj-mean 0.385+-0.029
```

### Seizures lost to the veto (true detections whose only matching event was vetoed; subject, set, arm, seed, reference-seizure duration)

```
subject     set arm         seed  ref_dur
  chb24   chb24  B4            -     16.0
  chb24   chb24  B4            -     28.0
  chb24   chb24  B4            -     28.0
  chb24   chb24  B4            -     32.0
  chb24   chb24  B4            -     32.0
  chb24   chb24  B4            -     76.0
  chb24   chb24   F clean_seed42     20.0
  chb24   chb24   F clean_seed42     20.0
  chb24   chb24   F  clean_seed1     20.0
  chb24   chb24   F  clean_seed2     20.0
  chb24   chb24   F  clean_seed3     20.0
  chb24   chb24   F clean_seed42     24.0
  chb24   chb24   F  clean_seed1     24.0
  chb24   chb24   F  clean_seed2     24.0
  chb24   chb24   F  clean_seed3     24.0
  chb24   chb24   F clean_seed42     28.0
  chb24   chb24   F clean_seed42     28.0
  chb24   chb24   F clean_seed42     28.0
  chb24   chb24   F  clean_seed1     28.0
  chb24   chb24   F  clean_seed1     28.0
  chb24   chb24   F  clean_seed1     28.0
  chb24   chb24   F  clean_seed2     28.0
  chb24   chb24   F  clean_seed2     28.0
  chb24   chb24   F  clean_seed2     28.0
  chb24   chb24   F  clean_seed2     28.0
  chb24   chb24   F  clean_seed3     28.0
  chb24   chb24   F  clean_seed3     28.0
  chb24   chb24   F  clean_seed3     28.0
  chb24   chb24   F  clean_seed3     28.0
  chb24   chb24   F clean_seed42     32.0
  chb24   chb24   F clean_seed42     32.0
  chb24   chb24   F  clean_seed1     32.0
  chb24   chb24   F  clean_seed2     32.0
  chb24   chb24   F  clean_seed2     32.0
  chb24   chb24   F  clean_seed3     32.0
  chb24   chb24   F  clean_seed3     32.0
  chb24   chb24   F clean_seed42     76.0
  chb24   chb24   F  clean_seed1     76.0
  chb24   chb24   F  clean_seed2     76.0
  chb24   chb24   F  clean_seed3     76.0
  chb24   chb24   G clean_seed42     20.0
  chb24   chb24   G  clean_seed2     20.0
  chb24   chb24   G  clean_seed3     20.0
  chb24   chb24   G clean_seed42     24.0
  chb24   chb24   G  clean_seed1     24.0
  chb24   chb24   G  clean_seed2     24.0
  chb24   chb24   G  clean_seed3     24.0
  chb24   chb24   G clean_seed42     28.0
  chb24   chb24   G clean_seed42     28.0
  chb24   chb24   G  clean_seed1     28.0
  chb24   chb24   G  clean_seed1     28.0
  chb24   chb24   G  clean_seed2     28.0
  chb24   chb24   G  clean_seed2     28.0
  chb24   chb24   G  clean_seed3     28.0
  chb24   chb24   G  clean_seed3     28.0
  chb24   chb24   G  clean_seed3     28.0
  chb24   chb24   G  clean_seed3     28.0
  chb24   chb24   G clean_seed42     32.0
  chb24   chb24   G clean_seed42     32.0
  chb24   chb24   G  clean_seed1     32.0
  chb24   chb24   G  clean_seed2     32.0
  chb24   chb24   G  clean_seed3     32.0
  chb24   chb24   G  clean_seed3     32.0
  chb24   chb24   G clean_seed42     76.0
  chb24   chb24   G  clean_seed1     76.0
  chb24   chb24   G  clean_seed2     76.0
  chb24   chb24   G  clean_seed3     76.0
  chb12     dev  B4            -     24.0
  chb12     dev  B4            -     36.0
  chb01     dev  B4            -     40.0
  chb08     dev  B4            -    192.0
  chb02     dev   F  clean_seed1     12.0
  chb12     dev   F  clean_seed1     28.0
  chb12     dev   F  clean_seed3     28.0
  chb20     dev   F clean_seed42     32.0
  chb20     dev   F  clean_seed3     32.0
  chb20     dev   F clean_seed42     40.0
  chb20     dev   F clean_seed42     40.0
  chb20     dev   F  clean_seed1     40.0
  chb20     dev   F  clean_seed2     40.0
  chb20     dev   F clean_seed42     44.0
  chb20     dev   F  clean_seed2     52.0
  chb21     dev   F  clean_seed3     56.0
  chb11     dev   G clean_seed42     24.0
  chb11     dev   G  clean_seed3     24.0
  chb23     dev   G  clean_seed3     28.0
  chb12     dev   G  clean_seed3     36.0
  chb20     dev   G clean_seed42     40.0
  chb20     dev   G  clean_seed1     40.0
  chb20     dev   G  clean_seed2     40.0
  chb20     dev   G  clean_seed3     40.0
  chb21     dev   G  clean_seed1     84.0
   PN10 siena14  B4            -     16.0
   PN14 siena14  B4            -     16.0
   PN10 siena14  B4            -     24.0
   PN10 siena14  B4            -     48.0
   PN00 siena14  B4            -     56.0
   PN10 siena14  B4            -     60.0
   PN10 siena14  B4            -     64.0
   PN07 siena14  B4            -     68.0
   PN07 siena14  B4            -     68.0
   PN10 siena14   F  clean_seed1     16.0
   PN10 siena14   F  clean_seed3     16.0
   PN14 siena14   F clean_seed42     32.0
   PN14 siena14   F  clean_seed1     32.0
   PN14 siena14   F  clean_seed2     32.0
   PN14 siena14   F  clean_seed3     32.0
   PN10 siena14   F clean_seed42     48.0
   PN10 siena14   F  clean_seed1     48.0
   PN10 siena14   F  clean_seed2     48.0
   PN10 siena14   F  clean_seed3     48.0
   PN13 siena14   F  clean_seed2     52.0
   PN00 siena14   F clean_seed42     56.0
   PN10 siena14   F  clean_seed1     60.0
   PN10 siena14   F  clean_seed2     60.0
   PN10 siena14   F  clean_seed2     64.0
   PN13 siena14   F  clean_seed1     68.0
   PN00 siena14   F  clean_seed1     76.0
   PN00 siena14   F  clean_seed1     76.0
   PN12 siena14   F clean_seed42     96.0
   PN12 siena14   F  clean_seed1     96.0
   PN12 siena14   F  clean_seed2     96.0
   PN16 siena14   F clean_seed42    112.0
   PN16 siena14   F  clean_seed1    112.0
   PN16 siena14   F  clean_seed2    112.0
   PN16 siena14   F  clean_seed3    112.0
   PN16 siena14   F clean_seed42    124.0
   PN16 siena14   F  clean_seed1    124.0
   PN16 siena14   F  clean_seed2    124.0
   PN16 siena14   F  clean_seed3    124.0
   PN13 siena14   F  clean_seed1    152.0
   PN13 siena14   F  clean_seed2    152.0
   PN13 siena14   F  clean_seed3    152.0
   PN14 siena14   G  clean_seed2     32.0
   PN00 siena14   G clean_seed42     56.0
   PN00 siena14   G  clean_seed2     64.0
   PN12 siena14   G clean_seed42     96.0
   PN12 siena14   G  clean_seed1     96.0
   PN16 siena14   G clean_seed42    112.0
   PN16 siena14   G clean_seed42    124.0
   PN16 siena14   G  clean_seed2    124.0
   PN16 siena14   G  clean_seed3    124.0
   PN13 siena14   G  clean_seed1    152.0
   PN13 siena14   G  clean_seed2    152.0
   PN13 siena14   G  clean_seed3    152.0
  chb06    test  B4            -     16.0
  chb06    test  B4            -     16.0
  chb14    test  B4            -     24.0
  chb14    test  B4            -     28.0
  chb16    test   F  clean_seed2      8.0
  chb16    test   F  clean_seed3     12.0
  chb06    test   F clean_seed42     16.0
  chb06    test   F clean_seed42     16.0
  chb06    test   F  clean_seed1     16.0
  chb06    test   F  clean_seed2     16.0
  chb06    test   F  clean_seed3     16.0
  chb06    test   F  clean_seed3     16.0
  chb14    test   F clean_seed42     16.0
  chb14    test   F  clean_seed1     16.0
  chb14    test   F  clean_seed2     16.0
  chb14    test   F  clean_seed3     16.0
  chb14    test   F clean_seed42     20.0
  chb14    test   F  clean_seed1     20.0
  chb14    test   F  clean_seed2     20.0
  chb14    test   F  clean_seed3     20.0
  chb14    test   F clean_seed42     28.0
  chb14    test   F  clean_seed1     28.0
  chb15    test   F  clean_seed3     32.0
  chb15    test   F clean_seed42     76.0
  chb15    test   F  clean_seed2     76.0
  chb15    test   F  clean_seed3     76.0
  chb17    test   F clean_seed42     88.0
  chb17    test   F  clean_seed1     88.0
  chb17    test   F  clean_seed3     88.0
  chb15    test   F clean_seed42    112.0
  chb15    test   F  clean_seed1    112.0
  chb15    test   F  clean_seed2    112.0
  chb15    test   F  clean_seed3    112.0
  chb15    test   F  clean_seed1    124.0
  chb15    test   F  clean_seed1    180.0
  chb15    test   F  clean_seed2    180.0
  chb15    test   F  clean_seed3    180.0
  chb15    test   F clean_seed42    208.0
  chb15    test   F  clean_seed2    208.0
  chb16    test   G  clean_seed1      8.0
  chb16    test   G  clean_seed2      8.0
  chb16    test   G  clean_seed2      8.0
  chb06    test   G clean_seed42     16.0
  chb06    test   G  clean_seed3     16.0
  chb13    test   G clean_seed42     20.0
  chb13    test   G  clean_seed1     20.0
  chb13    test   G  clean_seed3     20.0
  chb14    test   G clean_seed42     20.0
  chb14    test   G  clean_seed1     20.0
  chb14    test   G  clean_seed2     20.0
  chb14    test   G  clean_seed3     20.0
  chb14    test   G clean_seed42     28.0
  chb14    test   G  clean_seed1     28.0
  chb14    test   G  clean_seed2     28.0
  chb14    test   G  clean_seed3     28.0
  chb15    test   G  clean_seed2     76.0
  chb17    test   G  clean_seed1     88.0
  chb15    test   G  clean_seed3    112.0
  chb17    test   G clean_seed42    116.0
  chb17    test   G  clean_seed3    116.0
  chb15    test   G  clean_seed3    124.0
  chb15    test   G  clean_seed1    160.0
  chb15    test   G  clean_seed1    180.0
  chb15    test   G  clean_seed2    192.0
  chb15    test   G  clean_seed3    208.0
```