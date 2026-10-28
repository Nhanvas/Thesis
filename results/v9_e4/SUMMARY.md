# V9-E4 -- kNN baseline (B4) on every CHB-MIT case

Full tables: `results/v9_e4/*.csv`. Code: `src/v9_e4_knn24.py` (new; reuses src/v9_e1_baselines.py, src/v9_e1b_calibrate.py (matched_curve_k only) and every frozen script they call, read-only).

24 cases, chb01-chb24, same file rules as the thesis (files missing one of the 18 channels skipped, e.g. chb12_27/28/29). chb21 is the same subject as chb01 (recorded 1.5 years later): every aggregate below is reported twice, once over all 24 cases and once with chb21 removed (23 subjects), plus separately for the former development (15) and former CHB-MIT test (8) groups; chb24 (1 case) sits outside both of those former groups.

Two k_B4 variants, both reported at every case and every aggregate: **loo** = leave-one-case-out (`p3_levers.calibrate()` UNCHANGED, median q_i(k) = 0.005, run on every OTHER case's smoothed member-mean-z signal; chb01 and chb21 exclude EACH OTHER too, so neither ever calibrates on the other); **fixed_dev** = k_B4 = 11.618333 (results/v9_e1b/calibration.json, calibrated once on the 15 development patients only, V9-E1b) -- loaded verbatim, not recomputed, for reference. Same floor/cap (clip(q_i(k), 0.005, 0.02)), smoothing (5), merge (90 s) and kernel-CPD localizer for both. Everything downstream of B4's own per-channel distance (e17b order statistics, percentile-mean final scalar, member-mean-z budget signal, localizer, SzCORE scorer) is the frozen P3 chain used unmodified by V9-E1/V9-E1b.


### Per-case table, all 24 cases

```
case    set    n_sz  med_dur  mean_dur  hard   k_loo       | tp/ref    FP  sens   prec   F1    FP/day  || fixed-dev sens  FP/day
chb01  dev       7    56.0     65.7  -       10.7091  |   7.0/   7    30  1.000  0.189  0.318   17.81  || 1.000   11.28
chb02  dev       3    84.0     60.0  -       10.7917  |   2.0/   3    28  0.667  0.067  0.121   19.08  || 0.667   19.08
chb03  test      7    56.0     60.6  -       10.7917  |   7.0/   7    17  1.000  0.292  0.452   10.77  || 1.000   10.77
chb04  dev       4   112.0     99.0  -       10.7917  |   4.0/   4   152  1.000  0.026  0.050   23.39  || 1.000   23.39
chb05  dev       5   116.0    114.4  -       10.6685  |   5.0/   5     5  1.000  0.500  0.667    3.09  || 1.000    2.47
chb06  test     10    16.0     18.0  Y       10.7917  |   2.0/  10    44  0.200  0.043  0.071   15.84  || 0.200   15.84
chb07  dev       3   100.0    110.7  -       10.6685  |   3.0/   3    68  1.000  0.042  0.081   24.38  || 1.000   21.15
chb08  dev       5   176.0    187.2  -       10.6685  |   5.0/   5    11  1.000  0.312  0.476   13.37  || 1.000    8.51
chb09  dev       4    70.0     73.0  -       10.6685  |   4.0/   4    33  1.000  0.108  0.195   11.68  || 1.000   10.62
chb10  dev       7    68.0     66.9  -       10.6685  |   7.0/   7    21  1.000  0.250  0.400   10.10  || 1.000    9.62
chb11  dev       3    36.0    272.0  -       10.7917  |   4.0/   5    13  0.800  0.235  0.364   10.21  || 0.800   10.21
chb12  dev      27    36.0     40.1  -       10.7917  |   7.0/  26    13  0.269  0.350  0.304   15.31  || 0.269   15.31
chb13  test     12    54.0     48.0  -       10.6685  |   1.0/  12    29  0.083  0.033  0.048   21.19  || 0.083   19.00
chb14  test      8    22.0     24.5  Y       10.7917  |   8.0/   8    27  1.000  0.229  0.372   24.98  || 1.000   24.98
chb15  test     20    94.0    103.0  -       10.6685  |   6.0/  20    25  0.300  0.194  0.235   15.21  || 0.200   13.39
chb16  test     10    12.0     11.2  Y       10.7917  |   1.0/  10    20  0.100  0.048  0.065   25.30  || 0.100   25.30
chb17  test      3    92.0     98.7  -       10.7917  |   3.0/   3    18  1.000  0.143  0.250   21.25  || 1.000   21.25
chb18  test      6    54.0     55.3  -       10.6685  |   5.0/   6    42  0.833  0.106  0.189   28.36  || 0.833   24.99
chb19  dev       3    84.0     82.7  -       10.6685  |   3.0/   3    35  1.000  0.079  0.146   28.13  || 1.000   21.70
chb20  dev       8    40.0     40.5  -       10.6685  |   8.0/   8    13  1.000  0.381  0.552   11.34  || 1.000    8.72
chb21  dev       4    56.0     53.0  -       10.7091  |   1.0/   4    29  0.250  0.033  0.059   21.91  || 0.250   21.91
chb22  dev       3    76.0     73.3  -       10.6685  |   3.0/   3    30  1.000  0.091  0.167   23.27  || 1.000   17.84
chb23  dev       7    64.0     62.3  -       10.7917  |   7.0/   7    12  1.000  0.368  0.538   10.89  || 1.000   10.89
chb24  chb24    16    28.0     34.8  -       10.7917  |  13.0/  16    16  0.812  0.448  0.578   18.16  || 0.812   18.16
```

## All 24 CHB-MIT cases (24 cases)

### Each k variant's balanced point (floor 0.005 / cap 0.02), after the CPD localizer

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
B4, leave-one-case-out k               116.0/ 186  731.0  0.624  0.137  0.225   18.07 | 0.763  0.190  0.279  17.71
B4, fixed dev-15 k (reference)         114.0/ 186  673.0  0.613  0.145  0.234   16.63 | 0.759  0.205  0.296  16.10
```

### Sensitivity by seizure duration bin (localized stage)

```
arm                                    <=20s      21-40s     41-80s     >80s
B4, leave-one-case-out k               9/31       28/51      41/59      37/44    
B4, fixed dev-15 k (reference)         9/31       28/51      40/59      36/44    
```

### Patient bootstrap 95% CI for the per-case-mean sensitivity (B = 10,000)

```
B4, leave-one-case-out k               0.763  [0.619, 0.888]
B4, fixed dev-15 k (reference)         0.759  [0.612, 0.886]
```

### Localizer onset/offset |error| (median seconds, pooled matched events)

```
B4, leave-one-case-out k               onset median   4.0 s IQR [0.0, 8.0] bias  +0.0 | offset median  24.0 s IQR [6.0, 44.0] bias +16.0
B4, fixed dev-15 k (reference)         onset median   4.0 s IQR [4.0, 12.0] bias  +0.0 | offset median  24.0 s IQR [4.0, 44.0] bias +16.0
```

### System-stage curve (sweep k, per-case budget + CPD localizer every point): per-case-mean sensitivity @ FP/day 20.0, 27.5, 44.0

```
B4, leave-one-case-out k               20.0:0.770+-0.000  27.5:0.800+-0.000  44.0:0.869+-0.000
B4, fixed dev-15 k (reference)         20.0:0.772+-0.000  27.5:0.811+-0.000  44.0:0.872+-0.000
```

## All cases with chb21 removed (23 subjects) (23 cases)

### Each k variant's balanced point (floor 0.005 / cap 0.02), after the CPD localizer

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
B4, leave-one-case-out k               115.0/ 182  702.0  0.632  0.141  0.230   17.94 | 0.785  0.197  0.289  17.53
B4, fixed dev-15 k (reference)         113.0/ 182  644.0  0.621  0.149  0.241   16.46 | 0.781  0.212  0.306  15.85
```

### Sensitivity by seizure duration bin (localized stage)

```
arm                                    <=20s      21-40s     41-80s     >80s
B4, leave-one-case-out k               9/30       28/51      41/57      36/43    
B4, fixed dev-15 k (reference)         9/30       28/51      40/57      35/43    
```

### Patient bootstrap 95% CI for the per-case-mean sensitivity (B = 10,000)

```
B4, leave-one-case-out k               0.785  [0.645, 0.909]
B4, fixed dev-15 k (reference)         0.781  [0.638, 0.907]
```

### Localizer onset/offset |error| (median seconds, pooled matched events)

```
B4, leave-one-case-out k               onset median   4.0 s IQR [0.0, 8.0] bias  +0.0 | offset median  24.0 s IQR [5.0, 44.0] bias +16.0
B4, fixed dev-15 k (reference)         onset median   4.0 s IQR [4.0, 12.0] bias  +0.0 | offset median  24.0 s IQR [4.0, 44.0] bias +16.0
```

### System-stage curve (sweep k, per-case budget + CPD localizer every point): per-case-mean sensitivity @ FP/day 20.0, 27.5, 44.0

```
B4, leave-one-case-out k               20.0:0.793+-0.000  27.5:0.822+-0.000  44.0:0.871+-0.000
B4, fixed dev-15 k (reference)         20.0:0.795+-0.000  27.5:0.826+-0.000  44.0:0.872+-0.000
```

## Former development group (15 patients) (15 cases)

### Each k variant's balanced point (floor 0.005 / cap 0.02), after the CPD localizer

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
B4, leave-one-case-out k                70.0/  94  493.0  0.745  0.124  0.213   17.60 | 0.866  0.202  0.296  16.26
B4, fixed dev-15 k (reference)          70.0/  94  446.0  0.745  0.136  0.230   15.92 | 0.866  0.227  0.325  14.18
```

### Sensitivity by seizure duration bin (localized stage)

```
arm                                    <=20s      21-40s     41-80s     >80s
B4, leave-one-case-out k               0/3        17/30      23/29      29/31    
B4, fixed dev-15 k (reference)         0/3        17/30      23/29      29/31    
```

### Patient bootstrap 95% CI for the per-case-mean sensitivity (B = 10,000)

```
B4, leave-one-case-out k               0.866  [0.720, 0.978]
B4, fixed dev-15 k (reference)         0.866  [0.720, 0.978]
```

### Localizer onset/offset |error| (median seconds, pooled matched events)

```
B4, leave-one-case-out k               onset median   4.0 s IQR [0.0, 8.0] bias  +0.0 | offset median  32.0 s IQR [12.0, 48.0] bias +28.0
B4, fixed dev-15 k (reference)         onset median   4.0 s IQR [0.0, 12.0] bias  +0.0 | offset median  32.0 s IQR [12.0, 48.0] bias +28.0
```

### System-stage curve (sweep k, per-case budget + CPD localizer every point): per-case-mean sensitivity @ FP/day 20.0, 27.5, 44.0

```
B4, leave-one-case-out k               20.0:0.872+-0.000  27.5:0.899+-0.000  44.0:0.978+-0.000
B4, fixed dev-15 k (reference)         20.0:0.877+-0.000  27.5:0.919+-0.000  44.0:0.979+-0.000
```

## Former CHB-MIT test group (8 patients) (8 cases)

### Each k variant's balanced point (floor 0.005 / cap 0.02), after the CPD localizer

```
arm                                    tp/ref    FP   sens   prec    F1    FP/day | s-sens  s-prec  s-F1  s-FP/day
B4, leave-one-case-out k                33.0/  76  222.0  0.434  0.129  0.199   19.19 | 0.565  0.136  0.210  20.36
B4, fixed dev-15 k (reference)          31.0/  76  211.0  0.408  0.128  0.195   18.24 | 0.552  0.133  0.205  19.44
```

### Sensitivity by seizure duration bin (localized stage)

```
arm                                    <=20s      21-40s     41-80s     >80s
B4, leave-one-case-out k               7/24       3/12       15/27      8/13     
B4, fixed dev-15 k (reference)         7/24       3/12       14/27      7/13     
```

### Patient bootstrap 95% CI for the per-case-mean sensitivity (B = 10,000)

```
B4, leave-one-case-out k               0.565  [0.283, 0.846]
B4, fixed dev-15 k (reference)         0.552  [0.256, 0.846]
```

### Localizer onset/offset |error| (median seconds, pooled matched events)

```
B4, leave-one-case-out k               onset median   4.0 s IQR [4.0, 16.0] bias  +0.0 | offset median  16.0 s IQR [4.0, 28.0] bias  +8.0
B4, fixed dev-15 k (reference)         onset median   4.0 s IQR [4.0, 16.0] bias  +0.0 | offset median  16.0 s IQR [6.0, 30.0] bias  +8.0
```

### System-stage curve (sweep k, per-case budget + CPD localizer every point): per-case-mean sensitivity @ FP/day 20.0, 27.5, 44.0

```
B4, leave-one-case-out k               20.0:0.569+-0.000  27.5:0.613+-0.000  44.0:0.657+-0.000
B4, fixed dev-15 k (reference)         20.0:0.564+-0.000  27.5:0.607+-0.000  44.0:0.666+-0.000
```

## Hard-patient table (mean seizure duration < 30 s, loo k, localized stage)

- hard (mean seizure duration < 30 s): chb06, chb14, chb16
- other: chb01, chb02, chb03, chb04, chb05, chb07, chb08, chb09, chb10, chb11, chb12, chb13, chb15, chb17, chb18, chb19, chb20, chb21, chb22, chb23, chb24
- per-case sensitivity: hard mean 0.433 (n=3), other mean 0.810 (n=21)
- Mann-Whitney U (two-sided, descriptive, not a gate): U = 16.5, p = 0.1576

## Runtime measured
calibrate(): 14s (reads 24 cached m-signal arrays, 24 independent bisections). Per-subject --prep and --eval-one timing: each call's own stdout (printed elapsed seconds + peak RAM); every step is resumable (per-subject m-signal cache under results/v9_e4/_m/, part file under results/v9_e4/_parts/).